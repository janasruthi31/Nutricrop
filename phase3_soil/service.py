"""Phase 3 business logic: upload -> OCR -> review payload -> validate -> confirm -> validated soil profile."""
import hashlib
import io
import json
import os
import re
import uuid
from datetime import datetime, timezone

import pytesseract
from PIL import Image
from pypdf import PdfReader
from pypdf.errors import PyPdfError

from . import config, db, ocr as ocr_mod
from .extraction import extract_fields, extract_metadata, redact_text
from .tnau_reference import FIELDS, PRIMARY, TNAU_SOURCE
from .validation import (INVALID, MISSING, UNCERTAIN, VALID, issue, parse_float, validate_field, validate_metadata,
                         validate_profile)

FARMER_ID_RE = re.compile(r"^[A-Za-z0-9_\-]{1,64}$")
BANNER = "Extracted \u2014 Please Verify"
MSG_UNREADABLE = "Unable to reliably read the soil report. Please enter the values manually."


class SoilError(Exception):
    def __init__(self, code, message, http_status=400, details=None):
        super().__init__(message)
        self.code, self.message, self.http_status, self.details = code, message, http_status, details or {}

    def to_dict(self):
        return {"error": {"code": self.code, "message": self.message, "details": self.details}}


def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def check_farmer(farmer_id):
    if not farmer_id or not FARMER_ID_RE.match(str(farmer_id)):
        raise SoilError("INVALID_FARMER_ID", "A valid farmer id is required.", 400)
    return str(farmer_id)


