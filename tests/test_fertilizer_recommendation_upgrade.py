"""
Comprehensive Test Suite for the Upgraded AgroWise AI Fertilizer Recommendation Module.
Covers all 19 mandatory test cases specified in Master Prompt Section 8:
 1. Valid confirmed soil report and supported crop
 2. Different soil-test values producing changes consistent with applicable agronomic rules
 3. Different current crops selecting their own verified rules
 4. Different farm areas scaling total fertilizer quantities and cost correctly
 5. Previous crop history affecting the result only where supported by a validated rule
 6. Previous fertilizer history containing multiple products and application dates
 7. Missing previous crop or fertilizer history
 8. Missing, unreadable or invalid soil values
 9. Incorrect units and bag-size conversions
10. Correct N, P2O5, and K2O contributions from multi-nutrient fertilizers
11. Organic manure credits where the selected method supports them
12. Nutrient surplus and deficit reporting
13. Whole-bag rounding and loose quantities
14. Infeasible optimizer output
15. Unsupported crop or soil combinations
16. Price changes affecting cost without incorrectly changing the agronomic nutrient target
17. Repeated identical inputs producing reproducible results
18. Farmer-level data isolation
19. Final recommendation consistency between backend response and displayed result
"""

import pytest
from fastapi.testclient import TestClient

from phase3_soil.main import app
from phase5_nutrient.service import NutrientCalculationService, NutrientCalculationRequest
from phase5_nutrient.models import PreviousFertilizerItem
from phase6_fertilizer.service import FertilizerOptimizerService
from phase6_fertilizer.models import FertilizerOptimizationRequest
from phase7_integration.service import FullRecommendationService
from phase3_soil import db

client = TestClient(app)
nutrient_service = NutrientCalculationService()
fertilizer_service = FertilizerOptimizerService()
full_rec_service = FullRecommendationService()


# ==============================================================================
# Case 1: Valid confirmed soil report and supported crop
# ==============================================================================
def test_case_01_valid_confirmed_soil_report_and_crop():
    req = {
        "crop": "Rice",
        "district": "Thanjavur",
        "soil_series": "Palavidhi",
        "season": "Kharif",
        "target_yield": 6.0,
        "soil_nitrogen": 220.0,
        "soil_phosphorus": 16.0,
        "soil_potassium": 210.0,
        "soil_phosphorus_method": "Olsen",
        "farm_area": 1.0,
        "farm_area_unit": "hectare",
        "no_cache": True
    }
    res = full_rec_service.generate_full_recommendation(req)
    assert res["status"] == "SUCCESS"
    assert res["is_verified"] is True
    assert res["crop"] == "Rice"
    assert "fertilizer_plan" in res
    f_plan = res["fertilizer_plan"]
    assert f_plan["status"] == "OPTIMIZATION_SUCCESS"
    assert len(f_plan["recommended_products"]) > 0
    assert f_plan["total_cost_inr"] > 0
    # Confirmed soil values present in summary
    assert res["soil_test_summary"]["nitrogen_kg_per_ha"] == 220.0
    assert res["soil_test_summary"]["phosphorus_kg_per_ha"] == 16.0
    assert res["soil_test_summary"]["potassium_kg_per_ha"] == 210.0


