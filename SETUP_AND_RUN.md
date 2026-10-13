# Setup and Execution Guide

**Project Title:** AI-Based Soil-Specific Fertilizer Recommendation and Crop Yield Prediction System for Tamil Nadu Farmers  

---

## 1. System Requirements and Prerequisites

- **Operating System:** Windows 10/11, Ubuntu 20.04+, or macOS
- **Python:** Version 3.10 or 3.11 (tested on Python 3.11.0)
- **Flutter SDK:** Version 3.20.0 or higher (tested on Flutter 3.32.3 / Dart 3.8.1)
- **Git:** Version 2.30+
- **Optional OCR Dependencies (for real image/PDF parsing):**
  - Tesseract-OCR (`tesseract`)
  - Poppler utilities (`pdf2image` support)
  *(Note: All unit and automated tests include mock and QA fixture modes, so external OCR binaries are not required to run the test suite).*

---

## 2. Python Backend Setup

### Step 2.1: Create and Activate Virtual Environment
```bash
# In the project root directory
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Windows (Command Prompt):
.\venv\Scripts\activate.bat

# Linux / macOS:
source venv/bin/activate
```

### Step 2.2: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 2.3: Environment Configuration
Copy the provided `.env.example` template to `.env`:
```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```
Default parameters in `.env.example` use local SQLite storage and secure development defaults out of the box.

### Step 2.4: Launch FastAPI Backend Server
```bash
uvicorn phase3_soil.main:app --host 0.0.0.0 --port 8000 --reload
```
- **Health Check Endpoint:** `http://localhost:8000/health`
- **Interactive Swagger Documentation:** `http://localhost:8000/docs`

---

## 3. Flutter Mobile Application Setup

### Step 3.1: Navigate to Flutter Directory
```bash
cd flutter_app
```

### Step 3.2: Install Dart Dependencies
```bash
flutter pub get
```

### Step 3.3: Configure API Base URL
The backend connection host is configured in `flutter_app/lib/config.dart`:
```dart
// For local desktop / Chrome testing:
const String kDefaultApiBaseUrl = 'http://127.0.0.1:8000';

// For Android Emulator:
const String kAndroidEmulatorBaseUrl = 'http://10.0.2.2:8000';

// For physical device on local Wi-Fi:
// const String kDefaultApiBaseUrl = 'http://192.168.1.X:8000';
```

### Step 3.4: Launch Flutter Application
```bash
# Run on Chrome / Web browser:
flutter run -d chrome

# Run on Windows Desktop:
flutter run -d windows

# Run on connected Android / iOS device:
flutter run
```

---

## 4. Running the Automated Test Suite

### 4.1 Backend Pytest Suite
Run the 79 automated Python unit and integration tests:
```bash
# In the project root with virtual environment activated:
pytest
```
Expected output:
```text
======================== 79 passed, 5 warnings in 7.13s ========================
```

### 4.2 Flutter Static Analysis
Check Dart source code for warnings, dead code, and lints:
```bash
cd flutter_app
flutter analyze
```
Expected output:
```text
No issues found!
```

### 4.3 Flutter Widget & Unit Tests
Run the 18 automated Flutter UI and localization tests:
```bash
cd flutter_app
flutter test
```
Expected output:
```text
00:02 +18: All tests passed!
```

---

## 5. End-to-End Workflow Verification

1. **Authentication:**
   - Launch Flutter app, open Login screen, register a farmer or login with demo credentials (`testfarmer_auth@tnsih.agri` / `FarmerPass123!`).
2. **Soil Health Card Processing:**
   - Upload soil test report or choose manual entry. Review extracted pH, EC, Organic Carbon, Available N, P, K. Verify ratings (Low/Medium/High).
3. **Crop & Target Yield:**
   - Select crop (e.g., Rice, Cotton, Maize), input farm area (e.g., 2 Acres), and choose target yield.
4. **Agronomic NPK & Fertilizer Optimization:**
   - Review net N, P2O5, and K2O requirements calculated via TNAU STCR-IPNS equations.
   - Run cost optimizer to review subsidized bag allocations (Urea, DAP, MOP) with basal and top-dressing split schedules.
5. **Weather & Benchmark Yield:**
   - Review real-time Tamil Nadu agro-met advisory and regional crop yield benchmark (kg/ha).
6. **Download Report:**
   - Export bilingual PDF summary to device storage.
