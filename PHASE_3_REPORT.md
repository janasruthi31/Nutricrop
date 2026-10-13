# PHASE 3 REPORT - Soil Report OCR, Farmer Confirmation and Validation

## 0. Honest status
| Part | State |
|---|---|
| Backend: OCR (real Tesseract), extraction, units, validation, TNAU classification, SQLite, service layer | Implemented and **tested: 33/33 tests pass** (real Tesseract + real PDF rendering) |
| FastAPI router (`phase3_soil/api.py`, `main.py`) | Written and byte-compiled, **never executed**: FastAPI/uvicorn/httpx are not installed in the build sandbox and it had no network. The HTTP layer is a thin wrapper over the tested service functions. |
| Flutter app (4 screens + API client + validation logic + Dart tests) | Written, **never compiled or run**: no Flutter/Dart SDK in the sandbox. Expect to fix small compile errors on first build. |
| Phase 4 handoff | The validated profile JSON + `onValidatedProfile` callback. No fertilizer logic exists in Phase 3. |

Phase 3 should be called complete only after you run the API tests and the Flutter app once (see section 17).

## 1. Objective
Soil report (PDF/image/camera/manual) -> OCR -> extraction -> unit/method normalization -> validation -> "Extracted - Please Verify" -> farmer confirms/corrects -> final validation -> **validated soil profile**. Nothing downstream of that (no fertilizer type/dose/cost, no ML, XGBoost model untouched).

## 2. Architecture
Your package contained only the Phase 2 yield model (no backend, DB, auth or Flutter project), so Phase 3 is a self-contained package.
```
phase3_soil/  config.py  tnau_reference.py  units.py  classification.py  validation.py  crops.py
              extraction.py  ocr.py  db.py  service.py  api.py (FastAPI router)  main.py  tests/
flutter_app/  lib/{main,config}.dart  models/soil_field.dart  services/soil_api.dart  screens/*  test/
```
Mount in an existing FastAPI app with `app.include_router(soil_router)`. `crops.py` only reads `models/yield_prediction/metadata.json` (crop names) - the model file is never loaded or changed.

## 3. OCR workflow
upload (magic-byte sniffing, size/page limits, decode check) -> PDF pages rendered at 300 dpi (poppler) or image loaded (EXIF-rotated) -> OpenCV preprocessing (grayscale, upscale to >=1600 px width, denoise, deskew within 10 degrees, Otsu threshold) -> Tesseract 5 (`--oem 3 --psm 6`; if fewer than 3 fields are found, a second pass with `--psm 4` is tried and the better result kept) -> line reconstruction with per-word confidences -> regex field extraction -> normalization -> validation -> review payload.

## 4. Supported inputs
PDF (<=5 pages), JPG/JPEG, PNG, camera capture (Flutter `image_picker`), manual entry. Max 10 MB (configurable). Type is decided from file content, never the extension or MIME header.

## 5. Extracted fields
N, P (+ Olsen/Bray method), K, pH, OC, EC, S, Zn, Fe, Mn, Cu, B; district, village, sample ID, test date, laboratory, detected methods (Olsen, Bray, alkaline permanganate, Walkley-Black, ammonium acetate, DTPA). Farmer name and survey number are extracted for on-screen review only and are **never stored**. Anything not found stays `null` / `missing`.

## 6. Unit handling
Only exact conversions: ppm -> mg/kg, g/kg -> % (organic carbon only), uS/cm -> dS/m (EC only); mmhos/cm and mS/cm are treated as dS/m. **Never**: mg/kg <-> kg/ha, Olsen <-> Bray, P2O5/K2O conversion, kg/acre or lb/acre (flagged as unknown unit; the farmer must correct). N/P/K reported in mg/kg are kept as mg/kg and are not given a TNAU class (the thresholds are kg/ha). The original unit is retained as `original_unit`.

## 7. Validation rules
Statuses: `missing | invalid | uncertain | valid`.
- Not numeric -> invalid. Unit not accepted for the field -> uncertain at review, invalid at confirm.
- Outside physical range (e.g. pH outside 0-14, negative values) -> invalid, blocks confirmation.
- Outside "typical" range -> uncertain at review; after the farmer confirms it is accepted with a warning.
- Phosphorus method unknown -> uncertain at review; accepted at confirm with method `null` and **no classification**. Method other than Olsen/Bray -> invalid.
- Garbled OCR number (e.g. `28O`), decimal comma, P2O5/K2O basis, missing unit -> flagged uncertain with a message.
- Test date: must be a real YYYY-MM-DD date, not in the future; older than 3 years -> warning.
- District: normalised against the 38 names used by the Phase 2 model (aliases such as Trichy, Tuticorin); unrecognised -> warning. Crop (optional): checked against the Phase 2 crop list; unknown -> warning.
- Optional nutrients missing never block. Confirmation needs at least one value and no invalid field.
- `phase4_readiness.ready` is true only when N, P, K are present, the P method is known, and nothing is blocking.
- Duplicates: same file re-uploaded returns the existing document; same farmer + sample + date + values returns `409 DUPLICATE_SUBMISSION` with the existing profile id.

The "typical" and "physical" ranges are **engineering guard rails I chose, not TNAU values or agronomic advice**; have an agronomist review them (`tnau_reference.py`).

## 8. TNAU references
Thresholds implemented exactly as you specified: OC 0.5/0.75 %; N 280/450 kg/ha; K 118/280 kg/ha; Olsen P 11/22 kg/ha; Bray P 24.2/49.7 kg/ha. Low is `< lower`, High is `> upper`, Medium is inclusive of both bounds. **Verification caveat:** when I fetched https://agritech.tnau.ac.in/pdf/2.pdf, its text refers to the rating Tables 1 and 2 but the tables' numbers are not in the extracted text, so I could not independently confirm the figures. Please check them against the printed tables. Micronutrient, EC and pH ratings are not classified because no thresholds were specified.