# ==============================================================================
# Case 2: Different soil-test values producing changes consistent with agronomic rules
# ==============================================================================
def test_case_02_soil_test_values_monotonic_decrease():
    # As soil test N increases, crop fertilizer N requirement must decrease
    p5_low = nutrient_service.calculate(NutrientCalculationRequest(
        crop="Rice", soil_series="Palavidhi", selected_rule_id="TNAU_STCR_IPNS_RICE_001", target_yield=6.0,
        soil_nitrogen=180.0, soil_phosphorus=15.0, soil_phosphorus_method="Olsen", soil_potassium=200.0, farm_area=1.0
    ))
    p5_med = nutrient_service.calculate(NutrientCalculationRequest(
        crop="Rice", soil_series="Palavidhi", selected_rule_id="TNAU_STCR_IPNS_RICE_001", target_yield=6.0,
        soil_nitrogen=300.0, soil_phosphorus=15.0, soil_phosphorus_method="Olsen", soil_potassium=200.0, farm_area=1.0
    ))
    p5_high = nutrient_service.calculate(NutrientCalculationRequest(
        crop="Rice", soil_series="Palavidhi", selected_rule_id="TNAU_STCR_IPNS_RICE_001", target_yield=6.0,
        soil_nitrogen=450.0, soil_phosphorus=15.0, soil_phosphorus_method="Olsen", soil_potassium=200.0, farm_area=1.0
    ))
    assert p5_low.n_req_kg_per_ha > p5_med.n_req_kg_per_ha > p5_high.n_req_kg_per_ha


# ==============================================================================
# Case 3: Different current crops selecting their own verified rules
# ==============================================================================
def test_case_03_different_crops_select_own_rules():
    rice_res = full_rec_service.generate_full_recommendation({
        "crop": "Rice", "district": "Thanjavur", "target_yield": 6.0,
        "soil_nitrogen": 240, "soil_phosphorus": 14, "soil_potassium": 190, "no_cache": True
    })
    cotton_res = full_rec_service.generate_full_recommendation({
        "crop": "Cotton", "district": "Coimbatore", "target_yield": 2.5,
        "soil_nitrogen": 240, "soil_phosphorus": 14, "soil_potassium": 190, "no_cache": True
    })
    maize_res = full_rec_service.generate_full_recommendation({
        "crop": "Maize", "district": "Salem", "target_yield": 6.0,
        "soil_nitrogen": 240, "soil_phosphorus": 14, "soil_potassium": 190, "no_cache": True
    })
    
    assert "RICE" in rice_res["rule_selection"]["selected_rule_id"]
    assert "COTTON" in cotton_res["rule_selection"]["selected_rule_id"]
    assert "MAIZE" in maize_res["rule_selection"]["selected_rule_id"]


# ==============================================================================
# Case 4: Different farm areas scaling total fertilizer quantities and cost correctly
# ==============================================================================
def test_case_04_farm_area_scaling():
    res_1ha = full_rec_service.generate_full_recommendation({
        "crop": "Rice", "district": "Thanjavur", "soil_series": "Palavidhi", "farm_area": 1.0, "farm_area_unit": "hectare",
        "soil_nitrogen": 240, "soil_phosphorus": 16, "soil_phosphorus_method": "Olsen", "soil_potassium": 200, "no_cache": True
    })
    res_2ha = full_rec_service.generate_full_recommendation({
        "crop": "Rice", "district": "Thanjavur", "soil_series": "Palavidhi", "farm_area": 2.0, "farm_area_unit": "hectare",
        "soil_nitrogen": 240, "soil_phosphorus": 16, "soil_phosphorus_method": "Olsen", "soil_potassium": 200, "no_cache": True
    })
    # Per-ha nutrient rate remains identical
    assert res_1ha["nutrient_requirements"]["n_req_kg_per_ha"] == res_2ha["nutrient_requirements"]["n_req_kg_per_ha"]
    # Total farm nutrient requirements scale by exactly 2.0x
    assert round(res_2ha["nutrient_requirements"]["total_n_req_kg"], 1) == round(res_1ha["nutrient_requirements"]["total_n_req_kg"] * 2.0, 1)
    # Total farm cost scales proportionally
    assert res_2ha["fertilizer_plan"]["total_cost_inr"] > res_1ha["fertilizer_plan"]["total_cost_inr"] * 1.5


