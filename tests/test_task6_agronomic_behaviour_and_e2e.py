"""
Automated Behaviour and End-to-End Test Suite for AgroWise AI (Task 6).

Covers:
1. Behaviour: Changing soil N changes the dose (higher soil N -> lower dose).
2. Behaviour: Changing previous_crop changes the dose (legume credit reduces N).
3. Behaviour: Changing previous_fertilizers changes the dose (residual P reduces P2O5).
4. Behaviour: No previous fertilizer means 0 deduction.
5. Units: Unit conversions (kg/acre vs kg/ha, q/ha vs t/ha, acre vs ha).
6. Clamping: Negative calculated requirements clamp to 0.0.
7. Card Comparison: Missing printed P/K is reported as NOT_PRINTED, not defaulted to 0.0.
8. Fallback: Unmatched soil-series fallback is labelled "General recommendation (lower confidence)".
9. End-to-End: Upload -> Confirm -> Crop + Prev Crop + Prev Fertilizer -> Recommendation -> Bags -> PDF.
"""

import io
import os
import sys
import uuid
import pytest
from PIL import Image
from pypdf import PdfReader
from fastapi.testclient import TestClient

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from phase3_soil.main import app
from phase7_integration.service import get_full_recommendation
from phase5_nutrient.service import NutrientCalculationService, NutrientCalculationRequest
from phase5_nutrient.units import convert_kg_per_acre_to_kg_per_ha, convert_target_yield_to_tonnes_per_ha

client = TestClient(app)


def test_01_changing_soil_n_changes_dose():
    """Higher soil nitrogen supply must reduce the calculated fertilizer N dose."""
    base_payload = {
        "crop": "Rice",
        "district": "Thanjavur",
        "soil_series": "Palavidhi",
        "season": "Kharif",
        "irrigation_method": "Irrigated",
        "target_yield": 6.0,
        "soil_phosphorus": 16.0,
        "soil_potassium": 190.0,
        "soil_phosphorus_method": "Olsen",
        "farm_area": 1.0,
        "farm_area_unit": "ha",
        "allow_unverified": True,
        "no_cache": True
    }

    # Low soil N = 180 kg/ha
    req_low = dict(base_payload)
    req_low["soil_nitrogen"] = 180.0
    res_low = get_full_recommendation(req_low)
    assert res_low["status"] == "SUCCESS"
    n_dose_low = res_low["nutrient_requirements"]["n_req_kg_per_ha"]

    # High soil N = 260 kg/ha
    req_high = dict(base_payload)
    req_high["soil_nitrogen"] = 260.0
    res_high = get_full_recommendation(req_high)
    assert res_high["status"] == "SUCCESS"
    n_dose_high = res_high["nutrient_requirements"]["n_req_kg_per_ha"]

    # Higher soil N must require strictly LESS applied fertilizer N
    assert n_dose_low > n_dose_high
    assert (n_dose_low - n_dose_high) > 5.0


def test_02_changing_previous_crop_changes_dose():
    """Preceding legume crop (e.g. Blackgram / Green Gram) provides an organic N credit."""
    base_payload = {
        "crop": "Rice",
        "district": "Thanjavur",
        "soil_series": "Palavidhi",
        "season": "Kharif",
        "target_yield": 6.0,
        "soil_nitrogen": 220.0,
        "soil_phosphorus": 16.0,
        "soil_phosphorus_method": "Olsen",
        "soil_potassium": 190.0,
        "farm_area": 1.0,
        "farm_area_unit": "ha",
        "no_cache": True
    }

    # Without previous crop credit (fallow)
    req_no_credit = dict(base_payload)
    req_no_credit["previous_crop"] = "Fallow"
    res_no_credit = get_full_recommendation(req_no_credit)
    n_no_credit = res_no_credit["nutrient_requirements"]["n_req_kg_per_ha"]

    # With Blackgram as previous crop (20 kg N credit per TNAU CPG 2020)
    req_blackgram = dict(base_payload)
    req_blackgram["previous_crop"] = "Blackgram"
    res_blackgram = get_full_recommendation(req_blackgram)
    n_blackgram = res_blackgram["nutrient_requirements"]["n_req_kg_per_ha"]

    assert n_no_credit > n_blackgram
    # Credit should be 20.0 kg/ha
    assert pytest.approx(n_no_credit - n_blackgram, 0.1) == 20.0
    bd = res_blackgram["nutrient_requirements"]["nutrient_breakdown"]["N"]
    assert bd["previous_crop_credit"] == 20.0


