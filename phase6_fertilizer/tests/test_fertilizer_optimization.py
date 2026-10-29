"""
Automated unit tests for Phase 6: Fertilizer Type, Quantity, and Cost Optimization Engine.
"""

import pytest
from fastapi.testclient import TestClient
from phase3_soil.main import app
from phase6_fertilizer.service import FertilizerOptimizerService, optimize_fertilizer_plan
from phase6_fertilizer.models import FertilizerOptimizationRequest

client = TestClient(app)
service = FertilizerOptimizerService()


# 1. Valid LP cost-minimization optimization
def test_01_valid_lp_optimization():
    # Requirements for 2 hectares of Rice: 100 kg N, 50 kg P2O5, 60 kg K2O
    req = FertilizerOptimizationRequest(
        crop="Rice",
        n_req_kg=100.0,
        p2o5_req_kg=50.0,
        k2o_req_kg=60.0,
        farm_area_hectares=2.0
    )
    res = service.optimize(req)
    assert res.status == "OPTIMIZATION_SUCCESS"
    assert res.total_cost_inr > 0
    assert len(res.recommended_products) > 0
    assert res.nutrient_balance["nitrogen"].supplied_kg >= 100.0
    assert res.nutrient_balance["phosphorus_p2o5"].supplied_kg >= 50.0
    assert res.nutrient_balance["potassium_k2o"].supplied_kg >= 60.0
    assert len(res.split_application_schedule) == 3  # Rice 3-split schedule


# 2. Optimization directly consuming Phase 5 output
def test_02_consuming_phase5_output():
    phase5_payload = {
        "crop": "Rice",
        "selected_rule_id": "TNAU_STCR_IPNS_RICE_001",
        "n_req_kg_per_ha": 35.0,
        "p2o5_req_kg_per_ha": 25.0,
        "k2o_req_kg_per_ha": 20.0,
        "farm_area_hectares": 1.5,
        "total_n_req_kg": 52.5,
        "total_p2o5_req_kg": 37.5,
        "total_k2o_req_kg": 30.0
    }
    req = FertilizerOptimizationRequest(phase5_result=phase5_payload)
    res = service.optimize(req)
    assert res.status == "OPTIMIZATION_SUCCESS"
    assert res.crop == "Rice"
    assert res.farm_area_hectares == 1.5
    assert res.nutrient_balance["nitrogen"].required_kg == 52.5


# 3. Zero nutrient requirement input
def test_03_zero_nutrient_requirement():
    req = FertilizerOptimizationRequest(
        crop="Rice",
        n_req_kg=0.0,
        p2o5_req_kg=0.0,
        k2o_req_kg=0.0
    )
    res = service.optimize(req)
    assert res.status == "OPTIMIZATION_SUCCESS"
    assert res.total_cost_inr == 0.0
    assert len(res.recommended_products) == 0


# 4. Restricted allowed fertilizers list
def test_04_restricted_allowed_fertilizers():
    # Only allow straight fertilizers (Urea, MOP, SSP)
    req = FertilizerOptimizationRequest(
        crop="Cotton (lint)",
        n_req_kg=60.0,
        p2o5_req_kg=30.0,
        k2o_req_kg=40.0,
        allowed_fertilizers=["UREA", "SSP", "MOP"]
    )
    res = service.optimize(req)
    assert res.status == "OPTIMIZATION_SUCCESS"
    prod_ids = {p.product_id for p in res.recommended_products}
    assert prod_ids.issubset({"UREA", "SSP", "MOP"})


# 5. Infeasible/invalid input requirements
def test_05_invalid_input_requirements():
    # Missing requirements
    req = FertilizerOptimizationRequest(crop="Rice")
    res = service.optimize(req)
    assert res.status == "VALIDATION_ERROR"
    assert any("must be provided" in err.lower() for err in res.validation_errors)