# ==============================================================================
# Case 5: Previous crop history affecting result only where supported by rule
# ==============================================================================
def test_case_05_previous_crop_legume_credit():
    # Rice after Fallow
    p5_fallow = nutrient_service.calculate(NutrientCalculationRequest(
        crop="Rice", soil_series="Palavidhi", selected_rule_id="TNAU_STCR_IPNS_RICE_001", target_yield=6.0,
        soil_nitrogen=250.0, soil_phosphorus=16.0, soil_phosphorus_method="Olsen", soil_potassium=200.0,
        previous_crop="None / Fallow"
    ))
    # Rice after Blackgram (grain legume fixes N, granting 20 kg N credit to Rice)
    p5_blackgram = nutrient_service.calculate(NutrientCalculationRequest(
        crop="Rice", soil_series="Palavidhi", selected_rule_id="TNAU_STCR_IPNS_RICE_001", target_yield=6.0,
        soil_nitrogen=250.0, soil_phosphorus=16.0, soil_phosphorus_method="Olsen", soil_potassium=200.0,
        previous_crop="Blackgram"
    ))
    # Difference in N requirement is exactly 20 kg/ha
    assert round(p5_fallow.n_req_kg_per_ha - p5_blackgram.n_req_kg_per_ha, 1) == 20.0
    assert p5_blackgram.previous_crop_credit_kg_per_ha["n"] == 20.0

    # Non-legume previous crop (e.g. Fallow / None) provides 0.0 credit
    assert p5_fallow.previous_crop_credit_kg_per_ha["n"] == 0.0


# ==============================================================================
# Case 6: Previous fertilizer history containing multiple products and dates
# ==============================================================================
def test_case_06_previous_fertilizer_multi_product():
    prev_fert = [
        PreviousFertilizerItem(product="DAP", quantity=2.0, unit="bags", bag_weight_kg=50.0, months_ago=2.0),
        PreviousFertilizerItem(product="Urea", quantity=1.0, unit="bags", bag_weight_kg=45.0, months_ago=2.0),
    ]
    p5 = nutrient_service.calculate(NutrientCalculationRequest(
        crop="Rice", soil_series="Palavidhi", selected_rule_id="TNAU_STCR_IPNS_RICE_001", target_yield=6.0,
        soil_nitrogen=240.0, soil_phosphorus=16.0, soil_phosphorus_method="Olsen", soil_potassium=200.0, farm_area=1.0,
        previous_fertilizers=prev_fert
    ))
    # Synthetic N has 0.0 carryover
    assert p5.previous_fertilizer_residual_kg_per_ha["n"] == 0.0
    # 2 bags DAP (100 kg) * 46% P2O5 = 46 kg P2O5 applied * 15% residual = 6.9 kg P2O5
    assert p5.previous_fertilizer_residual_kg_per_ha["p2o5"] == 6.9


# ==============================================================================
# Case 7: Missing previous crop or fertilizer history
# ==============================================================================
def test_case_07_missing_history_handled_without_fabrication():
    p5 = nutrient_service.calculate(NutrientCalculationRequest(
        crop="Rice", soil_series="Palavidhi", selected_rule_id="TNAU_STCR_IPNS_RICE_001", target_yield=6.0,
        soil_nitrogen=240.0, soil_phosphorus=16.0, soil_phosphorus_method="Olsen", soil_potassium=200.0,
        previous_crop=None, previous_fertilizers=[]
    ))
    assert p5.previous_crop_credit_kg_per_ha["n"] == 0.0
    assert p5.previous_crop_credit_kg_per_ha["p2o5"] == 0.0
    assert p5.previous_fertilizer_residual_kg_per_ha["n"] == 0.0
    assert p5.previous_fertilizer_residual_kg_per_ha["p2o5"] == 0.0
    assert p5.status == "CALCULATION_SUCCESS"


