"""
Automated Test Suite for Groundnut NPK Audit & Unit Conversion (Tests A through I).
Tests:
- TEST A: Acre/hectare conversion
- TEST B: Report-based one-acre recommendation
- TEST C: Farm total calculation (2 acres)
- TEST D: Equivalent units producing identical farm totals
- TEST E: No double conversion
- TEST F: Soil-test values are never substituted as fertilizer rates
- TEST G: Crop-specific rules enforcement
- TEST H: Rule validation status (unverified never claims verified)
- TEST I: Optimizer receives correct farm totals and solves whole bags
"""

import math
import pytest
from phase5_nutrient.units import (
    HA_TO_ACRE,
    ACRE_TO_HA,
    convert_acre_to_hectare,
    convert_hectare_to_acre,
    convert_kg_per_acre_to_kg_per_ha,
    convert_kg_per_ha_to_kg_per_acre,
    calculate_farm_total_nutrient,
)
from phase5_nutrient.service import NutrientCalculationService, NutrientCalculationRequest
from phase5_nutrient.models import NutrientCalculationResponse
from agronomy.service import RuleSelectionService, RuleSelectionRequest
from phase6_fertilizer.service import FertilizerOptimizerService, FertilizerOptimizationRequest
from phase7_integration.service import FullRecommendationService


# ==============================================================================
# TEST A: Acre/hectare conversion
# 1 acre must convert to approximately 0.4046856422 hectares.
# 1 hectare must convert to approximately 2.4710538147 acres.
# ==============================================================================
def test_a_acre_hectare_conversion():
    # 1. Forward conversions
    ha_from_1_acre = convert_acre_to_hectare(1.0)
    assert abs(ha_from_1_acre - 0.4046856422) < 1e-9, f"Expected 0.4046856422 ha, got {ha_from_1_acre}"

    acre_from_1_ha = convert_hectare_to_acre(1.0)
    assert abs(acre_from_1_ha - 2.4710538147) < 1e-9, f"Expected 2.4710538147 acres, got {acre_from_1_ha}"

    # 2. Multi-acre conversions
    assert abs(convert_acre_to_hectare(2.5) - (2.5 * 0.4046856422)) < 1e-9
    assert abs(convert_hectare_to_acre(2.5) - (2.5 * 2.4710538147)) < 1e-9

    # 3. Round-trip consistency
    round_trip_ha = convert_acre_to_hectare(convert_hectare_to_acre(5.0))
    assert abs(round_trip_ha - 5.0) < 1e-6

    # 4. Nutrient rate conversions
    # 14 kg/acre -> ~34.5948 kg/ha
    rate_ha = convert_kg_per_acre_to_kg_per_ha(14.0)
    assert abs(rate_ha - (14.0 / 0.4046856422)) < 1e-6
    assert abs(round(rate_ha, 2) - 34.59) < 0.01

    # 34.5948 kg/ha -> 14.0 kg/acre
    rate_acre = convert_kg_per_ha_to_kg_per_acre(rate_ha)
    assert abs(rate_acre - 14.0) < 1e-6