# ------------------------------------------------------------------ upload
def detect_kind(data):
    if data[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if b"%PDF-" in data[:1024]:
        return "pdf"
    return None


def upload(farmer_id, data, db_path=None):
    farmer_id = check_farmer(farmer_id)
    if not data:
        raise SoilError("EMPTY_FILE", "The uploaded file is empty.", 400)
    if len(data) > config.MAX_UPLOAD_BYTES:
        raise SoilError("FILE_TOO_LARGE", f"File is larger than {config.MAX_UPLOAD_BYTES // (1024 * 1024)} MB.", 413)
    kind = detect_kind(data)  # content sniffing - the client-supplied name/MIME type is never trusted
    if kind is None:
        raise SoilError("UNSUPPORTED_FILE_TYPE", "Only PDF, JPG, JPEG or PNG files are supported.", 415)
    if kind == "pdf":
        try:
            reader = PdfReader(io.BytesIO(data))
            if reader.is_encrypted:
                raise SoilError("ENCRYPTED_PDF", "This PDF is password protected. Please upload an unlocked copy or enter values manually.", 422)
            n = len(reader.pages)
        except SoilError:
            raise
        except (PyPdfError, ValueError, KeyError, OSError, AssertionError, RecursionError):
            raise SoilError("CORRUPTED_PDF", "The PDF could not be opened. It may be damaged. Please re-upload or enter values manually.", 422)
        if n < 1:
            raise SoilError("CORRUPTED_PDF", "The PDF has no pages.", 422)
        if n > config.MAX_PDF_PAGES:
            raise SoilError("PDF_TOO_MANY_PAGES", f"PDF has {n} pages; the limit is {config.MAX_PDF_PAGES}.", 413)
    else:
        try:
            with Image.open(io.BytesIO(data)) as im:
                if im.width * im.height > config.MAX_IMAGE_PIXELS:
                    raise SoilError("IMAGE_TOO_LARGE", "Image resolution is too large.", 413)
                im.verify()
        except SoilError:
            raise
        except Exception:
            raise SoilError("CORRUPTED_IMAGE", "The image could not be read. Please retake or re-upload it.", 422)
    sha = hashlib.sha256(data).hexdigest()
    db.init_db(db_path)
    with db.connect(db_path) as con:
        row = con.execute("SELECT document_id, status FROM soil_documents WHERE farmer_id=? AND sha256=?", (farmer_id, sha)).fetchone()
        if row:
            existing_doc = con.execute("SELECT file_path FROM soil_documents WHERE document_id=?", (row["document_id"],)).fetchone()
            if existing_doc and existing_doc["file_path"]:
                fpath = existing_doc["file_path"]
                if not os.path.exists(fpath):
                    os.makedirs(os.path.dirname(fpath), exist_ok=True)
                    with open(fpath, "wb") as fh:
                        fh.write(data)
            return {"document_id": row["document_id"], "status": "uploaded", "duplicate_document": True}
        os.makedirs(config.STORAGE_DIR, exist_ok=True)
        doc_id = uuid.uuid4().hex
        ext = {"jpeg": "jpg", "png": "png", "pdf": "pdf"}[kind]
        path = os.path.join(config.STORAGE_DIR, f"{doc_id}.{ext}")  # server-generated name; original filename discarded
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        t = now()
        con.execute("INSERT INTO soil_documents VALUES (?,?,?,?,?,?,?,?,?)",
                    (doc_id, farmer_id, path, kind, len(data), sha, "uploaded", t, t))
    return {"document_id": doc_id, "status": "uploaded", "duplicate_document": False}


# ------------------------------------------------------------------ OCR
def _field_view(key, ex, conf_default=None):
    """Build one review-screen field from an extraction record (or a missing placeholder)."""
    spec = FIELDS[key]
    if ex is None:
        return {"field": key, "label": spec["label"], "ocr_value": None, "value": None, "unit": spec["canonical"],
                "test_method": None, "method_source": None, "ocr_confidence": None, "status": MISSING, "issues": [],
                "classification": None, "verification_state": "extracted_unverified"}
    v = validate_field(key, ex.get("value"), ex.get("unit"), ex.get("test_method"), ex.get("ocr_confidence"), "review")
    issues = list(ex.get("extraction_issues", [])) + v["issues"]
    status = v["status"]
    if ex.get("value") is None:  # garbled number: farmer must type it
        status = UNCERTAIN
    elif status == VALID and any(i["severity"] == "warning" for i in ex.get("extraction_issues", [])):
        status = UNCERTAIN
    return {"field": key, "label": spec["label"], "ocr_value": ex.get("ocr_value"), "value": v["value"],
            "unit": v["unit"] if v["unit"] is not None or key == "ph" else None,
            "original_unit": v.get("original_unit") or ex.get("unit"),
            "test_method": ex.get("test_method"), "method_source": ex.get("method_source"),
            "ocr_confidence": ex.get("ocr_confidence"), "status": status, "issues": issues,
            "classification": v["classification"], "verification_state": "extracted_unverified"}


def run_ocr(farmer_id, document_id, db_path=None):
    farmer_id = check_farmer(farmer_id)
    db.init_db(db_path)
    with db.connect(db_path) as con:
        doc = con.execute("SELECT * FROM soil_documents WHERE document_id=? AND farmer_id=?", (document_id, farmer_id)).fetchone()
        if not doc:
            raise SoilError("DOCUMENT_NOT_FOUND", "Document not found.", 404)
        path, kind = doc["file_path"], doc["file_kind"]
        cached = con.execute("SELECT * FROM soil_ocr_results WHERE document_id=? ORDER BY created_at DESC LIMIT 1", (document_id,)).fetchone()
        if cached:
            stored_fields = json.loads(cached["fields_json"])
            stored_meta = json.loads(cached["metadata_json"])
            mc = cached["mean_confidence"]
            warnings = []
            if mc is not None and mc < config.LOW_MEAN_WORD_CONF:
                warnings.append(issue("poor_image_quality", "warning", "The report was hard to read. Please check every value carefully."))
            for f in stored_fields:
                if f.get("field") == "phosphorus" and f.get("value") is not None and f.get("test_method") is None:
                    warnings.append(issue("p_method_unknown", "warning", "Phosphorus test method (Olsen / Bray) not found. Please select it if you know it."))
            cached_review = {k: stored_meta[k] for k in ("farmer_name", "survey_number") if k in stored_meta}
            return {"status": "extracted", "verification_required": True, "banner": BANNER, "document_id": document_id, "ocr_id": cached["ocr_id"],
                    "fields": stored_fields, "metadata": stored_meta, "review_only": cached_review,
                    "metadata_issues": [], "warnings": warnings,
                    "mean_ocr_confidence": None if mc is None else (round(mc / 100, 3) if mc > 1.0 else round(mc, 3)),
                    "confidence_note": "Tesseract's own word-confidence average; not a measured accuracy."}
    try:
        res = ocr_mod.run_ocr(path, "pdf" if kind == "pdf" else "image", psm=6)
        ex = extract_fields(res["lines"]) if res["lines"] else {}
        if len(ex) < 3 and res["lines"]:  # second pass with a different page-segmentation mode; keep the better one
            alt = ocr_mod.run_ocr(path, "pdf" if kind == "pdf" else "image", psm=4)
            ex_alt = extract_fields(alt["lines"]) if alt["lines"] else {}
            if len(ex_alt) > len(ex):
                res, ex = alt, ex_alt
    except ocr_mod.OcrUnavailable as e:
        raise SoilError("OCR_UNAVAILABLE", str(e), 503)
    except (pytesseract.TesseractError, OSError, ValueError, RuntimeError) as e:
        raise SoilError("OCR_FAILED", MSG_UNREADABLE, 422, {"reason": type(e).__name__})
    except Exception as e:  # pdf2image/poppler errors for damaged files
        raise SoilError("OCR_FAILED", MSG_UNREADABLE, 422, {"reason": type(e).__name__})
    finally:
        # Farmer Privacy (Task 5b): Delete raw uploaded card files immediately after OCR processing
        try:
            if os.path.exists(path):
                os.remove(path)
        except Exception:
            pass

    words = sum(len(l["words"]) for l in res["lines"])
    if not res["text"].strip() or words < config.MIN_WORDS_FOR_TEXT:
        _set_doc_status(document_id, "ocr_failed", db_path)
        raise SoilError("OCR_EMPTY", MSG_UNREADABLE, 422, {"words_read": words})
    if not ex:
        _set_doc_status(document_id, "ocr_failed", db_path)
        raise SoilError("OCR_NO_FIELDS", "Text was read but no soil values were recognised. " + MSG_UNREADABLE, 422, {"words_read": words})

    warnings = []
    mc = res["mean_confidence"]
    if mc is not None and mc < config.LOW_MEAN_WORD_CONF:
        warnings.append(issue("poor_image_quality", "warning", "The report was hard to read. Please check every value carefully."))
    if any(q["sharpness"] < 30 for q in res["quality"]):
        warnings.append(issue("blurry_image", "warning", "The image looks blurry. A clearer photo may read better."))
    if any(q["width"] < 800 for q in res["quality"]):
        warnings.append(issue("low_resolution", "warning", "The image resolution is low."))
    missing_p = [k for k in PRIMARY if k not in ex]
    if missing_p:
        warnings.append(issue("missing_primary_values", "warning", "Not found in the report: " + ", ".join(FIELDS[k]["label"] for k in missing_p) + ". You can enter them manually."))

    fields = [_field_view(k, ex.get(k)) for k in FIELDS]
    for f in fields:
        if f["field"] == "phosphorus" and f["value"] is not None and f["test_method"] is None:
            warnings.append(issue("p_method_unknown", "warning", "Phosphorus test method (Olsen / Bray) not found. Please select it if you know it."))
    meta = extract_metadata(res["lines"])
    review_only = {k: meta[k] for k in ("farmer_name", "survey_number") if k in meta}
    meta_issues, meta_norm = validate_metadata(meta)
    ocr_id = uuid.uuid4().hex
    try:
        ver = str(pytesseract.get_tesseract_version())
    except Exception:
        ver = None
    stored_fields = [{k: v for k, v in f.items()} for f in fields]
    with db.connect(db_path) as con:
        con.execute("INSERT INTO soil_ocr_results VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (ocr_id, document_id, "tesseract", ver, res["psm"], None if mc is None else round(mc / 100, 4),
                     redact_text(res["text"]), json.dumps(stored_fields), json.dumps(meta_norm), json.dumps(res["quality"]), now()))
        con.execute("UPDATE soil_documents SET status='ocr_done', updated_at=? WHERE document_id=?", (now(), document_id))
    return {"status": "extracted", "verification_required": True, "banner": BANNER, "document_id": document_id, "ocr_id": ocr_id,
            "fields": fields, "metadata": meta_norm, "review_only": review_only,
            "metadata_issues": meta_issues, "warnings": warnings,
            "mean_ocr_confidence": None if mc is None else round(mc / 100, 3),
            "confidence_note": "Tesseract's own word-confidence average; not a measured accuracy."}