# 6. API validation endpoint (POST /api/fertilizer/optimize)
def test_06_api_validation_endpoint():
    payload = {
        "crop": "Cotton (lint)",
        "n_req_kg": 80.0,
        "p2o5_req_kg": 40.0,
        "k2o_req_kg": 40.0,
        "farm_area_hectares": 1.0
    }
    response = client.post("/api/fertilizer/optimize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "OPTIMIZATION_SUCCESS"
    assert data["total_cost_inr"] > 0
    assert len(data["recommended_products"]) > 0
    assert len(data["split_application_schedule"]) >= 2


# 7. Infeasible optimization case (required nutrient unavailable in allowed catalog)
def test_07_infeasible_nutrient_constraint():
    # Requires 50 kg K2O, but only UREA and SSP (which have 0% K2O) are permitted
    req = FertilizerOptimizationRequest(
        crop="Rice",
        n_req_kg=40.0,
        p2o5_req_kg=20.0,
        k2o_req_kg=50.0,
        allowed_fertilizers=["UREA", "SSP"]
    )
    res = service.optimize(req)
    assert res.status in ("INFEASIBLE", "NO_FEASIBLE_SOLUTION")
    assert res.limiting_constraint is not None
    assert any("failed to find a feasible" in err.lower() for err in res.validation_errors)


# 8. Mathematical optimality validation: comparison against independent brute-force search
def test_08_milp_optimality_compared_to_brute_force():
    # Test case: N=30 kg, P2O5=20 kg, K2O=25 kg with candidate catalog [UREA, DAP, MOP]
    n_target = 30.0
    p_target = 20.0
    k_target = 25.0

    candidates = [p for p in service.catalog if p["id"] in ("UREA", "DAP", "MOP")]
    req = FertilizerOptimizationRequest(
        crop="Rice",
        n_req_kg=n_target,
        p2o5_req_kg=p_target,
        k2o_req_kg=k_target,
        allowed_fertilizers=["UREA", "DAP", "MOP"]
    )
    res = service.optimize(req)
    assert res.status == "OPTIMIZATION_SUCCESS"
    milp_cost = res.total_cost_inr

    # Independent brute-force search over all bag combinations [0..4]
    urea = next(c for c in candidates if c["id"] == "UREA")
    dap = next(c for c in candidates if c["id"] == "DAP")
    mop = next(c for c in candidates if c["id"] == "MOP")

    min_brute_cost = float("inf")
    best_combo = None

    for b_u in range(5):
        for b_d in range(5):
            for b_m in range(5):
                sup_n = b_u * urea["bag_size_kg"] * (urea["n_pct"] / 100.0) + \
                        b_d * dap["bag_size_kg"] * (dap["n_pct"] / 100.0)
                sup_p = b_d * dap["bag_size_kg"] * (dap["p2o5_pct"] / 100.0)
                sup_k = b_m * mop["bag_size_kg"] * (mop["k2o_pct"] / 100.0)

                if sup_n >= n_target and sup_p >= p_target and sup_k >= k_target:
                    cost = b_u * urea["price_per_bag_inr"] + \
                           b_d * dap["price_per_bag_inr"] + \
                           b_m * mop["price_per_bag_inr"]
                    if cost < min_brute_cost:
                        min_brute_cost = cost
                        best_combo = (b_u, b_d, b_m)

    assert round(milp_cost, 2) == round(min_brute_cost, 2), \
        f"MILP cost {milp_cost} does not match global minimum brute-force cost {min_brute_cost} (combo: {best_combo})"


# 9. Crop-specific phenological split schedules
def test_09_crop_specific_schedules():
    # Pulses: 100% basal schedule
    req_pulse = FertilizerOptimizationRequest(
        crop="Blackgram",
        n_req_kg=20.0,
        p2o5_req_kg=40.0,
        k2o_req_kg=20.0
    )
    res_pulse = service.optimize(req_pulse)
    assert len(res_pulse.split_application_schedule) == 1
    assert "Basal" in res_pulse.split_application_schedule[0].stage_name

    # Maize: 3 stages
    req_maize = FertilizerOptimizationRequest(
        crop="Maize",
        n_req_kg=120.0,
        p2o5_req_kg=60.0,
        k2o_req_kg=50.0
    )
    res_maize = service.optimize(req_maize)
    assert len(res_maize.split_application_schedule) == 3
    stage_names = [s.stage_name for s in res_maize.split_application_schedule]
    assert any("Knee-High" in name for name in stage_names)


# 10. Whole commercial bag discrete integrity
def test_10_whole_bag_integer_units():
    req = FertilizerOptimizationRequest(
        crop="Cotton (lint)",
        n_req_kg=75.0,
        p2o5_req_kg=35.0,
        k2o_req_kg=45.0
    )
    res = service.optimize(req)
    assert res.status == "OPTIMIZATION_SUCCESS"
    for p in res.recommended_products:
        assert isinstance(p.bags, int)
        assert p.bags >= 1
        assert round(p.quantity_kg, 2) == round(p.bags * p.bag_size_kg, 2)
        assert round(p.total_cost_inr, 2) == round(p.bags * p.price_per_bag_inr, 2)
        assert p.price_source != ""
        assert p.price_effective_date != ""


# 11. Fractional bag optimization for smallholders
def test_11_fractional_bags_for_smallholders():
    # Smallholder 0.05 ha plot: requires 6 kg N, 2 kg P2O5, 2 kg K2O
    req = FertilizerOptimizationRequest(
        crop="Rice",
        n_req_kg=6.0,
        p2o5_req_kg=2.0,
        k2o_req_kg=2.0,
        farm_area_hectares=0.05,
        allow_fractional_bags=True
    )
    res = service.optimize(req)
    assert res.status == "OPTIMIZATION_SUCCESS"
    assert res.total_cost_inr > 0
    # Must not force full whole 50kg bags
    total_delivered_kg = sum(p.quantity_kg for p in res.recommended_products)
    assert total_delivered_kg < 45.0  # Fraction is less than one single full bag
    assert any(isinstance(p.bags, float) or p.bags < 1.0 for p in res.recommended_products)


# 12. Surplus factor upper bound constraint
def test_12_surplus_factor_constraint():
    # Setting max_surplus_factor=1.2 on fractional bags
    req = FertilizerOptimizationRequest(
        crop="Rice",
        n_req_kg=50.0,
        p2o5_req_kg=25.0,
        k2o_req_kg=25.0,
        allow_fractional_bags=True,
        max_surplus_factor=1.2
    )
    res = service.optimize(req)
    assert res.status == "OPTIMIZATION_SUCCESS"
    assert res.nutrient_balance["nitrogen"].supplied_kg <= 50.0 * 1.2001
    assert res.nutrient_balance["phosphorus_p2o5"].supplied_kg <= 25.0 * 1.2001
    assert res.nutrient_balance["potassium_k2o"].supplied_kg <= 25.0 * 1.2001


# 13. Smallholder surplus packaging warning in whole bag mode
def test_13_smallholder_surplus_packaging_warning():
    # Very small plot with discrete whole bags -> oversupply > 1.5x triggers warning
    req = FertilizerOptimizationRequest(
        crop="Rice",
        n_req_kg=6.0,
        p2o5_req_kg=2.0,
        k2o_req_kg=2.0,
        farm_area_hectares=0.05,
        allow_fractional_bags=False
    )
    res = service.optimize(req)
    assert res.status == "OPTIMIZATION_SUCCESS"
    # Should flag packaging oversupply in warnings
    assert any("surplus over 1.5x" in w.lower() for w in res.warnings)


