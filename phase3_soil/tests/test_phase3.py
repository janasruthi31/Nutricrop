import json
import os
import shutil
import sqlite3
import tempfile
import unittest

from phase3_soil import config, service, units
from phase3_soil.classification import classify
from phase3_soil.extraction import extract_fields, parse_report_date, redact_text
from phase3_soil.service import SoilError
from phase3_soil.validation import validate_field, validate_profile
from phase3_soil.tests import fixtures as fx

FARMER = "farmer_001"


def confirm_body(run, **over):
    """Farmer accepts every OCR field exactly as extracted."""
    fields = {}
    for f in run["fields"]:
        if f["value"] is not None:
            fields[f["field"]] = {"value": f["value"], "unit": f["unit"], "test_method": f["test_method"], "action": "accept"}
    body = {"document_id": run["document_id"], "fields": fields, "district": run["metadata"].get("district"),
            "test_date": run["metadata"].get("test_date"), "sample_id": run["metadata"].get("sample_id"),
            "village": run["metadata"].get("village"), "farmer_confirmed": True}
    body.update(over)
    return body


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "t.sqlite3")
        self._old = config.STORAGE_DIR
        config.STORAGE_DIR = os.path.join(self.tmp, "store")

    def tearDown(self):
        config.STORAGE_DIR = self._old
        shutil.rmtree(self.tmp, ignore_errors=True)

    def ocr(self, data):
        up = service.upload(FARMER, data, self.db)
        return service.run_ocr(FARMER, up["document_id"], self.db)

    @staticmethod
    def fld(run, key):
        return next(f for f in run["fields"] if f["field"] == key)


