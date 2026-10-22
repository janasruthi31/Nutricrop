import json
import pytest
from fastapi.testclient import TestClient
from phase3_soil.main import app

client = TestClient(app)

def test_auth_registration_and_login():
    email = "testfarmer_auth@tnsih.agri"
    pwd = "SecretPassword123"

    # Register
    reg_res = client.post("/api/auth/register", json={
        "email": email,
        "password": pwd,
        "full_name": "Murugan Shanmugam",
        "phone": "+91 94441 23456",
        "preferred_language": "ta",
        "district": "Thanjavur"
    })
    # If already exists from prior test runs, register might return 400 or 200
    if reg_res.status_code == 200:
        data = reg_res.json()
        assert data["status"] == "SUCCESS"
        assert data["email"] == email

    # Login
    login_res = client.post("/api/auth/login", json={
        "email": email,
        "password": pwd
    })
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["status"] == "SUCCESS"
    assert "token" in login_data
    assert login_data["district"] == "Thanjavur"

def test_yield_meta_and_predict():
    # Meta
    meta_res = client.get("/api/yield/meta")
    assert meta_res.status_code == 200
    meta = meta_res.json()
    assert "districts" in meta
    assert "Thanjavur" in meta["districts"]
    assert "Rice" in meta["crops"]

    # Predict
    pred_res = client.post("/api/yield/predict", json={
        "district": "Thanjavur",
        "crop": "Rice",
        "season": "Samba/Thaladi/Pishanam",
        "year": 2024,
        "rain_swm": 330.0,
        "rain_nem": 640.0,
        "rain_winter": 40.0,
        "rain_hot": 150.0,
        "rain_annual": 1160.0
    })
    assert pred_res.status_code == 200
    pred = pred_res.json()
    assert pred["status"] == "SUCCESS"
    assert pred["district"] == "Thanjavur"
    assert pred["crop"] == "Rice"
    assert pred["unit"] == "kg/ha"
    assert pred["estimated_yield_kg_per_ha"] > 1000

from phase7_integration.extra_api import _create_jwt_token
from phase3_soil import db


def test_farm_and_fertilizer_history():
    token = _create_jwt_token("test_farmer_unit", "unit@test.tn", expire_seconds=3600)
    headers = {"Authorization": f"Bearer {token}"}

    # Save Farm
    farm_res = client.post("/api/farmer/farm", headers=headers, json={
        "district": "Tiruvarur",
        "village": "Needamangalam",
        "area": 2.5,
        "area_unit": "acre",
        "irrigation": "Irrigated",
        "soil_series": "Adanur"
    })
    assert farm_res.status_code == 200

    # Get Farm
    get_farm = client.get("/api/farmer/farm", headers=headers)
    assert get_farm.status_code == 200
    assert get_farm.json()["district"] == "Tiruvarur"

    # Add Fertilizer History
    fert_res = client.post("/api/farmer/fertilizer-history", headers=headers, json={
        "crop": "Rice",
        "season": "Kuruvai",
        "year": 2023,
        "fertilizer_product": "Urea",
        "quantity": 100.0,
        "unit": "kg",
        "application_date": "2023-08-15",
        "notes": "Basal application"
    })
    assert fert_res.status_code == 200
    item_id = fert_res.json()["id"]

    # List History
    list_res = client.get("/api/farmer/fertilizer-history", headers=headers)
    assert list_res.status_code == 200
    history = list_res.json()
    assert any(h["id"] == item_id for h in history)


