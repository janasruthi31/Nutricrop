"""
Automated tests for Phase 4: Agronomic Rule Database & Rule Selection Engine.
Tests all 12 required scenarios specified in Phase 4 requirements.
"""

import pytest
from fastapi.testclient import TestClient
from phase3_soil.main import app
from agronomy.service import RuleSelectionService, select_rule
from agronomy.models import RuleSelectionRequest, SoilValuesInput
from agronomy.registry import AgronomicRuleRegistry

client = TestClient(app)
service = RuleSelectionService()


# 1. Matching verified rule
def test_01_matching_verified_rule():
    req = RuleSelectionRequest(
        crop="Rice",
        district="Thanjavur",
        soil_series="Palavidhi",
        season="Kharif",
        irrigation_method="Irrigated",
        target_yield=6.0,
        soil_values=SoilValuesInput(
            nitrogen=220.0,
            phosphorus=16.0,
            potassium=190.0,
            phosphorus_method="Olsen"
        )
    )
    res = service.select_rule(req)
    assert res.status == "RULE_SELECTED"
    assert res.selected_rule_id == "TNAU_STCR_IPNS_RICE_001"
    assert res.crop == "Rice"
    assert res.recommendation_method == "STCR-IPNS"
    assert res.verification_status in ("VERIFIED", "PROVISIONAL")
    assert res.source_title == "TNAU Agriculture / STCR-IPNS Reference"
    assert res.source_url is not None
    assert len(res.missing_inputs) == 0


# 2. Unsupported crop
def test_02_unsupported_crop():
    req = RuleSelectionRequest(
        crop="DragonFruit",
        irrigation_method="Irrigated"
    )
    res = service.select_rule(req)
    assert res.status == "UNSUPPORTED_CROP"
    assert res.selected_rule_id is None
    assert "not supported" in res.warnings[0].lower()


# 3. Missing mandatory input
def test_03_missing_mandatory_input():
    # Rice STCR requires target_yield and soil_series and N, P, K
    req = RuleSelectionRequest(
        crop="Rice",
        soil_series="Palavidhi",
        irrigation_method="Irrigated",
        # target_yield missing!
        soil_values=SoilValuesInput(
            nitrogen=220.0,
            phosphorus=16.0,
            potassium=190.0,
            phosphorus_method="Olsen"
        )
    )
    res = service.select_rule(req)
    assert res.status == "NEEDS_MORE_INPUT"
    assert "target_yield" in res.missing_inputs
    assert res.selected_rule_id == "TNAU_STCR_IPNS_RICE_001"


# 4. Unsupported soil series
def test_04_unsupported_soil_series():
    # Cotton STCR is calibrated for Irugur / Pilamedu only
    req = RuleSelectionRequest(
        crop="Cotton (lint)",
        soil_series="UnknownInvalidSeries",
        irrigation_method="Irrigated",
        target_yield=2.5
    )
    res = service.select_rule(req)
    assert res.status == "UNSUPPORTED_SOIL_SERIES"
    assert res.selected_rule_id is None
    assert "soil series 'unknowninvalidseries' is not supported" in res.warnings[0].lower()


# 5. Irrigation mismatch
def test_05_irrigation_mismatch():
    # Rice STCR rule requires Irrigated. If farmer requests Rainfed, it fails matching.
    req = RuleSelectionRequest(
        crop="Rice",
        soil_series="Palavidhi",
        irrigation_method="Rainfed",
        target_yield=6.0,
        soil_values=SoilValuesInput(nitrogen=200, phosphorus=15, potassium=180, phosphorus_method="Olsen")
    )
    res = service.select_rule(req)
    # Rice STCR requires Irrigated; Rainfed doesn't match STCR or TNAU_STD_RICE (Irrigated)
    assert res.status == "NO_MATCHING_RULE"


# 6. Season mismatch
def test_06_season_mismatch():
    # Cotton STCR rule applies to Kharif/Winter/All. Requesting an invalid non-matching season should exclude.
    req = RuleSelectionRequest(
        crop="Cotton (lint)",
        soil_series="Irugur",
        season="SummerOffseasonSpecial",
        irrigation_method="Irrigated",
        target_yield=2.5,
        soil_values=SoilValuesInput(nitrogen=200, phosphorus=15, potassium=180, phosphorus_method="Olsen")
    )
    res = service.select_rule(req)
    assert res.status == "NO_MATCHING_RULE"