# ==============================================================================
# TEST B: Report-based one-acre recommendation
# Given:
# Area = 1 acre
# N = 14 kg/acre
# P2O5 = 23 kg/acre
# K2O = 15 kg/acre
# Expected farm totals: N = 14 kg, P2O5 = 23 kg, K2O = 15 kg
# Expected approximate per-hectare rates: N = 34.59 kg/ha, P2O5 = 56.83 kg/ha, K2O = 37.08 kg/ha
# ==============================================================================
def test_b_report_based_one_acre_recommendation():
    service = NutrientCalculationService()
    req = NutrientCalculationRequest(
        crop="Groundnut",
        farm_area=1.0,
        farm_area_unit="acre",
        recommendation_mode="SOIL_HEALTH_CARD",
        printed_n_rate=14.0,
        printed_p2o5_rate=23.0,
        printed_k2o_rate=15.0,
        printed_rate_unit="kg/acre",
        printed_source="Uploaded Soil Health Card",
    )
    res = service.calculate(req)

    assert res.status == "CALCULATION_SUCCESS"
    assert res.recommendation_mode == "SOIL_HEALTH_CARD"
    assert res.recommendation_source == "Uploaded Soil Health Card"

    # Exact farm totals for 1 acre
    assert res.total_n_req_kg == 14.0, f"Expected 14.0 kg, got {res.total_n_req_kg}"
    assert res.total_p2o5_req_kg == 23.0, f"Expected 23.0 kg, got {res.total_p2o5_req_kg}"
    assert res.total_k2o_req_kg == 15.0, f"Expected 15.0 kg, got {res.total_k2o_req_kg}"

    # Per-acre rates
    assert res.n_req_kg_per_acre == 14.0
    assert res.p2o5_req_kg_per_acre == 23.0
    assert res.k2o_req_kg_per_acre == 15.0

    # Approximate per-hectare rates
    assert round(res.n_req_kg_per_ha, 2) == 34.59, f"Expected 34.59 kg/ha, got {res.n_req_kg_per_ha}"
    assert round(res.p2o5_req_kg_per_ha, 2) == 56.83, f"Expected 56.83 kg/ha, got {res.p2o5_req_kg_per_ha}"
    # 15 / 0.4046856422 = 37.0658 -> 37.07 or 37.08 kg/ha
    assert round(res.k2o_req_kg_per_ha, 2) in (37.07, 37.08), f"Expected 37.07-37.08 kg/ha, got {res.k2o_req_kg_per_ha}"

    # Farm area preservation
    assert res.farm_area_original == 1.0
    assert res.farm_area_unit_original == "acre"
    assert abs(res.farm_area_hectares - 0.4046856422) < 1e-6


# ==============================================================================
# TEST C: Farm total calculation
# When farm area is 2 acres and rates are in kg/acre:
# N = 28 kg, P2O5 = 46 kg, K2O = 30 kg
# ==============================================================================
def test_c_farm_total_calculation_two_acres():
    service = NutrientCalculationService()
    req = NutrientCalculationRequest(
        crop="Groundnut",
        farm_area=2.0,
        farm_area_unit="acre",
        recommendation_mode="SOIL_HEALTH_CARD",
        printed_n_rate=14.0,
        printed_p2o5_rate=23.0,
        printed_k2o_rate=15.0,
        printed_rate_unit="kg/acre",
    )
    res = service.calculate(req)

    assert res.total_n_req_kg == 28.0, f"Expected 28.0 kg, got {res.total_n_req_kg}"
    assert res.total_p2o5_req_kg == 46.0, f"Expected 46.0 kg, got {res.total_p2o5_req_kg}"
    assert res.total_k2o_req_kg == 30.0, f"Expected 30.0 kg, got {res.total_k2o_req_kg}"

    # Also verify central utility directly
    assert calculate_farm_total_nutrient(14.0, "kg/acre", 2.0, "acre") == 28.0
    assert calculate_farm_total_nutrient(23.0, "kg/acre", 2.0, "acre") == 46.0
    assert calculate_farm_total_nutrient(15.0, "kg/acre", 2.0, "acre") == 30.0


# ==============================================================================
# TEST D: Equivalent units
# Confirm that calculating totals from kg/acre and from the equivalent kg/ha
# produces the same farm totals within numerical tolerance.
# ==============================================================================
def test_d_equivalent_units():
    # Given 14 kg/acre for 2.5 acres:
    rate_acre = 14.0
    area_acre = 2.5
    total_from_acre = calculate_farm_total_nutrient(rate_acre, "kg/acre", area_acre, "acre")

    # Equivalent rate in kg/ha and area in ha:
    rate_ha = convert_kg_per_acre_to_kg_per_ha(rate_acre)
    area_ha = convert_acre_to_hectare(area_acre)
    total_from_ha = calculate_farm_total_nutrient(rate_ha, "kg/ha", area_ha, "hectare")

    assert abs(total_from_acre - 35.0) < 1e-9
    assert abs(total_from_ha - 35.0) < 1e-5
    assert abs(total_from_acre - total_from_ha) < 1e-5, f"Discrepancy: {total_from_acre} vs {total_from_ha}"


