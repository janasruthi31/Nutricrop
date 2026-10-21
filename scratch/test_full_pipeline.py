import sys, os
sys.path.insert(0, os.path.abspath("."))
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
from phase3_soil.ocr import run_ocr
import re

res = run_ocr('phase3_soil/private_storage/d325ca16fa1e4b158e21108dda96c326.jpg', 'image')
lines = res['lines']

from phase3_soil.extraction import LABELS, FIELDS

# Add parenthesized labels
updated_labels = dict(LABELS)
updated_labels["nitrogen"] = LABELS["nitrogen"] + [r"\(\s*N\s*\)"]
updated_labels["phosphorus"] = LABELS["phosphorus"] + [r"\(\s*P\s*\)"]
updated_labels["potassium"] = LABELS["potassium"] + [r"\(\s*K\s*\)"]
updated_labels["ph"] = LABELS["ph"] + [r"\(\s*pH\s*[\)}]?"]
updated_labels["ec"] = LABELS["ec"] + [r"\(\s*EC\s*[\)}]?"]
updated_labels["organic_carbon"] = LABELS["organic_carbon"] + [r"\(\s*[0O]c\s*[\)}]?"]
updated_labels["sulphur"] = LABELS["sulphur"] + [r"\(\s*S\s*\)"]
updated_labels["zinc"] = LABELS["zinc"] + [r"\(\s*Zn\s*\)"]
updated_labels["boron"] = LABELS["boron"] + [r"\(\s*B\s*\)"]
updated_labels["iron"] = LABELS["iron"] + [r"\(\s*Fe\s*\)"]
updated_labels["manganese"] = LABELS["manganese"] + [r"\(\s*Mn\s*\)"]
updated_labels["copper"] = LABELS["copper"] + [r"\(\s*Cu\s*\)"]

def parse_chunk_number(chunk, field_key=None):
    tokens = chunk.split()
    for ti, tk in enumerate(tokens):
        clean_tk = re.sub(r'^[^\d]+|[^\d.,]+$', '', tk)
        if not clean_tk:
            continue
        # Check decimal
        if re.match(r'^\d+[.,]\d+$', clean_tk):
            return clean_tk.replace(',', '.')
        # Check split decimal: '163' followed by '00' or '13' followed by '75'
        if re.match(r'^\d+$', clean_tk) and ti + 1 < len(tokens):
            next_tk = re.sub(r'^[^\d]+|[^\d.,]+$', '', tokens[ti+1])
            if re.match(r'^\d{2}$', next_tk):
                # not followed by range dash
                if not (ti + 2 < len(tokens) and tokens[ti+2] in ('-', '–', '—', 'to')):
                    return f'{clean_tk}.{next_tk}'
        # Check 3-digit pH/iron scale like 775 -> 7.75
        if re.match(r'^\d{3}$', clean_tk) and field_key in ('ph', 'iron') and clean_tk[0] in '3456789':
            return f'{clean_tk[0]}.{clean_tk[1:]}'
        if re.match(r'^\d+$', clean_tk):
            return clean_tk
    return None

extracted = {}
for l in lines:
    t = l['text']
    line_hits = []
    for k, pats in updated_labels.items():
        if k in extracted:
            continue
        for p in pats:
            for m in re.finditer(p, t, re.I):
                line_hits.append((m.start(), m.end(), k))
    line_hits.sort()
    distinct_hits = []
    for h in line_hits:
        if not distinct_hits or h[0] >= distinct_hits[-1][1]:
            distinct_hits.append(h)
    for i, (st, en, key) in enumerate(distinct_hits):
        if key in extracted:
            continue
        next_st = distinct_hits[i+1][0] if i+1 < len(distinct_hits) else len(t)
        chunk = t[en:next_st]
        num = parse_chunk_number(chunk, key)
        if num is not None:
            extracted[key] = num

print('Extracted dictionary:')
for k, v in extracted.items():
    print(f'  {k}: {v}')
