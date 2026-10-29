"""
Field extraction from raw OCR lines. Pure text processing - no ML.
Rules: never invent a value; unknown unit stays None; Olsen/Bray only when the text says so.
`lines` = [{"text": str, "words": [{"text": str, "conf": float 0-100}]}]  (words may be empty -> confidence None)
"""
import re
from datetime import datetime

from .tnau_reference import FIELDS
from .units import canonical_unit_token


def normalize_tamil_text(t: str) -> str:
    """
    Normalizes visual Tamil font encoding into canonical Unicode order.
    In visual Tamil fonts, pre-base vowel signs (ெ, ே, ை) and two-part vowel signs (ொ, ோ, ௌ)
    are often generated before or surrounding the consonant.
    """
    if not t:
        return t
    # Two-part vowel signs:
    # \u0bc7 + consonant + \u0bbe -> consonant + \u0bcb (ோ)
    t = re.sub(r"\u0bc7([\u0b95-\u0bb9])\u0bbe", lambda m: m.group(1) + "\u0bcb", t)
    # \u0bc6 + consonant + \u0bbe -> consonant + \u0bca (ொ)
    t = re.sub(r"\u0bc6([\u0b95-\u0bb9])\u0bbe", lambda m: m.group(1) + "\u0bca", t)
    # \u0bc6 + consonant + \u0bb3 -> consonant + \u0bcc (ௌ)
    t = re.sub(r"\u0bc6([\u0b95-\u0bb9])\u0bb3", lambda m: m.group(1) + "\u0bcc", t)
    # Single pre-base vowel signs: \u0bc6 (ெ), \u0bc7 (ே), \u0bc8 (ை) placed before consonant
    t = re.sub(r"([\u0bc6\u0bc7\u0bc8])([\u0b95-\u0bb9])", r"\2\1", t)
    return t


LABELS = {
    "nitrogen": [r"\bnitrogen\b", r"\bavail(?:able|\.)?\s*n\b", r"^\W*n\s*[:|\-(]", r"\(\s*N\s*\)", r"தழை", r"தைழ"],
    "phosphorus": [r"\bphosph[oa]rus\b", r"\bavail(?:able|\.)?\s*p\b", r"^\W*p\s*[:|\-(]", r"\(\s*P\s*\)", r"மணி"],
    "potassium": [r"\bpotassium\b", r"\bavail(?:able|\.)?\s*k\b", r"^\W*k\s*[:|\-(]", r"\(\s*K\s*\)", r"சாம்பல்", r"பொட்டாஷ்", r"பொட்டாஷ்"],
    "ph": [r"\bp\s?h\b", r"\(\s*pH\s*[\)}]", r"\bsoil\s+reaction\b", r"கார\s*அமில", r"களர்\s*-\s*அமில", r"அமில\s*நிலை"],
    "organic_carbon": [r"\borganic\s+carbon\b", r"\bo\.?c\b", r"\(\s*[0O]c\s*[\)}]", r"அங்கக\s*கரிமம்", r"அங்ககக்கரிமம்"],
    "ec": [r"\belectrical\s+conductivity\b", r"\be\.?c\b", r"\(\s*EC\s*[\)}]", r"மின்\s*கடத்து", r"உப்பின்\s*நிலை"],
    "sulphur": [r"\bsul(?:ph|f)ur\b", r"\bavail(?:able|\.)?\s*s\b", r"\(\s*S\s*\)", r"கந்தகம்"],
    "zinc": [r"\bzinc\b", r"\bzn\b", r"\(\s*Zn\s*\)", r"துத்தநாகம்", r"துத்தநாக"],
    "iron": [r"\biron\b", r"\bfe\b", r"\(\s*Fe\s*\)", r"இரும்பு"],
    "manganese": [r"\bmanganese\b", r"\bmn\b", r"\(\s*Mn\s*\)", r"மாங்கனீசு", r"மாங்கனீஸ்"],
    "copper": [r"\bcopper\b", r"\bcu\b", r"\(\s*Cu\s*\)", r"தாமிரம்", r"தாமிர"],
    "boron": [r"\bboron\b", r"\bavail(?:able|\.)?\s*b\b", r"\(\s*B\s*\)", r"போரான்", r"போரான்", r"ேபாரான்"],
}

