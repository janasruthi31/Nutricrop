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

def test_farm_and_fertilizer_history():
    headers = {"Authorization": "Bearer test_farmer_unit"}

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
    headers = {"Authorization": "Bearer test_farmer_unit"}

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