def test_03_changing_previous_fertilizer_changes_dose():
    """Recent previous fertilizer application (e.g. 100 kg DAP applied 1 month ago) provides residual P credit."""
    base_payload = {
        "crop": "Rice",
        "district": "Thanjavur",
        "soil_series": "Palavidhi",
        "season": "Kharif",
        "target_yield": 6.0,
        "soil_nitrogen": 220.0,
        "soil_phosphorus": 16.0,
        "soil_phosphorus_method": "Olsen",
        "soil_potassium": 190.0,
        "farm_area": 1.0,
        "farm_area_unit": "ha",
        "no_cache": True
    }

    # No previous fertilizer
    res_clean = get_full_recommendation(base_payload)
    p_clean = res_clean["nutrient_requirements"]["p2o5_req_kg_per_ha"]

    # With 100 kg DAP applied recently
    req_with_dap = dict(base_payload)
    req_with_dap["previous_fertilizers"] = [
        {"product": "DAP", "quantity": 100.0, "unit": "kg", "months_ago": 1.0}
    ]
    res_with_dap = get_full_recommendation(req_with_dap)
    p_with_dap = res_with_dap["nutrient_requirements"]["p2o5_req_kg_per_ha"]

    # 100 kg DAP on 1 ha = 46 kg P2O5 * 0.15 residual = 6.9 kg P2O5 residual deduction
    assert p_clean > p_with_dap
    assert pytest.approx(p_clean - p_with_dap, 0.1) == 6.9
    bd = res_with_dap["nutrient_requirements"]["nutrient_breakdown"]["P2O5"]
    assert pytest.approx(bd["previous_fertilizer_residual_kg_per_ha"], 0.1) == 6.9


def test_04_no_previous_fertilizer_no_deduction():
    """Empty or missing previous fertilizer history results in strictly 0.0 kg residual deduction."""
    payload = {
        "crop": "Rice",
        "district": "Thanjavur",
        "soil_series": "Palavidhi",
        "target_yield": 6.0,
        "soil_nitrogen": 220.0,
        "soil_phosphorus": 16.0,
        "soil_phosphorus_method": "Olsen",
        "soil_potassium": 190.0,
        "previous_fertilizers": [],
        "no_cache": True
    }
    res = get_full_recommendation(payload)
    bd = res["nutrient_requirements"]["nutrient_breakdown"]
    assert bd["N"]["previous_fertilizer_residual"] == 0.0
    assert bd["P2O5"]["previous_fertilizer_residual"] == 0.0
    assert bd["K2O"]["previous_fertilizer_residual"] == 0.0


def test_05_unit_conversions_kg_per_acre_and_quintals():
    """
    Verify conversion fidelity:
    100 kg/acre = 247.1 kg/ha
    60 q/ha = 6.0 t/ha
    Area scaling: 2.47105 acres = 1.0 hectare
    """
    assert pytest.approx(convert_kg_per_acre_to_kg_per_ha(100.0), 0.1) == 247.11
    assert pytest.approx(convert_target_yield_to_tonnes_per_ha(60.0, "q/ha"), 0.01) == 6.0

    service = NutrientCalculationService()
    req = NutrientCalculationRequest(
        crop="Rice",
        soil_series="Palavidhi",
        selected_rule_id="TNAU_STCR_IPNS_RICE_001",
        target_yield=60.0,
        target_yield_unit="q/ha",
        soil_nitrogen=89.03,  # ~220 kg/ha
        soil_nitrogen_unit="kg/acre",
        soil_phosphorus=6.47,  # ~16 kg/ha
        soil_phosphorus_unit="kg/acre",
        soil_phosphorus_method="Olsen",
        soil_potassium=76.89,  # ~190 kg/ha
        soil_potassium_unit="kg/acre",
        fym_applied_t_per_ha=12.5,
        farm_area=1.0,
        farm_area_unit="ha",
        allow_unverified=True
    )
    res = service.calculate(req)
    assert res.status == "CALCULATION_SUCCESS"
    assert pytest.approx(res.n_req_kg_per_ha, 0.5) == 17.6
    assert pytest.approx(res.p2o5_req_kg_per_ha, 0.5) == 28.4
    assert pytest.approx(res.k2o_req_kg_per_ha, 0.5) == 10.2