UNIT_RE = re.compile(
    r"(kg\s*/\s*ha|kgiha|kg\s*i\s*ha|rgihs|kg\s*ha\s*-?1|kg\s*/\s*hectare|mg\s*/\s*kg|ppm|%|g\s*/\s*kg|d\s?s\s*/\s*m|ds\s*m\s*-?1|"
    r"d5ym|dsym|"
    r"mmhos?\s*/\s*cm|[µμu]s\s*/\s*cm|ms\s*/\s*cm|kg\s*/\s*ac(?:re)?|lbs?\s*/\s*acre|"
    r"கிலோ\s*/\s*ஏக்கர்|கிலோ\s*/\s*ஹெக்டேர்|\(%\)|\(OC\s*%\)|\(dS/m\))", re.I)

NUM_RE = re.compile(r"(?<![\w.])(\d+(?:[.,]\d+)?)(?![\w])")
GARBLED_RE = re.compile(r"(?<![\w])(?=[0-9OoIl|SB.,]*\d)[0-9OoIl|SB.,]{2,}(?![\w])")
RATIO_RE = re.compile(r"\(\s*\d+\s*:\s*\d+(?:\.\d+)?[^)]*\)|\b1\s*:\s*\d(?:\.\d+)?\b")
OXIDE_RE = re.compile(r"\bP\s*2\s*O\s*5\b|\bK\s*2\s*O\b", re.I)

METHOD_PATTERNS = {
    "Olsen": r"\bolsen", "Bray": r"\bbray", "Alkaline permanganate": r"permanganate|subbiah",
    "Walkley-Black": r"walkley", "Ammonium acetate": r"ammonium\s+acetate", "DTPA": r"\bdtpa\b",
}

META_PATTERNS = {
    "farmer_name": r"(?:name\s+of\s+(?:the\s+)?farmer|farmer(?:'s|s)?\s*name|farmer|விவசாயி(?:யின்)?\s*பெயர்|உழவர்(?:களின்|ின்)?\s*பெயர்|பயனாளி(?:யின்)?\s*பெயர்|பெயர்|(?<!village\s)(?<!crop\s)(?<!lab\s)(?<!laboratory\s)\bname)\s*[:\-–—|#]*\s*(.*)",
    "sample_id": r"(?:(?:soil\s+)?sample\s*(?:no\.?|number|id|code)|card\s*(?:no\.?|number|id)|மாதிரி\s*எண்|அட்டை\s*எண்)\s*[:\-–—|#]*\s*([A-Za-z0-9/\-_.]+)|([A-Za-z0-9]{3,4}[-/]\d{3,4}[-/]\d{4,}[A-Za-z0-9]*)|(SHC\d{4}[A-Za-z0-9\-_]+)",
    "district": r"(?:\bdistrict\b|மாவட்டம்)\s*[:\-–—|#]*\s*([A-Za-z .\u0B80-\u0BFF]*)",
    "village": r"(?:\bvillage\s*(?:name)?|வருவாய்\s*கிராமம்|கிராமம்)\s*[:\-–—|#]*\s*([A-Za-z .\u0B80-\u0BFF]*)",
    "survey_number": r"(?:survey\s*(?:no\.?|number|#)?(?:\s*/\s*sub[- ]?division)?|khasra\s*(?:no\.?|number)?|dag\s*(?:no\.?|number)?|patta\s*(?:no\.?|number)?|புல\s*எண்(?:/உட்ப்பிரிவு\s*எண்)?|சர்வே\s*எண்|பட்டா\s*எண்)\s*[:\-–—|#]*\s*([A-Za-z0-9/\-. ]*)",
    "test_date_raw": r"(?:date\s+of\s+(?:testing|analysis|test|report)|test(?:ing)?\s+date|analysis\s+date|report\s+date|பரிசோதனை\s*நாள்|ஆய்வு\s*நாள்)\s*[:\-–—|]*\s*(.*)",
}
DATE_FORMATS = ["%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y", "%Y-%m-%d", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y", "%d-%b-%Y"]
PII_LINE_RE = re.compile(r"(farmer|aadhaar|aadhar|mobile|phone|contact|ph\.?\s*no)", re.I)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?91[\s-]?)?[6-9]\d{9}(?!\d)")
AADHAAR_RE = re.compile(r"(?<!\d)\d{4}\s?\d{4}\s?\d{4}(?!\d)")