# ==============================================================================
# TEST E: No double conversion
# Ensure the application does not convert the same farm area or nutrient rate twice.
# ==============================================================================
def test_e_no_double_conversion():
    # If 1 acre and 14 kg/acre:
    # Double conversion bug 1: Converting rate to kg/ha (34.59) and multiplying by area in acres (1.0) -> 34.59 kg (BUG)
    # Double conversion bug 2: Multiplying rate in kg/acre (14.0) by area converted to ha (0.4047) -> 5.66 kg (BUG)
    # Correct total: exactly 14.0 kg
    tot = calculate_farm_total_nutrient(14.0, "kg/acre", 1.0, "acre")
    assert tot == 14.0
    assert tot != 34.59
    assert tot != pytest.approx(5.66, 0.1)

    # Similarly for ha:
    # 50 kg/ha on 2 ha = 100 kg
    tot_ha = calculate_farm_total_nutrient(50.0, "kg/ha", 2.0, "hectare")
    assert tot_ha == 100.0


# ==============================================================================
# TEST F: Soil-test values are not fertilizer rates
# Ensure N = 39, P = 4, and K = 259 kg/acre are never accidentally used as fertilizer application rates.
# ==============================================================================
def test_f_soil_test_values_are_not_fertilizer_rates():
    service = NutrientCalculationService()
    # Execute calculated agronomic mode with soil values 39, 4, 259
    req = NutrientCalculationRequest(
        crop="Groundnut",
        selected_rule_id="TNAU_STD_GROUNDNUT_001",
        farm_area=1.0,
        farm_area_unit="acre",
        soil_nitrogen=39.0,
        soil_phosphorus=4.0,
        soil_potassium=259.0,
        soil_phosphorus_method="Olsen",
        recommendation_mode="CALCULATED_AGRONOMIC",
        allow_unverified=True,
    )
    res = service.calculate(req)

    # Ensure fertilizer recommendations do not match measured soil values
    assert res.total_n_req_kg != 39.0
    assert res.total_p2o5_req_kg != 4.0
    assert res.total_k2o_req_kg != 259.0

    assert res.n_req_kg_per_acre != 39.0
    assert res.p2o5_req_kg_per_acre != 4.0
    assert res.k2o_req_kg_per_acre != 259.0

    # Execute SHC mode with report printed values 14, 23, 15
    req_shc = NutrientCalculationRequest(
        crop="Groundnut",
        farm_area=1.0,
        farm_area_unit="acre",
        recommendation_mode="SOIL_HEALTH_CARD",
        printed_n_rate=14.0,
        printed_p2o5_rate=23.0,
        printed_k2o_rate=15.0,
        soil_nitrogen=39.0,
        soil_phosphorus=4.0,
        soil_potassium=259.0,
    )
    res_shc = service.calculate(req_shc)
    assert res_shc.total_n_req_kg == 14.0
    assert res_shc.total_p2o5_req_kg == 23.0
    assert res_shc.total_k2o_req_kg == 15.0


# ==============================================================================
# TEST G: Crop-specific rules
# Ensure the groundnut rule cannot be applied to sugarcane and vice versa.
# ==============================================================================
def test_g_crop_specific_rules():
    rule_service = RuleSelectionService()

    # Rule selection for Sugarcane must select a Sugarcane rule, NOT Groundnut
    req_cane = RuleSelectionRequest(crop="Sugarcane", district="Cuddalore")
    res_cane = rule_service.select_rule(req_cane)
    assert res_cane.selected_rule_id != "TNAU_STD_GROUNDNUT_001"
    assert "SUGARCANE" in res_cane.selected_rule_id

    # Rule selection for Groundnut must select Groundnut rule, NOT Sugarcane or Rice
    req_gn = RuleSelectionRequest(crop="Groundnut", district="Tiruppur")
    res_gn = rule_service.select_rule(req_gn)
    assert res_gn.selected_rule_id == "TNAU_STD_GROUNDNUT_001"
    assert "GROUNDNUT" in res_gn.selected_rule_id

    # Applying Groundnut rule to Sugarcane in calculation must fail or reject
    nutrient_service = NutrientCalculationService()
    req_mismatch = NutrientCalculationRequest(
        crop="Sugarcane",
        selected_rule_id="TNAU_STD_GROUNDNUT_001",
        farm_area=1.0,
        farm_area_unit="acre",
        recommendation_mode="CALCULATED_AGRONOMIC",
    )
    res_mismatch = nutrient_service.calculate(req_mismatch)
    assert res_mismatch.status in ("UNSUPPORTED_CROP", "VALIDATION_ERROR", "INVALID_RULE_FOR_CROP")