def test_06_negative_results_clamp_to_zero():
    """Extremely fertile soil test values where the STCR formula produces negative results must clamp to 0.0 kg/ha."""
    service = NutrientCalculationService()
    req = NutrientCalculationRequest(
        crop="Rice",
        soil_series="Palavidhi",
        selected_rule_id="TNAU_STCR_IPNS_RICE_001",
        target_yield=4.0,  # low target yield
        soil_nitrogen=450.0,  # massive soil N
        soil_phosphorus=80.0,  # massive soil P
        soil_phosphorus_method="Olsen",
        soil_potassium=500.0,  # massive soil K
        fym_applied_t_per_ha=25.0,  # heavy organic manure
        farm_area=1.0,
        farm_area_unit="ha",
        allow_unverified=True
    )
    res = service.calculate(req)
    assert res.status == "CALCULATION_SUCCESS"
    assert res.n_req_kg_per_ha == 0.0
    assert res.p2o5_req_kg_per_ha == 0.0
    assert res.k2o_req_kg_per_ha == 0.0
    assert res.total_farm_n_kg == 0.0
    assert res.total_farm_p2o5_kg == 0.0
    assert res.total_farm_k2o_kg == 0.0


def test_07_missing_printed_pk_reported_not_zero():
    """When printed card reports N but omits P and K, comparison reports NOT_PRINTED instead of 0.0."""
    payload = {
        "crop": "Rice",
        "district": "Thanjavur",
        "soil_series": "Palavidhi",
        "target_yield": 6.0,
        "soil_nitrogen": 220.0,
        "soil_phosphorus": 16.0,
        "soil_phosphorus_method": "Olsen",
        "soil_potassium": 190.0,
        "printed_n_rate": 33.0,
        "printed_p2o5_rate": None,  # unprinted on card
        "printed_k2o_rate": None,   # unprinted on card
        "printed_rate_unit": "kg/acre",
        "no_cache": True
    }
    res = get_full_recommendation(payload)
    comp = res["nutrient_requirements"]["card_comparison"]
    assert comp is not None
    assert comp["comparison"]["N"]["status"] in ("CONSISTENT", "DIFFERENCE_FLAGGED")
    assert comp["comparison"]["P2O5"]["status"] == "NOT_PRINTED"
    assert comp["comparison"]["P2O5"]["printed"] == "not printed on card"
    assert comp["comparison"]["K2O"]["status"] == "NOT_PRINTED"
    assert comp["comparison"]["K2O"]["printed"] == "not printed on card"


def test_08_fallback_mode_labelled_and_lower_confidence():
    """When a general blanket recommendation is requested, it is labelled 'lower' confidence with explicit banner."""
    payload = {
        "crop": "Groundnut",
        "district": "Tiruppur",
        "recommendation_type": "GENERAL_BLANKET",
        "soil_nitrogen": 150.0,
        "soil_phosphorus": 14.0,
        "soil_phosphorus_method": "Olsen",
        "soil_potassium": 180.0,
        "farm_area": 1.0,
        "farm_area_unit": "acre",
        "no_cache": True
    }
    res = get_full_recommendation(payload)
    assert res["status"] == "SUCCESS"
    p5 = res["nutrient_requirements"]
    assert p5["confidence"] == "lower"
    assert "lower confidence" in p5["confidence_label"].lower()
    assert any("General recommendation (lower confidence)" in w for w in res["warnings"])