def _set_doc_status(document_id, status, db_path):
    with db.connect(db_path) as con:
        con.execute("UPDATE soil_documents SET status=?, updated_at=? WHERE document_id=?", (status, now(), document_id))


# ------------------------------------------------------------------ validate / confirm
def _payload_to_validation_input(body):
    fields = {}
    for k, v in (body.get("fields") or {}).items():
        if k not in FIELDS or not isinstance(v, dict):
            raise SoilError("UNKNOWN_FIELD", f"Unknown soil field '{k}'.", 400)
        if v.get("action") == "reject":
            continue
        fields[k] = {"value": v.get("value"), "unit": v.get("unit"), "test_method": v.get("test_method"),
                     "ocr_confidence": v.get("ocr_confidence")}
    return {"fields": fields, "district": body.get("district"), "test_date": body.get("test_date"), "crop": body.get("crop")}


def validate(body, stage="confirm"):
    """Dry-run validation. Nothing is stored."""
    res = validate_profile(_payload_to_validation_input(body), stage=stage)
    return {"status": "valid" if res["ok"] else "invalid", "verification_required": True, **res}


def _fingerprint(farmer_id, body_meta, fields):
    canon = {"f": farmer_id, "s": (body_meta.get("sample_id") or "").strip().lower(), "d": body_meta.get("test_date"),
             "v": sorted((k, r["value"], r["unit"], r["test_method"]) for k, r in fields.items() if r["value"] is not None)}
    return hashlib.sha256(json.dumps(canon, sort_keys=True).encode()).hexdigest()


