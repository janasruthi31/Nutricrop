"""
Regression and Verification Test Suite for Sections C, D, and E:
- Section C: Olsen/Bray Soil Phosphorus Test Method Compatibility & Preservation
- Section D: Fertilizer Optimizer Objectives, Multi-Nutrient Accounting & Constraints
- Section E: ML Yield Benchmark Target Definition, Units, Decoupling & Validation
"""

import pytest
import os
import json
from phase3_soil.extraction import extract_fields
from phase5_nutrient.service import NutrientCalculationService
from phase5_nutrient.models import NutrientCalculationRequest
from agronomy.service import RuleSelectionService, RuleSelectionRequest
from agronomy.registry import AgronomicRuleRegistry
from phase6_fertilizer.service import FertilizerOptimizerService
from phase6_fertilizer.models import FertilizerOptimizationRequest
from phase7_integration.service import get_full_recommendation
from predict_yield import predict_district_yield


# ==============================================================================
# SECTION C: SOIL PHOSPHORUS METHOD VALIDATION & COMPATIBILITY
# ==============================================================================

class TestSectionCSoilPhosphorusMethodCompatibility:
    """Verifies Olsen/Bray handling, non-invention by OCR, and metadata preservation."""

    def test_c01_ocr_does_not_invent_phosphorus_method(self):
        """When the report text does not mention Olsen or Bray, method remains None."""
        raw_text_no_method = """
        GOVERNMENT OF TAMIL NADU - SOIL TESTING LABORATORY
        Farmer Name: Murugan, District: Thanjavur
        Available Nitrogen: 210 kg/ha
        Available Phosphorus: 18.5 kg/ha
        Available Potassium: 195 kg/ha
        pH: 7.2, EC: 0.4 dS/m
        """
        lines = [{"text": l.strip(), "words": []} for l in raw_text_no_method.strip().splitlines()]
        extracted = extract_fields(lines)
        assert extracted["phosphorus"]["value"] == 18.5
        # Verify method is None, NOT guessed or invented
        assert extracted["phosphorus"]["test_method"] is None
        assert extracted["phosphorus"]["method_source"] is None

    def test_c02_ocr_extracts_explicit_olsen_method(self):
        """When text explicitly mentions Olsen, method is captured as 'olsen'."""
        raw_text_olsen = """
        SOIL HEALTH CARD - CUDDALORE
        Available Nitrogen: 240 kg/ha
        Available Phosphorus (Olsen): 14.2 kg/ha
        Available Potassium: 210 kg/ha
        """
        lines = [{"text": l.strip(), "words": []} for l in raw_text_olsen.strip().splitlines()]
        extracted = extract_fields(lines)
        assert extracted["phosphorus"]["value"] == 14.2
        assert extracted["phosphorus"]["test_method"] == "Olsen"
        assert extracted["phosphorus"]["method_source"] == "same_line"

    def test_c03_ocr_extracts_explicit_bray_method(self):
        """When text explicitly mentions Bray, method is captured as 'bray'."""
        raw_text_bray = """
        SOIL ANALYSIS REPORT - NILGIRIS
        Available Phosphorus (Bray): 22.0 kg/ha
        Available Potassium: 180 kg/ha
        pH: 5.2
        """
        lines = [{"text": l.strip(), "words": []} for l in raw_text_bray.strip().splitlines()]
        extracted = extract_fields(lines)
        assert extracted["phosphorus"]["value"] == 22.0
        assert extracted["phosphorus"]["test_method"] == "Bray"
        assert extracted["phosphorus"]["method_source"] == "same_line"

    def test_c04_missing_phosphorus_method_requires_clarification(self):
        """When phosphorus test method is missing, Phase 4 returns NEEDS_MORE_INPUT / MISSING_PHOSPHORUS_METHOD."""
        rule_service = RuleSelectionService()
        p4_req = RuleSelectionRequest(
            crop="Rice",
            district="Thanjavur",
            soil_series="Adanur",
            target_yield=5.0,
            soil_values={
                "nitrogen": 210.0,
                "phosphorus": 14.0,
                "potassium": 200.0,
                "phosphorus_method": None  # Missing!
            }
        )
        p4_res = rule_service.select_rule(p4_req)
        assert p4_res.status == "NEEDS_MORE_INPUT"
        assert p4_res.error_code == "MISSING_PHOSPHORUS_METHOD"
        assert "phosphorus_method" in p4_res.missing_inputs
        assert "Phosphorus test method" in p4_res.actionable_message

    def test_c05_incompatible_phosphorus_method_is_rejected(self):
        """When method is incompatible with verified STCR/RDF rules (e.g. Mehlich3 or Bray on Olsen-only), status is INCOMPATIBLE_SOIL_TEST_METHOD."""
        rule_service = RuleSelectionService()
        p4_req = RuleSelectionRequest(
            crop="Rice",
            district="Thanjavur",
            soil_series="Adanur",
            target_yield=5.0,
            soil_values={
                "nitrogen": 210.0,
                "phosphorus": 14.0,
                "potassium": 200.0,
                "phosphorus_method": "mehlich3"  # Incompatible!
            }
        )
        p4_res = rule_service.select_rule(p4_req)
        assert p4_res.status == "INCOMPATIBLE_SOIL_TEST_METHOD"
        assert p4_res.error_code == "INCOMPATIBLE_SOIL_TEST_METHOD"

    def test_c06_full_recommendation_preserves_phosphorus_metadata_and_no_conversion(self):
        """Phase 7 recommendation payload preserves original test method, unit, sampling date, and confirms conversion_applied is False."""
        req = {
            "crop": "Rice",
            "soil_series": "Adanur",
            "target_yield": 5.5,
            "soil_nitrogen": 220.0,
            "soil_phosphorus": 16.0,
            "soil_potassium": 210.0,
            "organic_carbon": 0.55,
            "soil_phosphorus_method": "olsen",
            "district": "Thanjavur",
            "season": "Kharif",
            "farm_area": 1.5,
            "farm_area_unit": "hectare",
            "test_date": "2026-10-15"
        }
        rec = get_full_recommendation(req)
        assert rec["status"] == "SUCCESS"
        soil_summary = rec["soil_test_summary"]
        assert soil_summary["phosphorus_method"] == "olsen"
        assert soil_summary["original_phosphorus_value"] == 16.0
        assert soil_summary["original_phosphorus_unit"] == "kg/ha"
        assert soil_summary["sampling_date"] == "2026-10-15"
        assert soil_summary["conversion_applied"] is False
        assert "No conversion factor applied between Olsen and Bray" in soil_summary["conversion_note"]


