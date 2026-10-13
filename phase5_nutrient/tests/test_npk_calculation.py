"""
Automated unit tests for Phase 5: NPK Nutrient Requirement Calculation Engine.
Tests all 14 required scenarios specified in Phase 5 requirements.
"""

import pytest
from fastapi.testclient import TestClient
from phase3_soil.main import app
from phase5_nutrient.service import NutrientCalculationService, calculate_nutrient_requirement
from phase5_nutrient.models import NutrientCalculationRequest
from phase5_nutrient.units import convert_area_to_hectares, normalize_soil_nutrient_value

client = TestClient(app)
service = NutrientCalculationService()


# 1. Valid STCR calculation
def test_01_valid_stcr_calculation():
    req = NutrientCalculationRequest(
        crop="Rice",
        selected_rule_id="TNAU_STCR_IPNS_RICE_001",
        target_yield=6.0,
        soil_nitrogen=220.0,
        soil_phosphorus=16.0,
        soil_potassium=190.0,
        soil_phosphorus_method="Olsen"
    )
    res = service.calculate(req)
    assert res.status == "CALCULATION_SUCCESS"
    assert res.selected_rule_id == "TNAU_STCR_IPNS_RICE_001"
    assert res.selected_method == "STCR-IPNS"
    # N = 22.4 * 6.0 - 0.44 * 220 - 20.0 = 134.4 - 96.8 - 20.0 = 17.6
    assert res.n_req_kg_per_ha == 17.6
    # P2O5 = 11.2 * 6.0 - 1.80 * 16 - 10.0 = 67.2 - 28.8 - 10.0 = 28.4
    assert res.p2o5_req_kg_per_ha == 28.4
    # K2O = 13.5 * 6.0 - 0.32 * 190 - 10.0 = 81.0 - 60.8 - 10.0 = 10.2
    assert res.k2o_req_kg_per_ha == 10.2
    assert res.units["per_ha"] == "kg/ha"
    assert res.source_title == "TNAU Agriculture / STCR-IPNS Reference"


# 2. Valid soil-test-based calculation
def test_02_valid_soil_test_based_calculation():
    # Blackgram Rainfed: Blanket RDF = 20 N : 40 P2O5 : 20 K2O
    # Soil N = 200 (Low < 280 -> +25% = 25.0 kg N)
    # Soil P = 18 (Medium 11-22 -> 100% = 40.0 kg P2O5)
    # Soil K = 200 (Medium 118-280 -> 100% = 20.0 kg K2O)
    req = NutrientCalculationRequest(
        crop="Blackgram",
        selected_rule_id="TNAU_STD_BLACKGRAM_RF_001",
        soil_nitrogen=200.0,
        soil_phosphorus=18.0,
        soil_potassium=200.0,
        soil_phosphorus_method="Olsen"
    )
    res = service.calculate(req)
    assert res.status == "CALCULATION_SUCCESS"
    assert res.selected_rule_id == "TNAU_STD_BLACKGRAM_RF_001"
    assert res.selected_method == "TNAU-SOIL-TEST"
    assert res.n_req_kg_per_ha == 25.0
    assert res.p2o5_req_kg_per_ha == 40.0
    assert res.k2o_req_kg_per_ha == 20.0


# 3. Missing target yield
def test_03_missing_target_yield():
    req = NutrientCalculationRequest(
        crop="Rice",
        selected_rule_id="TNAU_STCR_IPNS_RICE_001",
        # target_yield missing!
        soil_nitrogen=220.0,
        soil_phosphorus=16.0,
        soil_potassium=190.0
    )
    res = service.calculate(req)
    assert res.status == "MISSING_INPUTS"
    assert "target_yield" in res.missing_inputs


# 4. Missing required soil values
def test_04_missing_required_soil_values():
    req = NutrientCalculationRequest(
        crop="Rice",
        selected_rule_id="TNAU_STCR_IPNS_RICE_001",
        target_yield=6.0,
        # soil N, P, K missing!
    )
    res = service.calculate(req)
    assert res.status == "MISSING_INPUTS"
    assert "soil_nitrogen" in res.missing_inputs
    assert "soil_phosphorus" in res.missing_inputs
    assert "soil_potassium" in res.missing_inputs


# 5. Unsupported crop
def test_05_unsupported_crop():
    req = NutrientCalculationRequest(
        crop="DragonFruit",
        soil_nitrogen=200.0,
        soil_phosphorus=15.0,
        soil_potassium=180.0
    )
    res = service.calculate(req)
    assert res.status == "UNSUPPORTED_CROP"


# 6. Unverified rule
def test_06_unverified_rule():
    req = NutrientCalculationRequest(
        crop="Banana",
        selected_rule_id="TNAU_STCR_BANANA_001",
        target_yield=50.0,
        soil_nitrogen=200.0,
        soil_phosphorus=15.0,
        soil_potassium=180.0
    )
    res = service.calculate(req)
    assert res.status == "UNVERIFIED_RULE"
    assert res.selected_rule_id == "TNAU_STCR_BANANA_001"
    assert "is marked as 'PENDING_VERIFICATION'" in res.warnings[0]


# 7. Invalid nutrient units
def test_07_invalid_nutrient_units():
    req = NutrientCalculationRequest(
        crop="Rice",
        selected_rule_id="TNAU_STD_RICE_001",
        soil_nitrogen=200.0,
        soil_nitrogen_unit="lbs_per_acre",  # Invalid unit!
        soil_phosphorus=15.0,
        soil_potassium=180.0
    )
    res = service.calculate(req)
    assert res.status == "VALIDATION_ERROR"
    assert any("unsupported soil nutrient unit" in err.lower() for err in res.validation_errors)


