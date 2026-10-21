import sys, os
sys.path.insert(0, os.path.abspath("."))
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
from phase3_soil.ocr import run_ocr
import re

res = run_ocr('phase3_soil/private_storage/d325ca16fa1e4b158e21108dda96c326.jpg', 'image')
lines = res['lines']

symbols = [
    ('nitrogen', [r'\bnitrogen\b', r'\(\s*N\s*\)', r'தழை', r'தைழ']),
    ('phosphorus', [r'\bphosph[oa]rus\b', r'\(\s*P\s*\)', r'மணி']),
    ('potassium', [r'\bpotassium\b', r'\(\s*K\s*\)', r'சாம்பல்', r'பொட்டாஷ்']),
    ('ph', [r'\bp\s?h\b', r'\(\s*pH\s*[\)}]?']),
    ('ec', [r'\be\.?c\b', r'\(\s*EC\s*[\)}]?']),
    ('organic_carbon', [r'\bo\.?c\b', r'\(\s*[0O]c\s*[\)}]?']),
    ('sulphur', [r'\bsul(?:ph|f)ur\b', r'\(\s*S\s*\)', r'கந்தகம்']),
    ('zinc', [r'\bzinc\b', r'\(\s*Zn\s*\)', r'துத்தநாக']),
    ('boron', [r'\bboron\b', r'\(\s*B\s*\)', r'போரான்']),
    ('iron', [r'\biron\b', r'\(\s*Fe\s*\)', r'இரும்பு']),
    ('manganese', [r'\bmanganese\b', r'\(\s*Mn\s*\)', r'மாங்கனீ']),
    ('copper', [r'\bcopper\b', r'\(\s*Cu\s*\)', r'தாமிர'])
]

all_labels = []
for k, pats in symbols:
    for p in pats:
        all_labels.append((k, p))

for l in lines:
    t = l['text']
    hits = []
    for k, p in all_labels:
        for m in re.finditer(p, t, re.I):
            hits.append((m.start(), m.end(), k))
    hits.sort()
    filtered = []
    for h in hits:
        if not filtered or h[0] >= filtered[-1][1]:
            filtered.append(h)
    if filtered:
        for i, (st, en, key) in enumerate(filtered):
            next_st = filtered[i+1][0] if i+1 < len(filtered) else len(t)
            chunk = t[en:next_st]
            print(f"Line '{l['text']}'\n   --> {key}: '{chunk.strip()}'")
