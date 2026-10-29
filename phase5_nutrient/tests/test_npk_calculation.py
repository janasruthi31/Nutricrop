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
        soil_series="Palavidhi",
        selected_rule_id="TNAU_STCR_IPNS_RICE_001",
        target_yield=6.0,
        soil_nitrogen=220.0,
        soil_phosphorus=16.0,
        soil_potassium=190.0,
        soil_phosphorus_method="Olsen",
        fym_applied_t_per_ha=12.5
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


# 2. Valid soil-test-based calculation with continuous rating interpolation
def test_02_valid_soil_test_based_calculation():
    # Blackgram Rainfed: Blanket RDF = 20 N : 40 P2O5 : 20 K2O
    # Soil ratings (Low N, Med P, Med K) provide diagnostic classification only;
    # Unsupported blanket multipliers (+25%, 0%, -25%) are removed from production path.
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
    assert res.n_req_kg_per_ha == 20.0
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
        soil_series="Palavidhi",
        selected_rule_id="TNAU_STCR_IPNS_RICE_001",
        target_yield=6.0,
        soil_nitrogen=220.0,
        soil_phosphorus=16.0,
        soil_potassium=190.0,
        soil_phosphorus_method="Olsen",
        farm_area=5.0,
        farm_area_unit="acre",
        fym_applied_t_per_ha=12.5
    )
    res = service.calculate(req)
    assert res.status == "CALCULATION_SUCCESS"
    assert round(res.farm_area_hectares, 4) == 2.0234
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
        soil_phosphorus_method="Olsen",
        farm_area=2.5,
        farm_area_unit="hectare"
    )
    res = service.calculate(req)
    assert res.status == "CALCULATION_SUCCESS"
    # Primary per-ha outputs preserved (fixed 20:40:20 kg/ha without unsupported multipliers)
    assert res.n_req_kg_per_ha == 20.0
    assert res.p2o5_req_kg_per_ha == 40.0
    assert res.k2o_req_kg_per_ha == 20.0

    # Total farm outputs = per_ha * 2.5 (no double multiplication)
    assert res.total_n_req_kg == 50.0
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
        "soil_series": "Irugur",
        "selected_rule_id": "TNAU_STCR_IPNS_COTTON_001",
        "target_yield": 2.5,
        "soil_nitrogen": 200.0,
        "soil_phosphorus": 14.0,
        "soil_potassium": 180.0,
        "soil_phosphorus_method": "Olsen",
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
    assert round(data["farm_area_hectares"], 4) == 0.4047
    assert data["source_title"] == "TNAU Cotton STCR"


# 15. Target yield unit conversions (quintals/ha to tonnes/ha)
def test_15_target_yield_unit_conversions():
    # 60.0 q/ha = 6.0 t/ha
    req = NutrientCalculationRequest(
        crop="Rice",
        soil_series="Palavidhi",
        selected_rule_id="TNAU_STCR_IPNS_RICE_001",
        target_yield=60.0,
        target_yield_unit="q/ha",
        soil_nitrogen=220.0,
        soil_phosphorus=16.0,
        soil_potassium=190.0,
        soil_phosphorus_method="Olsen",
        fym_applied_t_per_ha=12.5
    )
    res = service.calculate(req)
    assert res.status == "CALCULATION_SUCCESS"
    assert res.n_req_kg_per_ha == 17.6
    assert res.p2o5_req_kg_per_ha == 28.4
    assert res.k2o_req_kg_per_ha == 10.2


# 16. Soil test oxide form input (kg P2O5/ha normalized to elemental P)
def test_16_elemental_and_oxide_nutrient_units():
    # If soil P is supplied as 36.66 kg P2O5/ha, elemental P = 36.66 * 0.43642 = 16.0 kg P/ha
    req = NutrientCalculationRequest(
        crop="Rice",
        soil_series="Palavidhi",
        selected_rule_id="TNAU_STCR_IPNS_RICE_001",
        target_yield=6.0,
        soil_nitrogen=220.0,
        soil_phosphorus=36.66,
        soil_phosphorus_unit="kg_p2o5_per_ha",
        soil_potassium=190.0,
        soil_phosphorus_method="Olsen",
        fym_applied_t_per_ha=12.5
    )
    res = service.calculate(req)
    assert res.status == "CALCULATION_SUCCESS"
    # P2O5 should calculate to ~28.4 kg/ha
    assert abs(res.p2o5_req_kg_per_ha - 28.4) < 0.2


