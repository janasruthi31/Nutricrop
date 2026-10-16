"""
Field extraction from raw OCR lines. Pure text processing - no ML.
Rules: never invent a value; unknown unit stays None; Olsen/Bray only when the text says so.
`lines` = [{"text": str, "words": [{"text": str, "conf": float 0-100}]}]  (words may be empty -> confidence None)
"""
import re
from datetime import datetime

from .tnau_reference import FIELDS

LABELS = {
    "nitrogen": [r"\bnitrogen\b", r"\bavail(?:able|\.)?\s*n\b", r"^\W*n\s*[:|\-(]", r"தழை", r"தைழ"],
    "phosphorus": [r"\bphosph[oa]rus\b", r"\bavail(?:able|\.)?\s*p\b", r"^\W*p\s*[:|\-(]", r"மணி"],
    "potassium": [r"\bpotassium\b", r"\bavail(?:able|\.)?\s*k\b", r"^\W*k\s*[:|\-(]", r"சாம்பல்", r"பொட்டாஷ்"],
    "ph": [r"\bp\s?h\b", r"\bsoil\s+reaction\b", r"கார\s*அமில", r"களர்\s*-\s*அமில", r"அமில\s*நிலை"],
    "organic_carbon": [r"\borganic\s+carbon\b", r"\bo\.?c\b", r"அங்கக\s*கரிமம்", r"அங்ககக்கரிமம்"],
    "ec": [r"\belectrical\s+conductivity\b", r"\be\.?c\b", r"மின்\s*கடத்து", r"உப்பின்\s*நிலை"],
    "sulphur": [r"\bsul(?:ph|f)ur\b", r"\bavail(?:able|\.)?\s*s\b", r"கந்தகம்"],
    "zinc": [r"\bzinc\b", r"\bzn\b", r"துத்தநாகம்", r"துத்தநாக"],
    "iron": [r"\biron\b", r"\bfe\b", r"இரும்பு"],
    "manganese": [r"\bmanganese\b", r"\bmn\b", r"மாங்கனீசு", r"மாங்கனீஸ்"],
    "copper": [r"\bcopper\b", r"\bcu\b", r"தாமிரம்", r"தாமிர"],
    "boron": [r"\bboron\b", r"\bavail(?:able|\.)?\s*b\b", r"போரான்", r"ேபாரான்"],
}
UNIT_RE = re.compile(
    r"(kg\s*/\s*ha|kg\s*ha\s*-?1|kg\s*/\s*hectare|mg\s*/\s*kg|ppm|%|g\s*/\s*kg|d\s?s\s*/\s*m|ds\s*m\s*-?1|"
    r"mmhos?\s*/\s*cm|[µμu]s\s*/\s*cm|ms\s*/\s*cm|kg\s*/\s*ac(?:re)?|lbs?\s*/\s*acre|"
    r"கிலோ\s*/\s*ஏக்கர்|கிலோ\s*/\s*ஹெக்டேர்)", re.I)
NUM_RE = re.compile(r"(?<![\w.])(\d+(?:[.,]\d+)?)(?![\w])")
GARBLED_RE = re.compile(r"(?<![\w])(?=[0-9OoIl|SB.,]*\d)[0-9OoIl|SB.,]{2,}(?![\w])")
RATIO_RE = re.compile(r"\(\s*\d+\s*:\s*\d+(?:\.\d+)?[^)]*\)|\b1\s*:\s*\d(?:\.\d+)?\b")
OXIDE_RE = re.compile(r"\bP\s*2\s*O\s*5\b|\bK\s*2\s*O\b", re.I)

