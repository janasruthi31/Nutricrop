# AgroWise AI — Physical Android Device & Local Network Run Guide

**Project:** AgroWise AI — AI-Based Soil-Specific Fertilizer Recommendation System  
**Audience:** Mobile Developers, Field Agronomists, QA Engineers  

---

## 1. Overview of Mobile Connectivity

When testing the AgroWise AI Flutter application on a physical Android device or emulator, `127.0.0.1` refers to the mobile device itself, not your development laptop. To connect the mobile app to your local FastAPI backend, choose either **Option A (Wi-Fi LAN)** or **Option B (USB Cable with ADB Reverse)**.

---

## 2. Option A: Wi-Fi LAN Connection (Recommended for Wireless Testing)

### Step 1: Start FastAPI Backend on all network interfaces
Open a PowerShell terminal in the project directory and bind uvicorn to `0.0.0.0`:
```powershell
.\venv\Scripts\uvicorn phase3_soil.main:app --host 0.0.0.0 --port 8000 --reload
```

### Step 2: Determine your laptop's Private LAN IPv4 Address
In PowerShell:
```powershell
ipconfig
```
Look for your active Wi-Fi adapter's **IPv4 Address** (e.g., `192.168.1.45` or `10.1.144.51`).

### Step 3: Configure Windows Defender Firewall
Ensure incoming traffic on TCP port 8000 is permitted through Windows Firewall:
```powershell
# Run in Administrator PowerShell:
New-NetFirewallRule -DisplayName "FastAPI AgroWise Port 8000" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
```

### Step 4: Run or Configure the Flutter Mobile App
Both your phone and laptop must be connected to the **same Wi-Fi router / mobile hotspot**.

**Method 1 — Build-time configuration:**
```bash
cd flutter_app
flutter run -d <your-device-id> --dart-define=SOIL_API_BASE=http://192.168.1.45:8000
```

**Method 2 — In-App Dynamic Server Settings:**
1. Open AgroWise AI on your phone.
2. Tap the **Settings** tab (Gear icon) in the bottom navigation bar.
3. Tap **Backend Server Configuration** (`DNS icon`).
4. Type `http://192.168.1.45:8000` and tap **Test & Save**.
5. The app verifies live connectivity with `/health` and immediately switches active traffic to your laptop.

---

## 3. Option B: USB Tethering with ADB Reverse (Fastest & Zero Network Lag)

If a shared Wi-Fi network is unavailable or restricted by enterprise AP isolation:

### Step 1: Connect your phone via USB
Ensure **USB Debugging** is turned ON in Android Developer Options.

### Step 2: Forward port 8000 from phone to laptop
In PowerShell / Command Prompt:
```bash
adb devices
adb reverse tcp:8000 tcp:8000
```

### Step 3: Run the Flutter app with default localhost
Because ADB reverse redirects the phone's port 8000 to the laptop:
```bash
cd flutter_app
flutter run -d <your-device-id> --dart-define=SOIL_API_BASE=http://127.0.0.1:8000
```

---

## 4. Troubleshooting Connectivity Issues

| Symptom | Cause | Solution |
|---|---|---|
| `ApiException: Could not reach server` | Backend listening on `127.0.0.1` only | Start uvicorn with `--host 0.0.0.0`. |
| Phone browser cannot open `http://<IP>:8000/health` | Windows Firewall blocking port 8000 | Add inbound firewall rule or temporarily set network profile to Private. |
| Connection times out on Wi-Fi | AP Client Isolation on router | Use mobile hotspot from phone to laptop, or use **Option B (USB Cable)**. |
| `ERR_CLEARTEXT_NOT_PERMITTED` | Android 9+ blocks plain HTTP by default | Verified: `AndroidManifest.xml` already includes `android:usesCleartextTraffic="true"`. |
| App logs out after closing | In-memory session destroyed | Update to use persistent secure storage; session will restore automatically. |

---

## 5. Production HTTPS Deployment Requirements

For production cloud deployment (AWS, GCP, Azure, DigitalOcean):
1. **Domain & SSL:** Deploy behind an Nginx reverse proxy with Let's Encrypt SSL (`https://api.agrowise.tn.gov.in`).
2. **Flutter Build:**
   ```bash
   flutter build apk --release --dart-define=SOIL_API_BASE=https://api.agrowise.tn.gov.in
   ```
3. **Android Security:** In production, disable `android:usesCleartextTraffic` in `AndroidManifest.xml` to mandate HTTPS.
