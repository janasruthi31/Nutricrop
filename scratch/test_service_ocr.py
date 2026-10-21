import sys, os
sys.path.insert(0, os.path.abspath('.'))
from phase3_soil.service import run_ocr

res = run_ocr('farmer_001', 'd325ca16fa1e4b158e21108dda96c326')
print('OCR Status:', res['status'])
print('Metadata:', res.get('metadata'))
print('Extracted Fields:')
for f in res.get('fields', []):
    if f.get('value') is not None or f.get('ocr_value') is not None:
        print(f"  {f['field']}: value={f['value']}, unit={f['unit']}, status={f['status']}")