# ==============================================================================
# TEST H: Rule validation
# Ensure an unverified rule (such as TNAU_STD_GROUNDNUT_001) never displays "Verified Rule".
# ==============================================================================
def test_h_rule_validation():
    rule_service = RuleSelectionService()
    res_gn = rule_service.select_rule(RuleSelectionRequest(crop="Groundnut"))
    assert res_gn.is_verified is False
    assert res_gn.verification_status in ("PENDING_AGRONOMIC_VALIDATION", "SOURCE_NOT_VERIFIED")

    # In nutrient calculation, is_verified_rule must be False
    nutrient_service = NutrientCalculationService()
    # 1. By default without allow_unverified, calculation must be rejected as UNVERIFIED_RULE
    req_default = NutrientCalculationRequest(
        crop="Groundnut",
        selected_rule_id="TNAU_STD_GROUNDNUT_001",
        recommendation_mode="CALCULATED_AGRONOMIC",
        allow_unverified=False,
    )
    res_default = nutrient_service.calculate(req_default)
    assert res_default.status == "UNVERIFIED_RULE"
    assert res_default.is_verified_rule is False

    # 2. When allow_unverified=True, returns PENDING_AGRONOMIC_VALIDATION, never claiming to be verified
    req = NutrientCalculationRequest(
        crop="Groundnut",
        selected_rule_id="TNAU_STD_GROUNDNUT_001",
        soil_nitrogen=39.0,
        soil_phosphorus=4.0,
        soil_phosphorus_method="Olsen",
        soil_potassium=259.0,
        recommendation_mode="CALCULATED_AGRONOMIC",
        allow_unverified=True,
    )
    res = nutrient_service.calculate(req)
    assert res.status == "PENDING_AGRONOMIC_VALIDATION"
    assert res.is_verified_rule is False
    assert res.verification_status == "PENDING_AGRONOMIC_VALIDATION"

    # Conversely, verified rules like Rice STCR must report is_verified_rule = True
    req_rice = RuleSelectionRequest(crop="Rice", district="Thanjavur")
    res_rice = rule_service.select_rule(req_rice)
    assert res_rice.verification_status in ("VERIFIED", "PROVISIONAL")


# ==============================================================================
# TEST I: Optimizer receives correct farm totals and solves whole bags
# Ensure FertilizerOptimizerService receives correct nutrient requirements
# (e.g. 14, 23, 15 kg for 1 acre groundnut) and produces a feasible MILP plan.
# ==============================================================================
def test_i_optimizer_receives_correct_farm_totals():
    opt_service = FertilizerOptimizerService()

    # Pass Phase 5 output for 1-acre groundnut (14 N, 23 P2O5, 15 K2O kg)
    phase5_mock = {
        "crop": "Groundnut",
        "total_n_req_kg": 14.0,
        "total_p2o5_req_kg": 23.0,
        "total_k2o_req_kg": 15.0,
        "farm_area_hectares": 0.4046856422,
    }
    opt_req = FertilizerOptimizationRequest(
        crop="Groundnut",
        phase5_result=phase5_mock,
    )
    opt_res = opt_service.optimize(opt_req)

    assert opt_res.status == "OPTIMIZATION_SUCCESS"
    assert opt_res.total_cost_inr > 0

    # Verify nutrient delivery >= required (no shortfall)
    bal = opt_res.nutrient_balance
    assert bal["nitrogen"].required_kg == 14.0
    assert bal["nitrogen"].supplied_kg >= 14.0
    assert bal["phosphorus_p2o5"].required_kg == 23.0
    assert bal["phosphorus_p2o5"].supplied_kg >= 23.0
    assert bal["potassium_k2o"].required_kg == 15.0
    assert bal["potassium_k2o"].supplied_kg >= 15.0

    # Verify whole commercial bags only
    for prod in opt_res.recommended_products:
        assert isinstance(prod.bags, int)
        assert prod.bags > 0
        assert prod.quantity_kg == prod.bags * prod.bag_size_kg
        assert prod.total_cost_inr == prod.bags * prod.price_per_bag_inr