METHOD_PATTERNS = {
    "Olsen": r"\bolsen", "Bray": r"\bbray", "Alkaline permanganate": r"permanganate|subbiah",
    "Walkley-Black": r"walkley", "Ammonium acetate": r"ammonium\s+acetate", "DTPA": r"\bdtpa\b",
}
META_PATTERNS = {
    "farmer_name": r"(?:name\s+of\s+(?:the\s+)?farmer|farmer(?:'s|s)?\s*name|farmer|பெயர்)\s*[:\-–—|]*\s*(.*)",
    "sample_id": r"(?:(?:soil\s+)?sample\s*(?:no\.?|number|id|code)|மாதிரி\s*எண்)\s*[:\-–—|#]*\s*([A-Za-z0-9/\-_.]*)",
    "district": r"(?:\bdistrict\b|மாவட்டம்)\s*[:\-–—|]*\s*([A-Za-z .\u0B80-\u0BFF]*)",
    "village": r"(?:\bvillage\s*(?:name)?|வருவாய்\s*கிராமம்|கிராமம்)\s*[:\-–—|]*\s*([A-Za-z .\u0B80-\u0BFF]*)",
    "survey_number": r"(?:survey\s*(?:no\.?|number)(?:\s*/\s*sub[- ]?division)?|புல\s*எண்(?:/உட்ப்பிரிவு\s*எண்)?|சர்வே\s*எண்)\s*[:\-–—|]*\s*([A-Za-z0-9/\-. ]*)",
    "test_date_raw": r"(?:date\s+of\s+(?:testing|analysis|test|report)|test(?:ing)?\s+date|analysis\s+date|report\s+date|பரிசோதனை\s*நாள்|ஆய்வு\s*நாள்)\s*[:\-–—|]*\s*(.*)",
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


def _find_header_unit(lines, idx, key=None):
    from .units import canonical_unit_token
    allowed = FIELDS.get(key, {}).get("units", []) if key else None
    for back in range(1, 45):
        if idx - back < 0:
            break
        t = lines[idx - back]["text"]
        um = UNIT_RE.search(t)
        if um:
            cand = re.sub(r"\s+", "", um.group(1))
            if allowed is not None:
                tok = canonical_unit_token(cand)
                if tok in allowed or cand in allowed:
                    return cand
            else:
                return cand
    return None


def extract_fields(lines):
    full_text = "\n".join(l["text"] for l in lines)
    doc_p_method = _doc_method(full_text)
    fields, used = {}, set()

    # Prioritize test results section if present
    test_results_start = 0
    for i, line in enumerate(lines):
        if "வேதியியல் பண்புகள்" in line["text"]:
            test_results_start = i
            break
    search_indices = list(range(test_results_start, len(lines))) + list(range(0, test_results_start))

    for idx in search_indices:
        line = lines[idx]
        text = line["text"]
        for key in FIELDS:
            if key in fields:
                continue
            m = _first_label(key, text)
            if not m:
                continue
            # Avoid fertilizer dosage lines (e.g. Urea, DAP, Ammonium Sulfate, Potash, fertilizer mixes)
            if any(f in text for f in ("யூரியா", "அம்மோனியம்", "டி ஏ பி", "சல்ேபட்", "சல்பேட்", "உரக்கலவை")):
                continue

            rest = RATIO_RE.sub(" ", text[m.end():])
            oxide = bool(OXIDE_RE.search(rest))
            rest_clean = OXIDE_RE.sub(" ", rest)
            nm = NUM_RE.search(rest_clean)
            garbled = None
            tok = None
            val_line = line
            unit_raw = None

            if nm:
                tok = nm.group(1)
                um = UNIT_RE.search(rest_clean[nm.end():]) or UNIT_RE.search(text[: m.start()] + " " + text[m.start():m.end()])
                if not um:
                    um = UNIT_RE.search(rest_clean[: nm.start()])
                unit_raw = re.sub(r"\s+", "", um.group(1)) if um else None
            else:
                gm = GARBLED_RE.search(rest_clean)
                if gm and re.search(r"[OoIl|SB]", gm.group(0)):
                    garbled = gm.group(0)
                else:
                    # Lookahead: value or unit may be on next lines (e.g. table format)
                    for offset in range(1, 4):
                        if idx + offset >= len(lines):
                            break
                        nxt_line = lines[idx + offset]
                        nxt = nxt_line["text"].strip()
                        nxt_um = UNIT_RE.search(nxt)
                        if nxt_um and not unit_raw:
                            unit_raw = re.sub(r"\s+", "", nxt_um.group(1))
                        # Skip symbols like (N), (P), (K), Fe, Zn, Mn, Cu, B or unit tokens
                        if re.fullmatch(r"[A-Za-z\(\)]+", nxt) or "dS/m" in nxt or "%" in nxt:
                            continue
                        # Skip benchmark/reference ranges (e.g. '113-180', '6.0 - 7.5', '> 2.0')
                        if any(sym in nxt for sym in ("-", "–", "—", ">", "<", "to")):
                            continue
                        nxt_nm = NUM_RE.search(nxt)
                        if nxt_nm:
                            tok = nxt_nm.group(1)
                            val_line = nxt_line
                            break

            if not tok and not garbled:
                continue  # label with no value on this line or adjacent lines -> keep looking

            # If unit still not found and not pH, check same line or context header unit
            if not unit_raw and key != "ph":
                um_text = UNIT_RE.search(text)
                if um_text:
                    unit_raw = re.sub(r"\s+", "", um_text.group(1))
                else:
                    unit_raw = _find_header_unit(lines, idx, key)

            f = {"field": key, "label": FIELDS[key]["label"], "line_index": idx, "extraction_issues": []}
            if garbled:
                f.update(ocr_value=garbled, value=None, unit=None, ocr_confidence=_word_conf(line.get("words"), garbled))
                f["extraction_issues"].append({"code": "ocr_parse_error", "severity": "warning",
                                               "message": f"Could not read '{garbled}' as a number. Please enter the value."})
            else:
                val, iss = _parse_number(tok)
                f.update(ocr_value=tok, value=val, unit=unit_raw,
                         ocr_confidence=_word_conf(val_line.get("words"), tok))
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
        for idx, l in enumerate(lines):
            m = re.search(pat, l["text"], re.I)
            if m:
                val = m.group(1).strip(" .:|-")
                # If label only was on line and value is on next line
                if not val and idx + 1 < len(lines):
                    val = lines[idx + 1]["text"].strip(" .:|-")
                if val:
                    # Check if farmer name contains sample ID like (TN/ERD/02488)
                    if k == "farmer_name":
                        sm = re.search(r"\((TN/[A-Z0-9/_\-]+)\)", val)
                        if sm and "sample_id" not in meta:
                            meta["sample_id"] = sm.group(1)
                            val = val[:sm.start()].strip()
                    meta[k] = val
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
