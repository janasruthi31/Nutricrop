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
