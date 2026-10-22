# OCR and Indic/Tamil PDF Generation Validation Report (Phases 11 & 12)

**Date:** 2026-10-21  
**Project:** AgroWise AI (OCR Extraction & Multilingual PDF Engine)  
**Status:** Validated, Unicode Confirmed, Binary-Checked  
**Technologies:** Tesseract OCR, Poppler (pdf2image), OpenCV, ReportLab, TrueType Indic Fonts (Nirmala.ttc / Noto Sans Tamil).

---

## 1. Executive Summary

Soil testing laboratories across Tamil Nadu issue Soil Health Cards in English and Tamil, as scanned physical documents or digital PDFs. Accurate digitisation without silent parameter corruption (e.g. swapping pH and EC or truncating decimal points) is critical for agricultural safety.

Furthermore, farmers require downloadable, printable advisory summaries in their native language (Tamil or Hindi). Previous ReportLab implementations crashed with `UnicodeEncodeError` when rendering Indic glyphs due to default Latin Helvetica encoding.

In Phases 11 & 12:
1. OCR extraction was fortified with multi-engine fallbacks, image quality filtering, and farmer confirmation checkpoints.
2. ReportLab PDF generation was upgraded with a dynamic Unicode font registry (`phase7_integration/pdf_fonts.py`) utilizing Windows `Nirmala.ttc` and Google `Noto Sans Tamil`, enabling seamless multilingual rendering of Tamil (`தமிழ்`), Hindi (`हिन्दी`), and English.

---

## 2. OCR Pipeline & System Dependency Management

### 2.1 System Binary Requirements & Discovery
Physical image processing requires external system binaries:
* **Tesseract OCR (v5.0+):** Required for optical character recognition on scanned paper photos.
* **Poppler (pdftoppm):** Required by `pdf2image` for rasterizing multipage PDF documents.

**Automated Binary Auto-Detection (`phase3_soil/ocr.py`):**
If `tesseract` is not in system `PATH`, the service automatically searches standard Windows install paths:
1. `os.environ.get("TESSERACT_CMD")`
2. `C:\Program Files\Tesseract-OCR\tesseract.exe`
3. `C:\Program Files (x86)\Tesseract-OCR\tesseract.exe`
4. `~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe`

### 2.2 Defensive Fallbacks & Clear Error Handling
* **Digital PDF Native Extraction:** Scans digital PDFs using `pypdf` / `fitz` before invoking OCR. If native text contains $\ge 8$ words, OCR execution is bypassed, eliminating unnecessary image rasterization.
* **Missing Binary Error Handling:** When Tesseract is missing and the document is a pure image without text metadata, the service raises `OcrUnavailable`, which `phase3_soil/api.py` catches and converts to a user-friendly **HTTP 503 Service Unavailable** with actionable installation instructions, avoiding unhandled 500 runtime crashes.

---

### 2.3 Image Preprocessing & Parameter Safety
Every uploaded report image passes through an OpenCV enhancement pipeline:
1. **Grayscale & Rescaling:** Scaled to a minimum width of 1,600 px via bicubic interpolation.
2. **Noise Reduction:** `cv2.fastNlMeansDenoising` preserves fine stroke boundaries while eliminating camera sensor noise.
3. **Deskewing:** Rotational correction using `cv2.minAreaRect` bounded to $[0.3^\circ, 10^\circ]$ to correct tilted camera angles without flipping pages.
4. **Binarization:** `cv2.threshold` with Otsu's optimal global thresholding.
5. **Quality Metrics:** Laplacian variance ($\sigma^2 < 30$ flags blurry images; width $< 800$ flags low resolution).

### 2.4 Integrity & Range Enforcement
Extracted parameters are validated against physiological bounds. Any value outside valid laboratory thresholds (e.g. $pH < 3.5$ or $> 10.5$, or confidence $< 80\%$) is marked `status: "UNCERTAIN"`, forcing the farmer to confirm or adjust the value on the review screen before calculating fertilizer requirements.

---

## 3. Indic & Tamil Unicode PDF Generation

### 3.1 Font Architecture & TrueType Registration
ReportLab core styles (`Helvetica`, `Times-Roman`) only support Latin-1 (CP1252) characters. Rendering Tamil strings (`தமிழ் உழவர் உரப்பரிந்துரை`) previously threw:
```
UnicodeEncodeError: 'latin-1' codec can't encode characters in position 0-3: ordinal not in range(256)
```

**Remediation (`phase7_integration/pdf_fonts.py`):**
A TrueType font registry dynamically locates and registers Indic fonts:
```python
# Primary: Windows System Nirmala UI TrueType Collection (subfont index 0)
pdfmetrics.registerFont(TTFont("Nirmala", "C:/Windows/Fonts/Nirmala.ttc", subfontIndex=0))
pdfmetrics.registerFont(TTFont("Nirmala-Bold", "C:/Windows/Fonts/Nirmalab.ttc", subfontIndex=0))
```
* **Supported Languages:** Tamil (`ta`), Hindi (`hi`), English (`en`).
* **Fallback Strategy:** If `Nirmala.ttc` or `NotoSansTamil-Regular.ttf` is not installed on the server, the generator applies character sanitization to render clean Latin transliterations rather than crashing.

---

### 3.2 Visual & Content Validation
The generated PDF report was downloaded and verified:
1. **Header:** Features bilingual title *"தமிழ்நாடு அரசு மண் பரிசோதனை & பயிர் உரப் பரிந்துரை அறிக்கை"* and English counterpart.
2. **Farmer Metadata:** Accurately prints farmer ID, district (`தஞ்சாவூர்`), village (`Needamangalam`), and farm area.
3. **Nutrient Target Table:** Clear tabular layout comparing Soil Test Values ($N, P, K$) with Required Nutrient Quantities ($FN, FP, FK$).
4. **Fertilizer Product Schedule:** Exact commercial product names (Neem Coated Urea, DAP, MOP), bag counts, package sizes, and split application timing.
5. **PDF Integrity:** Successfully generates valid `%PDF-1.4` binary stream over HTTP `GET /api/recommendations/{id}/pdf` with `content-type: application/pdf` and length $> 5,000$ bytes.
