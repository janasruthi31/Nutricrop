# Mobile and Backend Run Guide (Localhost & Physical Device Execution)
**Application Name:** AgroWise AI  
**Project Reference:** SIH1639 — Sustainable Fertilizer Usage Optimizer for Higher Yield  

---

## 1. Starting the Python/FastAPI Backend

Ensure your Python virtual environment is activated and dependencies are installed:

```powershell
# 1. Activate virtual environment
.\venv\Scripts\Activate.ps1

# 2. Verify dependencies
pip install -r requirements.txt

# 3. Start backend API server binding to all network interfaces
uvicorn phase3_soil.main:app --host 0.0.0.0 --port 8000 --reload
```

* **Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
* **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)
* **Binding to `0.0.0.0`:** Essential so that mobile devices on your local Wi-Fi network can reach the server.

---

## 2. Connecting a Physical Android Phone on the Same Local Network

When running the Flutter app on a physical Android phone, **never use `127.0.0.1` or `localhost`** directly in the phone's API URL (as `localhost` on the phone refers to the phone itself, not your development laptop).

### Option A: Wi-Fi LAN Connection (Recommended for Wireless Testing)
1. **Find Laptop IP Address:**
   Run in PowerShell:
   ```powershell
   ipconfig
   ```
   Look for the `IPv4 Address` under your active Wi-Fi adapter (e.g., `192.168.1.45` or `10.1.144.51`).
2. **Windows Firewall Rule:**
   Allow inbound traffic on port 8000:
   ```powershell
   New-NetFirewallRule -DisplayName "FastAPI AgroWise AI (Port 8000)" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
   ```
3. **Verify from Phone Browser:**
   Open Chrome on your phone (connected to the same Wi-Fi) and navigate to `http://<YOUR_LAPTOP_IP>:8000/health`. You should see `{"status":"ok"}`.
4. **Launch Flutter App with Custom API URL:**
   ```powershell
   cd flutter_app
   flutter run -d <DEVICE_ID> --dart-define=SOIL_API_BASE=http://<YOUR_LAPTOP_IP>:8000
   ```
5. **Runtime Settings In-App:**
   You can also change or test the backend URL directly on the phone by navigating to **Settings -> Backend API Server** and entering your laptop's IP address.

### Option B: USB Cable Connection via ADB Reverse (Fast & Reliable)
If your phone is plugged in via USB with USB Debugging enabled:
```powershell
# Forward phone port 8000 to laptop port 8000
adb reverse tcp:8000 tcp:8000

# Run Flutter app using localhost
cd flutter_app
flutter run -d <DEVICE_ID> --dart-define=SOIL_API_BASE=http://127.0.0.1:8000
```
With `adb reverse`, network requests from the phone to `127.0.0.1:8000` are seamlessly routed over the USB cable to your laptop's backend server.

---

## 3. Running and Building the Flutter Application

### A. Run in Google Chrome (Web Preview)
```powershell
cd flutter_app
flutter pub get
flutter run -d chrome
```

### B. Run Automated Widget & Screen Tests
```powershell
cd flutter_app
flutter test
```

### C. Build Production Release Artifacts
```powershell
# Build standalone Android APK
flutter build apk --release

# Build production Web bundle
flutter build web --release
```
The compiled Android APK will be generated at:
`flutter_app/build/app/outputs/flutter-apk/app-release.apk`