# ---------------------------------------------------------------- the 15 required scenarios (real OCR)
class TestRequiredScenarios(Base):
    def test_01_valid_soil_report(self):
        run = self.ocr(fx.png_bytes(fx.FULL))
        self.assertEqual(run["status"], "extracted")
        self.assertTrue(run["verification_required"])
        self.assertEqual(run["banner"], "Extracted \u2014 Please Verify")
        got = {f["field"]: (f["value"], f["unit"]) for f in run["fields"] if f["value"] is not None}
        self.assertEqual(got["nitrogen"], (280.0, "kg/ha"))
        self.assertEqual(got["phosphorus"], (18.0, "kg/ha"))
        self.assertEqual(got["potassium"], (160.0, "kg/ha"))
        self.assertEqual(got["ph"][0], 6.8)
        self.assertEqual(got["organic_carbon"], (0.62, "%"))
        self.assertEqual(got["ec"], (0.45, "dS/m"))
        self.assertEqual(run["metadata"]["district"], "Tiruppur")
        self.assertEqual(run["metadata"]["test_date"], "2025-03-12")
        self.assertEqual(run["review_only"]["farmer_name"], "Ravi Kumar")
        self.assertIsNotNone(self.fld(run, "nitrogen")["ocr_confidence"])

    def test_02_missing_n(self):
        run = self.ocr(fx.png_bytes(fx.replace_row(fx.FULL, "Available Nitrogen")))
        n = self.fld(run, "nitrogen")
        self.assertEqual(n["status"], "missing")
        self.assertIsNone(n["value"])
        self.assertTrue(any(w["code"] == "missing_primary_values" for w in run["warnings"]))
        res = service.confirm(FARMER, confirm_body(run), self.db)  # confirming without N is allowed...
        self.assertIn("nitrogen", res["soil_profile"]["missing_primary"])
        self.assertFalse(res["soil_profile"]["phase4_readiness"]["ready"])  # ...but is flagged for Phase 4
        self.assertIsNone(res["soil_profile"]["nitrogen"]["value"])

    def test_03_missing_p(self):
        run = self.ocr(fx.png_bytes(fx.replace_row(fx.FULL, "Available Phosphorus")))
        self.assertEqual(self.fld(run, "phosphorus")["status"], "missing")
        self.assertIn("phosphorus", service.confirm(FARMER, confirm_body(run), self.db)["soil_profile"]["missing_primary"])

    def test_04_missing_k(self):
        run = self.ocr(fx.png_bytes(fx.replace_row(fx.FULL, "Available Potassium")))
        self.assertEqual(self.fld(run, "potassium")["status"], "missing")
        self.assertIn("potassium", service.confirm(FARMER, confirm_body(run), self.db)["soil_profile"]["missing_primary"])

    def test_05_invalid_ph(self):
        run = self.ocr(fx.png_bytes(fx.replace_row(fx.FULL, "Soil pH", "Soil pH (1:2.5)  16.8")))
        self.assertEqual(self.fld(run, "ph")["value"], 16.8)
        with self.assertRaises(SoilError) as cm:  # farmer "accepting" an impossible value must be blocked
            service.confirm(FARMER, confirm_body(run), self.db)
        self.assertEqual(cm.exception.code, "VALIDATION_FAILED")
        self.assertEqual(self.fld(run, "ph")["status"], "invalid")

    def test_06_invalid_numeric_value(self):
        # Tesseract itself may "repair" 28O to 280 on a rendered image, so the garbled-number path is tested on OCR text
        # lines directly (deterministic), and through the service on a value that really is invalid.
        ex = extract_fields([{"text": "Available Nitrogen (N)  28O  kg/ha", "words": []}])
        self.assertIsNone(ex["nitrogen"]["value"])
        self.assertEqual(ex["nitrogen"]["ocr_value"], "28O")
        self.assertTrue(any(i["code"] == "ocr_parse_error" for i in ex["nitrogen"]["extraction_issues"]))
        from phase3_soil.service import _field_view
        v = _field_view("nitrogen", ex["nitrogen"])
        self.assertEqual(v["status"], "uncertain")
        self.assertIsNone(v["value"])
        r = validate_field("nitrogen", "abc", "kg/ha")
        self.assertEqual(r["status"], "invalid")
        self.assertEqual(r["issues"][0]["code"], "not_numeric")
        run = self.ocr(fx.png_bytes(fx.replace_row(fx.FULL, "Available Nitrogen", "Available Nitrogen (N)  -50  kg/ha")))
        body = confirm_body(run)
        body["fields"]["nitrogen"]["value"] = "28x"  # farmer types garbage
        with self.assertRaises(SoilError) as cm:
            service.confirm(FARMER, body, self.db)
        self.assertEqual(cm.exception.code, "VALIDATION_FAILED")

    def test_07_unknown_unit(self):
        run = self.ocr(fx.png_bytes(fx.replace_row(fx.FULL, "Available Nitrogen", "Available Nitrogen (N)  280")))
        n = self.fld(run, "nitrogen")
        self.assertIsNone(n["unit"])
        self.assertEqual(n["status"], "uncertain")
        self.assertTrue(any(i["code"] in ("unit_not_found", "unknown_unit") for i in n["issues"]))
        with self.assertRaises(SoilError):  # cannot be confirmed without a unit the farmer supplies
            service.confirm(FARMER, confirm_body(run), self.db)
        body = confirm_body(run)
        body["fields"]["nitrogen"].update(unit="kg/ha", action="edit")
        self.assertEqual(service.confirm(FARMER, body, self.db)["status"], "validated")

    def test_08_olsen_p(self):
        run = self.ocr(fx.png_bytes(fx.FULL))
        p = self.fld(run, "phosphorus")
        self.assertEqual(p["test_method"], "Olsen")
        self.assertEqual(p["classification"], "Medium")  # 18 in 11-22
        self.assertEqual(service.confirm(FARMER, confirm_body(run), self.db)["soil_profile"]["phosphorus"]["method"], "Olsen")

    def test_09_bray_p(self):
        rows = fx.replace_row(fx.FULL, "Available Phosphorus", "Available Phosphorus (P) Bray  30  kg/ha")
        run = self.ocr(fx.png_bytes(rows))
        p = self.fld(run, "phosphorus")
        self.assertEqual(p["test_method"], "Bray")
        self.assertEqual(p["classification"], "Medium")  # 30 in 24.2-49.7
        self.assertEqual(classify("phosphorus", 18, "kg/ha", "Bray"), "Low")  # same 18 is Low under Bray, Medium under Olsen
        self.assertEqual(classify("phosphorus", 18, "kg/ha", "Olsen"), "Medium")

    def test_10_ocr_correction(self):
        rows = fx.replace_row(fx.FULL, "Available Potassium", "Available Potassium (K)  160  kg/ha")
        run = self.ocr(fx.png_bytes(rows))
        body = confirm_body(run)
        body["fields"]["potassium"].update(value=190, action="edit")  # farmer corrects 160 -> 190
        res = service.confirm(FARMER, body, self.db)
        a = res["soil_profile"]["audit"]["potassium"]
        self.assertEqual(a["ocr_value"], "160")
        self.assertEqual(a["confirmed_value"], 190.0)
        self.assertTrue(a["modified_by_user"])
        self.assertFalse(res["soil_profile"]["audit"]["nitrogen"]["modified_by_user"])
        self.assertEqual(res["soil_profile"]["potassium"]["classification"], "Medium")
        with sqlite3.connect(self.db) as con:  # audit trail persisted
            row = con.execute("SELECT ocr_value, confirmed_value, modified_by_user FROM soil_profile_fields WHERE field='potassium'").fetchone()
        self.assertEqual(row, ("160", 190.0, 1))

    def test_11_manual_entry(self):
        body = {"fields": {"nitrogen": {"value": 250, "unit": "kg/ha"}, "phosphorus": {"value": 9, "unit": "kg/ha", "test_method": "Olsen"},
                           "potassium": {"value": 180, "unit": "kg/ha"}, "ph": {"value": 7.2}, "organic_carbon": {"value": 0.8, "unit": "%"}},
                "district": "Salem", "test_date": "2025-01-10", "farmer_confirmed": True}
        res = service.confirm(FARMER, body, self.db)
        sp = res["soil_profile"]
        self.assertEqual(sp["source"], "manual")
        self.assertEqual(sp["verification_status"], "farmer_confirmed")
        self.assertEqual((sp["nitrogen"]["classification"], sp["phosphorus"]["classification"], sp["potassium"]["classification"],
                          sp["organic_carbon"]["classification"]), ("Low", "Low", "Medium", "High"))
        self.assertTrue(sp["phase4_readiness"]["ready"])
        self.assertIsNone(sp["ec"]["value"])
        self.assertEqual(sp["ph"], 7.2)
        self.assertEqual(service.get_profile(FARMER, res["soil_profile_id"], self.db)["soil_profile_id"], res["soil_profile_id"])

    def test_12_invalid_file(self):
        for data, code in [(b"MZ\x90\x00 not a soil report", "UNSUPPORTED_FILE_TYPE"), (b"", "EMPTY_FILE"),
                           (b"%PDF-1.4 this is garbage, not a pdf", "CORRUPTED_PDF"), (b"\xff\xd8\xff garbage", "CORRUPTED_IMAGE"),
                           (b"\x89PNG\r\n\x1a\n broken", "CORRUPTED_IMAGE")]:
            with self.assertRaises(SoilError, msg=code) as cm:
                service.upload(FARMER, data, self.db)
            self.assertEqual(cm.exception.code, code)
        old = config.MAX_UPLOAD_BYTES
        config.MAX_UPLOAD_BYTES = 100
        try:
            with self.assertRaises(SoilError) as cm:
                service.upload(FARMER, fx.png_bytes(fx.FULL), self.db)
            self.assertEqual(cm.exception.code, "FILE_TOO_LARGE")
        finally:
            config.MAX_UPLOAD_BYTES = old
        self.assertEqual(os.listdir(config.STORAGE_DIR) if os.path.isdir(config.STORAGE_DIR) else [], [])  # nothing stored

    def test_13_empty_ocr(self):
        up = service.upload(FARMER, fx.blank_png(), self.db)
        with self.assertRaises(SoilError) as cm:
            service.run_ocr(FARMER, up["document_id"], self.db)
        self.assertEqual(cm.exception.code, "OCR_EMPTY")
        self.assertIn("enter the values manually", cm.exception.message)

    def test_14_duplicate_submission(self):
        run = self.ocr(fx.png_bytes(fx.FULL))
        first = service.confirm(FARMER, confirm_body(run), self.db)
        with self.assertRaises(SoilError) as cm:
            service.confirm(FARMER, confirm_body(run), self.db)
        self.assertEqual(cm.exception.code, "DUPLICATE_SUBMISSION")
        self.assertEqual(cm.exception.details["soil_profile_id"], first["soil_profile_id"])
        again = service.upload(FARMER, fx.png_bytes(fx.FULL), self.db)  # same file re-uploaded
        self.assertTrue(again["duplicate_document"])

    def test_15_successful_validation_pdf_and_jpeg(self):
        for name, data in (("pdf", fx.pdf_bytes(fx.FULL)), ("jpeg", fx.jpeg_bytes(fx.FULL))):
            with self.subTest(name):
                run = self.ocr(data)
                self.assertEqual(self.fld(run, "nitrogen")["value"], 280.0)
                body = confirm_body(run, sample_id=f"S-{name}")
                res = service.confirm(FARMER, body, self.db)
                self.assertEqual(res["status"], "validated")
                self.assertEqual(res["soil_profile"]["verification_status"], "farmer_confirmed")
                self.assertTrue(res["soil_profile"]["phase4_readiness"]["ready"])