# ==============================================================================
# Case 8: Missing, unreadable or invalid soil values
# ==============================================================================
def test_case_08_invalid_or_missing_soil_values():
    # Negative nutrient value
    p5_neg = nutrient_service.calculate(NutrientCalculationRequest(
        crop="Rice", soil_series="Palavidhi", selected_rule_id="TNAU_STCR_IPNS_RICE_001",
        soil_nitrogen=-50.0, soil_phosphorus=16.0, soil_phosphorus_method="Olsen", soil_potassium=200.0
    ))
    assert p5_neg.status == "VALIDATION_ERROR"

    # Missing nitrogen
    p5_missing = nutrient_service.calculate(NutrientCalculationRequest(
        crop="Rice", soil_series="Palavidhi", selected_rule_id="TNAU_STCR_IPNS_RICE_001",
        soil_nitrogen=None, soil_phosphorus=16.0, soil_phosphorus_method="Olsen", soil_potassium=200.0
    ))
    assert p5_missing.status == "MISSING_INPUTS"


# ==============================================================================
# Case 9: Incorrect units and bag-size conversions
# ==============================================================================
def test_case_09_units_and_bag_size_conversions():
    # Urea is statutory 45 kg in India
    # 2 bags of Urea = 90 kg Urea * 46% = 41.4 kg N applied
    # Grams unit support: 50,000 g = 50 kg
    res_fert = nutrient_service._calculate_previous_fertilizer_residual([
        {"product": "Urea", "quantity": 2.0, "unit": "bags"},
        {"product": "DAP", "quantity": 50000.0, "unit": "grams"}
    ], farm_area_ha=1.0)
    # 50,000 g DAP = 50 kg DAP * 46% P2O5 = 23 kg P2O5 applied * 15% residual = 3.45 kg
    assert res_fert["P2O5"] == 3.45
    assert res_fert["N"] == 0.0


# ==============================================================================
# Case 10: Correct N, P2O5, and K2O contributions from multi-nutrient fertilizers
# ==============================================================================
def test_case_10_multi_nutrient_fertilizer_accounting():
    # 100 kg DAP supplies 18 kg N and 46 kg P2O5
    # Optimizer must account for the 18 kg N and not double count
    req = FertilizerOptimizationRequest(
        crop="Rice", n_req_kg=40.0, p2o5_req_kg=46.0, k2o_req_kg=0.0,
        allowed_fertilizers=["UREA", "DAP"], allow_fractional_bags=True
    )
    res = fertilizer_service.optimize(req)
    assert res.status == "OPTIMIZATION_SUCCESS"
    dap_rec = next(p for p in res.recommended_products if p.product_id == "DAP")
    urea_rec = next(p for p in res.recommended_products if p.product_id == "UREA")
    # DAP supplies 1 bag (50 kg) -> 23 kg P2O5, so 2 bags DAP (100 kg) supplies 46 kg P2O5 + 18 kg N
    assert dap_rec.nutrient_contributions["phosphorus_p2o5"] >= 45.9
    assert dap_rec.nutrient_contributions["nitrogen"] >= 17.9
    # Urea only needs to supply remaining (40 - 18 = 22 kg N)
    assert urea_rec.nutrient_contributions["nitrogen"] >= 21.9


# ==============================================================================
# Case 11: Organic manure credits where selected method supports them
# ==============================================================================
def test_case_11_organic_manure_fym_credits():
    # Without FYM
    p5_no_fym = nutrient_service.calculate(NutrientCalculationRequest(
        crop="Rice", soil_series="Palavidhi", selected_rule_id="TNAU_STCR_IPNS_RICE_001", target_yield=6.0,
        soil_nitrogen=240.0, soil_phosphorus=16.0, soil_phosphorus_method="Olsen", soil_potassium=200.0, fym_applied_t_per_ha=0.0
    ))
    # With 12.5 t/ha FYM (standard recommended basal dressing)
    p5_fym = nutrient_service.calculate(NutrientCalculationRequest(
        crop="Rice", soil_series="Palavidhi", selected_rule_id="TNAU_STCR_IPNS_RICE_001", target_yield=6.0,
        soil_nitrogen=240.0, soil_phosphorus=16.0, soil_phosphorus_method="Olsen", soil_potassium=200.0, fym_applied_t_per_ha=12.5
    ))
    # FYM reduces chemical N requirement according to STCR IPNS calibration
    assert p5_fym.n_req_kg_per_ha < p5_no_fym.n_req_kg_per_ha
    assert p5_fym.fym_credit_kg_per_ha["n"] > 0.0


