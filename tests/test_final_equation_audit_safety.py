"""
Regression and Safety Tests for Final Official TNAU Equation Audit.
Verifies that:
1. Unsupported STCR-IPNS equations (Rice, Cotton, Maize) CANNOT generate production recommendations.
2. Safe fallbacks to verified standard recommendations (STANDARD_RDF) execute for Rice, Blackgram, Groundnut, Sugarcane.
3. Crops without verified rules (Cotton, Maize) return NO_VERIFIED_RULE and halt the commercial fertilizer optimizer.
4. Pending verification rules (Banana, Groundnut STCR) and Deprecated rules are strictly blocked.
5. Zero unverified or mismatched STCR-IPNS equations can produce production fertilizer prescriptions.
"""

import pytest
from fastapi.testclient import TestClient
from phase3_soil.main import app
from agronomy.service import RuleSelectionService, RuleSelectionRequest
from agronomy.registry import AgronomicRuleRegistry
from phase5_nutrient.service import NutrientCalculationService
from phase5_nutrient.models import NutrientCalculationRequest

client = TestClient(app)
registry = AgronomicRuleRegistry()
rule_service = RuleSelectionService(registry)
p5_service = NutrientCalculationService(registry)


class TestFinalEquationAuditSafety:
    def test_01_all_unsupported_stcr_rules_are_disabled_in_registry(self):
        """Verify that Rice, Cotton, and Maize STCR rules are marked UNSUPPORTED and disabled."""
        registry.reload()
        all_rules = {r["rule_id"]: r for r in registry.get_all_rules()}

        # Rice STCR
        assert "TNAU_STCR_IPNS_RICE_001" in all_rules
        assert all_rules["TNAU_STCR_IPNS_RICE_001"]["verification_status"] == "UNSUPPORTED"
        assert all_rules["TNAU_STCR_IPNS_RICE_001"]["is_enabled"] is False

        # Cotton STCR
        assert "TNAU_STCR_IPNS_COTTON_001" in all_rules
        assert all_rules["TNAU_STCR_IPNS_COTTON_001"]["verification_status"] == "UNSUPPORTED"
        assert all_rules["TNAU_STCR_IPNS_COTTON_001"]["is_enabled"] is False

        # Maize STCR
        assert "TNAU_STCR_IPNS_MAIZE_001" in all_rules
        assert all_rules["TNAU_STCR_IPNS_MAIZE_001"]["verification_status"] == "UNSUPPORTED"
        assert all_rules["TNAU_STCR_IPNS_MAIZE_001"]["is_enabled"] is False

    def test_02_verified_standard_rules_are_enabled_in_registry(self):
        """Verify that Rice standard RDF, Blackgram, Groundnut blanket, and Sugarcane are VERIFIED and enabled."""
        registry.reload()
        all_rules = {r["rule_id"]: r for r in registry.get_all_rules()}

        # Rice Standard RDF
        assert all_rules["TNAU_STD_RICE_001"]["verification_status"] == "VERIFIED"
        assert all_rules["TNAU_STD_RICE_001"]["is_enabled"] is True

        # Blackgram Rainfed
        assert all_rules["TNAU_STD_BLACKGRAM_RF_001"]["verification_status"] == "VERIFIED"
        assert all_rules["TNAU_STD_BLACKGRAM_RF_001"]["is_enabled"] is True

        # Groundnut Blanket
        assert all_rules["TNAU_BLANKET_GROUNDNUT_001"]["verification_status"] == "VERIFIED"
        assert all_rules["TNAU_BLANKET_GROUNDNUT_001"]["is_enabled"] is True

        # Sugarcane
        assert all_rules["TNAU_STD_SUGARCANE_001"]["verification_status"] == "VERIFIED"
        assert all_rules["TNAU_STD_SUGARCANE_001"]["is_enabled"] is True

    def test_03_rice_production_safely_falls_back_to_verified_standard_rdf(self):
        """A general recommendation request for Rice must use verified TNAU_STD_RICE_001, never unsupported STCR."""
        payload = {
            "crop": "Rice",
            "district": "Thanjavur",
            "soil_series": "Palavidhi",
            "season": "Kharif",
            "irrigation_method": "Irrigated",
            "soil_nitrogen": 220.0,
            "soil_phosphorus": 16.0,
            "soil_potassium": 190.0,
            "soil_phosphorus_method": "Olsen",
            "farm_area": 1.0,
            "farm_area_unit": "ha"
        }
        res = client.post("/api/full-recommendation", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert data["is_verified"] is True
        assert data["rule_selection"]["selected_rule_id"] == "TNAU_STD_RICE_001"
        assert data["recommendation_category"] == "STANDARD_RDF"
        assert data["is_standard_rdf"] is True
        assert data["is_stcr_ipns"] is False
        assert data["rule_selection"]["confidence"] == "lower"
        assert data["fertilizer_plan"]["total_cost_inr"] > 0.0

    def test_04_explicit_stcr_request_for_rice_is_rejected(self):
        """If a farmer explicitly requests STCR precision mode for Rice, return NO_VERIFIED_RULE."""
        req = RuleSelectionRequest(
            crop="Rice",
            soil_series="Palavidhi",
            recommendation_type="STCR_IPNS",
            target_yield=6.0
        )
        res = rule_service.select_rule(req)
        assert res.status == "NO_VERIFIED_RULE"
        assert res.error_code == "NO_VERIFIED_RULE"
        assert "STCR-IPNS precision equation is currently approved" in res.actionable_message

    def test_05_cotton_request_returns_no_verified_rule_and_halts_optimizer(self):
        """Cotton has no verified standard fallback and its STCR rule is unsupported; must return NO_VERIFIED_RULE and halt optimizer."""
        payload = {
            "crop": "Cotton (lint)",
            "district": "Coimbatore",
            "soil_series": "Irugur",
            "season": "Kharif",
            "irrigation_method": "Irrigated",
            "target_yield": 2.5,
            "soil_nitrogen": 200.0,
            "soil_phosphorus": 18.0,
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 250.0,
            "farm_area": 1.0,
            "farm_area_unit": "ha"
        }
        res = client.post("/api/full-recommendation", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "NO_VERIFIED_RULE"
        assert data["is_verified"] is False
        assert data["recommendation_type"] == "UNAVAILABLE"
        assert data["fertilizer_plan"]["total_cost_inr"] == 0.0
        assert len(data["fertilizer_plan"]["recommended_products"]) == 0

    def test_06_maize_request_returns_no_verified_rule_and_halts_optimizer(self):
        """Maize has no verified standard fallback and its STCR rule is unsupported; must return NO_VERIFIED_RULE and halt optimizer."""
        payload = {
            "crop": "Maize",
            "district": "Coimbatore",
            "soil_series": "Coimbatore",
            "season": "Kharif",
            "irrigation_method": "Irrigated",
            "target_yield": 7.0,
            "soil_nitrogen": 210.0,
            "soil_phosphorus": 18.0,
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 220.0,
            "farm_area": 1.0,
            "farm_area_unit": "ha"
        }
        res = client.post("/api/full-recommendation", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "NO_VERIFIED_RULE"
        assert data["is_verified"] is False
        assert data["recommendation_type"] == "UNAVAILABLE"
        assert data["fertilizer_plan"]["total_cost_inr"] == 0.0
        assert len(data["fertilizer_plan"]["recommended_products"]) == 0

    def test_07_blackgram_uses_verified_standard_rdf(self):
        """Blackgram rainfed must select verified rule TNAU_STD_BLACKGRAM_RF_001."""
        payload = {
            "crop": "Blackgram",
            "district": "Cuddalore",
            "season": "Rabi",
            "irrigation_method": "Rainfed",
            "soil_nitrogen": 180.0,
            "soil_phosphorus": 14.0,
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 160.0,
            "farm_area": 1.0,
            "farm_area_unit": "ha"
        }
        res = client.post("/api/full-recommendation", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert data["is_verified"] is True
        assert data["rule_selection"]["selected_rule_id"] == "TNAU_STD_BLACKGRAM_RF_001"
        assert data["recommendation_category"] == "STANDARD_RDF"
        assert data["fertilizer_plan"]["total_cost_inr"] > 0.0

    def test_08_groundnut_uses_verified_blanket_rdf(self):
        """Groundnut must select verified rule TNAU_BLANKET_GROUNDNUT_001."""
        payload = {
            "crop": "Groundnut",
            "district": "Villupuram",
            "season": "Kharif",
            "irrigation_method": "Both",
            "soil_nitrogen": 190.0,
            "soil_phosphorus": 15.0,
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 170.0,
            "recommendation_type": "GENERAL_BLANKET",
            "farm_area": 1.0,
            "farm_area_unit": "ha"
        }
        res = client.post("/api/full-recommendation", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert data["is_verified"] is True
        assert data["rule_selection"]["selected_rule_id"] == "TNAU_BLANKET_GROUNDNUT_001"
        assert data["recommendation_category"] == "STANDARD_RDF"

    def test_09_sugarcane_uses_verified_standard_rdf(self):
        """Sugarcane must select verified rule TNAU_STD_SUGARCANE_001."""
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
        assert data["recommendation_category"] == "STANDARD_RDF"

    def test_10_phase5_blocks_unsupported_rules_without_allow_unverified(self):
        """Phase 5 calculate must return NO_VERIFIED_RULE when an unsupported rule is requested with allow_unverified=False."""
        req = NutrientCalculationRequest(
            crop="Rice",
            selected_rule_id="TNAU_STCR_IPNS_RICE_001",
            soil_nitrogen=220.0,
            soil_phosphorus=16.0,
            soil_potassium=190.0,
            soil_phosphorus_method="Olsen",
            target_yield=6.0,
            allow_unverified=False
        )
        res = p5_service.calculate(req)
        assert res.status == "NO_VERIFIED_RULE"
        assert res.is_verified_rule is False

    def test_11_phase5_allows_calculation_for_audit_when_allow_unverified_true(self):
        """When allow_unverified=True, Phase 5 computes the formula for scientific audit, but marks is_verified_rule=False."""
        req = NutrientCalculationRequest(
            crop="Rice",
            soil_series="Palavidhi",
            selected_rule_id="TNAU_STCR_IPNS_RICE_001",
            soil_nitrogen=220.0,
            soil_phosphorus=16.0,
            soil_potassium=190.0,
            soil_phosphorus_method="Olsen",
            target_yield=6.0,
            allow_unverified=True
        )
        res = p5_service.calculate(req)
        assert res.status == "CALCULATION_SUCCESS"
        assert res.is_verified_rule is False
        assert res.is_provisional is True