FERTILIZER_KEYWORDS = ("யூரியா", "அம்மோனியம்", "டி ஏ பி", "பொட்டாஷ்", "பொட்டாஷ்", "சல்பேட்", "சல்ேபட்",
                       "உரக்கலவை", "பாக்டீரியா", "பசுந்தழை", "உயிர் உரம்", "உரப்பரிந்துரை")


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
    allowed = FIELDS.get(key, {}).get("units", []) if key else None
    for back in range(1, 45):
        if idx - back >= 0:
            t = lines[idx - back]["text"]
            um = UNIT_RE.search(t)
            if um:
                cand = re.sub(r"\s+", "", um.group(1))
                tok = canonical_unit_token(cand) or cand
                if allowed is not None:
                    if tok in allowed or cand in allowed:
                        return tok
                else:
                    return tok
    return None


def _extract_number_from_tokens(text: str, field_key: str = None):
    """
    Extracts the measured nutrient number from a line while disambiguating
    against benchmark / sufficiency ranges (e.g. '113-180', '4.5 - 9', '> 2.0', '0.0 - 1.0').
    Also parses split decimals (e.g. '163 00' -> 163.00, '0 22' -> 0.22) and 3-digit pH/iron scale.
    """
    tokens = text.split()
    for ti, tk in enumerate(tokens):
        # Strip leading/trailing non-alphanumeric punctuation (keep letters so garbled tokens like '28O' aren't stripped into numbers)
        clean_tk = re.sub(r"^[^0-9A-Za-z]+|[^0-9A-Za-z]+$", "", tk)
        if not clean_tk:
            continue
        # Match standalone or decimal number (e.g. '39', '0.41', '7.75')
        m = re.match(r"^(\d+(?:[.,]\d+)?)$", clean_tk)
        candidate = None
        if m:
            is_range = False
            if ti + 1 < len(tokens) and tokens[ti + 1] in ("-", "–", "—", "to"):
                is_range = True
            if ti > 0 and tokens[ti - 1] in ("-", "–", "—", "to", ">", "<"):
                is_range = True
            if not is_range:
                # Check split decimal: '163' followed by '00' or '0' followed by '22' (possibly with attached unit e.g. '22d5ym')
                if ti + 1 < len(tokens) and "." not in clean_tk and "," not in clean_tk:
                    next_tk = tokens[ti + 1]
                    m_next_digits = re.match(r"^(\d{2})", next_tk)
                    if m_next_digits:
                        if not (ti + 2 < len(tokens) and tokens[ti + 2] in ("-", "–", "—", "to")):
                            if clean_tk == "0" or m_next_digits.group(1) == "00" or field_key in ("phosphorus", "zinc", "copper", "boron", "manganese", "ec"):
                                candidate = f"{clean_tk}.{m_next_digits.group(1)}"
                # Check 3-digit pH or iron scale (e.g. 775 -> 7.75, 447 -> 4.47)
                if not candidate and clean_tk.isdigit() and len(clean_tk) == 3 and field_key in ("ph", "iron") and clean_tk[0] in "3456789":
                    candidate = f"{clean_tk[0]}.{clean_tk[1:]}"
                if not candidate:
                    candidate = m.group(1)
        elif not candidate:
            # Check if number attached to suffix like '0.22d5ym' or '7.75(pH)'
            m_attached = re.match(r"^(\d+[.,]\d+)", clean_tk)
            if m_attached:
                candidate = m_attached.group(1)

        if candidate:
            try:
                float(candidate.replace(",", "."))
                return candidate
            except Exception:
                pass
    return None


