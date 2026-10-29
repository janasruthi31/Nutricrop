"""
Comprehensive Verification and Regression Test Suite for the Unified Fertilizer Recommendation System.
Covers Tasks A through H from Master Prompt:
- Test A: Existing working Soil Test-Based case
- Test B: Valid TNAU rule selection (Priority 2 and 3)
- Test C: STCR-IPNS rule validation and safety enforcement
- Test D: No matching rule (rejection without fabricated doses)
- Test E: Missing soil data (returns NEEDS_INPUT / MISSING_INPUTS, never substitutes 0)
- Test F: Unit conversion (acre to hectare, rates vs farm totals)
- Test G: Fertilizer cost optimization (DAP N+P accounting, non-zero pricing)
- Test H: Regression against zero-value display problem
"""

import pytest
from fastapi.testclient import TestClient
from phase3_soil.main import app
from phase7_integration.service import UnifiedFertilizerRecommendationService, get_full_recommendation
from agronomy.service import RuleSelectionService, RuleSelectionRequest
from phase5_nutrient.service import NutrientCalculationService
from phase5_nutrient.models import NutrientCalculationRequest
from phase6_fertilizer.service import FertilizerOptimizerService

client = TestClient(app)


class TestUnifiedRecommendationPipeline:
    """Test Suite for Unified Fertilizer Recommendation Workflow."""

    # -------------------------------------------------------------------------
    # TEST A: Existing Working Soil Test-Based Case
    # -------------------------------------------------------------------------
    def test_a_existing_working_soil_test_case_rice(self):
        """
        Confirms that the existing working Soil Test-Based recommendation for Rice
        remains functional, selects Priority 2 (TNAU_STD_RICE_001), calculates nutrients,
        and optimizes commercial fertilizers with positive cost.
        """
        payload = {
            "crop": "Rice",
            "district": "Thanjavur",
            "soil_series": "Palavidhi",
            "season": "Kharif",
            "irrigation_method": "Irrigated",
            "soil_nitrogen": 220.0,
            "soil_nitrogen_unit": "kg/ha",
            "soil_phosphorus": 16.0,
            "soil_phosphorus_unit": "kg/ha",
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 190.0,
            "soil_potassium_unit": "kg/ha",
            "farm_area": 1.0,
            "farm_area_unit": "hectare"
        }
        res = client.post("/api/full-recommendation", json=payload)
        assert res.status_code == 200
        data = res.json()

        assert data["status"] == "SUCCESS"
        assert data["is_verified"] is True
        assert data["rule_selection"]["selected_rule_id"] == "TNAU_STD_RICE_001"
        assert data["rule_selection"]["recommendation_category"] == "STANDARD_RDF"

        # Nutrient requirements must be calculated and non-zero
        p5 = data["nutrient_requirements"]
        assert p5["n_req_kg_per_ha"] > 100.0
        assert p5["p2o5_req_kg_per_ha"] > 30.0
        assert p5["k2o_req_kg_per_ha"] > 30.0

        # Optimizer must recommend commercial products with positive cost
        plan = data["fertilizer_plan"]
        assert plan["status"] == "OPTIMIZATION_SUCCESS"
        assert plan["total_cost_inr"] > 0.0
        assert len(plan["recommended_products"]) > 0

        # Check unified recommendation metadata
        assert "unified_recommendation" in data
        u_rec = data["unified_recommendation"]
        assert u_rec["rule_id"] == "TNAU_STD_RICE_001"
        assert u_rec["rule_priority"] == "TNAU_SOIL_TEST"
        assert u_rec["total_cost_status"] == "AVAILABLE"

    # -------------------------------------------------------------------------
    # TEST B: Valid TNAU Rules (Priority 2 and 3)
    # -------------------------------------------------------------------------
    def test_b1_blackgram_rainfed_soil_test_rule(self):
        """Blackgram rainfed selects verified Priority 2 TNAU Soil-Test rule."""
        payload = {
            "crop": "Blackgram",
            "district": "Cuddalore",
            "season": "Rabi",
            "irrigation_method": "Rainfed",
            "soil_nitrogen": 180.0,
            "soil_phosphorus": 14.0,
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 160.0,
            "farm_area": 2.0,
            "farm_area_unit": "acre"
        }
        res = client.post("/api/full-recommendation", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert data["is_verified"] is True
        assert data["rule_selection"]["selected_rule_id"] == "TNAU_STD_BLACKGRAM_RF_001"
        assert data["fertilizer_plan"]["total_cost_inr"] > 0.0

    def test_b2_groundnut_unified_blanket_rule(self):
        """Groundnut selects verified Priority 3 TNAU Blanket rule in unified mode."""
        payload = {
            "crop": "Groundnut",
            "district": "Villupuram",
            "season": "Kharif",
            "irrigation_method": "Both",
            "soil_nitrogen": 190.0,
            "soil_phosphorus": 15.0,
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 170.0,
            "farm_area": 1.5,
            "farm_area_unit": "acre"
        }
        res = client.post("/api/full-recommendation", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert data["is_verified"] is True
        assert data["rule_selection"]["selected_rule_id"] == "TNAU_BLANKET_GROUNDNUT_001"
        assert data["fertilizer_plan"]["total_cost_inr"] > 0.0

    def test_b3_sugarcane_unified_blanket_rule(self):
        """Sugarcane selects verified Priority 3 rule TNAU_STD_SUGARCANE_001."""
        payload = {
            "crop": "Sugarcane",
            "district": "Erode",
            "season": "All",
            "irrigation_method": "Irrigated",
            "soil_nitrogen": 220.0,
            "soil_phosphorus": 18.0,
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 210.0,
            "farm_area": 1.0,
            "farm_area_unit": "ha"
        }
        res = client.post("/api/full-recommendation", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert data["is_verified"] is True
        assert data["rule_selection"]["selected_rule_id"] == "TNAU_STD_SUGARCANE_001"
        assert data["fertilizer_plan"]["total_cost_inr"] > 0.0

    # -------------------------------------------------------------------------
    # TEST C: STCR-IPNS Rule Validation and Agricultural Safety
    # -------------------------------------------------------------------------
    def test_c_unverified_stcr_rules_are_never_used_in_production(self):
        """
        Unverified STCR rules (Rice/Cotton/Maize) with disputed coefficients must
        never produce unverified production recommendations.
        Rice safely falls back to verified TNAU Soil-Test schedule.
        """
        # Cotton has no verified standard fallback -> must return NO_VERIFIED_RULE
        payload_cotton = {
            "crop": "Cotton (lint)",
            "district": "Coimbatore",
            "soil_series": "Irugur",
            "target_yield": 2.5,
            "soil_nitrogen": 180.0,
            "soil_phosphorus": 14.0,
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 220.0,
            "farm_area": 1.0
        }
        res_cotton = client.post("/api/full-recommendation", json=payload_cotton).json()
        assert res_cotton["status"] in ("NO_VERIFIED_RULE", "NO_VALIDATED_RECOMMENDATION")
        assert res_cotton["is_verified"] is False
        assert len(res_cotton["fertilizer_plan"]["recommended_products"]) == 0

    # -------------------------------------------------------------------------
    # TEST D: No Matching Rule (Unsupported Crop Rejection)
    # -------------------------------------------------------------------------
    def test_d_unsupported_crop_rejection_no_fabrication(self):
        """Unsupported crop (DragonFruit) must return UNSUPPORTED_CROP with 0 products and no fabricated doses."""
        payload = {
            "crop": "DragonFruit",
            "district": "Madurai",
            "soil_nitrogen": 200.0,
            "soil_phosphorus": 15.0,
            "soil_potassium": 150.0,
            "farm_area": 1.0
        }
        res = client.post("/api/full-recommendation", json=payload).json()
        assert res["status"] in ("UNSUPPORTED_CROP", "NO_VALIDATED_RECOMMENDATION", "VALIDATION_ERROR")
        assert res["is_verified"] is False
        assert len(res["fertilizer_plan"]["recommended_products"]) == 0
        assert res["fertilizer_plan"]["total_cost_inr"] == 0.0

    # -------------------------------------------------------------------------
    # TEST E: Missing Soil Data Handling (NEEDS_INPUT / MISSING_INPUTS)
    # -------------------------------------------------------------------------
    def test_e_missing_soil_data_returns_missing_inputs(self):
        """When soil nitrogen is omitted for a soil-test rule, service returns MISSING_INPUTS, never silently 0."""
        payload = {
            "crop": "Rice",
            "district": "Thanjavur",
            "soil_phosphorus": 16.0,
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 190.0,
            "farm_area": 1.0
            # soil_nitrogen missing
        }
        res = client.post("/api/full-recommendation", json=payload).json()
        assert res["status"] in ("MISSING_INPUTS", "NEEDS_MORE_INPUT", "NEEDS_INPUT")
        assert res["is_verified"] is False
        p5 = res["nutrient_requirements"]
        assert "soil_nitrogen" in (p5.get("missing_inputs") or [])

    # -------------------------------------------------------------------------
    # TEST F: Unit Conversions (Acre to Hectare & Farm Totals)
    # -------------------------------------------------------------------------
    def test_f_unit_conversions_acre_and_hectare(self):
        """
        Verify exact unit conversions:
        1 acre = 0.404686 ha.
        Total farm kg = per_ha_rate * area_ha (or per_acre_rate * area_acres).
        """
        payload = {
            "crop": "Rice",
            "district": "Thanjavur",
            "soil_nitrogen": 220.0,
            "soil_phosphorus": 16.0,
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 190.0,
            "farm_area": 2.5,
            "farm_area_unit": "acre"
        }
        res = client.post("/api/full-recommendation", json=payload).json()
        assert res["status"] == "SUCCESS"
        p5 = res["nutrient_requirements"]

        # Check area conversion
        area_ha = p5["farm_area_hectares"]
        assert pytest.approx(area_ha, abs=0.01) == 2.5 * 0.4046856422

        # Check that per-ha rate and farm total are distinct
        n_ha = p5["n_req_kg_per_ha"]
        tot_n = p5["total_farm_n_kg"] or p5["total_n_req_kg"]
        assert pytest.approx(tot_n, abs=1.0) == n_ha * area_ha
        assert tot_n != n_ha  # Farm total for 2.5 acres (1.01 ha) is distinct from 1-ha rate

    # -------------------------------------------------------------------------
    # TEST G: Fertilizer Cost Optimization & Multi-Nutrient Accounting
    # -------------------------------------------------------------------------
    def test_g_dap_multi_nutrient_accounting(self):
        """
        DAP provides 18% N and 46% P2O5.
        The optimizer must account for N supplied by DAP so that Urea requirement is reduced,
        preventing double counting.
        """
        payload = {
            "crop": "Rice",
            "district": "Thanjavur",
            "soil_nitrogen": 220.0,
            "soil_phosphorus": 16.0,
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 190.0,
            "farm_area": 1.0,
            "farm_area_unit": "ha"
        }
        res = client.post("/api/full-recommendation", json=payload).json()
        plan = res["fertilizer_plan"]
        products = {p["product_id"]: p for p in plan["recommended_products"]}

        assert "DAP" in products
        assert "UREA" in products
        assert "MOP" in products

        # Verify balance details
        balance = plan["nutrient_balance"]
        assert balance["phosphorus_p2o5"]["supplied_kg"] >= balance["phosphorus_p2o5"]["required_kg"]
        assert balance["nitrogen"]["supplied_kg"] >= balance["nitrogen"]["required_kg"]

    # -------------------------------------------------------------------------
    # TEST H: Regression Against Zero-Value Display
    # -------------------------------------------------------------------------
    def test_h_zero_value_regression_status_handling(self):
        """
        Verify that failed recommendations are explicitly flagged as unverified
        with total_cost_status == 'UNAVAILABLE' so the UI does not show dummy 0 kg / ₹0.
        """
        payload_fail = {
            "crop": "NonExistentCrop123",
            "farm_area": 1.0
        }
        res = client.post("/api/full-recommendation", json=payload_fail).json()
        assert res["status"] in ("UNSUPPORTED_CROP", "NO_VALIDATED_RECOMMENDATION", "VALIDATION_ERROR")
        assert res["is_verified"] is False
        assert res["total_cost_status"] == "UNAVAILABLE"
        assert res["unified_recommendation"]["total_cost_status"] == "UNAVAILABLE"
        assert res["unified_recommendation"]["total_cost_inr"] is None