# ---------------------------------------------------------------- additional unit tests
class TestUnitsAndRules(unittest.TestCase):
    def test_safe_units(self):
        self.assertEqual(units.normalize_value_unit("zinc", 1.2, "ppm")[:2], (1.2, "mg/kg"))
        self.assertEqual(units.normalize_value_unit("organic_carbon", 6.2, "g/kg")[:2], (0.62, "%"))
        self.assertEqual(units.normalize_value_unit("ec", 450, "uS/cm")[:2], (0.45, "dS/m"))
        self.assertEqual(units.normalize_value_unit("ec", 0.45, "mmhos/cm")[:2], (0.45, "dS/m"))
        v, u, *_ = units.normalize_value_unit("nitrogen", 280, "furlongs")
        self.assertIsNone(u)

    def test_no_mgkg_to_kgha_conversion(self):
        r = validate_field("nitrogen", 40, "mg/kg")
        self.assertEqual((r["value"], r["unit"]), (40.0, "mg/kg"))  # untouched
        self.assertIsNone(r["classification"])  # TNAU kg/ha thresholds are NOT applied to mg/kg
        self.assertIsNone(validate_field("phosphorus", 18, "mg/kg", "Olsen")["classification"])

    def test_p_method_never_guessed(self):
        r = validate_field("phosphorus", 18, "kg/ha", None)
        self.assertEqual(r["status"], "uncertain")
        self.assertIsNone(r["classification"])
        c = validate_field("phosphorus", 18, "kg/ha", None, stage="confirm")
        self.assertEqual(c["status"], "valid")
        self.assertIsNone(c["classification"])
        self.assertEqual(validate_field("phosphorus", 18, "kg/ha", "Mehlich", stage="confirm")["status"], "invalid")

    def test_tnau_boundaries(self):
        cases = [("nitrogen", 279.9, "Low"), ("nitrogen", 280, "Medium"), ("nitrogen", 450, "Medium"), ("nitrogen", 450.1, "High"),
                 ("potassium", 117.9, "Low"), ("potassium", 118, "Medium"), ("potassium", 280, "Medium"), ("potassium", 281, "High"),
                 ("organic_carbon", 0.49, "Low"), ("organic_carbon", 0.5, "Medium"), ("organic_carbon", 0.75, "Medium"), ("organic_carbon", 0.76, "High")]
        for k, v, want in cases:
            self.assertEqual(classify(k, v, "%" if k == "organic_carbon" else "kg/ha"), want, (k, v))
        self.assertEqual(classify("phosphorus", 10.9, "kg/ha", "Olsen"), "Low")
        self.assertEqual(classify("phosphorus", 22.1, "kg/ha", "Olsen"), "High")
        self.assertEqual(classify("phosphorus", 24.1, "kg/ha", "Bray"), "Low")
        self.assertEqual(classify("phosphorus", 49.8, "kg/ha", "Bray"), "High")
        self.assertIsNone(classify("zinc", 1, "mg/kg"))

    def test_empty_and_negative(self):
        self.assertEqual(validate_field("nitrogen", "", "kg/ha")["status"], "missing")
        self.assertEqual(validate_field("nitrogen", None, None)["status"], "missing")
        self.assertEqual(validate_field("nitrogen", -5, "kg/ha")["status"], "invalid")
        self.assertEqual(validate_field("nitrogen", float("nan"), "kg/ha")["status"], "invalid")
        self.assertEqual(validate_field("ph", 6.8, "kg/ha", stage="confirm")["status"], "invalid")

    def test_unusual_value_review_vs_confirm(self):
        self.assertEqual(validate_field("nitrogen", 3000, "kg/ha")["status"], "uncertain")
        c = validate_field("nitrogen", 3000, "kg/ha", stage="confirm")
        self.assertEqual(c["status"], "valid")
        self.assertTrue(any(i["code"] == "unusual_value" for i in c["issues"]))

    def test_metadata_checks(self):
        r = validate_profile({"fields": {"ph": {"value": 7}}, "district": "Trichy", "test_date": "2999-01-01", "crop": "Rice"}, "confirm")
        self.assertFalse(r["ok"])
        self.assertEqual(r["metadata"]["district"], "Tiruchirapalli")
        r = validate_profile({"fields": {"ph": {"value": 7}}, "district": "Atlantis", "test_date": "2025-02-30", "crop": "Dragonfruit"}, "confirm")
        codes = {i["code"] for i in r["metadata_issues"]}
        self.assertTrue({"unknown_district", "invalid_test_date", "unknown_crop"} <= codes)
        ok = validate_profile({"fields": {"ph": {"value": 7}}, "district": "salem", "test_date": "2025-02-01", "crop": "rice"}, "confirm")
        self.assertTrue(ok["ok"])
        self.assertEqual(ok["metadata"]["crop"], "Rice")

    def test_no_values_blocks_confirm(self):
        self.assertFalse(validate_profile({"fields": {}}, "confirm")["ok"])