# 8. Olsen/Bray method mismatch
def test_08_olsen_bray_method_mismatch():
    req = NutrientCalculationRequest(
        crop="Rice",
        selected_rule_id="TNAU_STD_RICE_001",
        soil_nitrogen=200.0,
        soil_phosphorus=15.0,
        soil_phosphorus_method="InvalidMethodName",  # Invalid P method!
        soil_potassium=180.0
    )
    res = service.calculate(req)
    assert res.status == "VALIDATION_ERROR"
    assert any("invalid phosphorus test method" in err.lower() for err in res.validation_errors)


# 9. Invalid farm area
def test_09_invalid_farm_area():
    req = NutrientCalculationRequest(
        crop="Rice",
        selected_rule_id="TNAU_STCR_IPNS_RICE_001",
        target_yield=6.0,
        soil_nitrogen=220.0,
        soil_phosphorus=16.0,
        soil_potassium=190.0,
        farm_area=-5.0,  # Negative farm area!
        farm_area_unit="hectare"
    )
    res = service.calculate(req)
    assert res.status == "VALIDATION_ERROR"
    assert any("greater than 0" in err.lower() for err in res.validation_errors)


# 10. Acre-to-hectare conversion
def test_10_acre_to_hectare_conversion():
    # 5.0 acres = 5.0 * 0.404686 = 2.02343 ha
    area_ha = convert_area_to_hectares(5.0, "acre")
    assert round(area_ha, 4) == 2.0234

    req = NutrientCalculationRequest(
        crop="Rice",
        selected_rule_id="TNAU_STCR_IPNS_RICE_001",
        target_yield=6.0,
        soil_nitrogen=220.0,
        soil_phosphorus=16.0,
        soil_potassium=190.0,
        farm_area=5.0,
        farm_area_unit="acre"
    )
    res = service.calculate(req)
    assert res.status == "CALCULATION_SUCCESS"
    assert res.farm_area_hectares == 2.0234
    assert res.total_n_req_kg == round(17.6 * 2.02343, 2)
    assert res.total_p2o5_req_kg == round(28.4 * 2.02343, 2)
    assert res.total_k2o_req_kg == round(10.2 * 2.02343, 2)


# 11. Per-hectare versus total-farm calculation
def test_11_per_hectare_vs_total_farm():
    req = NutrientCalculationRequest(
        crop="Blackgram",
        selected_rule_id="TNAU_STD_BLACKGRAM_RF_001",
        soil_nitrogen=200.0,
        soil_phosphorus=18.0,
        soil_potassium=200.0,
        farm_area=2.5,
        farm_area_unit="hectare"
    )
    res = service.calculate(req)
    assert res.status == "CALCULATION_SUCCESS"
    # Primary per-ha outputs preserved
    assert res.n_req_kg_per_ha == 25.0
    assert res.p2o5_req_kg_per_ha == 40.0
    assert res.k2o_req_kg_per_ha == 20.0

    # Total farm outputs = per_ha * 2.5 (no double multiplication)
    assert res.total_n_req_kg == 62.5
    assert res.total_p2o5_req_kg == 100.0
    assert res.total_k2o_req_kg == 50.0


# 12. Invalid numeric values
def test_12_invalid_numeric_values():
    req = NutrientCalculationRequest(
        crop="Rice",
        selected_rule_id="TNAU_STD_RICE_001",
        soil_nitrogen="invalid_not_a_number",  # Non-numeric string!
        soil_phosphorus=15.0,
        soil_potassium=180.0
    )
    res = service.calculate(req)
    assert res.status == "VALIDATION_ERROR"


# 13. Target yield outside the documented range
def test_13_target_yield_outside_documented_range():
    # Rice STCR documented range is 3.0 to 8.0 t/ha. Passing 15.0 t/ha triggers range validation error!
    req = NutrientCalculationRequest(
        crop="Rice",
        selected_rule_id="TNAU_STCR_IPNS_RICE_001",
        target_yield=15.0,  # Exceeds max 8.0 t/ha
        soil_nitrogen=220.0,
        soil_phosphorus=16.0,
        soil_potassium=190.0
    )
    res = service.calculate(req)
    assert res.status == "VALIDATION_ERROR"
    assert any("exceeds documented range" in err.lower() for err in res.validation_errors)


# 14. API validation endpoint (POST /api/nutrient-requirement/calculate)
def test_14_api_validation_endpoint():
    payload = {
        "crop": "Cotton (lint)",
        "selected_rule_id": "TNAU_STCR_IPNS_COTTON_001",
        "target_yield": 2.5,
        "soil_nitrogen": 200.0,
        "soil_phosphorus": 14.0,
        "soil_potassium": 180.0,
        "farm_area": 100.0,
        "farm_area_unit": "cent"  # 100 cents = 1 acre = 0.404686 ha
    }
    response = client.post("/api/nutrient-requirement/calculate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "CALCULATION_SUCCESS"
    assert data["crop"] == "Cotton (lint)"
    assert data["selected_rule_id"] == "TNAU_STCR_IPNS_COTTON_001"
    assert data["selected_method"] == "STCR-IPNS"
    assert data["n_req_kg_per_ha"] > 0
    assert data["p2o5_req_kg_per_ha"] > 0
    assert data["k2o_req_kg_per_ha"] > 0
    assert data["farm_area_hectares"] == 0.4047
    assert data["source_title"] == "TNAU Cotton STCR"
