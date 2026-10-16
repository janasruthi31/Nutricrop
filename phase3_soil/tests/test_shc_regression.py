"""
Regression and validation test suite for Soil Health Card (SHC) extraction,
unit validation, parameter mapping, and section separation.
"""
import os
import shutil
import tempfile
import unittest

from phase3_soil import config, service
from phase3_soil.extraction import extract_fields, extract_metadata, normalize_tamil_text
from phase3_soil.tnau_reference import FIELDS
from phase3_soil.validation import INVALID, MISSING, UNCERTAIN, VALID, validate_field

FIXTURE_PDF = os.path.join(os.path.dirname(__file__), "SHC-24.08.2026.pdf")
FARMER_ID = "farmer_shc_test"


class TestSHCRegression(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.db = os.path.join(self.tmp, "test_shc.sqlite3")
        self._old_storage = config.STORAGE_DIR
        config.STORAGE_DIR = os.path.join(self.tmp, "store")

    def tearDown(self):
        config.STORAGE_DIR = self._old_storage
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_01_sample_pdf_reference_values_and_units(self):
        """Verifies exact extraction of all 12 reference parameters from SHC-24.08.2026.pdf."""
        self.assertTrue(os.path.exists(FIXTURE_PDF), f"Fixture PDF not found at {FIXTURE_PDF}")
        with open(FIXTURE_PDF, "rb") as f:
            pdf_bytes = f.read()

        up = service.upload(FARMER_ID, pdf_bytes, self.db)
        run = service.run_ocr(FARMER_ID, up["document_id"], self.db)

        self.assertEqual(run["status"], "extracted")
        fields = {f["field"]: f for f in run["fields"]}

        # 12 Target Parameters
        expected = {
            "nitrogen": (39.0, "kg/acre"),
            "phosphorus": (4.0, "kg/acre"),
            "potassium": (259.0, "kg/acre"),
            "ph": (7.3, None),
            "ec": (0.41, "dS/m"),
            "organic_carbon": (0.45, "%"),
            "sulphur": (5.0, "kg/acre"),
            "zinc": (0.43, "kg/acre"),
            "iron": (1.9, "kg/acre"),
            "manganese": (2.59, "kg/acre"),
            "copper": (0.5, "kg/acre"),
            "boron": (0.56, "kg/acre"),
        }

        for param, (exp_val, exp_unit) in expected.items():
            self.assertIn(param, fields, f"Missing extracted field: {param}")
            fld = fields[param]
            self.assertAlmostEqual(fld["value"], exp_val, places=2,
                                   msg=f"Value mismatch for {param}: expected {exp_val}, got {fld['value']}")
            self.assertEqual(fld["unit"], exp_unit,
                             msg=f"Unit mismatch for {param}: expected {exp_unit}, got {fld['unit']}")

        # Metadata
        meta = run["metadata"]
        self.assertEqual(meta.get("crop"), "groundnut")
        self.assertEqual(meta.get("farm_area"), 1.0)
        self.assertEqual(meta.get("farm_area_unit"), "acre")
        self.assertEqual(meta.get("district"), "Erode")
        self.assertEqual(meta.get("sample_id"), "TN/ERD/02488")
        self.assertEqual(meta.get("village"), "வரதநல்லூர்")

        review_meta = run.get("review_only", {})
        self.assertEqual(review_meta.get("farmer_name"), "K.SELVAN")
        self.assertEqual(review_meta.get("survey_number"), "41 / 9")

    def test_02_prevent_incorrect_fertilizer_rate_mapping(self):
        """Ensures fertilizer recommendation rates (e.g. Urea 11, Potash 25, K 15, Zn 50ml/10kg) are not captured as soil test results."""
        with open(FIXTURE_PDF, "rb") as f:
            pdf_bytes = f.read()

        up = service.upload(FARMER_ID, pdf_bytes, self.db)
        run = service.run_ocr(FARMER_ID, up["document_id"], self.db)
        fields = {f["field"]: f for f in run["fields"]}

        # Potassium must be soil test 259, NOT fertilizer dose 15 or Potash 25
        self.assertEqual(fields["potassium"]["value"], 259.0)
        self.assertNotEqual(fields["potassium"]["value"], 15.0)
        self.assertNotEqual(fields["potassium"]["value"], 25.0)

        # Nitrogen must be 39, NOT fertilizer dose 14 or Urea 11
        self.assertEqual(fields["nitrogen"]["value"], 39.0)
        self.assertNotEqual(fields["nitrogen"]["value"], 14.0)
        self.assertNotEqual(fields["nitrogen"]["value"], 11.0)

        # Zinc must be 0.43, NOT bio-fertilizer dose 50 or zinc sulphate 10.00
        self.assertEqual(fields["zinc"]["value"], 0.43)
        self.assertNotEqual(fields["zinc"]["value"], 50.0)
        self.assertNotEqual(fields["zinc"]["value"], 10.0)

        # Percent unit must NEVER be attached to N, P, K, or micronutrients
        for p in ("nitrogen", "phosphorus", "potassium", "sulphur", "zinc", "iron", "manganese", "copper", "boron"):
            self.assertNotEqual(fields[p]["unit"], "%", f"Nutrient {p} was incorrectly assigned unit '%'")

    def test_03_prevent_sufficiency_range_mapping(self):
        """Verifies that sufficiency and benchmark ranges are not mistaken for measured values."""
        with open(FIXTURE_PDF, "rb") as f:
            pdf_bytes = f.read()

        up = service.upload(FARMER_ID, pdf_bytes, self.db)
        run = service.run_ocr(FARMER_ID, up["document_id"], self.db)
        fields = {f["field"]: f for f in run["fields"]}

        # pH must be 7.3, NOT 7.5 (which is the upper bound of the 6.0 - 7.5 range)
        self.assertEqual(fields["ph"]["value"], 7.3)
        self.assertNotEqual(fields["ph"]["value"], 7.5)

        # OC must be 0.45, NOT 0.75 (which is the upper bound of 0.51 - 0.75)
        self.assertEqual(fields["organic_carbon"]["value"], 0.45)
        self.assertNotEqual(fields["organic_carbon"]["value"], 0.75)

    def test_04_parameter_specific_unit_validation(self):
        """Verifies validation rules for kg/acre, kg/ha, mg/kg, dS/m, %, and unitless pH."""
        # kg/acre valid for N, P, K, S, micronutrients
        self.assertEqual(validate_field("nitrogen", 39.0, "kg/acre")["status"], VALID)
        self.assertEqual(validate_field("potassium", 259.0, "kg/acre")["status"], VALID)
        self.assertEqual(validate_field("sulphur", 5.0, "kg/acre")["status"], VALID)
        self.assertEqual(validate_field("zinc", 0.43, "kg/acre")["status"], VALID)
        self.assertEqual(validate_field("boron", 0.56, "kg/acre")["status"], VALID)

        # % rejected for N, P, K, S, micronutrients
        self.assertEqual(validate_field("nitrogen", 39.0, "%", stage="confirm")["status"], INVALID)
        self.assertEqual(validate_field("zinc", 0.43, "%", stage="confirm")["status"], INVALID)
        self.assertEqual(validate_field("boron", 0.56, "%", stage="confirm")["status"], INVALID)

        # pH is unitless
        self.assertEqual(validate_field("ph", 7.3, None)["status"], VALID)
        self.assertEqual(validate_field("ph", 7.3, "%", stage="confirm")["status"], INVALID)
        self.assertEqual(validate_field("ph", 7.3, "kg/ha", stage="confirm")["status"], INVALID)

        # EC in dS/m and uS/cm
        self.assertEqual(validate_field("ec", 0.41, "dS/m")["status"], VALID)
        self.assertEqual(validate_field("ec", 410.0, "uS/cm")["status"], VALID)

        # OC in % and g/kg
        self.assertEqual(validate_field("organic_carbon", 0.45, "%")["status"], VALID)
        self.assertEqual(validate_field("organic_carbon", 4.5, "g/kg")["status"], VALID)

    def test_05_missing_and_ambiguous_data_handling(self):
        """Verifies that missing and uncertain fields are handled correctly without fabricating values."""
        # Missing value
        v_missing = validate_field("nitrogen", None, "kg/ha")
        self.assertEqual(v_missing["status"], MISSING)
        self.assertIsNone(v_missing["value"])

        # Phosphorus without method in review stage is UNCERTAIN (requires farmer review)
        v_p = validate_field("phosphorus", 18.0, "kg/ha", method=None, stage="review")
        self.assertEqual(v_p["status"], UNCERTAIN)

        # Phosphorus with valid Olsen method is VALID
        v_p_olsen = validate_field("phosphorus", 18.0, "kg/ha", method="Olsen", stage="review")
        self.assertEqual(v_p_olsen["status"], VALID)

    def test_06_tamil_unicode_normalization(self):
        """Verifies that visual-order Tamil text with pre-base vowel signs is converted to canonical Unicode."""
        # Visual 'ேவ' (vowel sign EE + VA) -> Canonical 'வே' (VA + vowel sign EE)
        visual_va = "\u0bc7\u0bb5"
        canonical_va = "\u0bb5\u0bc7"
        self.assertEqual(normalize_tamil_text(visual_va), canonical_va)

        # Visual two-part 'போ' (vowel sign EE + PA + vowel sign AA) -> Canonical 'போ' (PA + vowel sign OO)
        visual_po = "\u0bc7\u0baa\u0bbe"
        canonical_po = "\u0baa\u0bcb"
        self.assertEqual(normalize_tamil_text(visual_po), canonical_po)


if __name__ == "__main__":
    unittest.main()
