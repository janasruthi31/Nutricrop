# API Architecture, Database Schema, and Security Audit
**Application Name:** AgroWise AI  
**Project Reference:** SIH1639 — Sustainable Fertilizer Usage Optimizer for Higher Yield  
**Module:** Backend Architecture, Authentication, Object-Level Authorization & Database Security  

---

## 1. API Route Registry & Endpoint Contracts

The FastAPI backend exposes modular, OpenAPI-documented routes categorized by subsystem:

| HTTP Method | Route Path | Responsibility | Authentication Required | Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/health` | Service health status check | No | 200 |
| `POST`| `/api/auth/register` | Register farmer account with preferred language | No | 200, 400 |
| `POST`| `/api/auth/login` | Authenticate farmer and issue HMAC-SHA256 JWT | No | 200, 401 |
| `GET` | `/api/auth/profile` | Retrieve farmer account details | Yes (`Bearer`) | 200, 401 |
| `PUT` | `/api/auth/profile` | Update profile information and language | Yes (`Bearer`) | 200, 401 |
| `POST`| `/api/soil/upload` | Upload Soil Health Card (PDF/JPEG/PNG) | Yes (`Bearer`) | 200, 400, 413, 415, 422 |
| `POST`| `/api/soil/ocr` | Run multi-pass Tesseract OCR | Yes (`Bearer`) | 200, 404, 422, 503 |
| `POST`| `/api/soil/validate` | Dry-run field plausibility check | Yes (`Bearer`) | 200, 400, 422 |
| `POST`| `/api/soil/confirm` | Store farmer-confirmed soil profile | Yes (`Bearer`) | 200, 400, 404, 409, 422 |
| `GET` | `/api/soil/{profile_id}`| Retrieve confirmed soil profile | Yes (`Bearer`) | 200, 401, 404 |
| `POST`| `/api/agronomy/select-rule` | Query verified TNAU agronomic rules | No / Yes | 200, 400 |
| `POST`| `/api/nutrient-requirement/calculate` | Compute NPK requirements | No / Yes | 200, 400, 422 |
| `POST`| `/api/fertilizer/optimize` | Mixed-Integer LP whole-bag optimizer | No / Yes | 200, 400, 422 |
| `GET` | `/api/weather/guidance` | Live agro-weather timing advisory | No | 200, 400 |
| `POST`| `/api/full-recommendation`| End-to-end master orchestration pipeline | No / Yes | 200, 400, 422 |
| `GET` | `/api/recommendations` | List authenticated farmer's saved history | Yes (`Bearer`) | 200, 401 |
| `POST`| `/api/recommendations` | Save full recommendation record | Yes (`Bearer`) | 200, 401 |
| `GET` | `/api/recommendations/{id}/pdf` | Download official bilingual ReportLab PDF | Yes (`Bearer`) | 200, 401, 403, 404 |

---

## 2. Authentication, Password Security & JWT Implementation

1. **Password Hashing (PBKDF2-HMAC-SHA256):**
   - User passwords are never stored in plaintext.
   - Every password is salted with a 16-byte cryptographically secure pseudorandom token (`secrets.token_hex(16)`).
   - Key derivation executes 100,000 iterations of PBKDF2-HMAC-SHA256.
2. **Cryptographic JWT Tokens:**
   - Stateless authentication tokens are generated and verified via HMAC-SHA256 using the server's `JWT_SECRET`.
   - Tokens embed standard claims: `sub` (user_id), `email`, `iat` (issued at), and `exp` (expiration timestamp).
   - Tampered tokens (modified payload or forged signature) and expired tokens are rejected with `401 Unauthorized`.
3. **Object-Level Authorization (Anti-IDOR):**
   - Insecure Direct Object References (IDOR) are strictly prevented.
   - Every database query for recommendations, documents, and notifications filters by `WHERE user_id = ?` or verifies ownership before returning records.
   - If Farmer A attempts to query or download Farmer B's recommendation (`GET /api/recommendations/REC_XYZ/pdf`), the server rejects the request with `403 Forbidden`.

---

## 3. Upload & File Ingestion Security

1. **Binary Magic-Byte Sniffing:**
   - Client-provided file extensions and MIME headers are untrusted.
   - Files are validated by inspecting binary headers:
     * JPEG: `\xff\xd8\xff`
     * PNG: `\x89PNG\r\n\x1a\n`
     * PDF: `%PDF-`
   - Unsupported or executable file formats are rejected with `415 Unsupported Media Type`.
2. **Denial-of-Service (DoS) Ingestion Guards:**
   - Upload size limit: 10 MB (`413 Payload Too Large`).
   - PDF page limit: Maximum 10 pages.
   - Image pixel limit: Maximum 50 megapixels to prevent image decompression bombs.
3. **Path Traversal Protection:**
   - Original client filenames are discarded upon receipt.
   - Files are stored using server-generated UUIDv4 filenames in an isolated storage directory (`config.STORAGE_DIR`) with restricted file permissions (`0o600`).
4. **SHA-256 Deduplication:**
   - Every uploaded document is hashed with SHA-256. Duplicate uploads by the same farmer reuse the existing document ID rather than consuming redundant server storage.

---

## 4. Database Schema Integrity & Concurrency Analysis

### Relational Schema (SQLite: `soil_phase3.sqlite3`)
1. `users`: Stores user credentials, hashed passwords, and localization preferences.
2. `farmer_farms`: Holds farm acreage, district, taluk, village, and GPS coordinates.
3. `farmer_fertilizer_history`: Historical usage records and previous farm practices.
4. `saved_recommendations`: Full audit trail of verified recommendations, NPK targets, and MILP purchase plans.
5. `user_notifications`: User-specific agro-alerts and system notices.
6. `soil_documents`: Document upload registry, file paths, and MIME metadata.
7. `soil_ocr_results`: Raw extracted text, mean word confidence, and page segmentation modes.
8. `soil_profiles`: Confirmed soil profiles, lab metadata, and sample IDs.
9. `soil_profile_fields`: Detailed field-by-field audit tracking raw OCR value vs. confirmed value.
10. `weather_cache`: Cached Open-Meteo observations with expiration timestamps.
11. `fertilizer_prices`: Statutory subsidized MRP price registry with effective dates.

### Concurrency Characteristics & Deployment Recommendations
* **Current Engine:** SQLite with Write-Ahead Logging (WAL) mode.
* **Workload Capability:** SQLite handles thousands of concurrent reads and supports atomic transactions across related writes. It is fully suitable for single-node deployments, project demonstrations, and local testing.
* **Production Recommendation:** For statewide enterprise deployment serving tens of thousands of concurrent extension workers, migrating the relational schema to PostgreSQL is recommended to support multi-master writes and connection pooling without database file locking.
