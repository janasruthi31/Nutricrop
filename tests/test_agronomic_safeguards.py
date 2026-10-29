"""
Automated Test Suite for Acceptance Criteria: Agronomic Safeguards.

Tests:
1. Provisional rule rejection
2. Verified fallback selection
3. No applicable verified rule
4. Expired or unavailable weather
5. Historical-normal fallback labeling
6. Nutrient quantities remaining unchanged when weather fails
7. Missing, expired, and conflicting fertilizer prices
8. Source and effective-date traceability
9. ReportLab PDF report safeguard disclaimers
"""

import os
import json
import io
import pytest
from unittest.mock import patch

from agronomy.service import RuleSelectionService, NO_VERIFIED_RULE_AVAILABLE
from agronomy.models import RuleSelectionRequest
from phase5_nutrient.service import NutrientCalculationService
from phase5_nutrient.models import NutrientCalculationRequest
from phase6_fertilizer.service import FertilizerOptimizerService
from phase6_fertilizer.models import FertilizerOptimizationRequest
from phase7_integration.service import UnifiedFertilizerRecommendationService
from phase7_integration.weather import get_weather_guidance, _get_seasonal_weather_estimate
from phase7_integration.extra_api import _create_jwt_token, download_recommendation_pdf
from phase3_soil import db




# ---------------------------------------------------------------------------
# Safeguard 1: Provisional Rule Rejection
# ---------------------------------------------------------------------------
def test_provisional_rule_rejection():
    """STCR equations marked PROVISIONAL or AUDIT are disabled for recommendation generation."""
    rule_service = RuleSelectionService()
    nutrient_service = NutrientCalculationService()

    # Cotton has only provisional STCR rules in agronomy rules catalog
    req = RuleSelectionRequest(
        crop="Cotton",
        soil_type="Black",
        target_yield=25.0
    )
    res = rule_service.select_rule(req)

    # Must reject the provisional STCR rule for confirmed recommendations
    assert res.selected_rule_id is None
    assert res.is_verified is False
    assert res.status == NO_VERIFIED_RULE_AVAILABLE
    assert res.provisional_rule_rejected == "TNAU_STCR_IPNS_COTTON_001"
    assert "TNAU_STCR_IPNS_COTTON_001" in res.provisional_rules_encountered

    # Phase 5 directly requested with provisional rule without allow_unverified
    p5_req = NutrientCalculationRequest(
        crop="Cotton",
        selected_rule_id="TNAU_STCR_IPNS_COTTON_001",
        target_yield=25.0,
        soil_nitrogen=180.0,
        soil_phosphorus=14.0,
        soil_potassium=220.0,
        allow_unverified=False
    )
    p5_res = nutrient_service.calculate(p5_req)
    assert p5_res.status == NO_VERIFIED_RULE_AVAILABLE
    assert not p5_res.is_verified_rule


# ---------------------------------------------------------------------------
# Safeguard 2: Verified Fallback Selection
# ---------------------------------------------------------------------------
def test_verified_fallback_selection():
    """When a provisional rule is encountered, automatically select an applicable VERIFIED alternative."""
    rule_service = RuleSelectionService()

    # Rice with an uncalibrated soil series encounters provisional STCR rule, falls back to verified standard rule
    req = RuleSelectionRequest(
        crop="Rice",
        soil_series="Unknown_Series_999",
        target_yield=6.0
    )
    res = rule_service.select_rule(req)

    assert res.selected_rule_id is not None
    assert res.is_verified is True
    assert res.verification_status == "VERIFIED"
    assert res.fallback_applied is True
    assert res.fallback_reason is not None
    assert "alternative" in res.fallback_reason.lower() or "fallback" in res.fallback_reason.lower()
    # Confirm it fell back to verified standard rule
    assert "TNAU_STD_RICE_001" in res.selected_rule_id or res.is_standard_rdf


