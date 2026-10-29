"""
Comprehensive Automated Test Suite for Soil-Series Coverage and Soil-Test Method Handling.

Tests:
1. Supported soil series for Rice (Palavidhi), Cotton (Irugur), and Maize (Coimbatore).
2. Unsupported soil series with explicit STCR request -> returns UNSUPPORTED_SOIL_SERIES.
3. Fallback selection to STANDARD_RDF when soil series is uncalibrated but statewide RDF exists (Rice).
4. Unsupported soil series with no verified standard fallback (Cotton) -> returns UNSUPPORTED_SOIL_SERIES.
5. Soil phosphorus Olsen-P method with STCR-IPNS equation -> CALCULATION_SUCCESS / SUCCESS.
6. Soil phosphorus Bray-1 method with STCR-IPNS equation -> INCOMPATIBLE_SOIL_TEST_METHOD.
7. Missing soil phosphorus test method -> MISSING_INPUTS with error_code MISSING_PHOSPHORUS_METHOD.
8. Bray-1 method with Standard RDF (Groundnut/Blackgram) -> SUCCESS with diagnostic interpretation.
9. Verification that no generic Bray-to-Olsen conversion factor is applied.
10. API-to-UI contract consistency (recommendation_category, recommendation_type, applicable_limitations, source_information).
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from phase3_soil.main import app
from agronomy.service import RuleSelectionService, RuleSelectionRequest
from phase5_nutrient.service import NutrientCalculationService
from phase5_nutrient.models import NutrientCalculationRequest
from phase7_integration.service import FullRecommendationService

client = TestClient(app)


class TestSoilSeriesCoverageAndMethods:
    """Suite testing soil series calibration enforcement and soil phosphorus method compatibility."""

    def test_01_supported_soil_series_rice(self):
        """Supported soil series (Palavidhi) for Rice returns STCR_IPNS rule with high confidence."""
        payload = {
            "crop": "Rice",
            "district": "Thanjavur",
            "soil_series": "Palavidhi",
            "season": "Kharif",
            "irrigation_method": "Irrigated",
            "target_yield": 6.0,
            "soil_nitrogen": 220.0,
            "soil_phosphorus": 16.0,
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 190.0,
            "farm_area": 1.0,
            "farm_area_unit": "ha"
        }
        res = client.post("/api/full-recommendation", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert data["is_verified"] is True
        assert data["recommendation_type"] in ("STCR_IPNS", "SOIL_SPECIFIC_STCR")
        assert data["recommendation_category"] == "STCR_IPNS"
        assert data["is_stcr_ipns"] is True
        assert data["is_standard_rdf"] is False
        assert data["rule_selection"]["selected_rule_id"] == "TNAU_STCR_IPNS_RICE_001"
        assert len(data["applicable_limitations"]) > 0
        assert any("Palavidhi" in lim for lim in data["applicable_limitations"])

    def test_02_supported_soil_series_cotton(self):
        """Supported soil series (Irugur) for Cotton returns STCR_IPNS rule."""
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
        assert data["status"] == "SUCCESS"
        assert data["rule_selection"]["selected_rule_id"] == "TNAU_STCR_IPNS_COTTON_001"
        assert data["recommendation_category"] == "STCR_IPNS"

    def test_03_supported_soil_series_maize(self):
        """Supported soil series (Coimbatore) for Maize returns STCR_IPNS rule."""
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
        assert data["status"] == "SUCCESS"
        assert data["rule_selection"]["selected_rule_id"] == "TNAU_STCR_IPNS_MAIZE_001"
        assert data["recommendation_category"] == "STCR_IPNS"

    def test_04_unsupported_soil_series_with_stcr_request(self):
        """Unsupported soil series with explicit STCR request must return UNSUPPORTED_SOIL_SERIES."""
        payload = {
            "crop": "Rice",
            "district": "Thanjavur",
            "soil_series": "UncalibratedSandySeries",
            "recommendation_type": "STCR_IPNS",
            "target_yield": 6.0,
            "soil_nitrogen": 220.0,
            "soil_phosphorus": 16.0,
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 190.0,
            "farm_area": 1.0
        }
        res = client.post("/api/full-recommendation", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "UNSUPPORTED_SOIL_SERIES"
        assert data["error_code"] == "UNSUPPORTED_SOIL_SERIES"
        assert "not calibrated" in data["actionable_message"]
        assert len(data["fertilizer_plan"]["recommended_products"]) == 0

    def test_05_fallback_to_standard_rdf_when_series_uncalibrated(self):
        """
        When soil series is uncalibrated but user allows standard fallback (no explicit STCR restriction),
        the system safely falls back to STANDARD_RDF with clear warning.
        """
        payload = {
            "crop": "Rice",
            "district": "Thanjavur",
            "soil_series": "UncalibratedSandySeries",
            "target_yield": 6.0,
            "soil_nitrogen": 220.0,
            "soil_phosphorus": 16.0,
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 190.0,
            "farm_area": 1.0
        }
        res = client.post("/api/full-recommendation", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert data["recommendation_category"] == "STANDARD_RDF"
        assert data["rule_selection"]["selected_rule_id"] == "TNAU_STD_RICE_001"
        assert any("not calibrated for STCR-IPNS" in w for w in data["warnings"])

    def test_06_unsupported_soil_series_no_fallback_for_cotton(self):
        """
        Cotton has STCR calibration only on Irugur and Pilamedu series;
        an uncalibrated series without standard fallback returns UNSUPPORTED_SOIL_SERIES.
        """
        payload = {
            "crop": "Cotton (lint)",
            "district": "Coimbatore",
            "soil_series": "KallidaikurichiSeries",
            "target_yield": 2.5,
            "soil_nitrogen": 200.0,
            "soil_phosphorus": 18.0,
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 250.0,
            "farm_area": 1.0
        }
        res = client.post("/api/full-recommendation", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "UNSUPPORTED_SOIL_SERIES"
        assert data["error_code"] == "UNSUPPORTED_SOIL_SERIES"

    def test_07_bray_phosphorus_incompatible_with_stcr_rice(self):
        """
        When report has Bray-1 phosphorus and STCR equation is calibrated for Olsen-P,
        the system must return INCOMPATIBLE_SOIL_TEST_METHOD and never convert with generic factors.
        """
        payload = {
            "crop": "Rice",
            "district": "Thanjavur",
            "soil_series": "Palavidhi",
            "season": "Kharif",
            "irrigation_method": "Irrigated",
            "target_yield": 6.0,
            "soil_nitrogen": 220.0,
            "soil_phosphorus": 16.0,
            "soil_phosphorus_method": "Bray",  # Bray-1 on STCR!
            "soil_potassium": 190.0,
            "farm_area": 1.0,
            "farm_area_unit": "ha"
        }
        res = client.post("/api/full-recommendation", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "INCOMPATIBLE_SOIL_TEST_METHOD"
        assert data["error_code"] == "INCOMPATIBLE_SOIL_TEST_METHOD"
        assert "Bray-1" in data["actionable_message"]
        assert "generic conversion" in data["actionable_message"].lower() or "prohibited" in data["actionable_message"].lower()
        # Optimizer must be bypassed: 0 products, 0 cost
        assert len(data["fertilizer_plan"]["recommended_products"]) == 0
        assert data["fertilizer_plan"]["total_cost_inr"] == 0.0

    def test_08_missing_phosphorus_method_returns_missing_inputs(self):
        """
        When soil phosphorus is provided but soil_phosphorus_method is missing,
        return MISSING_INPUTS with error_code MISSING_PHOSPHORUS_METHOD.
        """
        payload = {
            "crop": "Rice",
            "district": "Thanjavur",
            "soil_series": "Palavidhi",
            "target_yield": 6.0,
            "soil_nitrogen": 220.0,
            "soil_phosphorus": 16.0,
            # soil_phosphorus_method omitted!
            "soil_potassium": 190.0,
            "farm_area": 1.0
        }
        res = client.post("/api/full-recommendation", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "MISSING_INPUTS"
        assert data["error_code"] == "MISSING_PHOSPHORUS_METHOD"
        assert "soil_phosphorus_method" in data["nutrient_requirements"]["missing_inputs"] or "phosphorus_method" in data["rule_selection"]["missing_inputs"]
        assert "Soil Health Card" in data["actionable_message"]
        assert len(data["fertilizer_plan"]["recommended_products"]) == 0

    def test_09_bray_method_compatible_with_standard_rdf(self):
        """
        For crops using Standard Blanket RDF (Groundnut), Bray-1 phosphorus is compatible
        for diagnostic classification without error.
        """
        payload = {
            "crop": "Groundnut",
            "district": "Tiruppur",
            "recommendation_type": "GENERAL_BLANKET",
            "soil_nitrogen": 150.0,
            "soil_phosphorus": 28.0,
            "soil_phosphorus_method": "Bray",
            "soil_potassium": 180.0,
            "farm_area": 1.0,
            "farm_area_unit": "acre"
        }
        res = client.post("/api/full-recommendation", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert data["recommendation_category"] == "STANDARD_RDF"
        assert data["rule_selection"]["selected_rule_id"] == "TNAU_BLANKET_GROUNDNUT_001"

    def test_10_api_contract_consistency_fields(self):
        """
        Verify that API response returns all required distinction and source information fields:
        recommendation_category, recommendation_type_label, is_stcr_ipns, is_standard_rdf,
        applicable_limitations, source_information.
        """
        payload = {
            "crop": "Rice",
            "district": "Thanjavur",
            "soil_series": "Palavidhi",
            "target_yield": 6.0,
            "soil_nitrogen": 220.0,
            "soil_phosphorus": 16.0,
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 190.0,
            "farm_area": 1.0
        }
        res = client.post("/api/full-recommendation", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert "recommendation_category" in data
        assert "recommendation_type_label" in data
        assert "is_stcr_ipns" in data
        assert "is_standard_rdf" in data
        assert "applicable_limitations" in data
        assert "source_information" in data
        assert isinstance(data["applicable_limitations"], list)
        assert len(data["applicable_limitations"]) > 0