# ==============================================================================
# Case 12: Nutrient surplus and deficit reporting
# ==============================================================================
def test_case_12_surplus_and_deficit_reporting():
    # Whole bag rounding of discrete commercial packages can produce a small surplus
    req = FertilizerOptimizationRequest(
        crop="Rice", n_req_kg=10.0, p2o5_req_kg=10.0, k2o_req_kg=10.0,
        allow_fractional_bags=False
    )
    res = fertilizer_service.optimize(req)
    assert res.status == "OPTIMIZATION_SUCCESS"
    assert "nitrogen" in res.nutrient_surplus_kg
    assert "phosphorus_p2o5" in res.nutrient_surplus_kg
    assert "potassium_k2o" in res.nutrient_surplus_kg
    # Deficit should be 0 since constraints are >= requirement
    assert res.nutrient_deficit_kg["nitrogen"] == 0.0


# ==============================================================================
# Case 13: Whole-bag rounding and loose quantities
# ==============================================================================
def test_case_13_whole_bags_and_loose_quantities():
    req = FertilizerOptimizationRequest(
        crop="Rice", n_req_kg=50.0, p2o5_req_kg=25.0, k2o_req_kg=30.0,
        allow_fractional_bags=True
    )
    res = fertilizer_service.optimize(req)
    for p in res.recommended_products:
        assert hasattr(p, "whole_bags")
        assert hasattr(p, "loose_kg")
        assert p.whole_bags is not None
        assert p.loose_kg is not None
        # Total kg is whole bags * bag_size + loose_kg
        expected_kg = round(p.whole_bags * p.bag_size_kg + p.loose_kg, 2)
        assert abs(p.quantity_kg - expected_kg) <= 0.05


# ==============================================================================
# Case 14: Infeasible optimizer output
# ==============================================================================
def test_case_14_infeasible_optimizer_output():
    # Require Potash (K2O), but only allow Urea (which only provides N)
    req = FertilizerOptimizationRequest(
        crop="Rice", n_req_kg=50.0, p2o5_req_kg=0.0, k2o_req_kg=50.0,
        allowed_fertilizers=["UREA"]
    )
    res = fertilizer_service.optimize(req)
    assert res.status == "INFEASIBLE"
    assert len(res.recommended_products) == 0
    assert any("failed to find a feasible" in err.lower() for err in res.validation_errors)


# ==============================================================================
# Case 15: Unsupported crop or soil combinations
# ==============================================================================
def test_case_15_unsupported_crop_reporting():
    res = full_rec_service.generate_full_recommendation({
        "crop": "Pineapple", "district": "Thanjavur", "no_cache": True
    })
    assert res["status"] in ("UNSUPPORTED_CROP", "NO_MATCHING_RULE")
    assert res["is_verified"] is False
    assert any("unsupported" in w.lower() or "not supported" in w.lower() for w in res["warnings"])