# ---------------------------------------------------------------------------
# Safeguard 3: No Applicable Verified Rule Available
# ---------------------------------------------------------------------------
def test_no_applicable_verified_rule():
    """If no verified rule applies, return NO_VERIFIED_RULE_AVAILABLE rather than fabricating."""
    rule_service = RuleSelectionService()

    # Request Cotton: provisional rule exists in repository, but no verified alternative applies
    req = RuleSelectionRequest(
        crop="Cotton",
        soil_type="Black",
        target_yield=25.0
    )
    res = rule_service.select_rule(req)

    assert res.status == NO_VERIFIED_RULE_AVAILABLE
    assert res.selected_rule_id is None
    assert res.is_verified is False
    assert res.provisional_rule_rejected == "TNAU_STCR_IPNS_COTTON_001"
    assert "No verified" in (res.actionable_message or "") or "PROVISIONAL" in (res.actionable_message or "")


# ---------------------------------------------------------------------------
# Safeguard 4 & 5: Expired / Unavailable Weather & Historical Normals Labeling
# ---------------------------------------------------------------------------
def test_expired_or_unavailable_weather_historical_normals():
    """When live weather is unavailable, historical rainfall normals provide context only."""
    # Simulate failed live weather / cache by patching _fetch_open_meteo to raise exception
    with patch("phase7_integration.weather._fetch_open_meteo", side_effect=Exception("Connection timed out")):
        with patch("phase7_integration.weather._get_cached_weather", return_value=None):
            weather_res = get_weather_guidance(district="Thanjavur", lat=10.78, lon=79.13)

    assert weather_res["status"] == "UNKNOWN / HISTORICAL_NORMALS"
    assert weather_res["guidance_status"] == "UNKNOWN"
    assert weather_res["is_suitable"] is None
    assert weather_res["suitability"] == "UNKNOWN"
    assert "1970–2020" in weather_res["historical_period"]
    assert "India Meteorological Department (IMD)" in weather_res["historical_source"]

    # Verify that it DOES NOT claim conditions are currently suitable or unsuitable
    assert "safe to apply" not in weather_res["actionable_advice"].lower()
    assert "cannot be evaluated from historical normals alone" in weather_res["actionable_advice"]


# ---------------------------------------------------------------------------
# Safeguard 6: Nutrient Quantities Invariant to Weather Status
# ---------------------------------------------------------------------------
def test_nutrient_quantities_invariant_to_weather():
    """Weather failure must not alter calculated nutrient requirements or fertilizer quantities."""
    service = UnifiedFertilizerRecommendationService()

    base_payload = {
        "crop": "Rice",
        "district": "Thanjavur",
        "farm_area": 2.0,
        "farm_area_unit": "acre",
        "soil_nitrogen": 210.0,
        "soil_phosphorus": 16.0,
        "soil_potassium": 190.0,
        "target_yield": 5.5,
        "fym_applied": 0.0
    }

    # Case A: Live weather returns clear/suitable
    mock_suitable_weather = {
        "status": "AVAILABLE",
        "guidance_status": "SUITABLE",
        "is_suitable": True,
        "suitability": "SUITABLE",
        "risk_level": "LOW",
        "current_condition": "Clear",
        "actionable_advice": "Weather is clear. Safe for fertilizer application.",
        "data_source": "live"
    }

    # Case B: Weather fails -> UNKNOWN / HISTORICAL_NORMALS
    mock_failed_weather = {
        "status": "UNKNOWN / HISTORICAL_NORMALS",
        "guidance_status": "UNKNOWN",
        "is_suitable": None,
        "suitability": "UNKNOWN",
        "risk_level": "UNKNOWN",
        "historical_period": "1970–2020 (50-year climatological normal)",
        "historical_source": "India Meteorological Department (IMD)",
        "actionable_advice": "Live forecast unavailable. Safe timing cannot be evaluated from historical normals alone.",
        "data_source": "historical_normals"
    }

    with patch("phase7_integration.service.get_weather_guidance", return_value=mock_suitable_weather):
        rec_suitable = service.generate_full_recommendation(dict(base_payload))

    with patch("phase7_integration.service.get_weather_guidance", return_value=mock_failed_weather):
        rec_failed = service.generate_full_recommendation(dict(base_payload))

    p5_suitable = rec_suitable["nutrient_requirements"]
    p5_failed = rec_failed["nutrient_requirements"]

    # N, P2O5, K2O requirements must be EXACTLY identical
    assert p5_suitable["total_n_req_kg"] == p5_failed["total_n_req_kg"]
    assert p5_suitable["total_p2o5_req_kg"] == p5_failed["total_p2o5_req_kg"]
    assert p5_suitable["total_k2o_req_kg"] == p5_failed["total_k2o_req_kg"]

    # Fertilizer bags and quantities must be EXACTLY identical
    p6_suitable = rec_suitable["fertilizer_plan"]["recommended_products"]
    p6_failed = rec_failed["fertilizer_plan"]["recommended_products"]

    assert len(p6_suitable) == len(p6_failed)
    for prod_s, prod_f in zip(p6_suitable, p6_failed):
        assert prod_s["product_id"] == prod_f["product_id"]
        assert prod_s["quantity_kg"] == prod_f["quantity_kg"]
        assert prod_s["bags"] == prod_f["bags"]

    # Weather failure must include the timing warning
    warnings_failed = " ".join(rec_failed["warnings"])
    assert "Timing warning: Live weather forecast is unavailable" in warnings_failed