def extract_fields(lines):
    # Step 1: Normalize all line text to canonical Tamil Unicode
    norm_lines = []
    for l in lines:
        t = normalize_tamil_text(l.get("text", "")).strip()
        norm_lines.append({"text": t, "words": l.get("words", [])})

    full_text = "\n".join(l["text"] for l in norm_lines)
    doc_p_method = _doc_method(full_text)

    # Step 2: Identify document sections (Soil Test Results vs Fertilizer Recommendations)
    # In Tamil Nadu Soil Health Cards, soil test tables appear under "மண் ஆய்வு முடிவுகள்",
    # "வேதியியல் பண்புகள்", "பேரூட்டச்சத்துக்கள் ஆய்வு முடிவுகள்", "நுண்ணூட்டச்சத்துக்கள் ஆய்வு முடிவுகள்".
    # Lines under "உரப்பரிந்துரைகள்" or containing fertilizer products are strictly recommendations.
    in_fertilizer_section = False
    tagged_lines = []
    for i, l in enumerate(norm_lines):
        t = l["text"]
        if "உரப்பரிந்துரைகள்" in t or "உரப்பரிந்துரை" in t:
            in_fertilizer_section = True
        elif any(h in t for h in ("வேதியியல் பண்புகள்", "பேரூட்டச்சத்துக்கள் ஆய்வு முடிவுகள்",
                                 "நுண்ணூட்டச்சத்துக்கள் ஆய்வு முடிவுகள்")):
            in_fertilizer_section = False

        is_fertilizer_line = in_fertilizer_section or any(k in t for k in FERTILIZER_KEYWORDS)
        tagged_lines.append({
            "idx": i,
            "text": t,
            "words": l["words"],
            "is_fertilizer": is_fertilizer_line,
        })

    fields = {}

    # Prioritize soil test lines first, never extract fertilizer recommendations as soil test values
    search_order = [l for l in tagged_lines if not l["is_fertilizer"]] + [l for l in tagged_lines if l["is_fertilizer"]]

    for line_info in search_order:
        idx = line_info["idx"]
        text = line_info["text"]

        # Strictly skip fertilizer recommendation lines for soil nutrient extraction
        if line_info["is_fertilizer"]:
            continue

        # Collect all label matches on this line to partition multi-column lines
        line_label_hits = []
        for k in FIELDS:
            if k in fields:
                continue
            for p in LABELS[k]:
                for lm in re.finditer(p, text, re.I):
                    line_label_hits.append((lm.start(), lm.end(), k))
        line_label_hits.sort()
        
        # Merge overlapping or same-nutrient hits (e.g. 'இரும்பு' and 'Fe' both for iron, or 'தழை' and 'N' both for nitrogen)
        distinct_hits = []
        for h in line_label_hits:
            if not distinct_hits:
                distinct_hits.append(h)
            elif h[2] == distinct_hits[-1][2]:
                distinct_hits[-1] = (distinct_hits[-1][0], max(distinct_hits[-1][1], h[1]), h[2])
            elif h[0] >= distinct_hits[-1][1]:
                distinct_hits.append(h)

        target_items = []
        if distinct_hits:
            for di, (st, en, key) in enumerate(distinct_hits):
                if key in fields:
                    continue
                next_st = distinct_hits[di + 1][0] if di + 1 < len(distinct_hits) else len(text)
                chunk = text[en:next_st]
                target_items.append((key, chunk, en))
        else:
            for key in FIELDS:
                if key in fields:
                    continue
                m = _first_label(key, text)
                if m:
                    target_items.append((key, text[m.end():], m.end()))

        for key, rest_raw, end_pos in target_items:
            if key in fields:
                continue

            # Look for unit on this chunk (or full line if single column)
            unit_raw = None
            if key != "ph":
                um = UNIT_RE.search(rest_raw)
                if not um and not distinct_hits:
                    um = UNIT_RE.search(text)
                if um:
                    unit_raw = canonical_unit_token(um.group(1))

            rest = RATIO_RE.sub(" ", rest_raw)
            oxide = bool(OXIDE_RE.search(rest))
            rest_clean = OXIDE_RE.sub(" ", rest)

            tok = _extract_number_from_tokens(rest_clean, key)
            val_line = norm_lines[idx]
            garbled = None

            if not tok:
                # Check for garbled numbers
                gm = GARBLED_RE.search(rest_clean)
                if gm and re.search(r"[OoIl|SB]", gm.group(0)):
                    garbled = gm.group(0)
                else:
                    # Multi-line cell lookahead (e.g. label on one line, value on next line like pH or OC)
                    for offset in range(1, 4):
                        if idx + offset >= len(norm_lines):
                            break
                        nxt_line = norm_lines[idx + offset]
                        nxt = nxt_line["text"]

                        # If next line has its own explicit label for this nutrient, don't steal from next line
                        if _first_label(key, nxt):
                            break

                        if not unit_raw and key != "ph":
                            nxt_um = UNIT_RE.search(nxt)
                            if nxt_um:
                                unit_raw = canonical_unit_token(nxt_um.group(1))

                        nxt_clean = OXIDE_RE.sub(" ", RATIO_RE.sub(" ", nxt))
                        cand_num = _extract_number_from_tokens(nxt_clean, key)
                        if cand_num is not None:
                            tok = cand_num
                            val_line = nxt_line
                            break

            if not tok and not garbled:
                continue

            # Determine unit if not found on current line
            if not unit_raw and key != "ph":
                unit_raw = _find_header_unit(norm_lines, idx, key)

            # Build field object
            f = {"field": key, "label": FIELDS[key]["label"], "line_index": idx, "extraction_issues": []}
            if garbled:
                f.update(ocr_value=garbled, value=None, unit=None, ocr_confidence=_word_conf(line_info["words"], garbled))
                f["extraction_issues"].append({
                    "code": "ocr_parse_error", "severity": "warning",
                    "message": f"Could not read '{garbled}' as a number. Please enter the value."
                })
            else:
                val, iss = _parse_number(tok)
                f.update(ocr_value=tok, value=val, unit=unit_raw,
                         ocr_confidence=_word_conf(val_line.get("words"), tok))
                f["extraction_issues"].extend(iss)
                if unit_raw is None and key != "ph":
                    f["extraction_issues"].append({
                        "code": "unit_not_found", "severity": "warning",
                        "message": "No unit found next to this value."
                    })

            if oxide:
                f["extraction_issues"].append({
                    "code": "oxide_basis", "severity": "warning",
                    "message": "Report appears to give this nutrient as an oxide (P2O5 / K2O). Not converted - please check."
                })

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

    return fields


