"""
Field extraction from raw OCR lines. Pure text processing - no ML.
Rules: never invent a value; unknown unit stays None; Olsen/Bray only when the text says so.
`lines` = [{"text": str, "words": [{"text": str, "conf": float 0-100}]}]  (words may be empty -> confidence None)
"""
import re
from datetime import datetime

from .tnau_reference import FIELDS

LABELS = {
    "nitrogen": [r"\bnitrogen\b", r"\bavail(?:able|\.)?\s*n\b", r"^\W*n\s*[:|\-(]"],
    "phosphorus": [r"\bphosph[oa]rus\b", r"\bavail(?:able|\.)?\s*p\b", r"^\W*p\s*[:|\-(]"],
    "potassium": [r"\bpotassium\b", r"\bavail(?:able|\.)?\s*k\b", r"^\W*k\s*[:|\-(]"],
    "ph": [r"\bp\s?h\b", r"\bsoil\s+reaction\b"],
    "organic_carbon": [r"\borganic\s+carbon\b", r"\bo\.?c\b"],
    "ec": [r"\belectrical\s+conductivity\b", r"\be\.?c\b"],
    "sulphur": [r"\bsul(?:ph|f)ur\b", r"\bavail(?:able|\.)?\s*s\b"],
    "zinc": [r"\bzinc\b", r"\bzn\b"],
    "iron": [r"\biron\b", r"\bfe\b"],
    "manganese": [r"\bmanganese\b", r"\bmn\b"],
    "copper": [r"\bcopper\b", r"\bcu\b"],
    "boron": [r"\bboron\b", r"\(\s*b\s*\)"],
}
UNIT_RE = re.compile(
    r"(kg\s*/\s*ha|kg\s*ha\s*-?1|kg\s*/\s*hectare|mg\s*/\s*kg|ppm|%|g\s*/\s*kg|d\s?s\s*/\s*m|ds\s*m\s*-?1|"
    r"mmhos?\s*/\s*cm|[µμu]s\s*/\s*cm|ms\s*/\s*cm|kg\s*/\s*ac(?:re)?|lbs?\s*/\s*acre)", re.I)
NUM_RE = re.compile(r"(?<![\w.])(\d+(?:[.,]\d+)?)(?![\w])")
GARBLED_RE = re.compile(r"(?<![\w])(?=[0-9OoIl|SB.,]*\d)[0-9OoIl|SB.,]{2,}(?![\w])")
RATIO_RE = re.compile(r"\(\s*\d+\s*:\s*\d+(?:\.\d+)?[^)]*\)|\b1\s*:\s*\d(?:\.\d+)?\b")
OXIDE_RE = re.compile(r"\bP\s*2\s*O\s*5\b|\bK\s*2\s*O\b", re.I)

METHOD_PATTERNS = {
    "Olsen": r"\bolsen", "Bray": r"\bbray", "Alkaline permanganate": r"permanganate|subbiah",
    "Walkley-Black": r"walkley", "Ammonium acetate": r"ammonium\s+acetate", "DTPA": r"\bdtpa\b",
}
META_PATTERNS = {
    "farmer_name": r"(?:name\s+of\s+(?:the\s+)?farmer|farmer(?:'s|s)?\s*name|farmer)\s*[:\-–—|]+\s*(.+)",
    "sample_id": r"(?:soil\s+)?sample\s*(?:no\.?|number|id|code)\s*[:\-–—|#]*\s*([A-Za-z0-9/\-_.]+)",
    "district": r"\bdistrict\s*[:\-–—|]+\s*([A-Za-z .]+)",
    "village": r"\bvillage\s*(?:name)?\s*[:\-–—|]+\s*([A-Za-z .]+)",
    "survey_number": r"survey\s*(?:no\.?|number)(?:\s*/\s*sub[- ]?division)?\s*[:\-–—|]+\s*([A-Za-z0-9/\-. ]+)",
    "test_date_raw": r"(?:date\s+of\s+(?:testing|analysis|test|report)|test(?:ing)?\s+date|analysis\s+date|report\s+date)\s*[:\-–—|]+\s*(.+)",
}
DATE_FORMATS = ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y", "%d-%b-%Y"]
PII_LINE_RE = re.compile(r"(farmer|aadhaar|aadhar|mobile|phone|contact|ph\.?\s*no)", re.I)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)")
AADHAAR_RE = re.compile(r"(?<!\d)\d{4}\s?\d{4}\s?\d{4}(?!\d)")