# ---------------------------------------------------------------------------
# Safeguard 7: Missing, Expired, and Conflicting Fertilizer Prices
# ---------------------------------------------------------------------------
def test_missing_expired_and_conflicting_prices():
    """Missing, expired, and conflicting prices return COST_UNAVAILABLE while preserving nutrient recommendation."""
    optimizer = FertilizerOptimizerService()

    base_opt_req = {
        "n_req_kg": 100.0,
        "p2o5_req_kg": 50.0,
        "k2o_req_kg": 50.0,
        "crop": "Rice",
        "farm_area_hectares": 1.0,
        "allowed_fertilizers": ["UREA", "DAP", "MOP"]
    }

    # Case A: Missing price for MOP
    req_missing = FertilizerOptimizationRequest(
        **base_opt_req,
        custom_prices={"MOP": None}
    )
    res_missing = optimizer.optimize(req_missing)
    assert res_missing.status == "OPTIMIZATION_SUCCESS"
    assert res_missing.total_cost_status == "COST_UNAVAILABLE"
    assert res_missing.total_cost_inr is None
    # Nutrient recommendations must STILL be present
    assert len(res_missing.recommended_products) >= 2
    mop_rec = next(p for p in res_missing.recommended_products if p.product_id == "MOP")
    assert mop_rec.price_status == "COST_UNAVAILABLE"
    assert mop_rec.price_per_bag_inr is None
    assert mop_rec.total_cost_inr is None
    assert mop_rec.bags > 0

    # Case B: Expired price for DAP
    req_expired = FertilizerOptimizationRequest(
        **base_opt_req,
        custom_prices={"DAP": "EXPIRED"}
    )
    res_expired = optimizer.optimize(req_expired)
    assert res_expired.status == "OPTIMIZATION_SUCCESS"
    assert res_expired.total_cost_status == "COST_UNAVAILABLE"
    assert res_expired.total_cost_inr is None
    dap_rec = next(p for p in res_expired.recommended_products if p.product_id == "DAP")
    assert dap_rec.price_status == "EXPIRED"
    assert dap_rec.total_cost_inr is None

    # Case C: Conflicting price for Urea
    req_conflicting = FertilizerOptimizationRequest(
        **base_opt_req,
        custom_prices={"UREA": "CONFLICTING"}
    )
    res_conflicting = optimizer.optimize(req_conflicting)
    assert res_conflicting.status == "OPTIMIZATION_SUCCESS"
    assert res_conflicting.total_cost_status == "COST_UNAVAILABLE"
    assert res_conflicting.total_cost_inr is None
    urea_rec = next(p for p in res_conflicting.recommended_products if p.product_id == "UREA")
    assert urea_rec.price_status == "CONFLICTING"
    assert urea_rec.total_cost_inr is None


