"""Validation layer. Status vocabulary: missing | invalid | uncertain | valid."""
import math
from datetime import date, datetime

from . import config
from .classification import classify
from .tnau_reference import (DISTRICT_ALIASES, FIELDS, P_METHODS, PLAUSIBILITY, PRIMARY, TN_DISTRICTS)
from .units import normalize_value_unit

MISSING, INVALID, UNCERTAIN, VALID = "missing", "invalid", "uncertain", "valid"


def issue(code, severity, message):
    return {"code": code, "severity": severity, "message": message}


def parse_float(v):
    """Strict numeric parse. Returns float or None. Does NOT repair OCR letters (O->0 etc.)."""
    if v is None or isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v) if math.isfinite(v) else None
    s = str(v).strip()
    try:
        f = float(s)
    except ValueError:
        return None
    return f if math.isfinite(f) else None


def resolve_district(name):
    if not name or not str(name).strip():
        return None
    k = " ".join(str(name).strip().lower().split())
    for d in TN_DISTRICTS:
        if d.lower() == k:
            return d
    return DISTRICT_ALIASES.get(k) or DISTRICT_ALIASES.get(k.replace(" ", ""))


def parse_iso_date(s):
    if isinstance(s, date):
        return s
    try:
        return datetime.strptime(str(s).strip(), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def validate_field(key, value, unit, method=None, ocr_confidence=None, stage="review"):
    """
    stage='review'  : strict - unusual values/unknown P method => 'uncertain' so the UI asks the farmer to look.
    stage='confirm' : farmer has looked - unusual values / unknown P method become warnings on a 'valid' field;
                      impossible values and unknown units remain 'invalid'.
    """
    spec = FIELDS[key]
    res = {"value": None, "unit": unit, "test_method": method, "status": MISSING, "issues": [], "classification": None}
    if value is None or (isinstance(value, str) and not value.strip()):
        return res
    f = parse_float(value)
    if f is None:
        res["status"] = INVALID
        res["issues"].append(issue("not_numeric", "error", f"'{value}' is not a valid number."))
        return res
    res["value"] = f
    f, nunit, note, orig_unit = normalize_value_unit(key, f, unit)
    res["value"], res["unit"] = f, nunit
    if note:
        res["issues"].append(issue("unit_converted", "info", note))
    if orig_unit not in (None, nunit):
        res["original_unit"] = orig_unit

    # unit
    allowed = spec["units"]
    if nunit not in allowed:
        sev = "error" if stage == "confirm" else "warning"
        shown = unit if unit not in (None, "") else "(none)"
        res["status"] = INVALID if stage == "confirm" else UNCERTAIN
        res["issues"].append(issue("unknown_unit", sev, f"Unit '{shown}' is not accepted for {spec['label']}. "
                                   f"Expected one of: {', '.join(str(a) for a in allowed if a)}." if key != "ph" else
                                   "pH must not carry a unit."))
        return res

    bounds = PLAUSIBILITY[(key, nunit)]
    lo, hi = bounds["hard"]
    if f < lo or f > hi:
        res["status"] = INVALID
        res["issues"].append(issue("out_of_physical_range", "error", f"{spec['label']} = {f:g} is outside the possible range {lo}-{hi}."))
        return res

    status = VALID
    slo, shi = bounds["soft"]
    if f < slo or f > shi:
        res["issues"].append(issue("unusual_value", "warning", f"{spec['label']} = {f:g} is unusual (typical {slo}-{shi}). Please double-check."))
        status = UNCERTAIN if stage == "review" else VALID

    if key == "phosphorus":
        if method is not None and method not in P_METHODS:
            res["status"] = INVALID
            res["issues"].append(issue("invalid_p_method", "error", f"Phosphorus method must be one of {P_METHODS} or empty."))
            return res
        if method is None:
            res["issues"].append(issue("p_method_unknown", "warning", "Phosphorus test method (Olsen or Bray) is not known. "
                                       "Fertility status cannot be classified without it."))
            if stage == "review":
                status = UNCERTAIN

    if ocr_confidence is not None and stage == "review" and ocr_confidence < 0.5:
        res["issues"].append(issue("low_ocr_confidence", "warning", "OCR was not confident about this value."))
        status = UNCERTAIN

    res["status"] = status
    res["classification"] = classify(key, f, nunit, method)
    return res


def validate_metadata(meta, crop=None, today=None):
    """Validate district, test date, crop. Returns (issues, normalized_meta)."""
    today = today or date.today()
    issues, out = [], dict(meta or {})
    d = out.get("district")
    if d:
        r = resolve_district(d)
        if r:
            out["district"] = r
        else:
            issues.append(issue("unknown_district", "warning", f"District '{d}' is not a recognised Tamil Nadu district."))
    td = out.get("test_date")
    if td:
        p = parse_iso_date(td)
        if p is None:
            issues.append(issue("invalid_test_date", "error", "Test date must be a real date in YYYY-MM-DD format."))
        elif p > today:
            issues.append(issue("future_test_date", "error", "Test date is in the future."))
        else:
            out["test_date"] = p.isoformat()
            if (today - p).days > 365 * config.TEST_DATE_STALE_YEARS:
                issues.append(issue("stale_test_date", "warning", f"Test is more than {config.TEST_DATE_STALE_YEARS} years old; values may be outdated."))
    if crop:
        from .crops import known_crop
        c = known_crop(crop)
        if c:
            out["crop"] = c
        else:
            issues.append(issue("unknown_crop", "warning", f"Crop '{crop}' is not in the crop list used by the yield model."))
    return issues, out


def validate_profile(payload, stage="review", today=None):
    """
    payload: {"fields": {key: {value, unit, test_method, ocr_confidence}}, "district", "test_date", "crop", ...}
    Returns dict: fields, metadata_issues, missing_primary, blocking_errors, ok, phase4_ready
    """
    fields_in = payload.get("fields") or {}
    out_fields, blocking = {}, []
    for key in FIELDS:
        fin = fields_in.get(key) or {}
        r = validate_field(key, fin.get("value"), fin.get("unit"), fin.get("test_method"), fin.get("ocr_confidence"), stage)
        out_fields[key] = r
        if r["status"] == INVALID:
            blocking.append({"field": key, "issues": [i for i in r["issues"] if i["severity"] == "error"]})
    meta_issues, meta = validate_metadata(payload, payload.get("crop"), today)
    for i in meta_issues:
        if i["severity"] == "error":
            blocking.append({"field": i["code"], "issues": [i]})
    present = [k for k, r in out_fields.items() if r["value"] is not None and r["status"] != INVALID]
    if not present and stage == "confirm":
        blocking.append({"field": "fields", "issues": [issue("no_values", "error", "No soil values were provided.")]})
    missing_primary = [k for k in PRIMARY if out_fields[k]["status"] == MISSING]
    p = out_fields["phosphorus"]
    p4_missing = [k for k in ("nitrogen", "phosphorus", "potassium") if out_fields[k]["value"] is None]
    p4_notes = []
    if p["value"] is not None and p["test_method"] is None:
        p4_notes.append("phosphorus method unknown")
    return {
        "fields": out_fields, "metadata": meta, "metadata_issues": meta_issues, "missing_primary": missing_primary,
        "blocking_errors": blocking, "ok": not blocking,
        "phase4_readiness": {"ready": not p4_missing and not p4_notes and not blocking, "missing": p4_missing, "notes": p4_notes},
    }