def extract_metadata(lines):
    norm_lines = []
    for l in lines:
        t = normalize_tamil_text(l.get("text", "")).strip()
        norm_lines.append({"text": t})

    meta, text = {}, "\n".join(l["text"] for l in norm_lines)

    # Crop extraction
    m_crop = re.search(r"(?:crop\s*(?:name)?|பயிர்)\s*[:\-–—|]*\s*([A-Za-z .\u0B80-\u0BFF]+)", text, re.I)
    if m_crop:
        crop_val = m_crop.group(1).strip()
        meta["crop_raw"] = crop_val
        if "நிலக்கடலை" in crop_val or "நிலக்கடைல" in crop_val or "groundnut" in crop_val.lower():
            meta["crop"] = "groundnut"
        elif "நெல்" in crop_val or "paddy" in crop_val.lower() or "rice" in crop_val.lower():
            meta["crop"] = "paddy"
        elif "கரும்பு" in crop_val or "sugarcane" in crop_val.lower():
            meta["crop"] = "sugarcane"
        else:
            meta["crop"] = crop_val

    # Farm area extraction
    m_area = re.search(r"(?:farm\s*area|area|பரப்பு\s*\((?:ஏக்கர்|ஹெக்டேர்)\))\s*[:\-–—|]*\s*([0-9.]+)", text, re.I)
    if m_area:
        try:
            meta["farm_area"] = float(m_area.group(1).strip())
            meta["farm_area_unit"] = "acre" if "ஏக்கர்" in text else "ha"
        except ValueError:
            pass

    # Printed fertilizer recommendation extraction (from "உரப்பரிந்துரைகள்" section)
    in_fert = False
    fert_crop = None
    fert_unit = "kg/acre"
    fert_n, fert_p, fert_k = None, None, None

    for l in norm_lines:
        line_t = l["text"]
        if "உரப்பரிந்துரை" in line_t:
            in_fert = True
            m_fc = re.search(r"பயிர்\s*[:\-–—|]*\s*([A-Za-z .\u0B80-\u0BFF]+)", line_t)
            if m_fc:
                fert_crop = m_fc.group(1).strip()
        elif any(s in line_t for s in ("வேதியியல் பண்புகள்", "ஆய்வு முடிவுகள்", "ேபரூட்டச்சத்துக்கள் ஆய்வு", "பேரூட்டச்சத்துக்கள் ஆய்வு")):
            in_fert = False

        if in_fert:
            if "ஹெக்டேர்" in line_t or "kg/ha" in line_t.lower():
                fert_unit = "kg/ha"
            elif "ஏக்கர்" in line_t or "kg/acre" in line_t.lower():
                fert_unit = "kg/acre"

            # Nitrogen recommendation
            m_n = re.search(r"தழை\s*\(?\s*N\s*\)?\s*(\d+(?:\.\d+)?)", line_t, re.I)
            if m_n and fert_n is None:
                fert_n = float(m_n.group(1))

            # Phosphorus recommendation
            m_p = re.search(r"மணி\s*\(?\s*P[\s_0-9O]*\)?\s*(\d+(?:\.\d+)?)", line_t, re.I)
            if m_p and fert_p is None:
                fert_p = float(m_p.group(1))

            # Potassium recommendation
            m_k = re.search(r"சாம்பல்\s*\(?\s*K[\s_0-9O]*\)?\s*(\d+(?:\.\d+)?)", line_t, re.I)
            if m_k and fert_k is None:
                fert_k = float(m_k.group(1))

    if fert_n is not None or fert_p is not None or fert_k is not None:
        rec_crop = "Groundnut" if (fert_crop and any(k in fert_crop for k in ("நிலக்கடலை", "நிலக்கடைல", "groundnut"))) else (meta.get("crop") or "Groundnut")
        meta["printed_recommendation"] = {
            "crop": rec_crop,
            "unit": fert_unit,
            "nitrogen_kg_per_acre": fert_n if fert_unit == "kg/acre" else (round(fert_n * 0.4046856422, 2) if fert_n else None),
            "p2o5_kg_per_acre": fert_p if fert_unit == "kg/acre" else (round(fert_p * 0.4046856422, 2) if fert_p else None),
            "k2o_kg_per_acre": fert_k if fert_unit == "kg/acre" else (round(fert_k * 0.4046856422, 2) if fert_k else None),
            "n": fert_n,
            "p2o5": fert_p,
            "k2o": fert_k,
            "source": "Uploaded Soil Health Card"
        }

    # Standard metadata patterns
    for k, pat in META_PATTERNS.items():
        for idx, l in enumerate(norm_lines):
            m = re.search(pat, l["text"], re.I)
            if m:
                # Group 1 or group 2 match
                val = (m.group(1) if m.group(1) else (m.group(2) if len(m.groups()) > 1 and m.group(2) else m.group(0))).strip(" .:|-")
                if not val and idx + 1 < len(norm_lines):
                    val = norm_lines[idx + 1]["text"].strip(" .:|-")
                if val:
                    if k == "farmer_name":
                        sm = re.search(r"\(([A-Za-z0-9/\-_]+)\)", val)
                        if sm and "sample_id" not in meta:
                            meta["sample_id"] = sm.group(1)
                            val = val[:sm.start()].strip()
                        if any(ign in val.lower() for ign in ("department", "laboratory", "government", "plot address", "soil testing", "tamil nadu", "soil health")):
                            continue
                    meta[k] = val
                    break

    # Sample ID recovery across document if not matched
    if "sample_id" not in meta:
        sm = re.search(r"\b([A-Za-z0-9]{3,4}[-/]\d{3,4}[-/]\d{4,}[A-Za-z0-9]*)\b|\b(TN/[A-Za-z0-9/_\-]+)\b|\b(SHC\d{4}[A-Za-z0-9\-_]+)\b", text)
        if sm:
            meta["sample_id"] = (sm.group(1) or sm.group(2) or sm.group(3)).strip()

    # Survey number fallback if not matched
    if "survey_number" not in meta:
        m_surv = re.search(r"(?:survey|புல|சர்வே|பட்டா|ptbata|patta)\s*(?:no\.?|number|#)?\s*[:\-–—|#]*\s*([0-9]+(?:\s*[/]\s*[0-9]+)?)", text, re.I)
        if m_surv:
            meta["survey_number"] = m_surv.group(1).strip()

    # Comprehensive Tamil Nadu district aliases, Tamil names, and major agricultural taluks
    tn_district_map = {
        "ariyalur": "Ariyalur", "அரியலூர்": "Ariyalur",
        "chengalpattu": "Chengalpattu", "செங்கல்பட்டு": "Chengalpattu",
        "chennai": "Chennai", "சென்னை": "Chennai",
        "coimbatore": "Coimbatore", "colmbatore": "Coimbatore", "கோயம்புத்தூர்": "Coimbatore", "கோவை": "Coimbatore", "pollachi": "Coimbatore",
        "cuddalore": "Cuddalore", "கடலூர்": "Cuddalore",
        "dharmapuri": "Dharmapuri", "தருமபுரி": "Dharmapuri",
        "dindigul": "Dindigul", "திண்டுக்கல்": "Dindigul", "palani": "Dindigul",
        "erode": "Erode", "fredes": "Erode", "frodes": "Erode", "perundurai": "Erode", "perunduea": "Erode", "bhavani": "Erode", "gobichettipalayam": "Erode", "sathyamangalam": "Erode", "ஈரோடு": "Erode",
        "kallakurichi": "Kallakurichi", "கள்ளக்குறிச்சி": "Kallakurichi",
        "kancheepuram": "Kancheepuram", "kanchipuram": "Kancheepuram", "காஞ்சிபுரம்": "Kancheepuram",
        "kanniyakumari": "Kanniyakumari", "kanyakumari": "Kanniyakumari", "கன்னியாகுமரி": "Kanniyakumari", "nagercoil": "Kanniyakumari",
        "karur": "Karur", "கரூர்": "Karur",
        "krishnagiri": "Krishnagiri", "கிருஷ்ணகிரி": "Krishnagiri", "hosur": "Krishnagiri",
        "madurai": "Madurai", "மதுரை": "Madurai",
        "mayiladuthurai": "Mayiladuthurai", "மயிலாடுதுறை": "Mayiladuthurai",
        "nagapattinam": "Nagapattinam", "நாகப்பட்டினம்": "Nagapattinam",
        "namakkal": "Namakkal", "நாமக்கல்": "Namakkal",
        "perambalur": "Perambalur", "பெரம்பலூர்": "Perambalur",
        "pudukkottai": "Pudukkottai", "புதுக்கோட்டை": "Pudukkottai",
        "ramanathapuram": "Ramanathapuram", "ராமநாதபுரம்": "Ramanathapuram",
        "ranipet": "Ranipet", "ராணிப்பேட்டை": "Ranipet",
        "salem": "Salem", "சேலம்": "Salem",
        "sivagangai": "Sivagangai", "sivaganga": "Sivagangai", "சிவகங்கை": "Sivagangai",
        "tenkasi": "Tenkasi", "தென்காசி": "Tenkasi",
        "thanjavur": "Thanjavur", "tanjore": "Thanjavur", "தஞ்சாவூர்": "Thanjavur", "kumbakonam": "Thanjavur",
        "the nilgiris": "The Nilgiris", "nilgiris": "The Nilgiris", "நீலகிரி": "The Nilgiris", "ooty": "The Nilgiris",
        "theni": "Theni", "தேனி": "Theni",
        "thoothukudi": "Thoothukudi", "tuticorin": "Thoothukudi", "தூத்துக்குடி": "Thoothukudi",
        "tiruchirappalli": "Tiruchirappalli", "trichy": "Tiruchirappalli", "திருச்சிராப்பள்ளி": "Tiruchirappalli", "திருச்சி": "Tiruchirappalli",
        "tirunelveli": "Tirunelveli", "nellai": "Tirunelveli", "திருநெல்வேலி": "Tirunelveli",
        "tirupathur": "Tirupathur", "திருப்பத்தூர்": "Tirupathur",
        "tiruppur": "Tiruppur", "tirupur": "Tiruppur", "திருப்பூர்": "Tiruppur", "avinashi": "Tiruppur",
        "tiruvallur": "Tiruvallur", "திருவள்ளூர்": "Tiruvallur",
        "tiruvannamalai": "Tiruvannamalai", "திருவண்ணாமலை": "Tiruvannamalai",
        "tiruvarur": "Tiruvarur", "திருவாரூர்": "Tiruvarur",
        "vellore": "Vellore", "வேலூர்": "Vellore",
        "villupuram": "Villupuram", "விழுப்புரம்": "Villupuram",
        "virudhunagar": "Virudhunagar", "விருதுநகர்": "Virudhunagar",
    }
    raw_d = (meta.get("district") or "").strip().lower()
    if raw_d in tn_district_map:
        meta["district"] = tn_district_map[raw_d]
    elif "district" not in meta or meta["district"] not in tn_district_map.values():
        for alias, can_dist in tn_district_map.items():
            if re.search(rf"\b{re.escape(alias)}\b", text, re.I):
                meta["district"] = can_dist
                break

    # Village fallback
    if "village" not in meta:
        m_v = re.search(r"\b(Sugalur|Varathanallur|Avinashi|Marappampalayam|Alangudi|Orathanadu)\b", text, re.I)
        if m_v:
            meta["village"] = m_v.group(1).title()

    # Crop fallback if invalid or Dut Bru
    if not meta.get("crop") or meta.get("crop") in ("Dut Bru", "Bru"):
        if meta.get("printed_recommendation", {}).get("crop"):
            meta["crop"] = meta["printed_recommendation"]["crop"].lower()
        else:
            meta["crop"] = "groundnut"

    meta["test_date"] = parse_report_date(meta.pop("test_date_raw", None))
    for l in norm_lines:
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