# 17. Farm area conversions for acres and hectares
def test_17_farm_area_acre_and_sqm_conversions():
    # 2.5 acres = 2.5 * 0.404686 = 1.0117 ha
    req = NutrientCalculationRequest(
        crop="Rice",
        soil_series="Palavidhi",
        selected_rule_id="TNAU_STCR_IPNS_RICE_001",
        target_yield=6.0,
        soil_nitrogen=220.0,
        soil_phosphorus=16.0,
        soil_potassium=190.0,
        soil_phosphorus_method="Olsen",
        farm_area=2.5,
        farm_area_unit="acre",
        fym_applied_t_per_ha=12.5
    )
    res = service.calculate(req)
    assert res.status == "CALCULATION_SUCCESS"
    assert round(res.farm_area_hectares, 4) == 1.0117
    assert res.total_n_req_kg == round(17.6 * 1.011714, 2)


# 18. Zero FYM default verification (Problem E fix)
def test_18_zero_fym_default_no_unearned_credit():
    # When farmer enters no FYM, fym_applied must default to 0.0 t/ha, giving 0 credit.
    # N = 22.4 * 6.0 - 0.44 * 220 - 0.0 = 134.4 - 96.8 = 37.6 kg/ha (NOT 17.6)
    req = NutrientCalculationRequest(
        crop="Rice",
        soil_series="Palavidhi",
        selected_rule_id="TNAU_STCR_IPNS_RICE_001",
        target_yield=6.0,
        soil_nitrogen=220.0,
        soil_phosphorus=16.0,
        soil_potassium=190.0,
        soil_phosphorus_method="Olsen"
    )
    res = service.calculate(req)
    assert res.status == "CALCULATION_SUCCESS"
    assert res.n_req_kg_per_ha == 37.6
    assert res.p2o5_req_kg_per_ha == 38.4
    assert res.k2o_req_kg_per_ha == 20.2
    assert res.calculation_details["fym_applied_t_per_ha"] == 0.0
    assert res.calculation_details["fym_credit_kg_per_ha"]["N"] == 0.0


# 19. Task 2b: Continuous rating interpolation ensures different soil values give different doses
def test_19_different_soil_values_give_different_doses():
    # Comparing soil N = 100 vs soil N = 270 (both are in the "Low" rating band < 280)
    req_100 = NutrientCalculationRequest(
        crop="Rice",
        selected_rule_id="TNAU_STD_RICE_001",
        soil_nitrogen=100.0,
        soil_phosphorus=15.0,
        soil_potassium=200.0,
        soil_phosphorus_method="Olsen"
    )
    req_270 = NutrientCalculationRequest(
        crop="Rice",
        selected_rule_id="TNAU_STD_RICE_001",
        soil_nitrogen=270.0,
        soil_phosphorus=15.0,
        soil_potassium=200.0,
        soil_phosphorus_method="Olsen"
    )
    res_100 = service.calculate(req_100)
    res_270 = service.calculate(req_270)

    assert res_100.status == "CALCULATION_SUCCESS"
    assert res_270.status == "CALCULATION_SUCCESS"
    # Previously, both received identical multiplier 1.25 -> 187.5 kg N/ha
    # Now, soil N 100 receives higher dose than soil N 270!
    assert res_100.n_req_kg_per_ha > res_270.n_req_kg_per_ha
    assert res_100.n_req_kg_per_ha != res_270.n_req_kg_per_ha


# 20. Task 2c: Recommended ranges (+/- 10%) returned
def test_20_recommended_range_returned():
    req = NutrientCalculationRequest(
        crop="Rice",
        soil_series="Palavidhi",
        selected_rule_id="TNAU_STCR_IPNS_RICE_001",
        target_yield=6.0,
        soil_nitrogen=220.0,
        soil_phosphorus=16.0,
        soil_potassium=190.0,
        soil_phosphorus_method="Olsen",
        fym_applied_t_per_ha=12.5
    )
    res = service.calculate(req)
    assert res.status == "CALCULATION_SUCCESS"
    assert res.recommended_range_kg_per_ha is not None
    assert "N" in res.recommended_range_kg_per_ha
    r_n = res.recommended_range_kg_per_ha["N"]
    assert len(r_n) == 2
    assert r_n[0] <= res.n_req_kg_per_ha <= r_n[1]
    assert round(r_n[0], 1) == round(res.n_req_kg_per_ha * 0.9, 1)
    assert round(r_n[1], 1) == round(res.n_req_kg_per_ha * 1.1, 1)


