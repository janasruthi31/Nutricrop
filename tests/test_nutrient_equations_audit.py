"""
Automated Agronomic Nutrient Equation Audit & Validation Test Suite (NutriCrop Phase 5).

Verifies the 11 agronomic scenarios required by the nutrient equation audit:
1. Known crop/equation example independently verified against official TNAU source (CPG 2020 p. 64).
2. Target yield variations across valid agronomic ranges (monotonic increase in requirement).
3. Soil-test sensitivity across rating bands (monotonic decrease with higher soil supply).
4. Unit conversions (ha/acre, elemental P/K vs oxide P2O5/K2O, t/ha vs q/ha).
5. Correct handling of zero and negative intermediate results (clamping at 0.0 with documentation).
6. Missing or invalid soil-test values (MISSING_INPUTS and VALIDATION_ERROR).
7. Unsupported crop, soil series, or target-yield range (clear rejection).
8. Missing or unverified coefficients (PENDING_VERIFICATION blocked in production).
9. FYM credits and previous-crop credits, including double-counting prevention.
10. Correct farm-total calculations from per-hectare requirements without double conversion.
11. End-to-end consistency between Python calculation, API response, and Flutter UI schema.
"""

import pytest
from starlette.testclient import TestClient

from phase5_nutrient.service import NutrientCalculationService
from phase5_nutrient.models import NutrientCalculationRequest, PreviousFertilizerItem
from phase5_nutrient.units import (
    convert_area_to_hectares,
    convert_kg_per_ha_to_kg_per_acre,
    convert_kg_per_acre_to_kg_per_ha,
    convert_oxide_to_elemental,
    convert_target_yield_to_tonnes_per_ha,
    calculate_farm_total_nutrient,
)
from phase3_soil.main import app

service = NutrientCalculationService()
client = TestClient(app)