class TestExtractionText(unittest.TestCase):
    def L(self, *t):
        return [{"text": x, "words": []} for x in t]

    def test_ratio_not_taken_as_value(self):
        f = extract_fields(self.L("Soil pH (1:2.5) 6.8", "EC (1:2) 0.3 dS/m"))
        self.assertEqual(f["ph"]["value"], 6.8)
        self.assertEqual(f["ec"]["value"], 0.3)

    def test_ppm_and_gkg_extracted_raw(self):
        f = extract_fields(self.L("Zinc (Zn) 0.9 ppm", "Organic Carbon 6.2 g/kg"))
        self.assertEqual((f["zinc"]["value"], f["zinc"]["unit"]), (0.9, "ppm"))
        self.assertIsNone(f["zinc"]["ocr_confidence"])  # no word data -> null, never fabricated

    def test_decimal_comma_and_thousands(self):
        f = extract_fields(self.L("pH 6,8", "Available Nitrogen 1,200 kg/ha"))
        self.assertEqual(f["ph"]["value"], 6.8)
        self.assertTrue(any(i["code"] == "decimal_comma" for i in f["ph"]["extraction_issues"]))
        self.assertEqual(f["nitrogen"]["value"], 1200.0)

    def test_p2o5_flagged(self):
        f = extract_fields(self.L("Available Phosphorus (P2O5) 40 kg/ha"))
        self.assertEqual(f["phosphorus"]["value"], 40.0)
        self.assertTrue(any(i["code"] == "oxide_basis" for i in f["phosphorus"]["extraction_issues"]))

    def test_method_from_document_only_if_unambiguous(self):
        one = extract_fields(self.L("Phosphorus determined by Olsen method", "Available Phosphorus 14 kg/ha"))
        self.assertEqual(one["phosphorus"]["test_method"], "Olsen")
        both = extract_fields(self.L("Olsen Bray", "Available Phosphorus 14 kg/ha"))
        self.assertIsNone(both["phosphorus"]["test_method"])
        none = extract_fields(self.L("Available Phosphorus 14 kg/ha"))
        self.assertIsNone(none["phosphorus"]["test_method"])

    def test_dates_and_redaction(self):
        self.assertEqual(parse_report_date("12/03/2025"), "2025-03-12")
        self.assertEqual(parse_report_date("5 Jan 2024"), "2024-01-05")
        self.assertIsNone(parse_report_date("garbage"))
        red = redact_text("Farmer Name : Ravi Kumar\nMobile : 9876543210\nNote 98765 43210 call\nNitrogen 280")
        self.assertNotIn("Ravi", red)
        self.assertNotIn("9876543210", red)
        self.assertIn("Nitrogen 280", red)


