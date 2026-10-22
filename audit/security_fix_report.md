# Security Fix Report: AgroWise AI Security Hardening and Remediation

**Date:** 2026-10-21  
**Project:** AgroWise AI (Tamil Nadu Soil & Yield Optimization System)  
**Status:** Remediated & Verified  
**Audit Scope:** Authentication, Authorization, Database Diagnostics, Session Management, CORS, and Password Reset Flow.

---

## Executive Summary

A comprehensive security audit of AgroWise AI identified critical vulnerabilities in identity verification, database diagnostics exposure, CORS misconfiguration, and authentication session handling. Unauthenticated users were previously able to supply arbitrary strings as tokens or use caller-controlled headers to access farmer data, and production database tables could be browsed anonymously via `/db`.

All identified security defects have been systematically repaired, fortified with defensive security controls, and validated with regression tests.

---

## 1. Vulnerability Details & Remediations

### 1.1 Critical Vulnerability: Authentication Bypass & Arbitrary Identity Impersonation
* **Affected Component:** `phase7_integration/extra_api.py` (`_get_current_user_id()`, `_verify_jwt_token()`) and `phase3_soil/api.py` (`_guard()`).
* **Root Cause:** 
  1. The legacy implementation included an unverified fallback where any non-JWT token was assigned directly as an authenticated `user_id`:
     ```python
     # VULNERABLE LEGACY LOGIC:
     if token.count(".") == 2:
         ...
     else:
         user_id = token  # Attacker can supply "admin" or any farmer_id!
     ```
  2. The service accepted `X-Farmer-Id` headers without validating token authenticity or ownership.
  3. Profile endpoints fell back to mock data (`farmer_default`) when tokens were invalid instead of returning HTTP 401 Unauthorized.
* **Remediation Implemented:**
  - Removed all arbitrary string fallbacks. Tokens are now strictly parsed as standard signed JWTs (`header.payload.signature`).
  - Cryptographic verification via HMAC-SHA256 (`secrets.compare_digest` for timing-attack resistance) using `JWT_SECRET_KEY`.
  - Enforced token expiration (`exp` claim) validation.
  - Rejected missing, malformed, expired, or tampered tokens with HTTP 401 Unauthorized.
  - Caller-controlled `X-Farmer-Id` headers are strictly rejected as proof of identity unless accompanied by a verified JWT matching that identity.
  - Test bypass logic is completely isolated behind an explicit configuration environment variable (`AGRI_ALLOW_TEST_BYPASS="true"`) that defaults to `false` and cannot be enabled accidentally in production.
  - In `phase3_soil/api.py`, `_guard` validates JWT Bearer tokens and extracts claims before executing soil report operations.

---

### 1.2 Critical Vulnerability: Public Database Viewer & Schema Scraping
* **Affected Component:** `phase3_soil/main.py` (`/db`, `/api/db/status`).
* **Root Cause:**
  - Unauthenticated endpoints `/db` and `/api/db/status` allowed any remote user to browse SQLite database tables, schema definitions, and row counts.
  - Sensitive columns (including `users.password_hash`, user emails, phone numbers, and session records) were exposed publicly over HTTP.
* **Remediation Implemented:**
  - Disabled public database browsing by default.
  - Database diagnostics now require `ENABLE_ADMIN_DIAGNOSTICS="true"` AND a verified `X-Admin-Key` header matching `ADMIN_API_KEY`.
  - Added strict table allowlist enforcement (`ALLOWED_DIAGNOSTIC_TABLES`):
    - Permitted: `soil_profiles`, `soil_documents`, `recommendations`, `fertilizer_prices`.
    - Strictly Excluded: `users` and `password_resets` to guarantee zero exposure of password hashes, emails, or reset tokens.
  - Queries return HTTP 403 Forbidden on any unauthorized or anonymous access attempt.

---

### 1.3 High Vulnerability: Mocked Forgot Password Flow & Account Enumeration
* **Affected Component:** `login_screen.dart` and `phase7_integration/extra_api.py`.
* **Root Cause:**
  - The Flutter application previously displayed a mock success dialog ("Password reset instructions sent") without dispatching any backend request.
  - No server-side password reset protocol existed, leaving locked-out users stranded.
