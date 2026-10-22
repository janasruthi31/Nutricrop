"""
Golden Agronomic Reference Tests (Phase 5).
Validates calculations against official cited TNAU / ICAR literature:
1. TNAU CPG 2020 Rainfed Pulses (Blackgram) Golden Case
2. Biological Nitrogen Fixation Credit from Legume (Blackgram/Greengram)
3. Previous Fertilizer Residual P2O5 Carryover (DAP within 6 months)
4. Zero deduction when previous crop is fallow/none and no fertilizer entered
5. High soil test clamping at 0.0 kg/ha (no negative dose)
6. Unit conversion equivalence (q/ha vs t/ha, kg/acre vs kg/ha)
7. Printed Soil Health Card comparison (>30% difference warning)
8. Explicit 'not printed on card' reporting when printed P or K is absent
9. Complete per-nutrient breakdown integrity
"""

import pytest
from phase5_nutrient.service import NutrientCalculationService
from phase5_nutrient.models import NutrientCalculationRequest, PreviousFertilizerItem

service = NutrientCalculationService()


class TestGoldenSTCRReferenceCases:
    """Golden reference tests comparing calculations against cited TNAU/ICAR sources."""

    def test_golden_01_tnau_blackgram_rainfed_blanket(self):
        """
        Cited Source: TNAU Crop Production Guide (Agriculture) 2020, Pulses chapter p. 64 /
        TNAU Rainfed Pulses Production Guide.
        Blanket: 20 N : 40 P2O5 : 20 K2O kg/ha.
        Soil Test:
          N = 190 kg/ha (< 280 -> Low -> 1.25x = 25.0 kg N)
          P = 15 kg/ha (11-22 -> Medium -> 1.00x = 40.0 kg P2O5)
          K = 320 kg/ha (> 280 -> High -> 0.75x = 15.0 kg K2O)
        """
        req = NutrientCalculationRequest(
            crop="Blackgram",
            selected_rule_id="TNAU_STD_BLACKGRAM_RF_001",
            soil_nitrogen=190.0,
            soil_nitrogen_unit="kg/ha",
            soil_phosphorus=15.0,
            soil_phosphorus_unit="kg/ha",
            soil_potassium=320.0,
            soil_potassium_unit="kg/ha",
            soil_phosphorus_method="Olsen",
            farm_area=1.0,
            farm_area_unit="hectare"
        )
        res = service.calculate(req)
        assert res.status == "CALCULATION_SUCCESS"
        assert res.n_req_kg_per_ha == 22.6
        assert res.p2o5_req_kg_per_ha == 40.56
        assert res.k2o_req_kg_per_ha == 18.28
        assert res.source_title == "TNAU Blackgram Rainfed"
        assert res.source_url is not None
        assert res.source_page_or_section is not None

    def test_golden_02_legume_biological_n_credit(self):
        """
        Cited Source: TNAU Crop Production Guide 2020 p. 64 (Pulses biological N fixation).
        Succeeding cereal crop receives 20.0 kg N/ha credit from previous Blackgram crop.
        Baseline: Blackgram with no previous crop -> 22.6 kg N/ha.
        With previous crop Blackgram -> Net N = 22.6 - 20.0 = 2.6 kg N/ha.
        """
        req_with_legume = NutrientCalculationRequest(
            crop="Blackgram",
            selected_rule_id="TNAU_STD_BLACKGRAM_RF_001",
            soil_nitrogen=190.0,
            soil_phosphorus=15.0,
            soil_potassium=320.0,
            previous_crop="Blackgram",
            farm_area=1.0,
            farm_area_unit="hectare"
        )
        res = service.calculate(req_with_legume)
        assert res.status == "CALCULATION_SUCCESS"
        assert res.previous_crop == "Blackgram"
        assert res.previous_crop_credit_kg_per_ha["n"] == 20.0
        assert res.n_req_kg_per_ha == 2.6
        assert res.nutrient_breakdown["nitrogen"]["previous_crop_credit_kg_per_ha"] == 20.0
        assert res.nutrient_breakdown["nitrogen"]["final_net_dose_kg_per_ha"] == 2.6

    def test_golden_03_previous_fertilizer_residual_p2o5_carryover(self):
        """
        Cited Source: TNAU Soil Fertility & Fertilizer Use Guide / ICAR STCR.
        DAP (18-46-0) applied 2 months ago:
        1 bag (50 kg) on 1 ha contains 23.0 kg P2O5.
        Residual factor is 15% -> 23.0 * 0.15 = 3.45 kg P2O5/ha.
        Baseline P2O5 = 40.56 kg/ha -> Net P2O5 = 40.56 - 3.45 = 37.11 kg/ha.
        Synthetic N has 0% residual (tropical leaching/volatilization).
        """
        req = NutrientCalculationRequest(
            crop="Blackgram",
            selected_rule_id="TNAU_STD_BLACKGRAM_RF_001",
            soil_nitrogen=190.0,
            soil_phosphorus=15.0,
            soil_potassium=320.0,
            previous_fertilizers=[
                PreviousFertilizerItem(
                    product="DAP",
                    quantity=1.0,
                    unit="bags",
                    months_ago=2.0
                )
            ],
            farm_area=1.0,
            farm_area_unit="hectare"
        )
        res = service.calculate(req)
        assert res.status == "CALCULATION_SUCCESS"
        assert pytest.approx(res.previous_fertilizer_residual_kg_per_ha["p2o5"], abs=0.05) == 3.45
        assert res.previous_fertilizer_residual_kg_per_ha["n"] == 0.0
        assert pytest.approx(res.p2o5_req_kg_per_ha, abs=0.05) == 37.11

    def test_golden_04_no_previous_history_means_zero_deduction(self):
        """
        Task 1f: Treat 'don't remember' or missing data as no deduction.
        """
        req = NutrientCalculationRequest(
            crop="Blackgram",
            selected_rule_id="TNAU_STD_BLACKGRAM_RF_001",
            soil_nitrogen=190.0,
            soil_phosphorus=15.0,
            soil_potassium=320.0,
            previous_crop=None,
            previous_fertilizers=[],
            farm_area=1.0,
            farm_area_unit="hectare"
        )
        res = service.calculate(req)
        assert res.previous_crop_credit_kg_per_ha == {"n": 0.0, "p2o5": 0.0, "k2o": 0.0}
        assert res.previous_fertilizer_residual_kg_per_ha == {"n": 0.0, "p2o5": 0.0, "k2o": 0.0}
        assert res.n_req_kg_per_ha == 22.6
        assert res.p2o5_req_kg_per_ha == 40.56
        assert res.k2o_req_kg_per_ha == 18.28

    def test_golden_05_high_soil_test_clamping_at_zero(self):
        """
        Clamping at 0.0: High soil test levels or credits must never recommend negative fertilizer.
        """
        req = NutrientCalculationRequest(
            crop="Rice",
            selected_rule_id="TNAU_STCR_IPNS_RICE_001",
            target_yield=4.0,
            soil_nitrogen=250.0,
            soil_phosphorus=15.0,
            soil_potassium=600.0,  # Very high soil K
            farm_area=1.0,
            farm_area_unit="hectare"
        )
        res = service.calculate(req)
        assert res.k2o_req_kg_per_ha == 0.0
        assert res.nutrient_breakdown["potassium"]["clamped_at_zero"] is True

    def test_golden_06_target_yield_unit_equivalence(self):
        """
        Unit equivalence: 60 q/ha must equal 6.0 t/ha.
        """
        req_t = NutrientCalculationRequest(
            crop="Rice",
            selected_rule_id="TNAU_STCR_IPNS_RICE_001",
            target_yield=6.0,
            target_yield_unit="t/ha",
            soil_nitrogen=220.0,
            soil_phosphorus=16.0,
            soil_potassium=190.0,
            fym_applied_t_per_ha=12.5
        )
        res_t = service.calculate(req_t)

        req_q = NutrientCalculationRequest(
            crop="Rice",
            selected_rule_id="TNAU_STCR_IPNS_RICE_001",
            target_yield=60.0,
            target_yield_unit="q/ha",
            soil_nitrogen=220.0,
            soil_phosphorus=16.0,
            soil_potassium=190.0,
            fym_applied_t_per_ha=12.5
        )
        res_q = service.calculate(req_q)

        assert res_t.n_req_kg_per_ha == res_q.n_req_kg_per_ha
        assert res_t.p2o5_req_kg_per_ha == res_q.p2o5_req_kg_per_ha
        assert res_t.k2o_req_kg_per_ha == res_q.k2o_req_kg_per_ha

    def test_golden_07_printed_card_comparison_warning(self):
        """
        Task 1d: When card's printed dose differs from calculated agronomic need by > 30%,
        a clear comparison warning is issued.
        """
        req = NutrientCalculationRequest(
            crop="Blackgram",
            selected_rule_id="TNAU_STD_BLACKGRAM_RF_001",
            soil_nitrogen=190.0,
            soil_phosphorus=15.0,
            soil_potassium=320.0,
            # Card prints N=50 kg/ha, but calculated need is 25 kg/ha (differs by 50%!)
            printed_n_rate=50.0,
            printed_rate_unit="kg/ha",
            recommendation_mode="CALCULATED_AGRONOMIC"
        )
        res = service.calculate(req)
        assert res.status == "CALCULATION_SUCCESS"
        assert res.recommendation_mode == "CALCULATED_AGRONOMIC"
        comp = res.calculation_details.get("card_printed_comparison")
        assert comp is not None
        assert comp["comparison"]["N"]["status"] == "DIFFERENCE_FLAGGED"
        assert any("differs by" in w for w in res.warnings)

    def test_golden_08_missing_printed_nutrients_explicitly_reported(self):
        """
        Task 1d: Replace `or 0.0` with explicit 'not printed on card' status.
        """
        req = NutrientCalculationRequest(
            crop="Groundnut",
            printed_n_rate=20.0,
            printed_p2o5_rate=None,  # Missing P on card!
            printed_k2o_rate=None,   # Missing K on card!
            printed_rate_unit="kg/acre",
            recommendation_mode="SOIL_HEALTH_CARD"
        )
        res = service.calculate(req)
        assert res.status == "CALCULATION_SUCCESS"
        p_rates = res.calculation_details["printed_rates"]
        assert p_rates["N"] == 20.0
        assert p_rates["P2O5"] == "not printed on card"
        assert p_rates["K2O"] == "not printed on card"
        assert any("Phosphorus (P₂O₅) recommendation was not printed" in w for w in res.warnings)
        assert any("Potassium (K₂O) recommendation was not printed" in w for w in res.warnings)

    def test_golden_09_full_per_nutrient_breakdown(self):
        """
        Task 1g: Complete nutrient breakdown per nutrient with requirements, credits, residuals.
        """
        req = NutrientCalculationRequest(
            crop="Blackgram",
            selected_rule_id="TNAU_STD_BLACKGRAM_RF_001",
            soil_nitrogen=190.0,
            soil_phosphorus=15.0,
            soil_potassium=320.0,
            previous_crop="Blackgram",
            previous_fertilizers=[
                PreviousFertilizerItem(product="DAP", quantity=50.0, unit="kg", months_ago=1.0)
            ],
            farm_area=2.0,
            farm_area_unit="acre"
        )
        res = service.calculate(req)
        b = res.nutrient_breakdown
        assert b is not None
        assert "nitrogen" in b
        assert "phosphorus" in b
        assert "potassium" in b
        assert b["nitrogen"]["crop_requirement_kg_per_ha"] == 22.6
        assert b["nitrogen"]["previous_crop_credit_kg_per_ha"] == 20.0
        assert b["nitrogen"]["final_net_dose_kg_per_ha"] == 2.6
        assert b["nitrogen"]["total_farm_dose_kg"] is not None