def parse_report_date(raw):
    """dd/mm/yyyy is the Indian convention and is assumed for numeric dates; the farmer verifies it on screen."""
    if not raw:
        return None
    s = re.sub(r"\s+", " ", str(raw)).strip().rstrip(".")
    s = s.split(" ")[0] if re.match(r"^\d{1,4}[/.\-]\d{1,2}[/.\-]\d{1,4}", s) else s
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(s, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _word_conf(words, token):
    t = token.replace(",", ".")
    for w in words or []:
        wt = (w.get("text") or "").replace(",", ".")
        if t and t in wt and w.get("conf", -1) >= 0:
            return round(w["conf"] / 100.0, 3)
    return None


def _first_label(key, text):
    for pat in LABELS[key]:
        m = re.search(pat, text, re.I)
        if m:
            return m
    return None


def _parse_number(tok):
    """Return (float, issues). Handles '6,8' (decimal comma) and '1,200' (thousands) explicitly."""
    issues = []
    if "," in tok:
        if re.fullmatch(r"\d{1,3}(,\d{3})+", tok):
            tok = tok.replace(",", "")
        else:
            tok = tok.replace(",", ".")
            issues.append({"code": "decimal_comma", "severity": "warning", "message": "A comma was read as a decimal point. Please check."})
    return float(tok), issues


def _doc_method(text):
    hits = {m for m, p in (("Olsen", r"\bolsen"), ("Bray", r"\bbray")) if re.search(p, text, re.I)}
    return hits.pop() if len(hits) == 1 else None


def extract_fields(lines):
    full_text = "\n".join(l["text"] for l in lines)
    doc_p_method = _doc_method(full_text)
    fields, used = {}, set()
    for idx, line in enumerate(lines):
        text = line["text"]
        for key in FIELDS:
            if key in fields:
                continue
            m = _first_label(key, text)
            if not m:
                continue
            rest = RATIO_RE.sub(" ", text[m.end():])
            oxide = bool(OXIDE_RE.search(rest))
            rest_clean = OXIDE_RE.sub(" ", rest)
            nm = NUM_RE.search(rest_clean)
            garbled = None
            if not nm:
                gm = GARBLED_RE.search(rest_clean)
                if gm and re.search(r"[OoIl|SB]", gm.group(0)):
                    garbled = gm.group(0)
                else:
                    continue  # label with no value on this line (e.g. table header) -> keep looking
            f = {"field": key, "label": FIELDS[key]["label"], "line_index": idx, "extraction_issues": []}
            if garbled:
                f.update(ocr_value=garbled, value=None, unit=None, ocr_confidence=_word_conf(line.get("words"), garbled))
                f["extraction_issues"].append({"code": "ocr_parse_error", "severity": "warning",
                                               "message": f"Could not read '{garbled}' as a number. Please enter the value."})
            else:
                tok = nm.group(1)
                val, iss = _parse_number(tok)
                um = UNIT_RE.search(rest_clean[nm.end():]) or UNIT_RE.search(text[: m.start()] + " " + text[m.start():m.end()])
                if not um:  # unit printed between label and value, e.g. "Nitrogen (kg/ha) 280"
                    um = UNIT_RE.search(rest_clean[: nm.start()])
                unit_raw = re.sub(r"\s+", "", um.group(1)) if um else None
                f.update(ocr_value=tok, value=val, unit=unit_raw,
                         ocr_confidence=_word_conf(line.get("words"), tok))
                f["extraction_issues"].extend(iss)
                if unit_raw is None and key != "ph":
                    f["extraction_issues"].append({"code": "unit_not_found", "severity": "warning", "message": "No unit found next to this value."})
            if oxide:
                f["extraction_issues"].append({"code": "oxide_basis", "severity": "warning",
                                               "message": "Report appears to give this nutrient as an oxide (P2O5 / K2O). Not converted - please check."})
            if key == "phosphorus":
                lm = {m_ for m_, p in (("Olsen", r"\bolsen"), ("Bray", r"\bbray")) if re.search(p, text, re.I)}
                if len(lm) == 1:
                    f["test_method"], f["method_source"] = lm.pop(), "same_line"
                elif doc_p_method:
                    f["test_method"], f["method_source"] = doc_p_method, "document_text"
                else:
                    f["test_method"], f["method_source"] = None, None
            else:
                f["test_method"], f["method_source"] = None, None
            fields[key] = f
            used.add(idx)
    return fields


def extract_metadata(lines):
    meta, text = {}, "\n".join(l["text"] for l in lines)
    for k, pat in META_PATTERNS.items():
        for l in lines:
            m = re.search(pat, l["text"], re.I)
            if m:
                meta[k] = m.group(1).strip(" .:|-")
                break
    meta["test_date"] = parse_report_date(meta.pop("test_date_raw", None))
    for l in lines:
        if re.search(r"laborator|soil\s+testing|\bstl\b", l["text"], re.I) and len(l["text"]) < 90 and not re.search(r"[:|]\s*\d", l["text"]):
            meta["laboratory"] = l["text"].strip(" :|-")
            break
    meta["methods_detected"] = [n for n, p in METHOD_PATTERNS.items() if re.search(p, text, re.I)]
    return {k: v for k, v in meta.items() if v not in (None, "", [])}


def redact_text(text):
    """Privacy: drop lines naming the farmer/contacts and mask phone / Aadhaar-like numbers before storing OCR text."""
    out = []
    for line in text.splitlines():
        if PII_LINE_RE.search(line) and re.search(r"[:|\-]", line):
            label = re.split(r"[:|\-]", line, 1)[0]
            out.append(f"{label.strip()}: [redacted]")
            continue
        line = AADHAAR_RE.sub("[redacted]", PHONE_RE.sub("[redacted]", line))
        out.append(line)
    return "\n".join(out)