def confirm(farmer_id, body, db_path=None):
    farmer_id = check_farmer(farmer_id)
    if body.get("farmer_confirmed") is not True:
        raise SoilError("CONFIRMATION_REQUIRED", "The farmer must explicitly confirm the values (farmer_confirmed=true).", 400)
    db.init_db(db_path)
    document_id, ocr_by_field, ocr_meta, source = body.get("document_id"), {}, {}, "manual"
    if document_id:
        with db.connect(db_path) as con:
            doc = con.execute("SELECT 1 FROM soil_documents WHERE document_id=? AND farmer_id=?", (document_id, farmer_id)).fetchone()
            if not doc:
                raise SoilError("DOCUMENT_NOT_FOUND", "Document not found.", 404)
            row = con.execute("SELECT fields_json, metadata_json FROM soil_ocr_results WHERE document_id=? ORDER BY created_at DESC LIMIT 1", (document_id,)).fetchone()
        if not row:
            raise SoilError("OCR_NOT_RUN", "OCR has not been run for this document.", 409)
        ocr_by_field = {f["field"]: f for f in json.loads(row["fields_json"])}  # server-side OCR record is authoritative
        if row["metadata_json"]:
            try:
                ocr_meta = json.loads(row["metadata_json"])
            except Exception:
                pass
        source = "ocr"

    val_in = _payload_to_validation_input(body)
    result = validate_profile(val_in, stage="confirm")
    if not result["ok"]:
        raise SoilError("VALIDATION_FAILED", "Some values need correction before they can be confirmed.", 422,
                        {"blocking_errors": result["blocking_errors"], "fields": {k: v for k, v in result["fields"].items() if v["status"] == INVALID}})
    meta = result["metadata"]
    meta_in = {k: (str(body.get(k)).strip()[:120] if body.get(k) else None) for k in ("village", "sample_id", "laboratory")}
    meta_in["test_date"] = meta.get("test_date")
    fp = _fingerprint(farmer_id, meta_in, result["fields"])
    pid, t = uuid.uuid4().hex, now()
    audit, profile = {}, {}
    for key, r in result["fields"].items():
        sub = (body.get("fields") or {}).get(key) or {}
        o = ocr_by_field.get(key) or {}
        ocr_raw = o.get("ocr_value")
        action = sub.get("action") or ("manual" if source == "manual" else "accept")
        changed = False
        if source == "ocr":
            if action == "reject" and ocr_raw is not None:
                changed = True
            elif ocr_raw is None and r["value"] is not None:
                changed = True
            elif r["value"] is not None:
                ov = parse_float(str(ocr_raw).replace(",", ".")) if ocr_raw is not None else None
                changed = (ov is None or abs(ov - r["value"]) > 1e-9 or (o.get("unit") != r["unit"] and o.get("original_unit") != sub.get("unit"))
                           or (o.get("test_method") != r["test_method"]))
        audit[key] = {"ocr_value": ocr_raw, "confirmed_value": r["value"], "modified_by_user": bool(changed),
                      "ocr_confidence": o.get("ocr_confidence"), "action": action, "status": r["status"],
                      "issues": [i for i in r["issues"] if i["severity"] != "info"]}
        entry = {"value": r["value"], "unit": r["unit"] if key != "ph" else None, "status": r["status"], "classification": r["classification"]}
        if key == "phosphorus":
            entry["method"] = r["test_method"]
        profile[key] = entry
    ph = profile.pop("ph")
    farm_area_val = body.get("farm_area") or meta.get("farm_area") or ocr_meta.get("farm_area")
    farm_area_u = body.get("farm_area_unit") or meta.get("farm_area_unit") or ocr_meta.get("farm_area_unit")
    printed_rec = body.get("printed_recommendation") or ocr_meta.get("printed_recommendation")

    profile_json = {
        "soil_profile_id": pid, "farmer_id": farmer_id, "district": meta.get("district"), "village": meta_in["village"],
        "sample_id": meta_in["sample_id"], "test_date": meta.get("test_date"), "laboratory": meta_in["laboratory"],
        "crop": meta.get("crop"), "source": source, **profile,
        "farm_area": farm_area_val, "farm_area_unit": farm_area_u, "printed_recommendation": printed_rec,
        "ph": ph["value"], "ph_status": ph["status"],
        "verification_status": "farmer_confirmed",
        "soil_status": {k: profile[k]["classification"] for k in ("nitrogen", "phosphorus", "potassium", "organic_carbon")},
        "soil_status_reference": TNAU_SOURCE, "soil_status_note": "Soil-status classes only; not fertilizer recommendations.",
        "missing_primary": result["missing_primary"], "phase4_readiness": result["phase4_readiness"],
        "warnings": [i for i in result["metadata_issues"]] + [i for r in result["fields"].values() for i in r["issues"] if i["severity"] == "warning"],
        "audit": audit, "created_at": t, "updated_at": t,
    }
    with db.connect(db_path) as con:
        dup = con.execute("SELECT soil_profile_id FROM soil_profiles WHERE farmer_id=? AND fingerprint=?", (farmer_id, fp)).fetchone()
        if dup:
            if not body.get("allow_duplicate", False):
                raise SoilError("DUPLICATE_SUBMISSION", "This soil report has already been confirmed.", 409, {"soil_profile_id": dup["soil_profile_id"]})
            existing_pid = dup["soil_profile_id"]
            profile_json["soil_profile_id"] = existing_pid
            con.execute("UPDATE soil_profiles SET district=?, village=?, sample_id=?, test_date=?, laboratory=?, crop=?, profile_json=?, updated_at=? WHERE soil_profile_id=?",
                        (profile_json["district"], profile_json["village"], profile_json["sample_id"], profile_json["test_date"],
                         profile_json["laboratory"], profile_json["crop"], json.dumps(profile_json), t, existing_pid))
            if document_id:
                con.execute("UPDATE soil_documents SET status='confirmed', updated_at=? WHERE document_id=?", (t, document_id))
            return {"status": "validated", "soil_profile_id": existing_pid, "soil_profile": profile_json, "reused": True}
        con.execute("INSERT INTO soil_profiles VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (pid, farmer_id, document_id, source, fp, profile_json["district"], profile_json["village"], profile_json["sample_id"],
                     profile_json["test_date"], profile_json["laboratory"], profile_json["crop"], "farmer_confirmed", json.dumps(profile_json), t, t))
        for key, a in audit.items():
            r = result["fields"][key]
            con.execute("INSERT INTO soil_profile_fields VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                        (pid, key, a["ocr_value"], r["value"], r["unit"], r["test_method"], r["status"], r["classification"],
                         a["ocr_confidence"], int(a["modified_by_user"]), a["action"]))
        if document_id:
            con.execute("UPDATE soil_documents SET status='confirmed', updated_at=? WHERE document_id=?", (t, document_id))
    return {"status": "validated", "soil_profile_id": pid, "soil_profile": profile_json}


def get_profile(farmer_id, soil_profile_id, db_path=None):
    farmer_id = check_farmer(farmer_id)
    db.init_db(db_path)
    with db.connect(db_path) as con:
        row = con.execute("SELECT profile_json FROM soil_profiles WHERE soil_profile_id=? AND farmer_id=?", (soil_profile_id, farmer_id)).fetchone()
    if not row:
        raise SoilError("PROFILE_NOT_FOUND", "Soil profile not found.", 404)
    return json.loads(row["profile_json"])