def test_09_end_to_end_flow(tmp_path):
    """
    End-to-End Workflow:
    1. Upload Soil Health Card image
    2. Confirm extracted values
    3. Generate recommendation with crop + previous_crop + previous_fertilizers
    4. Save recommendation and optimize commercial bags
    5. Download official multilingual PDF report with disclaimers
    """
    # Step 1: Upload a valid synthetic card image
    farmer_id = f"test_farmer_{uuid.uuid4().hex[:8]}"
    auth_headers = {"Authorization": f"Bearer {farmer_id}"}

    img = Image.new("RGB", (600, 400), color=(255, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    img_bytes = buf.getvalue()

    upload_res = client.post(
        "/api/soil/upload",
        files={"file": ("card_sample.jpg", img_bytes, "image/jpeg")},
        headers=auth_headers
    )
    assert upload_res.status_code == 200
    doc_id = upload_res.json()["document_id"]

    # Step 2: Farmer confirms soil test values
    confirm_payload = {
        "farmer_confirmed": True,
        "allow_duplicate": True,
        "sample_id": f"SMP-{uuid.uuid4().hex[:6]}",
        "district": "Thanjavur",
        "crop": "Rice",
        "fields": {
            "nitrogen": {"value": 220.0, "unit": "kg/ha", "action": "accept"},
            "phosphorus": {"value": 16.0, "unit": "kg/ha", "test_method": "Olsen", "action": "accept"},
            "potassium": {"value": 190.0, "unit": "kg/ha", "action": "accept"},
            "ph": {"value": 7.2, "unit": None, "action": "accept"},
            "organic_carbon": {"value": 0.55, "unit": "%", "action": "accept"},
            "zinc": {"value": 0.9, "unit": "ppm", "action": "accept"},
        }
    }
    confirm_res = client.post("/api/soil/confirm", json=confirm_payload, headers=auth_headers)
    assert confirm_res.status_code == 200
    profile_id = confirm_res.json()["soil_profile_id"]

    # Step 3: Recommendation calculation with all agronomic factors
    rec_payload = {
        "soil_profile_id": profile_id,
        "crop": "Rice",
        "district": "Thanjavur",
        "soil_series": "Palavidhi",
        "season": "Kharif",
        "target_yield": 6.0,
        "farm_area": 2.0,
        "farm_area_unit": "acre",
        "previous_crop": "Blackgram",
        "previous_fertilizers": [
            {"product": "DAP", "quantity": 50.0, "unit": "kg", "months_ago": 1.5}
        ],
        "fym_applied_t_per_ha": 5.0,
        "no_cache": True
    }
    rec_res = client.post("/api/full-recommendation", json=rec_payload)
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert rec_data["status"] == "SUCCESS"
    assert rec_data["nutrient_requirements"]["n_req_kg_per_ha"] > 0
    assert rec_data["fertilizer_plan"]["total_cost_inr"] > 0
    assert len(rec_data["fertilizer_plan"]["recommended_products"]) > 0

    # Step 4: Save recommendation
    save_res = client.post("/api/recommendations", json=rec_data, headers=auth_headers)
    assert save_res.status_code == 200
    saved_rec_id = save_res.json()["recommendation_id"]

    # Step 5: Download PDF report
    pdf_res = client.get(f"/api/recommendations/{saved_rec_id}/pdf", headers=auth_headers)
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    assert pdf_res.content.startswith(b"%PDF")

    # Verify content in generated PDF
    pdf_reader = PdfReader(io.BytesIO(pdf_res.content))
    pdf_text = " ".join([page.extract_text() for page in pdf_reader.pages])
    assert "Confirm with your local agriculture officer" in pdf_text
    assert "Based on TNAU Guidelines" in pdf_text or "based on TNAU guidelines" in pdf_text.lower()
    assert "Rice" in pdf_text
    assert "Thanjavur" in pdf_text
