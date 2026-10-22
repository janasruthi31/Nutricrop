# AgroWise AI: Offline Capabilities & Airplane-Mode Verification Checklist (Task 4a)

AgroWise AI (SIH1639: "Sustainable Fertilizer Usage Optimizer for Higher Yield") is engineered to serve smallholder farmers in remote rural Tamil Nadu where cellular connectivity is intermittent.

---

## 1. Feature Connectivity Matrix

The table below delineates exactly which features require an active internet connection versus those that function seamlessly offline:

| Feature / Screen | Mode | Offline Behavior & Data Source | Requires Internet? |
| :--- | :--- | :--- | :--- |
| **Fertilizer Calculation & Recommendation** | **Offline & Live** | Served from on-device local cache or backend 3-hour district cache (`_RECOMMENDATION_CACHE`). When inputs match, recommendation generates in `< 2 ms`. | **No** (if cached) / Yes (first-time live calculation) |
| **Short Flow (விரைவு முறை)** | **Offline & Live** | Instant 3-step recommendation using TNAU blanket guidelines. Cached for offline usage. | **No** (after initial sync) |
| **Weather Guidance** | **Resilient Fallback** | 1. Fresh cache within **3 hours** (`CACHE_TTL_SECONDS = 10800`).<br>2. Beyond 3h: falls back to **TNAU Seasonal Agro-Climatology** with normal monthly temperatures and rainfall probabilities labeled `"seasonal estimate"`. | **No** (Never crashes; uses live API when available, seasonal estimate when offline) |
| **Tamil Voice Audio Guidance** | **Offline Capable** | Local conversational Tamil text template generated immediately; uses device TTS / cached audio script. | **No** |
| **Saved Recommendations History** | **Full Offline** | Stored in on-device SQLite / `SharedPreferences` cache. Farmers can review past recommendations anytime. | **No** |
| **PDF Report Generation** | **Full Offline** | Downloaded PDF reports are stored in local storage and can be viewed or printed via Bluetooth printer offline. | **No** |
| **Soil Health Card OCR (Upload)** | **Online Only** | High-precision computer vision, redaction, image deskewing, and Tesseract neural OCR engine require backend server processing. | **Yes** |
| **Reverse Geocoding / GPS Village Lookup** | **Online with Centroid Fallback** | GPS coordinates mapped to district via local Tamil Nadu centroid boundaries table if offline. | **No** (falls back to local centroid) |

---

## 2. Offline Request Queue & Resiliency Protocol

When a farmer submits a recommendation, profile update, or fertilizer history while disconnected:
1. **Network Guard (`_guard` in `api_client.dart`)**:
   - Automatically retries network requests up to **3 times** with exponential backoff (`300 ms * attempts`).
2. **Offline Request Queue**:
   - Failed requests are captured in `agri_offline_request_queue` in persistent storage.
   - Upon network reconnection, pending records are automatically synced with the server.
3. **Response Transparency**:
   - The UI and API explicitly label whether data is `"live"` or a `"seasonal estimate"`.

---

## 3. Airplane-Mode Quality Assurance Checklist

Follow this checklist during field verification or testing:

### Step 1: Baseline Online Synchronization
- [ ] Connect device to Wi-Fi or mobile data.
- [ ] Open AgroWise AI and log in as a farmer.
- [ ] View the dashboard: confirm live weather observation for your district is loaded.
- [ ] Run a sample recommendation for Rice (1.0 ha in Thanjavur).
- [ ] Verify recommendation displays and is saved.

### Step 2: Switch to Airplane Mode
- [ ] Turn on **Airplane Mode** (disable Wi-Fi, Mobile Data, and Bluetooth).
- [ ] Confirm no internet connection icon is active on the device.

### Step 3: Offline Verification Test Cases
- [ ] **Test Case 1 (Cached Recommendation)**:
  - Re-run the same calculation (Rice, 1.0 ha, Thanjavur).
  - *Expected Result*: Instant response loaded from 3-hour cache (`is_cached: true`).
- [ ] **Test Case 2 (Short Flow / No Soil Test)**:
  - Tap "Short Flow / விரைவு முறை".
  - Select Crop = Blackgram, Area = 1.0 acre.
  - Tap "Get Instant Recommendation".
  - *Expected Result*: Generates TNAU blanket recommendation with disclaimer.
- [ ] **Test Case 3 (Weather Resilience)**:
  - Open Weather screen or trigger weather guidance.
  - *Expected Result*: Does NOT show a network crash screen; displays the 3-hour cached data or TNAU seasonal climatology labeled `"seasonal estimate"`.
- [ ] **Test Case 4 (Tamil Voice Guidance)**:
  - On the recommendation result screen, tap `"பரிந்துரையை தமிழில் கேளுங்கள்"`.
  - *Expected Result*: Tamil audio voice dialog appears with spoken conversational Tamil text.
- [ ] **Test Case 5 (Local Dealer Custom Prices)**:
  - Expand "Enter Local Dealer Bag Prices" and enter custom rates (e.g. Urea ₹280, DAP ₹1400).
  - Tap "Re-calculate with My Prices".
  - *Expected Result*: Recalculates cost and updates bag breakdown using custom prices.
- [ ] **Test Case 6 (Offline History & PDF)**:
  - Open "History" tab: previously saved recommendations display offline.
  - Open previously generated PDF report: opens directly from local storage.
- [ ] **Test Case 7 (OCR Graceful Disabling)**:
  - Navigate to "Upload Card" and attempt upload.
  - *Expected Result*: Friendly error message: "OCR processing requires an active internet connection. Please use 'Short Flow' or manual entry while offline."

### Step 4: Reconnection & Sync
- [ ] Turn off Airplane Mode (reconnect to internet).
- [ ] App automatically drains `agri_offline_request_queue` and syncs pending farm records.