# ==============================================================================
# SECTION D: FERTILIZER OPTIMIZER CONSTRAINTS & MULTI-NUTRIENT ACCOUNTING
# ==============================================================================

class TestSectionDFertilizerOptimizerConstraints:
    """Verifies multi-nutrient balance, prohibited mixtures, availability, and infeasibility."""

    @pytest.fixture
    def optimizer(self):
        return FertilizerOptimizerService()

    def test_d01_multi_nutrient_product_dap_accounts_for_n_and_p(self, optimizer):
        """DAP (18% N, 46% P2O5) must satisfy both N and P requirements simultaneously."""
        # Target: 18 kg N, 46 kg P2O5, 0 kg K2O on 1 ha
        # 1 bag of DAP (50 kg) provides 9 kg N and 23 kg P2O5.
        # 2 bags of DAP (100 kg) provide exactly 18 kg N and 46 kg P2O5.
        req = FertilizerOptimizationRequest(
            crop="Rice",
            n_req_kg=18.0,
            p2o5_req_kg=46.0,
            k2o_req_kg=0.0,
            farm_area_hectares=1.0,
            allowed_fertilizers=["DAP", "UREA", "MOP"],
            allow_fractional_bags=False,
            max_surplus_factor=1.5
        )
        res = optimizer.optimize(req)
        assert res.status == "OPTIMIZATION_SUCCESS"
        # DAP should supply the required P2O5
        dap_item = next((item for item in res.recommended_products if item.product_id == "DAP"), None)
        assert dap_item is not None
        assert dap_item.bags == 2  # 100 kg of DAP
        # N supplied by DAP must be counted: 100 kg * 0.18 = 18 kg
        assert res.nutrient_balance["nitrogen"].supplied_kg >= 18.0
        # No extra Urea needed because DAP alone supplied 18 kg N!
        urea_item = next((item for item in res.recommended_products if item.product_id == "UREA"), None)
        assert urea_item is None or urea_item.bags == 0

    def test_d02_prohibited_combinations_rejected(self, optimizer):
        """Authoritative agronomic prohibition: Urea and CAN must not be requested together."""
        req = FertilizerOptimizationRequest(
            crop="Rice",
            n_req_kg=100.0,
            p2o5_req_kg=0.0,
            k2o_req_kg=0.0,
            farm_area_hectares=1.0,
            allowed_fertilizers=["UREA", "CAN"]
        )
        res = optimizer.optimize(req)
        # Should detect prohibition and return NO_FEASIBLE_SOLUTION / INFEASIBLE
        assert res.status in ("INFEASIBLE", "NO_FEASIBLE_SOLUTION")
        assert "Prohibited" in str(res.limiting_constraint)

    def test_d03_unavailable_or_unpriced_fertilizers_are_excluded(self):
        """Fertilizers with is_available=False or price <= 0 must never be selected."""
        custom_catalog = [
            {
                "id": "FREE_UREA",
                "name": "Free Urea Invalid",
                "category": "Nitrogen",
                "n_pct": 46.0,
                "p2o5_pct": 0.0,
                "k2o_pct": 0.0,
                "price_per_bag_inr": 0.0,  # Invalid price <= 0
                "bag_size_kg": 50.0,
                "is_available": True
            },
            {
                "id": "UNAVAIL_UREA",
                "name": "Unavailable Urea",
                "category": "Nitrogen",
                "n_pct": 46.0,
                "p2o5_pct": 0.0,
                "k2o_pct": 0.0,
                "price_per_bag_inr": 200.0,
                "bag_size_kg": 50.0,
                "is_available": False  # Unavailable!
            },
            {
                "id": "VALID_UREA",
                "name": "Valid Subsidized Urea",
                "category": "Nitrogen",
                "n_pct": 46.0,
                "p2o5_pct": 0.0,
                "k2o_pct": 0.0,
                "price_per_bag_inr": 266.5,
                "bag_size_kg": 45.0,
                "is_available": True
            }
        ]
        custom_optimizer = FertilizerOptimizerService(catalog=custom_catalog)
        req = FertilizerOptimizationRequest(
            crop="Rice",
            n_req_kg=46.0,
            p2o5_req_kg=0.0,
            k2o_req_kg=0.0,
            farm_area_hectares=1.0,
            allow_fractional_bags=True
        )
        res = custom_optimizer.optimize(req)
        assert res.status == "OPTIMIZATION_SUCCESS"
        selected_ids = [item.product_id for item in res.recommended_products]
        assert "FREE_UREA" not in selected_ids
        assert "UNAVAIL_UREA" not in selected_ids
        assert "VALID_UREA" in selected_ids

    def test_d04_infeasible_problem_returns_explicit_limiting_constraint(self, optimizer):
        """When a required nutrient cannot be supplied by available products, returns limiting_constraint."""
        # Need P2O5, but only N fertilizer (Urea) and K fertilizer (MOP) are available
        req = FertilizerOptimizationRequest(
            crop="Rice",
            n_req_kg=50.0,
            p2o5_req_kg=60.0,  # Impossible to supply
            k2o_req_kg=40.0,
            farm_area_hectares=1.0,
            allowed_fertilizers=["UREA", "MOP"],
            allow_fractional_bags=True
        )
        res = optimizer.optimize(req)
        assert res.status in ("INFEASIBLE", "NO_FEASIBLE_SOLUTION")
        assert res.limiting_constraint is not None
        assert "Phosphorus" in res.limiting_constraint or "P2O5" in res.limiting_constraint

    def test_d05_package_rounding_effects_and_timestamp_reported(self, optimizer):
        """Optimizer reports package rounding effects and price data timestamp."""
        req = FertilizerOptimizationRequest(
            crop="Rice",
            n_req_kg=30.0,
            p2o5_req_kg=20.0,
            k2o_req_kg=20.0,
            farm_area_hectares=0.4,  # Smallholder: ~1 acre
            allow_fractional_bags=False,
            max_surplus_factor=2.5
        )
        res = optimizer.optimize(req)
        assert res.status == "OPTIMIZATION_SUCCESS"
        assert res.price_data_timestamp == "2026-10-22"
        assert res.package_rounding_effects is not None
        assert "whole_bags_total" in res.package_rounding_effects
        assert "packaging_description" in res.package_rounding_effects


