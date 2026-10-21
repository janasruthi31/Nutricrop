"""
Automated Test for Economic Benefit Evaluation (Phase 11 Audit).
Validates reproducible comparison of baseline farmer practices against
STCR-IPNS requirement calculations and SciPy MILP optimized whole-bag plans.
"""

import os
import sys
import pytest

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from scripts.evaluate_economic_benefits import evaluate_scenario


def test_economic_evaluation_rice():
    res = evaluate_scenario(
        name="Rice Delta Test",
        crop="Rice",
        district="Thanjavur",
        soil_series="Palavidhi",
        target_yield=6.0,
        sn=220.0,
        sp=16.0,
        sk=190.0,
        farm_area_ha=1.0,
        baseline_bags={"UREA": 4, "DAP": 2, "MOP": 2},
        baseline_desc="4 Urea + 2 DAP + 2 MOP"
    )
    assert res["baseline_cost_inr"] == 7166.00
    assert res["optimized_cost_inr"] <= res["baseline_cost_inr"]
    assert res["percentage_cost_reduction"] > 0.0
    assert res["rule_id"] == "TNAU_STCR_IPNS_RICE_001"
    # Mass balance: supplied nutrients satisfy targets
    assert res["optimized_nutrients"]["N"] >= res["target_nutrients_req"]["N"]
    assert res["optimized_nutrients"]["P2O5"] >= res["target_nutrients_req"]["P2O5"]
    assert res["optimized_nutrients"]["K2O"] >= res["target_nutrients_req"]["K2O"]


def test_economic_evaluation_maize():
    res = evaluate_scenario(
        name="Maize Test",
        crop="Maize",
        district="Coimbatore",
        soil_series="Coimbatore",
        target_yield=7.0,
        sn=240.0,
        sp=18.0,
        sk=220.0,
        farm_area_ha=1.0,
        baseline_bags={"UREA": 5, "DAP": 3, "MOP": 2},
        baseline_desc="5 Urea + 3 DAP + 2 MOP"
    )
    assert res["baseline_cost_inr"] == 8782.50
    assert res["percentage_cost_reduction"] > 50.0
    assert res["rule_id"] == "TNAU_STCR_IPNS_MAIZE_001"
    assert res["optimized_nutrients"]["P2O5"] >= res["target_nutrients_req"]["P2O5"]


def test_economic_evaluation_cotton_high_target():
    res = evaluate_scenario(
        name="Cotton High Target Test",
        crop="Cotton (lint)",
        district="Coimbatore",
        soil_series="Irugur",
        target_yield=2.5,
        sn=210.0,
        sp=15.0,
        sk=200.0,
        farm_area_ha=1.0,
        baseline_bags={"UREA": 4, "DAP": 2, "MOP": 2},
        baseline_desc="4 Urea + 2 DAP + 2 MOP"
    )
    # Target demand for 2.5 t/ha cotton exceeds baseline supply:
    assert res["target_nutrients_req"]["N"] > 100.0
    assert res["optimized_nutrients"]["N"] >= res["target_nutrients_req"]["N"]
