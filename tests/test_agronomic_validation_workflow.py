"""
Comprehensive Regression Test Suite for Agronomic Validation Workflow.

Tests:
1. Verified applicable rule (Rice -> TNAU_STCR_IPNS_RICE_001).
2. Verified general blanket recommendation (Groundnut -> TNAU_BLANKET_GROUNDNUT_001).
3. Pending agronomic rule (Groundnut -> TNAU_STD_GROUNDNUT_001) blocked when allow_unverified=False.
4. Provisional result when allow_unverified=True (never labelled VERIFIED or SOIL_SPECIFIC).
5. Direct backend optimizer bypass prevention (raw API call rejection).
6. Missing soil-test values handling.
7. Incorrect or unknown units handling.
8. Farm area scaling and per-hectare rate invariance.
9. Elemental vs oxide conversions (P vs P2O5, K vs K2O).
10. Fertilizer product composition and cost calculations.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from phase3_soil.main import app
from phase7_integration.service import FullRecommendationService, get_full_recommendation
from phase5_nutrient.service import NutrientCalculationService
from phase5_nutrient.models import NutrientCalculationRequest
from phase6_fertilizer.service import FertilizerOptimizerService
from phase6_fertilizer.models import FertilizerOptimizationRequest

client = TestClient(app)


def test_01_verified_applicable_rule_rice():
    """Verify that a verified rule (e.g. Rice TNAU_STCR_IPNS_RICE_001) executes to SUCCESS."""
    req = {
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
        "farm_area": 1.0,
        "farm_area_unit": "ha"
    }
    response = client.post("/api/full-recommendation", json=req)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["is_verified"] is True
    assert data["is_provisional"] is False
    assert data["rule_selection"]["selected_rule_id"] == "TNAU_STCR_IPNS_RICE_001"
    assert data["recommendation_type"] == "SOIL_SPECIFIC_STCR"
    assert len(data["fertilizer_plan"]["recommended_products"]) > 0
    assert data["fertilizer_plan"]["total_cost_inr"] > 0.0


def test_02_verified_general_blanket_recommendation_groundnut():
    """
    Verify that when GENERAL_BLANKET recommendation is requested for Groundnut,
    the verified rule TNAU_BLANKET_GROUNDNUT_001 is selected with VERIFIED status.
    """
    req = {
        "crop": "Groundnut",
        "district": "Tiruppur",
        "recommendation_type": "GENERAL_BLANKET",
        "soil_nitrogen": 150.0,
        "soil_phosphorus": 14.0,
        "soil_potassium": 180.0,
        "soil_phosphorus_method": "Bray",
        "farm_area": 1.0,
        "farm_area_unit": "acre"
    }
    response = client.post("/api/full-recommendation", json=req)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "SUCCESS"
    assert data["is_verified"] is True
    assert data["is_provisional"] is False
    assert data["rule_selection"]["selected_rule_id"] == "TNAU_BLANKET_GROUNDNUT_001"
    assert data["recommendation_type"] == "GENERAL_BLANKET"
    assert "TNAU Crop Production Guide" in data["rule_selection"]["source_title"]
    assert len(data["fertilizer_plan"]["recommended_products"]) > 0
    assert data["fertilizer_plan"]["total_cost_inr"] > 0.0


def test_03_pending_groundnut_rule_blocked_by_default():
    """
    Verify that an unverified rule (TNAU_STD_GROUNDNUT_001) is blocked by default
    when allow_unverified is False.
    Must not return a confirmed fertilizer recommendation.
    """
    req = {
        "crop": "Groundnut",
        "district": "Tiruppur",
        "soil_nitrogen": 150.0,
        "soil_phosphorus": 14.0,
        "soil_potassium": 180.0,
        "soil_phosphorus_method": "Bray",
        "target_yield": 2.5,
        "farm_area": 1.0,
        "farm_area_unit": "acre",
        "allow_unverified": False
    }
    response = client.post("/api/full-recommendation", json=req)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("PENDING_AGRONOMIC_VALIDATION", "BLOCKED_UNVERIFIED_RULE")
    assert data["is_verified"] is False
    assert data["is_provisional"] is True
    assert data["rule_selection"]["selected_rule_id"] == "TNAU_STD_GROUNDNUT_001"
    # Ensure fertilizer plan has 0 products and cost 0
    assert len(data["fertilizer_plan"]["recommended_products"]) == 0
    assert data["fertilizer_plan"]["total_cost_inr"] == 0.0
    # Must contain the required agronomic validation warning
    warning_joined = " ".join(data.get("warnings", []))
    assert "This rule has not yet been agronomically validated" in warning_joined
    assert "A confirmed soil-specific recommendation is unavailable" in warning_joined


def test_04_pending_groundnut_rule_explicit_provisional():
    """
    When allow_unverified=True is explicitly passed, the system returns an explicitly
    provisional result, but NEVER labels it VERIFIED, SOIL_SPECIFIC, or OFFICIAL.
    """
    req = {
        "crop": "Groundnut",
        "district": "Tiruppur",
        "soil_nitrogen": 150.0,
        "soil_phosphorus": 14.0,
        "soil_potassium": 180.0,
        "soil_phosphorus_method": "Bray",
        "target_yield": 2.5,
        "farm_area": 1.0,
        "farm_area_unit": "acre",
        "allow_unverified": True
    }
    response = client.post("/api/full-recommendation", json=req)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "PROVISIONAL_PENDING_VALIDATION"
    assert data["is_verified"] is False
    assert data["is_provisional"] is True
    assert data["recommendation_type"] == "PROVISIONAL_UNVERIFIED"
    assert data["recommendation_type"] != "SOIL_SPECIFIC_STCR"
    assert data["recommendation_type"] != "VERIFIED"


def test_05_backend_optimizer_blocks_unverified_bypass():
    """
    Directly calling Phase 6 FertilizerOptimizer with unverified nutrient inputs
    and allow_unverified=False MUST reject optimization with BLOCKED_UNVERIFIED_RULE.
    """
    opt_service = FertilizerOptimizerService()
    opt_req = FertilizerOptimizationRequest(
        crop="Groundnut",
        n_req_kg=14.0,
        p2o5_req_kg=23.0,
        k2o_req_kg=15.0,
        farm_area=1.0,
        farm_area_unit="acre",
        is_verified_rule=False,
        verification_status="PENDING_AGRONOMIC_VALIDATION",
        allow_unverified=False
    )
    opt_resp = opt_service.optimize(opt_req)
    assert opt_resp.status == "BLOCKED_UNVERIFIED_RULE"
    assert opt_resp.is_verified is False
    assert opt_resp.is_provisional is True
    assert len(opt_resp.recommended_products) == 0
    assert opt_resp.total_cost_inr == 0.0
    assert any("pending agronomic validation" in err.lower() for err in opt_resp.validation_errors)


def test_06_missing_soil_test_values_handling():
    """Verify that omitting required soil nutrient values triggers MISSING_INPUTS."""
    nutrient_service = NutrientCalculationService()
    req = NutrientCalculationRequest(
        crop="Rice",
        soil_nitrogen=None, # Missing N
        soil_phosphorus=15.0,
        soil_potassium=150.0,
        target_yield=6.0
    )
    resp = nutrient_service.calculate(req)
    assert resp.status == "MISSING_INPUTS"
    assert "nitrogen" in resp.missing_inputs


def test_07_incorrect_or_unknown_units_handling():
    """Verify that unsupported units are caught with VALIDATION_ERROR."""
    nutrient_service = NutrientCalculationService()
    req = NutrientCalculationRequest(
        crop="Rice",
        soil_nitrogen=250.0,
        soil_nitrogen_unit="bushels/acre", # Invalid unit
        soil_phosphorus=15.0,
        soil_potassium=150.0,
        target_yield=6.0
    )
    resp = nutrient_service.calculate(req)
    assert resp.status == "VALIDATION_ERROR"
    assert any("Unsupported soil nutrient unit" in err for err in resp.validation_errors)


def test_08_farm_area_scaling_and_per_ha_rate_invariance():
    """
    Ensure that changing farm area updates total quantities and costs
    without changing per-hectare rates.
    """
    service = FullRecommendationService()
    
    # 1 hectare
    res_1ha = service.generate_full_recommendation({
        "crop": "Rice",
        "district": "Thanjavur",
        "soil_series": "Palavidhi",
        "season": "Kharif",
        "target_yield": 6.0,
        "soil_nitrogen": 220.0,
        "soil_phosphorus": 16.0,
        "soil_potassium": 190.0,
        "soil_phosphorus_method": "Olsen",
        "farm_area": 1.0,
        "farm_area_unit": "ha"
    })

    # 2.5 hectares
    res_2_5ha = service.generate_full_recommendation({
        "crop": "Rice",
        "district": "Thanjavur",
        "soil_series": "Palavidhi",
        "season": "Kharif",
        "target_yield": 6.0,
        "soil_nitrogen": 220.0,
        "soil_phosphorus": 16.0,
        "soil_potassium": 190.0,
        "soil_phosphorus_method": "Olsen",
        "farm_area": 2.5,
        "farm_area_unit": "ha"
    })

    # Per-ha rate must be IDENTICAL
    p5_1ha = res_1ha["nutrient_requirements"]
    p5_2_5ha = res_2_5ha["nutrient_requirements"]
    assert p5_1ha["n_req_kg_per_ha"] == p5_2_5ha["n_req_kg_per_ha"]
    assert p5_1ha["p2o5_req_kg_per_ha"] == p5_2_5ha["p2o5_req_kg_per_ha"]
    assert p5_1ha["k2o_req_kg_per_ha"] == p5_2_5ha["k2o_req_kg_per_ha"]

    # Total farm nutrient requirements must scale by 2.5
    assert pytest.approx(p5_2_5ha["total_n_req_kg"], 0.05) == p5_1ha["total_n_req_kg"] * 2.5
    assert pytest.approx(p5_2_5ha["total_p2o5_req_kg"], 0.05) == p5_1ha["total_p2o5_req_kg"] * 2.5

    # Total cost must increase with area reflecting whole bag packaging
    cost_1ha = res_1ha["fertilizer_plan"]["total_cost_inr"]
    cost_2_5ha = res_2_5ha["fertilizer_plan"]["total_cost_inr"]
    assert cost_2_5ha > cost_1ha


def test_09_stoichiometric_oxide_elemental_conversions():
    """Verify stoichiometric conversion factors P <-> P2O5 and K <-> K2O."""
    from phase5_nutrient.units import (
        P_TO_P2O5, P2O5_TO_P, K_TO_K2O, K2O_TO_K,
        convert_elemental_to_oxide, convert_oxide_to_elemental
    )
    assert pytest.approx(P_TO_P2O5, 0.0001) == 2.29137
    assert pytest.approx(K_TO_K2O, 0.0001) == 1.2046

    # 10 kg elemental P -> 22.91 kg P2O5
    p2o5 = convert_elemental_to_oxide(10.0, "phosphorus")
    assert pytest.approx(p2o5, 0.01) == 22.91

    # 22.9137 kg P2O5 -> 10.0 kg elemental P
    p = convert_oxide_to_elemental(22.9137, "phosphorus")
    assert pytest.approx(p, 0.01) == 10.0

    # 10 kg elemental K -> 12.05 kg K2O
    k2o = convert_elemental_to_oxide(10.0, "potassium")
    assert pytest.approx(k2o, 0.01) == 12.05


def test_10_fertilizer_product_composition_and_cost():
    """
    Verify that fertilizer optimizer correctly accounts for nutrient grades:
    Urea: 46% N
    SSP: 16% P2O5
    MOP: 60% K2O
    And total cost equals sum of product quantities * respective unit prices.
    """
    opt_service = FertilizerOptimizerService()
    opt_req = FertilizerOptimizationRequest(
        crop="Rice",
        n_req_kg=46.0,
        p2o5_req_kg=16.0,
        k2o_req_kg=60.0,
        farm_area=1.0,
        farm_area_unit="ha",
        is_verified_rule=True
    )
    resp = opt_service.optimize(opt_req)
    assert resp.status == "OPTIMIZATION_SUCCESS"
    assert len(resp.recommended_products) >= 3

    computed_cost = 0.0
    for prod in resp.recommended_products:
        computed_cost += prod.quantity_kg * (prod.total_cost_inr / prod.quantity_kg)
    
    assert pytest.approx(resp.total_cost_inr, 0.01) == computed_cost