# ==============================================================================
# SECTION E: ML YIELD BENCHMARK DEFINITION, EVALUATION & LIMITATIONS
# ==============================================================================

class TestSectionEYieldBenchmarkClarityAndValidation:
    """Verifies target variable (kg/ha yield), Table V-A ground truth, decoupling, and limitations."""

    def test_e01_yield_prediction_contract_returns_kg_per_ha(self):
        """Predict endpoint returns yield in kg/ha, not total production tonnes."""
        yield_kg_per_ha = predict_district_yield(
            district="Thanjavur",
            crop="Rice",
            season="Samba/Thaladi/Pishanam",
            year=2024
        )
        assert yield_kg_per_ha > 0
        # Derived production calculation for 2.0 ha
        derived_tonnes = round((yield_kg_per_ha / 1000.0) * 2.0, 2)
        assert derived_tonnes > 0

    def test_e02_unsupported_district_or_crop_returns_not_validated_or_error(self):
        """Requesting unsupported district or crop raises ValueError / not validated."""
        with pytest.raises(ValueError) as excinfo:
            predict_district_yield(
                district="NonExistentDistrict",
                crop="Rice",
                season="Kharif"
            )
        assert "not supported by the district yield benchmark model" in str(excinfo.value)

    def test_e03_yield_prediction_completely_decoupled_from_nutrient_requirements(self):
        """Varying rainfall and district yield does NOT alter agronomic nutrient targets."""
        # Request 1: Thanjavur (High rainfall delta)
        req1 = {
            "crop": "Rice",
            "soil_series": "Adanur",
            "target_yield": 5.0,
            "soil_nitrogen": 220.0,
            "soil_phosphorus": 16.0,
            "soil_potassium": 210.0,
            "organic_carbon": 0.55,
            "soil_phosphorus_method": "olsen",
            "district": "Thanjavur",
            "season": "Kharif",
            "farm_area": 1.0,
            "farm_area_unit": "hectare"
        }
        rec1 = get_full_recommendation(req1)

        # Request 2: Madurai (Different rainfall and district yield)
        req2 = {
            "crop": "Rice",
            "soil_series": "Adanur",
            "target_yield": 5.0,
            "soil_nitrogen": 220.0,
            "soil_phosphorus": 16.0,
            "soil_potassium": 210.0,
            "organic_carbon": 0.55,
            "soil_phosphorus_method": "olsen",
            "district": "Madurai",
            "season": "Kharif",
            "farm_area": 1.0,
            "farm_area_unit": "hectare"
        }
        rec2 = get_full_recommendation(req2)

        # 1. Agronomic nutrient requirements MUST be identical!
        assert rec1["nutrient_requirements"]["n_req_kg_per_ha"] == rec2["nutrient_requirements"]["n_req_kg_per_ha"]
        assert rec1["nutrient_requirements"]["p2o5_req_kg_per_ha"] == rec2["nutrient_requirements"]["p2o5_req_kg_per_ha"]
        assert rec1["nutrient_requirements"]["k2o_req_kg_per_ha"] == rec2["nutrient_requirements"]["k2o_req_kg_per_ha"]

        # 2. Fertilizer doses MUST be identical!
        assert rec1["fertilizer_plan"]["total_cost_inr"] == rec2["fertilizer_plan"]["total_cost_inr"]

        # 3. Only the district yield benchmark estimate differs by district
        assert rec1["district_yield_prediction"]["estimated_yield_kg_per_ha"] != rec2["district_yield_prediction"]["estimated_yield_kg_per_ha"]

    def test_e04_full_recommendation_includes_yield_limitations_and_source(self):
        """Full recommendation metadata explicitly contains model limitations and Table V-A source."""
        req = {
            "crop": "Rice",
            "soil_series": "Adanur",
            "target_yield": 5.0,
            "soil_nitrogen": 220.0,
            "soil_phosphorus": 16.0,
            "soil_potassium": 210.0,
            "organic_carbon": 0.55,
            "soil_phosphorus_method": "olsen",
            "district": "Madurai",
            "season": "Kharif",
            "farm_area": 1.0,
            "farm_area_unit": "hectare"
        }
        rec = get_full_recommendation(req)
        yield_pred = rec["district_yield_prediction"]
        assert yield_pred["status"] == "DISTRICT_BENCHMARK_ESTIMATE"
        assert "Season & Crop Report Table V-A" in yield_pred["target_definition"]
        assert len(yield_pred["limitations"]) >= 3
        # Check evaluation metrics are recorded
        assert "evaluation_metrics" in yield_pred
        assert yield_pred["evaluation_metrics"]["R2"] > 0.90
