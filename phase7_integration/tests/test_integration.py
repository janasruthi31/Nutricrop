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
    assert len(res["fertilizer_plan"]["recommended_products"]) > 0
    assert res["district_yield_prediction"]["estimated_production_tonnes"] > 0
    assert res["weather_guidance"]["guidance_status"] is not None


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