## 9. Manual confirmation
Every field is an editable card with Accept / Edit / Reject. The server keeps the original OCR record and treats it as authoritative; the client sends only the farmer's final values plus an `action` and `farmer_confirmed: true`. Per field the profile stores `ocr_value`, `confirmed_value`, `modified_by_user`, `ocr_confidence`, `action`. OCR output never becomes `farmer_confirmed` without that explicit flag (the app also asks for a tick-box acknowledgement).

## 10. Database (SQLite, new)
`soil_documents` (private file path, kind, size, sha256, status, timestamps), `soil_ocr_results` (engine/version, psm, mean confidence, **redacted** text, fields JSON, quality metrics), `soil_profiles` (farmer, source, fingerprint, district, village, sample, test date, lab, crop, verification status, profile JSON, timestamps; unique per farmer+fingerprint), `soil_profile_fields` (per-field audit rows). No existing schema was present to integrate with.

## 11. API
| Endpoint | Purpose |
|---|---|
| `POST /api/soil/upload` | multipart `file` -> `{document_id, status:"uploaded"}` |
| `POST /api/soil/ocr` | `{document_id}` -> `{status:"extracted", verification_required:true, banner, fields[], metadata, warnings}` |
| `POST /api/soil/validate` | dry-run validation of edited values, nothing stored |
| `POST /api/soil/confirm` | farmer-confirmed values -> `{status:"validated", soil_profile_id, soil_profile}` |
| `GET /api/soil/{id}` | stored validated profile (owner only; other farmers get 404) |

Headers: `X-Farmer-Id` (required), `X-API-Key` (required if env `SOIL_API_KEY` is set). Errors: `{"error":{"code","message","details"}}`.

## 12. Flutter screens
Upload (PDF / Image / Take Photo / Enter Manually) -> Processing ("Reading your soil report...") -> Verify ("Review Extracted Soil Information", "Extracted - Please Verify", editable cards, "Confirm & Validate") -> Result (checklist, TNAU status, "Continue to Fertilizer Recommendation" calls `onValidatedProfile(profile)`).

## 13. Error handling
Unsupported type (415), empty/oversized file (400/413), corrupted PDF/image and encrypted PDF (422), too many pages, poor/blurry/low-resolution warnings, OCR empty (`OCR_EMPTY`) and no recognised fields (`OCR_NO_FIELDS`) with "Unable to reliably read the soil report. Please enter the values manually.", missing NPK warning, unknown unit, invalid number, unknown P method, network/server failures with retry and manual-entry fallback. No value is ever guessed.

## 14. Privacy and security
Files stored under a private directory (not served), random server names, mode 0600, original filename discarded; content-sniffed types; bounded reads; files are never executed. OCR text is stored with farmer/contact lines and phone/Aadhaar-like numbers redacted. Farmer name and survey number are not stored. Per-farmer ownership checks. **Authentication is a placeholder** (`X-Farmer-Id` header, optional API key) because no auth existed; replace it with your real auth before deployment, otherwise the farmer id is trivially spoofable.

## 15. Tests (33 backend, run on real OCR)
Required scenarios 1-15 (valid report, missing N/P/K, invalid pH, invalid number, unknown unit, Olsen, Bray, OCR correction, manual entry, invalid file, empty OCR, duplicate, successful validation for PNG/JPEG/PDF) plus unit-conversion safety, TNAU boundary values, P-method never guessed, metadata checks, comma/ratio/P2O5 parsing, redaction, farmer isolation, reject action, confirmation flag, blurry image. Result: **33 run, 33 passed** (about 57 s). Flutter: 7 Dart tests for validation/confirm-gate logic are written but **not run**. HTTP-level (FastAPI) tests are **not written or run**.

## 16. Known limitations
- Fixtures are clean synthetic renderings. **No OCR accuracy has been measured on real Soil Health Cards, and none is claimed.** Tesseract may misread real photos, Tamil-script cards (only English `eng` data is installed/used) or complex tables; the farmer-verification step exists for this reason.
- The stored per-field "confidence" is Tesseract's word confidence for the value token, not a probability of correctness.
- Field extraction is label-regex based; unusual layouts (values in separate columns/rows from labels) may be missed and appear as "not found".
- Digital PDFs are OCR'd from rendered pages rather than read from their text layer.
- Numeric dates are read as dd/mm/yyyy; the farmer verifies the date.
- kg/acre cards are not converted (flagged for manual entry).
- Authentication placeholder; SQLite only; no virus scanning or encryption at rest.

## 17. How to run and test
Backend (from the project root, with `tesseract-ocr` and `poppler-utils` installed):
```
pip install -r phase3_soil/requirements.txt
python -m unittest phase3_soil.tests.test_phase3 -v
uvicorn phase3_soil.main:app --host 0.0.0.0 --port 8000
```
Flutter:
```
cd flutter_app
flutter create . --platforms=android,ios      # generates platform folders around the supplied lib/ and pubspec.yaml
flutter pub get
flutter test
flutter run --dart-define=SOIL_API_BASE=http://10.0.2.2:8000 --dart-define=FARMER_ID=farmer_001
```
Add the camera permission (Android `CAMERA`, iOS `NSCameraUsageDescription`) and allow cleartext HTTP for local development.
Manual check: upload a report -> confirm the "Extracted - Please Verify" screen shows values -> edit one -> tick the box -> Confirm & Validate -> result screen -> `GET /api/soil/{id}` returns the profile with `audit` showing `modified_by_user: true` for the edited field.
