import sys, os
sys.path.insert(0, os.path.abspath("."))
from phase3_soil.tests import fixtures as fx
from phase3_soil import service, config
import tempfile, os, shutil, json

tmp = tempfile.mkdtemp()
db = os.path.join(tmp, "t.sqlite3")
config.STORAGE_DIR = os.path.join(tmp, "store")

up = service.upload("farmer_001", fx.png_bytes(fx.FULL), db)
run = service.run_ocr("farmer_001", up["document_id"], db)

with service.db.connect(db) as con:
    row = con.execute("SELECT fields_json, raw_text_redacted FROM soil_ocr_results").fetchone()
    print("RAW TEXT:\n", row["raw_text_redacted"])

for f in run["fields"]:
    if f["field"] == "potassium":
        print("POTASSIUM FIELD:", json.dumps(f, indent=2))

shutil.rmtree(tmp, ignore_errors=True)