class TestNutrientEquationsAuditMatrix:
    """Comprehensive 11-point agronomic validation test suite."""

    # =========================================================================
    # 1. Known crop/equation example verified against official source
    # =========================================================================
    def test_01_known_crop_verified_against_official_source(self):
        """
        Official Source: TNAU Crop Production Guide (Agriculture) 2020, Pulses Chapter, p. 64;
        TNAU Rainfed Pulses Production Guide.
        Crop: Blackgram (Rainfed), Rule: TNAU_STD_BLACKGRAM_RF_001.
        Blanket RDF: 20 kg N : 40 kg P2O5 : 20 kg K2O / ha.
        Soil Test (Olsen):
          SN = 190.0 kg/ha (< 280, Low rating - diagnostic only)
          SP = 15.0 kg/ha (11-22, Medium rating - diagnostic only)
          SK = 320.0 kg/ha (> 280, High rating - diagnostic only)

        Independently calculated expected net doses (Official TNAU RDF without unsupported multipliers):
          N    = 20.00 kg/ha
          P2O5 = 40.00 kg/ha
          K2O  = 20.00 kg/ha
        """
        req = NutrientCalculationRequest(
            crop="Blackgram",
            selected_rule_id="TNAU_STD_BLACKGRAM_RF_001",
            soil_nitrogen=190.0,
            soil_phosphorus=15.0,
            soil_potassium=320.0,
            soil_phosphorus_method="Olsen",
            farm_area=1.0,
            farm_area_unit="hectare"
        )
        res = service.calculate(req)
        assert res.status == "CALCULATION_SUCCESS"
        assert res.is_verified_rule is True
        assert res.verification_status == "VERIFIED"
        assert res.source_title == "TNAU Blackgram Rainfed"

        # Check independently verified numerical values within 0.05 kg/ha
        assert pytest.approx(res.n_req_kg_per_ha, abs=0.05) == 20.00
        assert pytest.approx(res.p2o5_req_kg_per_ha, abs=0.05) == 40.00
        assert pytest.approx(res.k2o_req_kg_per_ha, abs=0.05) == 20.00

    # =========================================================================
    # 2. Target yield variations across valid agronomic ranges
    # =========================================================================
    def test_02_target_yield_variations_monotonic_increase(self):
        """
        In targeted yield STCR equations, higher yield goals require proportionally
        more nutrients according to the crop uptake coefficient a.
        Rice STCR (TNAU_STCR_IPNS_RICE_001):
          Target yields: 5.0, 6.0, 7.0 t/ha (valid range: 3.0 to 8.0 t/ha).
          Baseline soil: SN=220, SP=16, SK=190, FYM=0.
          a_N = 22.4, a_P = 11.2, a_K = 13.5.
          Each 1.0 t/ha yield increase must increase requirement by exactly a_N, a_P, a_K.
        """
        y_targets = [5.0, 6.0, 7.0]
        results = []
        for ty in y_targets:
            req = NutrientCalculationRequest(
                crop="Rice",
                soil_series="Palavidhi",
                selected_rule_id="TNAU_STCR_IPNS_RICE_001",
                target_yield=ty,
                soil_nitrogen=220.0,
                soil_phosphorus=16.0,
                soil_phosphorus_method="Olsen",
                soil_potassium=190.0,
                fym_applied_t_per_ha=0.0,
                farm_area=1.0,
                farm_area_unit="ha",
                allow_unverified=True
            )
            res = service.calculate(req)
            assert res.status == "CALCULATION_SUCCESS"
            results.append(res)

        # Monotonicity checks
        assert results[0].n_req_kg_per_ha < results[1].n_req_kg_per_ha < results[2].n_req_kg_per_ha
        assert results[0].p2o5_req_kg_per_ha < results[1].p2o5_req_kg_per_ha < results[2].p2o5_req_kg_per_ha
        assert results[0].k2o_req_kg_per_ha < results[1].k2o_req_kg_per_ha < results[2].k2o_req_kg_per_ha

        # Step size equality: Delta for 1 t/ha must equal coefficient
        delta_n_1 = results[1].n_req_kg_per_ha - results[0].n_req_kg_per_ha
        delta_n_2 = results[2].n_req_kg_per_ha - results[1].n_req_kg_per_ha
        assert pytest.approx(delta_n_1, abs=0.1) == 22.4
        assert pytest.approx(delta_n_2, abs=0.1) == 22.4

        delta_p_1 = results[1].p2o5_req_kg_per_ha - results[0].p2o5_req_kg_per_ha
        assert pytest.approx(delta_p_1, abs=0.1) == 11.2

        delta_k_1 = results[1].k2o_req_kg_per_ha - results[0].k2o_req_kg_per_ha
        assert pytest.approx(delta_k_1, abs=0.1) == 13.5

    # =========================================================================
    # 3. Soil-test values at different valid levels (monotonic decrease)
    # =========================================================================
    def test_03_soil_test_sensitivity_monotonic_decrease(self):
        """
        Higher soil test nutrients (indigenous soil fertility) must monotonically
        decrease recommended fertilizer dose across Low, Medium, and High ratings.
        TNAU Blanket Rating Mode for Rice (TNAU_STD_RICE_001): Blanket 150 : 50 : 50 kg/ha.
          Low fertility:    SN=180 (<280),   SP=8 (<11),   SK=90 (<118)
          Medium fertility: SN=350 (280-450), SP=16 (11-22), SK=200 (118-280)
          High fertility:   SN=500 (>450),   SP=28 (>22),  SK=320 (>280)
        """
        req_low = NutrientCalculationRequest(
            crop="Rice", selected_rule_id="TNAU_STD_RICE_001",
            soil_nitrogen=180.0, soil_phosphorus=8.0, soil_phosphorus_method="Olsen", soil_potassium=90.0,
            farm_area=1.0, farm_area_unit="hectare"
        )
        req_med = NutrientCalculationRequest(
            crop="Rice", selected_rule_id="TNAU_STD_RICE_001",
            soil_nitrogen=350.0, soil_phosphorus=16.0, soil_phosphorus_method="Olsen", soil_potassium=200.0,
            farm_area=1.0, farm_area_unit="hectare"
        )
        req_high = NutrientCalculationRequest(
            crop="Rice", selected_rule_id="TNAU_STD_RICE_001",
            soil_nitrogen=500.0, soil_phosphorus=28.0, soil_phosphorus_method="Olsen", soil_potassium=320.0,
            farm_area=1.0, farm_area_unit="hectare"
        )

        res_low = service.calculate(req_low)
        res_med = service.calculate(req_med)
        res_high = service.calculate(req_high)

        # Monotonically decreasing requirement with increasing soil fertility
        assert res_low.n_req_kg_per_ha > res_med.n_req_kg_per_ha > res_high.n_req_kg_per_ha
        assert res_low.p2o5_req_kg_per_ha > res_med.p2o5_req_kg_per_ha > res_high.p2o5_req_kg_per_ha
        assert res_low.k2o_req_kg_per_ha > res_med.k2o_req_kg_per_ha > res_high.k2o_req_kg_per_ha

        # Exact bounds check: Low is >150 kg N/ha, Medium is ~150 kg N/ha, High is <150 kg N/ha
        assert res_low.n_req_kg_per_ha > 150.0
        assert pytest.approx(res_med.n_req_kg_per_ha, abs=5.0) == 150.0
        assert res_high.n_req_kg_per_ha < 150.0

    # =========================================================================
    # 4. Unit conversions (ha/acre, elemental P/K vs oxide, t/ha vs q/ha)
    # =========================================================================
    def test_04_unit_conversions_integrity(self):
        """
        Verifies explicit dimensional integrity:
        - 1 ha = 2.47105 acres (1 acre = 0.404686 ha).
        - Elemental P * 2.2914 = P2O5; Elemental K * 1.2046 = K2O.
        - 1 tonne/ha = 10 quintals/ha.
        """
        # 4a: Area conversion
        assert pytest.approx(convert_area_to_hectares(1.0, "acre"), 0.0001) == 0.404686
        assert pytest.approx(convert_area_to_hectares(2.47105, "acre"), 0.001) == 1.0

        # Rate per ha to per acre
        rate_ha = 100.0
        rate_acre = convert_kg_per_ha_to_kg_per_acre(rate_ha)
        assert pytest.approx(rate_acre, 0.01) == 40.47
        assert pytest.approx(convert_kg_per_acre_to_kg_per_ha(rate_acre), 0.01) == rate_ha

        # 4b: Elemental to Oxide conversion
        elem_p = 10.0
        p2o5_eq = round(elem_p * 2.291367, 2)
        assert p2o5_eq == 22.91
        assert pytest.approx(convert_oxide_to_elemental(p2o5_eq, "P"), 0.01) == elem_p

        elem_k = 100.0
        k2o_eq = round(elem_k * 1.20459, 2)
        assert k2o_eq == 120.46
        assert pytest.approx(convert_oxide_to_elemental(k2o_eq, "K"), 0.01) == elem_k

        # 4c: Target yield quintals to tonnes
        assert convert_target_yield_to_tonnes_per_ha(60.0, "q/ha") == 6.0
        assert convert_target_yield_to_tonnes_per_ha(60.0, "quintal/ha") == 6.0
        assert convert_target_yield_to_tonnes_per_ha(6.0, "t/ha") == 6.0

    # =========================================================================
    # 5. Handling of zero and negative intermediate results
    # =========================================================================
    def test_05_negative_results_clamping_and_documentation(self):
        """
        When soil test supply exceeds crop demand, intermediate STCR formula
        yields negative numbers. Verified agronomy clamps net dose to 0.0 kg/ha
        and documents clamping notes in calculation details.
        Rice STCR: T=4.0, SK=500 kg/ha (Very high soil K).
        raw_K = 13.5*4.0 - 0.32*500 = 54.0 - 160.0 = -106.0 kg/ha.
        Net K2O requirement must be 0.0 kg/ha.
        """
        req = NutrientCalculationRequest(
            crop="Rice",
            soil_series="Palavidhi",
            selected_rule_id="TNAU_STCR_IPNS_RICE_001",
            target_yield=4.0,
            soil_nitrogen=250.0,
            soil_phosphorus=18.0,
            soil_phosphorus_method="Olsen",
            soil_potassium=500.0,
            farm_area=1.0,
            farm_area_unit="ha",
            allow_unverified=True
        )
        res = service.calculate(req)
        assert res.status == "CALCULATION_SUCCESS"
        assert res.k2o_req_kg_per_ha == 0.0
        assert res.k2o_req_kg_per_acre == 0.0
        assert res.total_k2o_req_kg == 0.0

        # Verify clamping documentation in breakdown and details
        assert res.nutrient_breakdown["potassium"]["clamped_at_zero"] is True
        assert res.nutrient_breakdown["potassium"]["final_net_dose_kg_per_ha"] == 0.0
        raw_k_val = res.calculation_details["raw_calculated_rates_kg_per_ha"]["K2O"]
        assert raw_k_val < 0.0
        assert any("Potassium requirement was negative" in note for note in res.calculation_details["clamping_notes"])

    # =========================================================================
    # 6. Missing or invalid soil-test values
    # =========================================================================
    def test_06_missing_and_invalid_soil_inputs(self):
        """
        Missing required soil nutrients in STCR mode returns MISSING_INPUTS.
        Negative or corrupt values return VALIDATION_ERROR.
        Invalid phosphorus method returns VALIDATION_ERROR.
        """
        # Missing Nitrogen in STCR mode
        req_missing = NutrientCalculationRequest(
            crop="Rice",
            selected_rule_id="TNAU_STCR_IPNS_RICE_001",
            target_yield=6.0,
            soil_nitrogen=None,
            soil_phosphorus=16.0,
            soil_phosphorus_method="Olsen",
            soil_potassium=190.0,
            allow_unverified=True,
        )
        res_missing = service.calculate(req_missing)
        assert res_missing.status == "MISSING_INPUTS"
        assert "soil_nitrogen" in res_missing.missing_inputs

        # Negative soil nutrient
        req_neg = NutrientCalculationRequest(
            crop="Rice",
            selected_rule_id="TNAU_STCR_IPNS_RICE_001",
            target_yield=6.0,
            soil_nitrogen=-50.0,
            soil_phosphorus=16.0,
            soil_phosphorus_method="Olsen",
            soil_potassium=190.0,
            allow_unverified=True,
        )
        res_neg = service.calculate(req_neg)
        assert res_neg.status == "VALIDATION_ERROR"
        assert any("cannot be negative" in err.lower() for err in res_neg.validation_errors)

        # Invalid phosphorus extraction method
        req_bad_p = NutrientCalculationRequest(
            crop="Rice",
            selected_rule_id="TNAU_STCR_IPNS_RICE_001",
            target_yield=6.0,
            soil_nitrogen=220.0,
            soil_phosphorus=16.0,
            soil_potassium=190.0,
            soil_phosphorus_method="Mehlich3",
            allow_unverified=True,
        )
        res_bad_p = service.calculate(req_bad_p)
        assert res_bad_p.status == "VALIDATION_ERROR"
        assert any("Mehlich3" in err for err in res_bad_p.validation_errors)

    # =========================================================================
    # 7. Unsupported crop, soil series, or target-yield range
    # =========================================================================
    def test_07_unsupported_crop_soil_and_target_range(self):
        """
        Rejects crops without verified rules (UNSUPPORTED_CROP).
        Rejects target yields outside calibrated biological limits (VALIDATION_ERROR).
        """
        # Unsupported crop
        req_crop = NutrientCalculationRequest(crop="Dragonfruit")
        res_crop = service.calculate(req_crop)
        assert res_crop.status == "UNSUPPORTED_CROP"

        # Out-of-bounds target yield: Rice STCR range is 3.0 to 8.0 t/ha
        req_high_y = NutrientCalculationRequest(
            crop="Rice",
            selected_rule_id="TNAU_STCR_IPNS_RICE_001",
            target_yield=12.0,  # Exceeds max 8.0 t/ha
            soil_nitrogen=220.0,
            soil_phosphorus=16.0,
            soil_phosphorus_method="Olsen",
            soil_potassium=190.0,
            allow_unverified=True,
        )
        res_high_y = service.calculate(req_high_y)
        assert res_high_y.status == "VALIDATION_ERROR"
        assert any("exceeds documented range" in err for err in res_high_y.validation_errors)

        req_low_y = NutrientCalculationRequest(
            crop="Rice",
            selected_rule_id="TNAU_STCR_IPNS_RICE_001",
            target_yield=1.5,  # Below min 3.0 t/ha
            soil_nitrogen=220.0,
            soil_phosphorus=16.0,
            soil_phosphorus_method="Olsen",
            soil_potassium=190.0,
            allow_unverified=True,
        )
        res_low_y = service.calculate(req_low_y)
        assert res_low_y.status == "VALIDATION_ERROR"
        assert any("below documented range" in err for err in res_low_y.validation_errors)

    # =========================================================================
    # 8. Missing or unverified coefficients
    # =========================================================================
    def test_08_unverified_rule_blocked_from_production(self):
        """
        Rules marked PENDING_VERIFICATION (Banana STCR) or UNSUPPORTED (1980 Blanket)
        must return UNVERIFIED_RULE and be blocked from production unless allow_unverified=True.
        """
        # Banana STCR (PENDING_VERIFICATION)
        req_banana = NutrientCalculationRequest(
            crop="Banana",
            selected_rule_id="TNAU_STCR_BANANA_001",
            target_yield=50.0,
            soil_nitrogen=200.0,
            soil_phosphorus=15.0,
            soil_potassium=250.0,
            allow_unverified=False
        )
        res_banana = service.calculate(req_banana)
        assert res_banana.status in ("UNVERIFIED_RULE", "NO_VERIFIED_RULE")
        assert res_banana.is_verified_rule is False
        assert res_banana.is_provisional is True
        assert any("cannot be used for production" in w for w in res_banana.warnings)

        # Deprecated Rice Rule (UNSUPPORTED)
        req_dep = NutrientCalculationRequest(
            crop="Rice",
            selected_rule_id="TNAU_DEPRECATED_RICE_000",
            soil_nitrogen=200.0,
            soil_phosphorus=15.0,
            soil_potassium=200.0,
            allow_unverified=False
        )
        res_dep = service.calculate(req_dep)
        assert res_dep.status in ("UNVERIFIED_RULE", "NO_VERIFIED_RULE")
        assert res_dep.verification_status in ("UNSUPPORTED", "DEPRECATED")

    # =========================================================================
    # 9. FYM credits and double-counting prevention
    # =========================================================================
    def test_09_fym_credits_and_double_counting_prevention(self):
        """
        STCR-IPNS incorporates basal FYM via calibrated coefficient c_fym:
        - Rice STCR: c_fym = 20 kg N for 12.5 t/ha FYM.
        - Baseline at T=6.0, SN=220, FYM=0 -> N = 37.60 kg/ha.
        - With 12.5 t/ha FYM -> N = 37.60 - 20.00 = 17.60 kg/ha.
        - Double-counting prevention: If farmer enters fym_applied_t_per_ha = 12.5,
          AND lists FYM in previous_fertilizers for the current/recent application,
          the system must not deduct FYM a second time.
        """
        # Case A: Standard basal FYM application
        req_fym = NutrientCalculationRequest(
            crop="Rice",
            soil_series="Palavidhi",
            selected_rule_id="TNAU_STCR_IPNS_RICE_001",
            target_yield=6.0,
            soil_nitrogen=220.0,
            soil_phosphorus=16.0,
            soil_phosphorus_method="Olsen",
            soil_potassium=190.0,
            fym_applied_t_per_ha=12.5,
            previous_fertilizers=[],
            allow_unverified=True,
        )
        res_fym = service.calculate(req_fym)
        assert res_fym.n_req_kg_per_ha == 17.60
        assert res_fym.fym_credit_kg_per_ha["n"] == 20.00

        # Case B: Double-counting attack (FYM in fym_applied AND in previous_fertilizers)
        req_double = NutrientCalculationRequest(
            crop="Rice",
            soil_series="Palavidhi",
            selected_rule_id="TNAU_STCR_IPNS_RICE_001",
            target_yield=6.0,
            soil_nitrogen=220.0,
            soil_phosphorus=16.0,
            soil_phosphorus_method="Olsen",
            soil_potassium=190.0,
            fym_applied_t_per_ha=12.5,
            previous_fertilizers=[
                PreviousFertilizerItem(
                    product="FYM",
                    quantity=12.5,
                    unit="tonnes",
                    months_ago=1.0  # Same recent season
                )
            ],
            allow_unverified=True,
        )
        res_double = service.calculate(req_double)
        # Because basal FYM is already applied, previous fertilizer residual must NOT deduct FYM again
        assert res_double.previous_fertilizer_residual_kg_per_ha["n"] == 0.0
        assert res_double.n_req_kg_per_ha == 17.60  # Exactly preserved, no double deduction!

    # =========================================================================
    # 10. Correct farm-total calculations from per-hectare requirements
    # =========================================================================
    def test_10_farm_total_scaling_without_double_conversion(self):
        """
        Farm total nutrient quantities must scale linearly with farm area
        without double-conversion discrepancies:
        - 2.5 hectares at 20.00 kg N/ha -> Total N = 50.00 kg.
        - 5.0 acres at 20.00 kg N/ha:
            Rate per acre = 20.00 * 0.40468564 = 8.0937 kg/acre.
            Total farm N = 8.0937 * 5.0 = 40.47 kg.
            Area in ha = 5.0 * 0.40468564 = 2.0234 ha.
            Total farm N = 20.00 * 2.0234 = 40.47 kg.
        """
        # Hectare area scaling
        tot_ha = calculate_farm_total_nutrient(20.00, "kg/ha", 2.5, "hectare")
        assert pytest.approx(tot_ha, 0.01) == 50.00

        # Acre area scaling
        tot_acre = calculate_farm_total_nutrient(20.00, "kg/ha", 5.0, "acre")
        assert pytest.approx(tot_acre, 0.05) == 40.47

        # Via service execution
        req_acre = NutrientCalculationRequest(
            crop="Blackgram",
            selected_rule_id="TNAU_STD_BLACKGRAM_RF_001",
            soil_nitrogen=190.0,
            soil_phosphorus=15.0,
            soil_phosphorus_method="Olsen",
            soil_potassium=320.0,
            farm_area=5.0,
            farm_area_unit="acre"
        )
        res_acre = service.calculate(req_acre)
        assert pytest.approx(res_acre.total_n_req_kg, 0.1) == 40.47
        assert pytest.approx(res_acre.total_farm_n_kg, 0.1) == 40.47

    # =========================================================================
    # 11. Consistency between Python calculation, API output, and Flutter UI
    # =========================================================================
    def test_11_api_response_and_flutter_data_contract_consistency(self):
        """
        Calls /api/full-recommendation and verifies that response contains all
        keys required by Flutter UI screens (npk_requirement_screen.dart &
        final_recommendation_screen.dart) with valid, non-null values.
        """
        payload = {
            "crop": "Rice",
            "district": "Thanjavur",
            "soil_series": "Palavidhi",
            "season": "Kharif",
            "irrigation_method": "Irrigated",
            "target_yield": 6.0,
            "soil_nitrogen": 220.0,
            "soil_nitrogen_unit": "kg/ha",
            "soil_phosphorus": 16.0,
            "soil_phosphorus_unit": "kg/ha",
            "soil_phosphorus_method": "Olsen",
            "soil_potassium": 190.0,
            "soil_potassium_unit": "kg/ha",
            "fym_applied_t_per_ha": 12.5,
            "farm_area": 2.0,
            "farm_area_unit": "acre"
        }
        resp = client.post("/api/full-recommendation", json=payload)
        assert resp.status_code == 200, resp.text
        data = resp.json()

        assert data["status"] == "SUCCESS"
        assert data["is_verified"] is True
        assert data["is_provisional"] is False

        # Flutter 'nutrient_requirements' contract validation
        p5 = data["nutrient_requirements"]
        assert "n_req_kg_per_ha" in p5 and p5["n_req_kg_per_ha"] is not None
        assert "p2o5_req_kg_per_ha" in p5 and p5["p2o5_req_kg_per_ha"] is not None
        assert "k2o_req_kg_per_ha" in p5 and p5["k2o_req_kg_per_ha"] is not None

        assert "n_req_kg_per_acre" in p5 and p5["n_req_kg_per_acre"] is not None
        assert "p2o5_req_kg_per_acre" in p5 and p5["p2o5_req_kg_per_acre"] is not None
        assert "k2o_req_kg_per_acre" in p5 and p5["k2o_req_kg_per_acre"] is not None

        assert "total_n_req_kg" in p5 and p5["total_n_req_kg"] is not None
        assert "total_p2o5_req_kg" in p5 and p5["total_p2o5_req_kg"] is not None
        assert "total_k2o_req_kg" in p5 and p5["total_k2o_req_kg"] is not None

        assert p5["selected_rule_id"] in ("TNAU_STD_RICE_001", "TNAU_STCR_IPNS_RICE_001")
        assert p5["verification_status"] == "VERIFIED"
        assert p5["farm_area_original"] == 2.0
        assert p5["farm_area_unit_original"] == "acre"

        # Check recommended ranges (+/- 10%) for Flutter UI chips
        ranges_acre = p5["recommended_range_kg_per_acre"]
        assert "N" in ranges_acre and len(ranges_acre["N"]) == 2
        assert "P2O5" in ranges_acre and len(ranges_acre["P2O5"]) == 2
        assert "K2O" in ranges_acre and len(ranges_acre["K2O"]) == 2
