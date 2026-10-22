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
    assert res["weather_guidance"]["risk_level"] in ("LOW", "MEDIUM", "HIGH", "UNKNOWN")
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


# 8. Offline weather failure resilience: soil-based recommendation remains active
def test_08_weather_offline_fallback_preserves_soil_recommendations(monkeypatch):
    from phase7_integration import weather

    # Simulate Open-Meteo 503 network outage
    def mock_fetch_fail(lat, lon):
        raise urllib.error.HTTPError("https://api.open-meteo.com/v1/forecast", 503, "Service Unavailable", {}, None)

    import urllib.error
    monkeypatch.setattr(weather, "_fetch_open_meteo", mock_fetch_fail)
    monkeypatch.setattr(weather, "_get_cached_weather", lambda k: None)
    monkeypatch.setattr(weather, "_get_stale_cached_weather", lambda k: None)

    # Calling guidance endpoint directly when external service is down
    guidance = weather.get_weather_guidance(district="Perambalur")
    assert guidance["status"] == "WEATHER_UNAVAILABLE"
    assert guidance["guidance_status"] == "WEATHER_UNAVAILABLE"
    assert guidance["risk_level"] == "UNKNOWN"
    assert "unreachable" in guidance["advisory_en"].lower()

    # Calling master full recommendation pipeline when external weather is down
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
        "farm_area": 2.0,
        "farm_area_unit": "acre"
    }
    rec = get_full_recommendation(payload)
    # Master recommendation must succeed even when weather is offline!
    assert rec["status"] == "SUCCESS"
    assert rec["nutrient_requirements"]["n_req_kg_per_ha"] > 0
    assert rec["fertilizer_plan"]["total_cost_inr"] > 0
    assert len(rec["fertilizer_plan"]["recommended_products"]) > 0
    assert rec["weather_guidance"]["status"] == "WEATHER_UNAVAILABLE"
    assert rec["weather_guidance"]["risk_level"] == "UNKNOWN"


# 9. Stale weather cache fallback when live API fails
def test_09_stale_weather_cache_fallback(monkeypatch):
    from phase7_integration import weather

    # Mock unexpired cache miss, but stale cache hit
    monkeypatch.setattr(weather, "_get_cached_weather", lambda k: None)
    monkeypatch.setattr(weather, "_get_stale_cached_weather", lambda k: {
        "current": {"temperature_c": 29.5, "condition_en": "Partly Cloudy", "condition_ta": "பகுதி மேகமூட்டம்", "relative_humidity_pct": 65, "wind_speed_kmh": 12.0},
        "forecast": {"days": [], "rainfall_next_24h_mm": 5.0, "rainfall_next_48h_mm": 10.0},
        "observation_time": "2026-10-17T08:00",
        "source": "Open-Meteo (Stale Cache Fallback)",
        "district": "Madurai"
    })

    def mock_fetch_fail(lat, lon):
        raise ConnectionResetError("Connection reset by peer")

    monkeypatch.setattr(weather, "_fetch_open_meteo", mock_fetch_fail)

    live = weather.get_live_weather(district="Madurai")
    assert live["status"] == "SUCCESS"
    assert live["is_cached"] is True
    assert live["is_stale"] is True
    assert "Stale Cache" in live["source"]
    assert live["current"]["temperature_c"] == 29.5


# 10. Task 4e: Custom local bag prices and nutrient surplus reporting
def test_10_task4_custom_prices_and_surplus():
    payload_default = {
        "crop": "Rice",
        "district": "Thanjavur",
        "soil_series": "Palavidhi",
        "season": "Kharif",
        "target_yield": 6.0,
        "soil_nitrogen": 220.0,
        "soil_phosphorus": 16.0,
        "soil_potassium": 190.0,
        "farm_area": 1.0,
        "farm_area_unit": "ha",
        "no_cache": True
    }
    res_def = get_full_recommendation(payload_default)
    assert res_def["status"] == "SUCCESS"
    assert "nutrient_surplus_kg" in res_def
    assert "surplus_summary" in res_def
    assert res_def["custom_prices_applied"] is False
    cost_default = res_def["fertilizer_plan"]["total_cost_inr"]

    # Now apply custom higher local bag prices for Urea and DAP
    payload_custom = dict(payload_default)
    payload_custom["custom_prices"] = {
        "UREA": 350.0,  # default is 266.50
        "DAP": 1600.0,  # default is 1350.00
    }
    res_custom = get_full_recommendation(payload_custom)
    assert res_custom["status"] == "SUCCESS"
    assert res_custom["custom_prices_applied"] is True
    assert res_custom["fertilizer_plan"]["custom_prices_applied"] is True
    cost_custom = res_custom["fertilizer_plan"]["total_cost_inr"]
    # With higher local prices, the total cost must reflect the custom prices
    assert cost_custom > cost_default


# 11. Task 4d & 4a: Last updated dates and 3-hour recommendation caching
def test_11_task4_caching_and_dates():
    from phase7_integration.service import _RECOMMENDATION_CACHE
    _RECOMMENDATION_CACHE.clear()

    payload = {
        "crop": "Cotton (lint)",
        "district": "Coimbatore",
        "soil_series": "Irugur",
        "season": "Kharif",
        "target_yield": 2.5,
        "soil_nitrogen": 200.0,
        "soil_phosphorus": 14.0,
        "soil_potassium": 180.0,
        "farm_area": 1.0,
        "farm_area_unit": "hectare"
    }
    res1 = get_full_recommendation(payload)
    assert res1["status"] == "SUCCESS"
    assert res1["prices_last_updated"] == "2026-10-22"
    assert res1["rules_last_updated"] == "2026-10-22"
    assert res1["is_cached"] is False

    # Repeat identical call should hit the 3-hour recommendation cache
    res2 = get_full_recommendation(payload)
    assert res2["status"] == "SUCCESS"
    assert res2["is_cached"] is True


# 12. Task 4b: Tamil Voice Summary endpoint
def test_12_task4_tamil_voice_summary_endpoint():
    rec_payload = {
        "crop": "Rice",
        "district": "Thanjavur",
        "fertilizer_plan": {
            "total_cost_inr": 3450.0,
            "recommended_products": [
                {"name": "Neem Coated Urea", "bags": 3, "product_name": "Neem Coated Urea"},
                {"name": "Di-Ammonium Phosphate (DAP)", "bags": 2, "product_name": "Di-Ammonium Phosphate (DAP)"}
            ]
        }
    }
    response = client.post("/api/voice/tamil-summary", json=rec_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert "tamil_speech_script" in data
    assert "வணக்கம் உழவரே" in data["tamil_speech_script"]
    assert "யூரியா" in data["tamil_speech_script"]
    assert data["voice_locale"] == "ta-IN"


# 13. Task 4a: Seasonal weather estimate fallback when offline
def test_13_task4_seasonal_weather_estimate_fallback(monkeypatch):
    from phase7_integration import weather

    # Force cache miss and network failure
    monkeypatch.setattr(weather, "_get_cached_weather", lambda k: None)
    monkeypatch.setattr(weather, "_get_stale_cached_weather", lambda k: None)

    def mock_net_fail(lat, lon):
        raise ConnectionError("Network unreachable")

    monkeypatch.setattr(weather, "_fetch_open_meteo", mock_net_fail)

    guidance = weather.get_weather_guidance(district="Tiruchirappalli")
    assert guidance["status"] == "WEATHER_UNAVAILABLE"
    assert guidance["data_source"] == "seasonal estimate"
    assert guidance["temperature_c"] is not None
    assert guidance["rainfall_mm_24h"] is not None