# ---------------------------------------------------------------------------
# Safeguard 8: Source and Effective-Date Traceability
# ---------------------------------------------------------------------------
def test_price_source_and_effective_date_traceability():
    """Fertilizer prices must include name, price basis, source, effective date, and pricing mechanism."""
    optimizer = FertilizerOptimizerService()

    req = FertilizerOptimizationRequest(
        n_req_kg=80.0,
        p2o5_req_kg=40.0,
        k2o_req_kg=40.0,
        crop="Rice",
        farm_area_hectares=1.0,
        allowed_fertilizers=["UREA", "DAP", "MOP"]
    )
    res = optimizer.optimize(req)

    assert res.status == "OPTIMIZATION_SUCCESS"
    assert res.total_cost_status == "AVAILABLE"
    assert res.total_cost_inr > 0

    for prod in res.recommended_products:
        assert prod.product_name is not None
        assert prod.price_source is not None
        assert prod.price_effective_date is not None
        assert prod.price_basis is not None
        assert prod.pricing_mechanism in ("OFFICIAL_CONTROLLED_PRICE", "SUBSIDY_RELATED_PRICE", "DEALER_QUOTATION")

        # Urea must specifically be official controlled price
        if prod.product_id == "UREA":
            assert prod.pricing_mechanism == "OFFICIAL_CONTROLLED_PRICE"
            assert "Statutory" in prod.price_basis or "Controlled" in prod.price_basis
        # DAP and MOP are subsidy-related
        elif prod.product_id in ("DAP", "MOP"):
            assert prod.pricing_mechanism == "SUBSIDY_RELATED_PRICE"
            assert "Subsidy" in prod.price_basis or "NBS" in prod.price_basis


# ---------------------------------------------------------------------------
# Safeguard 9: PDF Report Safeguard Disclaimers
# ---------------------------------------------------------------------------
def test_pdf_report_safeguard_disclaimers():
    """PDF report must include fallback disclaimers, price traceability, and historical normal weather notice."""
    from pypdf import PdfReader

    user_id = "test_farmer_safeguards"
    jwt_token = _create_jwt_token(user_id=user_id, email="safeguards@agrowise.ai")

    # Generate full recommendation with fallback applied and historical normal weather
    service = UnifiedFertilizerRecommendationService()
    payload = {
        "crop": "Rice",
        "district": "Thanjavur",
        "soil_series": "Uncalibrated_Series",
        "farm_area": 1.5,
        "farm_area_unit": "acre",
        "soil_nitrogen": 200.0,
        "soil_phosphorus": 15.0,
        "soil_potassium": 180.0,
        "soil_phosphorus_method": "Olsen",
        "target_yield": 5.0,
        "custom_prices": {"MOP": "COST_UNAVAILABLE"}  # trigger COST_UNAVAILABLE
    }

    mock_failed_weather = {
        "status": "UNKNOWN / HISTORICAL_NORMALS",
        "guidance_status": "UNKNOWN",
        "is_suitable": None,
        "suitability": "UNKNOWN",
        "risk_level": "UNKNOWN",
        "historical_period": "1970–2020 (50-year climatological normal)",
        "historical_source": "India Meteorological Department (IMD) / Table V",
        "actionable_advice": "Live forecast unavailable. Safe timing cannot be evaluated from historical normals alone.",
        "data_source": "historical_normals"
    }

    with patch("phase7_integration.service.get_weather_guidance", return_value=mock_failed_weather):
        rec_res = service.generate_full_recommendation(payload)

    # Save to database
    rec_id = "REC_TEST_SAFEGUARDS_PDF_001"
    with db.connect() as con:
        con.execute(
            """INSERT OR REPLACE INTO saved_recommendations 
               (recommendation_id, user_id, crop, district, farm_area, farm_area_unit, response_json, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
            (rec_id, user_id, "Rice", "Thanjavur", 1.5, "acre", json.dumps(rec_res))
        )

    # Download PDF
    auth_header = f"Bearer {jwt_token}"
    response = download_recommendation_pdf(rec_id=rec_id, authorization=auth_header, x_farmer_id=None)
    assert response.status_code == 200
    assert response.media_type == "application/pdf"

    # Extract text from PDF (clean wrapped line breaks)
    pdf_reader = PdfReader(io.BytesIO(response.body))
    extracted_text = " ".join([page.extract_text().replace("\n", " ") for page in pdf_reader.pages])

    # 1. Fallback attribution disclosure: never claim exact STCR-IPNS
    assert "FALLBACK" in extracted_text or "Fallback Rule" in extracted_text
    assert "Not STCR-IPNS" in extracted_text or "not an exact STCR-IPNS prescription" in extracted_text.lower()

    # 2. Historical weather normals disclosure: never claim live suitability
    assert "1970" in extracted_text and "2020" in extracted_text
    assert "cannot be evaluated from historical normals alone" in extracted_text

    # 3. Cost unavailable disclosure
    assert "COST UNAVAILABLE" in extracted_text