* **Remediation Implemented:**
  - Created a database-backed, anti-enumeration password recovery system:
    - `POST /api/auth/forgot-password`: Generates a cryptographically random 6-digit OTP (`secrets.randbelow(900000) + 100000`).
    - Stored as a PBKDF2-SHA256 hash in SQLite (`password_resets.token_hash`) with a 15-minute time-to-live (`expires_at`). Never stored in plaintext.
    - Rate-limited to a maximum of 3 requests per 15 minutes per email to mitigate brute-force attacks.
    - Anti-enumeration guarantee: Returns uniform HTTP 200 response regardless of whether the email address exists in the database.
    - `POST /api/auth/reset-password`: Verifies OTP hash, updates `password_hash`, marks the reset token as used (`used = 1`), and invalidates all prior sessions.
  - Updated Flutter `ApiClient` and `LoginScreen` to invoke the real backend recovery endpoints.

---

### 1.4 Medium Vulnerability: CORS Wildcard Misconfiguration
* **Affected Component:** `phase3_soil/main.py`.
* **Root Cause:**
  - `CORSMiddleware` configured `allow_origins=["*"]` alongside `allow_credentials=True`. Modern web security standards and browser engines reject credentialed requests with wildcard origins.
* **Remediation Implemented:**
  - Configured `allow_credentials=False` for wildcard origins in development, while supporting explicit domain lists in production via `ALLOWED_ORIGINS` environment variable.

---

### 1.5 Medium Vulnerability: Client Session Persistence & Token Leakage
* **Affected Component:** `flutter_app/lib/services/api_client.dart` & `splash_screen.dart`.
* **Root Cause:**
  - Tokens were stored only in ephemeral memory; app restart lost the session.
* **Remediation Implemented:**
  - Integrated `shared_preferences` for secure local session persistence.
  - Preserved token, authenticated user email, preferred language, and district.
  - Added `clearSession()` on logout which explicitly purges tokens and sensitive cached records.

---

## 2. Regression Test Verification Matrix

All security controls were tested using automated Pytest regression suites:

| Test Case | Scenario | Expected Outcome | Actual Result | Status |
| :--- | :--- | :--- | :--- | :--- |
| `test_unauthenticated_requests_rejected` | Request without Authorization header | HTTP 401 Unauthorized | HTTP 401 Unauthorized | **PASSED** |
| `test_unauthenticated_requests_rejected` | Request with caller `X-Farmer-Id` only | HTTP 401 Unauthorized | HTTP 401 Unauthorized | **PASSED** |
| `test_unauthenticated_requests_rejected` | Request with arbitrary non-JWT string | HTTP 401 Unauthorized | HTTP 401 Unauthorized | **PASSED** |
| `test_cross_user_data_isolation` | Farmer B accesses Farmer A's saved recommendation | HTTP 403 Forbidden | HTTP 403 Forbidden | **PASSED** |
| `test_cross_user_data_isolation` | Farmer B downloads Farmer A's PDF report | HTTP 403 Forbidden | HTTP 403 Forbidden | **PASSED** |
| `test_jwt_tampering_and_expiration` | Tampered token signature | HTTP 401 Unauthorized | HTTP 401 Unauthorized | **PASSED** |
| `test_jwt_tampering_and_expiration` | Expired JWT token | HTTP 401 Unauthorized | HTTP 401 Unauthorized | **PASSED** |
| `test_forgot_password_and_reset_flow` | Anti-enumeration forgot-password request | HTTP 200 generic message | HTTP 200 generic message | **PASSED** |
| `test_forgot_password_and_reset_flow` | Reset password with invalid OTP | HTTP 400 Bad Request | HTTP 400 Bad Request | **PASSED** |
| `test_forgot_password_and_reset_flow` | Reset password with valid OTP & login check | HTTP 200, old login 401 | HTTP 200, old login 401 | **PASSED** |
| `test_admin_database_access_lockdown` | Anonymous request to `/db` | HTTP 403 Forbidden | HTTP 403 Forbidden | **PASSED** |
| `test_admin_database_access_lockdown` | Anonymous request to `/api/db/status` | HTTP 403 Forbidden | HTTP 403 Forbidden | **PASSED** |
| `test_admin_database_access_lockdown` | Admin query targeting `users` table | HTTP 403 Forbidden | HTTP 403 Forbidden | **PASSED** |

---

## 3. Residual Risk & Production Guidance

1. **Production JWT Secret:** Set `JWT_SECRET_KEY` in production environment to a 256-bit cryptographically secure string (e.g., `openssl rand -hex 32`). Do not use default development strings.
2. **Admin Diagnostic Keys:** Ensure `ENABLE_ADMIN_DIAGNOSTICS` remains `false` in production deployment configurations unless required for internal monitoring.
3. **SMS / Email Gateway:** The backend password reset flow currently logs the OTP in diagnostic environments; hook up an enterprise SMS gateway (e.g. CDAC SMS Seva / Twilio / AWS SNS) by injecting the provider client into `_send_reset_notification()`.