class TestPrivacyAndAccess(Base):
    def test_farmer_isolation_and_privacy(self):
        run = self.ocr(fx.png_bytes(fx.FULL))
        res = service.confirm(FARMER, confirm_body(run), self.db)
        with self.assertRaises(SoilError) as cm:
            service.get_profile("someone_else", res["soil_profile_id"], self.db)
        self.assertEqual(cm.exception.code, "PROFILE_NOT_FOUND")
        with self.assertRaises(SoilError):
            service.run_ocr("someone_else", run["document_id"], self.db)
        blob = json.dumps(res)
        self.assertNotIn("Ravi", blob)  # farmer name never persisted/returned in the profile
        with sqlite3.connect(self.db) as con:
            txt = con.execute("SELECT raw_text_redacted FROM soil_ocr_results").fetchone()[0]
        self.assertNotIn("Ravi", txt)
        for fn in os.listdir(config.STORAGE_DIR):  # server-generated names, owner-only permissions
            if os.name != "nt":
                self.assertEqual(oct(os.stat(os.path.join(config.STORAGE_DIR, fn)).st_mode & 0o777), "0o600")


    def test_confirmation_flag_required_and_reject_action(self):
        run = self.ocr(fx.png_bytes(fx.FULL))
        b = confirm_body(run)
        b["farmer_confirmed"] = False
        with self.assertRaises(SoilError) as cm:
            service.confirm(FARMER, b, self.db)
        self.assertEqual(cm.exception.code, "CONFIRMATION_REQUIRED")
        b = confirm_body(run)
        b["fields"]["ec"]["action"] = "reject"
        res = service.confirm(FARMER, b, self.db)
        self.assertIsNone(res["soil_profile"]["ec"]["value"])
        self.assertTrue(res["soil_profile"]["audit"]["ec"]["modified_by_user"])
        self.assertEqual(res["soil_profile"]["audit"]["ec"]["ocr_value"], "0.45")

    def test_ocr_not_run_and_unknown_field(self):
        up = service.upload(FARMER, fx.png_bytes(fx.FULL), self.db)
        with self.assertRaises(SoilError) as cm:
            service.confirm(FARMER, {"document_id": up["document_id"], "fields": {"ph": {"value": 7}}, "farmer_confirmed": True}, self.db)
        self.assertEqual(cm.exception.code, "OCR_NOT_RUN")
        with self.assertRaises(SoilError) as cm:
            service.validate({"fields": {"selenium": {"value": 1}}})
        self.assertEqual(cm.exception.code, "UNKNOWN_FIELD")

    def test_blurry_image_warns_or_fails_gracefully(self):
        up = service.upload(FARMER, fx.png_bytes(fx.FULL, blur=True), self.db)
        try:
            run = service.run_ocr(FARMER, up["document_id"], self.db)
            self.assertTrue(run["verification_required"])  # whatever was read still needs verification
        except SoilError as e:
            self.assertIn(e.code, ("OCR_EMPTY", "OCR_NO_FIELDS"))
            self.assertIn("manually", e.message)


if __name__ == "__main__":
    unittest.main()