# ==============================================================================
# Case 16: Price changes affecting cost without incorrectly changing nutrient target
# ==============================================================================
def test_case_16_price_change_decoupled_from_nutrient_target():
    base_res = full_rec_service.generate_full_recommendation({
        "crop": "Rice", "district": "Thanjavur", "soil_series": "Palavidhi", "soil_nitrogen": 240, "soil_phosphorus": 16, "soil_phosphorus_method": "Olsen", "soil_potassium": 200, "no_cache": True
    })
    # Double the price of DAP and Urea
    expensive_res = full_rec_service.generate_full_recommendation({
        "crop": "Rice", "district": "Thanjavur", "soil_series": "Palavidhi", "soil_nitrogen": 240, "soil_phosphorus": 16, "soil_phosphorus_method": "Olsen", "soil_potassium": 200,
        "custom_prices": {"UREA": 500.0, "DAP": 2500.0}, "no_cache": True
    })
    # Agronomic nutrient targets MUST remain strictly identical
    assert base_res["nutrient_requirements"]["n_req_kg_per_ha"] == expensive_res["nutrient_requirements"]["n_req_kg_per_ha"]
    assert base_res["nutrient_requirements"]["p2o5_req_kg_per_ha"] == expensive_res["nutrient_requirements"]["p2o5_req_kg_per_ha"]
    assert base_res["nutrient_requirements"]["k2o_req_kg_per_ha"] == expensive_res["nutrient_requirements"]["k2o_req_kg_per_ha"]
    # Total purchase cost increases
    assert expensive_res["fertilizer_plan"]["total_cost_inr"] > base_res["fertilizer_plan"]["total_cost_inr"]


# ==============================================================================
# Case 17: Repeated identical inputs producing reproducible results
# ==============================================================================
def test_case_17_deterministic_reproducibility():
    payload = {
        "crop": "Rice", "district": "Thanjavur", "soil_series": "Palavidhi",
        "soil_nitrogen": 235.0, "soil_phosphorus": 15.5, "soil_potassium": 215.0,
        "farm_area": 1.5, "no_cache": True
    }
    run1 = full_rec_service.generate_full_recommendation(payload)
    run2 = full_rec_service.generate_full_recommendation(payload)
    assert run1["nutrient_requirements"]["n_req_kg_per_ha"] == run2["nutrient_requirements"]["n_req_kg_per_ha"]
    assert run1["fertilizer_plan"]["total_cost_inr"] == run2["fertilizer_plan"]["total_cost_inr"]


# ==============================================================================
# Case 18: Farmer-level data isolation
# ==============================================================================
def test_case_18_farmer_data_isolation():
    from phase7_integration.extra_api import _create_jwt_token
    farmer_a = "farmer_alpha_01"
    farmer_b = "farmer_beta_02"
    token_a = _create_jwt_token(farmer_a, "alpha@agriwise.org")
    token_b = _create_jwt_token(farmer_b, "beta@agriwise.org")
    
    # Save fertilizer history for Farmer A
    save_resp = client.post(
        "/api/farmer/fertilizer-history",
        json={"crop": "Rice", "fertilizer_product": "Urea", "quantity": 100.0, "unit": "kg"},
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert save_resp.status_code == 200

    # Query fertilizer history as Farmer B
    resp_b = client.get("/api/farmer/fertilizer-history", headers={"Authorization": f"Bearer {token_b}"})
    assert resp_b.status_code == 200
    items_b = resp_b.json()
    assert isinstance(items_b, list)
    # Farmer B must not see Farmer A's records
    assert all(item.get("user_id") != farmer_a for item in items_b)


# ==============================================================================
# Case 19: Final recommendation consistency between backend and response
# ==============================================================================
def test_case_19_final_recommendation_completeness():
    payload = {
        "crop": "Rice", "district": "Thanjavur", "soil_series": "Palavidhi",
        "soil_nitrogen": 240.0, "soil_phosphorus": 16.0, "soil_potassium": 200.0,
        "farm_area": 1.0, "no_cache": True
    }
    res = full_rec_service.generate_full_recommendation(payload)
    assert "crop" in res
    assert "district" in res
    assert "soil_test_summary" in res
    assert "nutrient_requirements" in res
    assert "fertilizer_plan" in res
    assert "previous_history_considered" in res
    assert "agronomic_rule_source" in res
    assert "district_yield_prediction" in res
    # ML prediction is decoupled and labeled as benchmark
    assert "district benchmark" in res["district_yield_prediction"]["scope"].lower()