# 7. Target yield outside a documented range
def test_07_target_yield_outside_documented_range():
    # Rice STCR target yield range is 3.0 to 8.0 t/ha. Target yield = 15.0 t/ha is outside range.
    req = RuleSelectionRequest(
        crop="Rice",
        soil_series="Palavidhi",
        irrigation_method="Irrigated",
        target_yield=15.0,  # Exceeds max 8.0 t/ha
        soil_values=SoilValuesInput(nitrogen=200, phosphorus=15, potassium=180, phosphorus_method="Olsen")
    )
    res = service.select_rule(req)
    # Should reject STCR rule due to yield out of range, falling back to general rule or NO_MATCHING_RULE if parameters don't match
    assert res.selected_rule_id != "TNAU_STCR_IPNS_RICE_001"


# 8. Pending verification rule
def test_08_pending_verification_rule():
    req = RuleSelectionRequest(
        crop="Banana",
        variety="Grand Naine",
        soil_series="Thonnackal",
        irrigation_method="Irrigated",
        target_yield=50.0,
        soil_values=SoilValuesInput(nitrogen=200, phosphorus=15, potassium=180, phosphorus_method="Olsen")
    )
    res = service.select_rule(req)
    assert res.status == "PENDING_VERIFICATION"
    assert res.selected_rule_id == "TNAU_STCR_BANANA_001"
    assert res.verification_status == "PENDING_VERIFICATION"
    assert "pending verification" in res.warnings[0].lower()


# 9. No matching rule
def test_09_no_matching_rule():
    # Combination with valid crop but incompatible parameters where no rule matches
    req = RuleSelectionRequest(
        crop="Sugarcane",
        irrigation_method="Rainfed",  # Sugarcane rule is Irrigated only
        season="Winter"
    )
    res = service.select_rule(req)
    assert res.status == "NO_MATCHING_RULE"


# 10. API validation (POST /api/agronomy/select-rule)
def test_10_api_validation_endpoint():
    payload = {
        "crop": "Blackgram",
        "irrigation_method": "Rainfed",
        "season": "Rabi",
        "soil_values": {
            "nitrogen": 180.0,
            "phosphorus": 12.0,
            "potassium": 140.0,
            "phosphorus_method": "Olsen"
        }
    }
    response = client.post("/api/agronomy/select-rule", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "RULE_SELECTED"
    assert data["selected_rule_id"] == "TNAU_STD_BLACKGRAM_RF_001"
    assert data["crop"] == "Blackgram"
    assert data["recommendation_method"] == "TNAU-SOIL-TEST"
    assert data["verification_status"] in ("VERIFIED", "PROVISIONAL")


# 11. Correct source traceability
def test_11_correct_source_traceability():
    req = RuleSelectionRequest(
        crop="Cotton (lint)",
        soil_series="Irugur",
        irrigation_method="Irrigated",
        target_yield=2.5,
        soil_values=SoilValuesInput(
            nitrogen=200.0,
            phosphorus=14.0,
            potassium=180.0,
            phosphorus_method="Olsen"
        )
    )
    res = service.select_rule(req)
    assert res.status == "RULE_SELECTED"
    assert res.selected_rule_id == "TNAU_STCR_IPNS_COTTON_001"
    assert res.source_title == "TNAU Cotton STCR"
    assert "agritech.tnau.ac.in" in res.source_url
    assert res.source_page_or_section is not None


# 12. Rule-selection precedence (STCR-IPNS preferred over generic TNAU-SOIL-TEST when both match)
def test_12_rule_selection_precedence():
    # Rice with Palavidhi soil series and target yield 5.0 t/ha matches BOTH STCR-IPNS (TNAU_STCR_IPNS_RICE_001)
    # and general TNAU soil test (TNAU_STD_RICE_001).
    # STCR-IPNS MUST take precedence!
    req = RuleSelectionRequest(
        crop="Rice",
        soil_series="Palavidhi",
        irrigation_method="Irrigated",
        target_yield=5.0,
        soil_values=SoilValuesInput(
            nitrogen=220.0,
            phosphorus=15.0,
            potassium=190.0,
            phosphorus_method="Olsen"
        )
    )
    res = service.select_rule(req)
    assert res.status == "RULE_SELECTED"
    assert res.selected_rule_id == "TNAU_STCR_IPNS_RICE_001"  # STCR-IPNS chosen over TNAU_STD_RICE_001
    assert res.recommendation_method == "STCR-IPNS"

    # Now if soil series is NOT provided, STCR-IPNS cannot match, so it should fall back to TNAU_STD_RICE_001
    req_no_series = RuleSelectionRequest(
        crop="Rice",
        irrigation_method="Irrigated",
        soil_values=SoilValuesInput(
            nitrogen=220.0,
            phosphorus=15.0,
            potassium=190.0,
            phosphorus_method="Olsen"
        )
    )
    res_fallback = service.select_rule(req_no_series)
    assert res_fallback.status == "RULE_SELECTED"
    assert res_fallback.selected_rule_id == "TNAU_STD_RICE_001"
    assert res_fallback.recommendation_method == "TNAU-SOIL-TEST"