def test_recommendation_save_and_pdf():
    token = _create_jwt_token("test_farmer_unit", "unit@test.tn", expire_seconds=3600)
    headers = {"Authorization": f"Bearer {token}"}

    # Full Recommendation payload
    mock_payload = {
        "crop": "Rice",
        "district": "Thanjavur",
        "nutrient_requirements": {
            "net_n_kg_per_ha": 120.0,
            "net_p2o5_kg_per_ha": 40.0,
            "net_k2o_kg_per_ha": 40.0,
            "farm_area_hectares": 1.0,
            "total_farm_n_kg": 120.0,
            "total_farm_p2o5_kg": 40.0,
            "total_farm_k2o_kg": 40.0,
            "calculation_method": "STCR-IPNS",
            "selected_rule_id": "TNAU_STCR_IPNS_RICE_001"
        },
        "fertilizer_plan": {
            "total_cost_inr": 3450.0,
            "recommended_products": [
                {"name": "Neem Coated Urea", "quantity_kg": 135.0, "bags": 3, "bag_size_kg": 45, "total_cost_inr": 799.50},
                {"name": "Di-Ammonium Phosphate (DAP)", "quantity_kg": 87.0, "bags": 2, "bag_size_kg": 50, "total_cost_inr": 2700.0}
            ]
        },
        "district_yield_prediction": {
            "estimated_yield_kg_per_ha": 4200.0
        },
        "weather_guidance": {
            "actionable_advice": "Fair weather for basal application.",
            "risk_level": "LOW",
            "current_condition": "Clear"
        }
    }

    # Save
    save_res = client.post("/api/recommendations", headers=headers, json=mock_payload)
    assert save_res.status_code == 200
    rec_id = save_res.json()["recommendation_id"]

    # List
    list_res = client.get("/api/recommendations", headers=headers)
    assert list_res.status_code == 200
    assert any(r["recommendation_id"] == rec_id for r in list_res.json())

    # Get details
    get_res = client.get(f"/api/recommendations/{rec_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["crop"] == "Rice"

    # PDF Download
    pdf_res = client.get(f"/api/recommendations/{rec_id}/pdf", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert len(pdf_res.content) > 1000
    assert pdf_res.content.startswith(b"%PDF")


def test_unauthenticated_requests_rejected():
    # Requests without Authorization or with arbitrary strings must return 401 Unauthorized
    res = client.get("/api/recommendations")
    assert res.status_code == 401
    assert "authentication required" in res.json()["detail"].lower()

    # Reject caller-controlled X-Farmer-Id header
    res_hdr = client.get("/api/recommendations", headers={"X-Farmer-Id": "fake_farmer_123"})
    assert res_hdr.status_code == 401

    # Reject arbitrary non-JWT string in Authorization
    res_raw = client.get("/api/recommendations", headers={"Authorization": "Bearer arbitrary_user_id"})
    assert res_raw.status_code == 401

    res_pdf = client.get("/api/recommendations/REC_TEST123/pdf")
    assert res_pdf.status_code == 401

    res_farm = client.get("/api/farmer/farm")
    assert res_farm.status_code == 401


def test_cross_user_data_isolation():
    token_a = _create_jwt_token("test_farmer_alice", "alice@test.tn", expire_seconds=3600)
    token_b = _create_jwt_token("test_farmer_bob", "bob@test.tn", expire_seconds=3600)
    farmer_a_headers = {"Authorization": f"Bearer {token_a}"}
    farmer_b_headers = {"Authorization": f"Bearer {token_b}"}

    # Farmer A creates a saved recommendation
    payload = {
        "crop": "Sugarcane",
        "district": "Coimbatore",
        "nutrient_requirements": {"n_req_kg_per_ha": 250.0},
        "fertilizer_plan": {"total_cost_inr": 8500.0, "recommended_products": []}
    }
    create_res = client.post("/api/recommendations", headers=farmer_a_headers, json=payload)
    assert create_res.status_code == 200
    rec_id = create_res.json()["recommendation_id"]

    # Farmer A can retrieve it
    get_a = client.get(f"/api/recommendations/{rec_id}", headers=farmer_a_headers)
    assert get_a.status_code == 200

    # Farmer B attempts to retrieve Farmer A's recommendation -> 403 Forbidden!
    get_b = client.get(f"/api/recommendations/{rec_id}", headers=farmer_b_headers)
    assert get_b.status_code == 403
    assert "forbidden" in get_b.json()["detail"].lower()

    # Farmer B attempts to download Farmer A's PDF -> 403 Forbidden!
    pdf_b = client.get(f"/api/recommendations/{rec_id}/pdf", headers=farmer_b_headers)
    assert pdf_b.status_code == 403
    assert "forbidden" in pdf_b.json()["detail"].lower()


def test_duplicate_registration_and_invalid_login():
    email = "unique_farmer_999@tnsih.agri"
    pwd = "StrongPassword456"

    # Register first time
    r1 = client.post("/api/auth/register", json={
        "email": email, "password": pwd, "full_name": "Unique Farmer"
    })
    # Duplicate registration must return 400
    r2 = client.post("/api/auth/register", json={
        "email": email, "password": pwd, "full_name": "Duplicate Farmer"
    })
    assert r2.status_code == 400
    assert "already exists" in r2.json()["detail"].lower()

    # Login with wrong password must return 401
    r_bad = client.post("/api/auth/login", json={
        "email": email, "password": "WrongPassword999"
    })
    assert r_bad.status_code == 401
    assert "invalid email or password" in r_bad.json()["detail"].lower()


def test_jwt_tampering_and_expiration():
    # Insert farmer_jwt_valid into database first
    with db.connect() as con:
        con.execute(
            "INSERT OR REPLACE INTO users (user_id, email, password_hash, full_name, phone, preferred_language, district, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            ("farmer_jwt_valid", "jwt@valid.tn", "dummy_hash", "JWT Farmer", "+91 90000 11111", "en", "Thanjavur", "2026-01-01T00:00:00", "2026-01-01T00:00:00")
        )

    # 1. Valid token
    valid_token = _create_jwt_token("farmer_jwt_valid", "jwt@valid.tn", expire_seconds=3600)
    res_valid = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {valid_token}"})
    assert res_valid.status_code == 200
    assert res_valid.json()["email"] == "jwt@valid.tn"

    # 2. Tampered token signature
    parts = valid_token.split(".")
    tampered_token = f"{parts[0]}.{parts[1]}.tampered_signature_xyz"
    res_tampered = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {tampered_token}"})
    assert res_tampered.status_code == 401
    assert "tampered" in res_tampered.json()["detail"].lower()

    # 3. Expired token (expire_seconds = -100)
    expired_token = _create_jwt_token("farmer_jwt_expired", "jwt@expired.tn", expire_seconds=-100)
    res_expired = client.get("/api/auth/profile", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_expired.status_code == 401
    assert "expired" in res_expired.json()["detail"].lower()

    # 4. Logout endpoint
    logout_res = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {valid_token}"})
    assert logout_res.status_code == 200
    assert logout_res.json()["status"] == "SUCCESS"


def test_forgot_password_and_reset_flow():
    from phase7_integration.extra_api import _hash_password
    import time
    email = f"farmer_reset_{int(time.time())}@tnsih.agri"
    pwd_old = "OldPassword123"
    pwd_new = "BrandNewPassword456"

    # Register user if not exists
    client.post("/api/auth/register", json={
        "email": email, "password": pwd_old, "full_name": "Reset Test Farmer"
    })
    with db.connect() as con:
        u_row = con.execute("SELECT user_id FROM users WHERE email = ?", (email,)).fetchone()
        user_id = u_row["user_id"]

    # 1. Forgot password request (anti-enumeration: returns SUCCESS even if email exists or not)
    forgot_res = client.post("/api/auth/forgot-password", json={"email": email})
    assert forgot_res.status_code == 200
    data = forgot_res.json()
    assert data["status"] == "SUCCESS"
    assert "recovery instructions" in data["message"].lower()

    # Insert a known test OTP hash into password_resets for testing deterministic verification
    test_otp = "654321"
    now_ts = int(time.time())
    with db.connect() as con:
        con.execute(
            """INSERT OR REPLACE INTO password_resets (id, email, user_id, token_hash, expires_at, used, created_at)
               VALUES (?, ?, ?, ?, ?, 0, ?)""",
            (f"RESET_{int(time.time())}", email, user_id, _hash_password(test_otp), now_ts + 900, "2026-01-01T00:00:00")
        )

    # 2. Reset password with wrong OTP -> 400
    bad_reset = client.post("/api/auth/reset-password", json={
        "email": email, "reset_token": "999999", "new_password": pwd_new
    })
    assert bad_reset.status_code == 400

    # 3. Reset password with correct OTP -> 200
    good_reset = client.post("/api/auth/reset-password", json={
        "email": email, "reset_token": test_otp, "new_password": pwd_new
    })
    assert good_reset.status_code == 200
    assert good_reset.json()["status"] == "SUCCESS"

    # 4. Login with old password fails
    fail_login = client.post("/api/auth/login", json={"email": email, "password": pwd_old})
    assert fail_login.status_code == 401

    # 5. Login with new password succeeds
    ok_login = client.post("/api/auth/login", json={"email": email, "password": pwd_new})
    assert ok_login.status_code == 200


def test_admin_database_access_lockdown():
    # Public anonymous access to /db must be blocked (403 Forbidden)
    res_db = client.get("/db")
    assert res_db.status_code == 403

    # Public anonymous access to /api/db/status must be blocked (403 Forbidden)
    res_status = client.get("/api/db/status")
    assert res_status.status_code == 403

    # Attempting to access sensitive users table via diagnostic query must be blocked
    res_users = client.get("/db?table=users", headers={"X-Admin-Key": "tnau_agri_admin_secret_key_2026"})
    assert res_users.status_code == 403



