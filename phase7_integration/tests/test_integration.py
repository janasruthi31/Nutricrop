"""
Automated tests for Phase 7: Weather Guidance and End-to-End Master Pipeline Integration.
"""

import pytest
from fastapi.testclient import TestClient
from phase3_soil.main import app
from phase7_integration.service import get_full_recommendation
from phase7_integration.weather import get_weather_guidance

client = TestClient(app)


# 1. Weather guidance endpoint
def test_01_weather_guidance_endpoint():
    response = client.get("/api/weather/guidance?district=Thanjavur")
    assert response.status_code == 200
    data = response.json()
    assert data["district"] == "Thanjavur"
    assert "guidance_status" in data
    assert "advisory_en" in data
    assert "advisory_ta" in data


# 2. Master full recommendation pipeline service
def test_02_master_pipeline_service():
    payload = {
        "crop": "Rice",
        "district": "Thanjavur",
        "soil_series": "Palavidhi",
        "season": "Kharif",
        "irrigation_method": "Irrigated",
        "target_yield": 6.0,
        "soil_nitrogen": 220.0,
        "soil_phosphorus": 16.0,
        "soil_potassium": 190.0,
        "soil_phosphorus_method": "Olsen",
        "farm_area": 2.5,
        "farm_area_unit": "acre"
    }
    res = get_full_recommendation(payload)
    assert res["status"] == "SUCCESS"
    assert res["crop"] == "Rice"
    assert res["district"] == "Thanjavur"
    assert res["rule_selection"]["selected_rule_id"] == "TNAU_STCR_IPNS_RICE_001"
    assert res["nutrient_requirements"]["n_req_kg_per_ha"] > 0
    # Schema alias checks
    assert res["nutrient_requirements"]["net_n_kg_per_ha"] == res["nutrient_requirements"]["n_req_kg_per_ha"]
    assert res["nutrient_requirements"]["total_farm_n_kg"] == res["nutrient_requirements"]["total_n_req_kg"]
    assert res["nutrient_requirements"]["calculation_method"] is not None
    # Fertilizer product name checks
    products = res["fertilizer_plan"]["recommended_products"]
    assert len(products) > 0
    for prod in products:
        assert prod["product_name"]
        assert prod["name"] == prod["product_name"]
        assert prod["bags"] > 0
    assert res["district_yield_prediction"]["estimated_production_tonnes"] > 0
    # Weather guidance alias checks
    assert res["weather_guidance"]["guidance_status"] is not None
    assert res["weather_guidance"]["risk_level"] in ("LOW", "MEDIUM", "HIGH")
    assert res["weather_guidance"]["actionable_advice"] is not None


# 3. Master full recommendation API endpoint
def test_03_full_recommendation_api():
    payload = {
        "crop": "Cotton (lint)",
        "district": "Coimbatore",
        "soil_series": "Irugur",
        "season": "Kharif",
        "irrigation_method": "Irrigated",
        "target_yield": 2.5,
        "soil_nitrogen": 200.0,
        "soil_phosphorus": 14.0,
        "soil_potassium": 180.0,
        "soil_phosphorus_method": "Olsen",
        "farm_area": 1.0,
        "farm_area_unit": "hectare"
    }
    response = client.post("/api/full-recommendation", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["rule_selection"]["selected_rule_id"] == "TNAU_STCR_IPNS_COTTON_001"
    assert data["fertilizer_plan"]["total_cost_inr"] > 0

    # Save and test PDF report from real pipeline response
    headers = {"Authorization": "Bearer test_farmer_e2e"}
    save_res = client.post("/api/recommendations", headers=headers, json=data)
    assert save_res.status_code == 200
    rec_id = save_res.json()["recommendation_id"]

    pdf_res = client.get(f"/api/recommendations/{rec_id}/pdf", headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")


# 4. Live weather current and forecast endpoints
def test_04_live_weather_endpoints():
    curr_res = client.get("/api/weather/current?district=Erode&lat=11.341&lon=77.717")
    assert curr_res.status_code == 200
    curr_data = curr_res.json()
    assert curr_data["district"] == "Erode"
    assert "observation_time" in curr_data
    assert "source" in curr_data
    assert "current" in curr_data
    assert "temperature_c" in curr_data["current"]

    fc_res = client.get("/api/weather/forecast?district=Erode&lat=11.341&lon=77.717")
    assert fc_res.status_code == 200
    fc_data = fc_res.json()
    assert "forecast" in fc_data
    assert len(fc_data["forecast"]["days"]) > 0


# 5. Reverse geocoding endpoint
def test_05_reverse_geocode_endpoint():
    res = client.get("/api/location/reverse-geocode?lat=11.341&lon=77.717")
    assert res.status_code == 200
    data = res.json()
    assert data["state"] == "Tamil Nadu"
    assert data["district"] == "Erode"
    assert data["is_in_tamil_nadu"] is True


# 6. Traceable fertilizer prices endpoint
def test_06_fertilizer_prices_endpoint():
    res = client.get("/api/fertilizer/prices")
    assert res.status_code == 200
    prices = res.json()
    assert len(prices) >= 5
    for p in prices:
        assert "product_id" in p
        assert "price_per_kg_inr" in p
        assert "source" in p
        assert "effective_date" in p


# 7. Coordinates validation error handling
def test_07_invalid_coordinates_handling():
    res = client.get("/api/location/reverse-geocode?lat=999.0&lon=77.717")
    assert res.status_code == 400
    assert "Invalid coordinates" in res.json()["detail"]