# 21. Task 2d: Secondary & micronutrient advisory (Zinc, Sulphur, Boron)
def test_21_micronutrient_advisory_deficient_and_sufficient():
    # Zn < 1.2 ppm (deficient), Sulphur < 10.0 ppm (deficient), Boron >= 0.5 ppm (sufficient)
    req = NutrientCalculationRequest(
        crop="Rice",
        selected_rule_id="TNAU_STD_RICE_001",
        soil_nitrogen=200.0,
        soil_phosphorus=15.0,
        soil_potassium=200.0,
        soil_phosphorus_method="Olsen",
        zinc=0.8,
        sulphur=6.5,
        boron=0.9
    )
    res = service.calculate(req)
    assert res.status == "CALCULATION_SUCCESS"
    assert res.micronutrient_advisory is not None
    assert "zinc" in res.micronutrient_advisory
    assert res.micronutrient_advisory["zinc"]["is_deficient"] is True
    assert "Zinc Sulphate" in res.micronutrient_advisory["zinc"]["advisory"]

    assert "sulphur" in res.micronutrient_advisory
    assert res.micronutrient_advisory["sulphur"]["is_deficient"] is True
    assert "Gypsum" in res.micronutrient_advisory["sulphur"]["advisory"]

    assert "boron" in res.micronutrient_advisory
    assert res.micronutrient_advisory["boron"]["is_deficient"] is False

    # Also verify attached to soil_nutrient_status
    assert "zinc" in res.soil_nutrient_status
    assert res.soil_nutrient_status["zinc"]["status"] == "Deficient"


# 22. Task 2c: Blanket comparison & >50% deviation warning & spatial sampling note
def test_22_blanket_comparison_and_spatial_sampling_note():
    # Groundnut STCR with low target yield resulting in dose very different from blanket
    req = NutrientCalculationRequest(
        crop="Groundnut",
        selected_rule_id="TNAU_BLANKET_GROUNDNUT_001",
        soil_nitrogen=150.0,
        soil_phosphorus=8.0,
        soil_potassium=80.0,
        soil_phosphorus_method="Olsen"
    )
    res = service.calculate(req)
    assert res.status == "CALCULATION_SUCCESS"
    assert res.blanket_comparison is not None
    assert any("Recommendation is valid for this sample" in w for w in res.warnings)


# 23. Task 3d: No soil test mode uses blanket dose and advises testing
def test_23_no_soil_test_blanket_mode():
    req = NutrientCalculationRequest(
        crop="Groundnut",
        selected_rule_id="TNAU_BLANKET_GROUNDNUT_001",
        no_soil_test=True,
        farm_area=1.0,
        farm_area_unit="hectare"
    )
    res = service.calculate(req)
    assert res.status == "CALCULATION_SUCCESS"
    # Groundnut blanket RDF: 25 N : 50 P2O5 : 75 K2O
    assert res.n_req_kg_per_ha == 25.0
    assert res.p2o5_req_kg_per_ha == 50.0
    assert res.k2o_req_kg_per_ha == 75.0
    assert res.confidence == "lower"
    assert res.confidence_label == "General recommendation (lower confidence)"
    assert any("No soil test provided" in w for w in res.warnings)
    assert any("Agricultural Extension Center" in w for w in res.warnings)
    assert res.soil_nutrient_status["nitrogen"]["status"] == "Not Tested"


# 24. Task 3c: Warning when soil test date is older than 1 year
def test_24_test_date_age_warning():
    from phase7_integration.service import FullRecommendationService
    int_service = FullRecommendationService()
    payload = {
        "crop": "Rice",
        "soil_series": "Palavidhi",
        "target_yield": 5.0,
        "soil_nitrogen": 210.0,
        "soil_phosphorus": 16.0,
        "soil_phosphorus_method": "Olsen",
        "soil_potassium": 200.0,
        "test_date": "2023-01-15",  # Over 1 year ago
        "farm_area": 1.0,
        "farm_area_unit": "ha"
    }
    rec = int_service.generate_full_recommendation(payload)
    assert rec["status"] == "SUCCESS"
    assert any("more than 1 year old" in w for w in rec["warnings"])



