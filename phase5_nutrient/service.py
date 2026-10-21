"""
Nutrient Requirement Calculation Engine Service (Phase 5).
Calculates exact N, P2O5, and K2O nutrient requirements using verified Phase 4 agronomic rules
OR copies and scales printed fertilizer recommendations from uploaded Soil Health Cards.
Does NOT calculate final fertilizer product quantities (Phase 6 responsibility).
"""

from typing import Any, Dict, List, Optional
from agronomy.registry import AgronomicRuleRegistry
from agronomy.service import RuleSelectionService, RuleSelectionRequest
from phase3_soil.classification import classify
from .models import NutrientCalculationRequest, NutrientCalculationResponse
from .units import (
    convert_area_to_hectares,
    normalize_soil_nutrient_value,
    convert_target_yield_to_tonnes_per_ha,
    convert_oxide_to_elemental,
    convert_kg_per_acre_to_kg_per_ha,
    convert_kg_per_ha_to_kg_per_acre,
    calculate_farm_total_nutrient,
    ACRE_TO_HA,
    HA_TO_ACRE,
)

CALCULATION_SUCCESS = "CALCULATION_SUCCESS"
UNVERIFIED_RULE = "UNVERIFIED_RULE"
PENDING_AGRONOMIC_VALIDATION = "PENDING_AGRONOMIC_VALIDATION"
MISSING_INPUTS = "MISSING_INPUTS"
VALIDATION_ERROR = "VALIDATION_ERROR"
UNSUPPORTED_CROP = "UNSUPPORTED_CROP"
CALCULATION_FAILED = "CALCULATION_FAILED"
INVALID_RULE_FOR_CROP = "INVALID_RULE_FOR_CROP"


class NutrientCalculationService:
    def __init__(self, registry: Optional[AgronomicRuleRegistry] = None):
        self.registry = registry or AgronomicRuleRegistry()
        self.rule_selection_service = RuleSelectionService(self.registry)

    def calculate(self, req: NutrientCalculationRequest) -> NutrientCalculationResponse:
        validation_errors: List[str] = []
        missing_inputs: List[str] = []
        warnings: List[str] = []

        # =====================================================================
        # MODE 1: Soil Health Card Printed Recommendation
        # =====================================================================
        if req.recommendation_mode == "SOIL_HEALTH_CARD" or (req.printed_n_rate is not None and req.recommendation_mode != "CALCULATED_AGRONOMIC"):
            if req.printed_n_rate is None and req.printed_p2o5_rate is None and req.printed_k2o_rate is None:
                return NutrientCalculationResponse(
                    status=MISSING_INPUTS,
                    crop=req.crop or "Groundnut",
                    selected_rule_id="SOIL_HEALTH_CARD_PRINTED",
                    selected_method="Report Printed Recommendation",
                    recommendation_mode="SOIL_HEALTH_CARD",
                    recommendation_type="SOIL_HEALTH_CARD",
                    recommendation_source=req.printed_source or "Uploaded Soil Health Card",
                    verification_status="SOIL_HEALTH_CARD_PRINTED",
                    is_verified_rule=False,
                    missing_inputs=["printed_recommendation"],
                    validation_errors=[
                        "Uploaded Soil Health Card does not contain printed fertilizer recommendations ('உரப்பரிந்துரைகள்'). "
                        "Please select 'Soil-Specific STCR' or 'General Blanket' mode to calculate fertilizer recommendations from soil test results."
                    ]
                )

            n_val = float(req.printed_n_rate or 0.0)
            p_val = float(req.printed_p2o5_rate or 0.0)
            k_val = float(req.printed_k2o_rate or 0.0)
            rate_unit = req.printed_rate_unit or "kg/acre"

            farm_area = float(req.farm_area) if req.farm_area is not None else 1.0
            farm_area_unit = (req.farm_area_unit or "acre").strip().lower()

            if "acre" in rate_unit:
                n_acre = n_val
                p2o5_acre = p_val
                k2o_acre = k_val
                n_ha = round(convert_kg_per_acre_to_kg_per_ha(n_acre), 2)
                p2o5_ha = round(convert_kg_per_acre_to_kg_per_ha(p2o5_acre), 2)
                k2o_ha = round(convert_kg_per_acre_to_kg_per_ha(k2o_acre), 2)
            else:
                n_ha = n_val
                p2o5_ha = p_val
                k2o_ha = k_val
                n_acre = round(convert_kg_per_ha_to_kg_per_acre(n_ha), 2)
                p2o5_acre = round(convert_kg_per_ha_to_kg_per_acre(p2o5_ha), 2)
                k2o_acre = round(convert_kg_per_ha_to_kg_per_acre(k2o_ha), 2)

            farm_area_ha = convert_area_to_hectares(farm_area, farm_area_unit)

            # Farm totals: deterministic, exact calculation without double conversion
            total_n = round(calculate_farm_total_nutrient(n_val, rate_unit, farm_area, farm_area_unit), 2)
            total_p2o5 = round(calculate_farm_total_nutrient(p_val, rate_unit, farm_area, farm_area_unit), 2)
            total_k2o = round(calculate_farm_total_nutrient(k_val, rate_unit, farm_area, farm_area_unit), 2)

            return NutrientCalculationResponse(
                status=CALCULATION_SUCCESS,
                crop=req.crop or "Groundnut",
                selected_rule_id="SOIL_HEALTH_CARD_PRINTED",
                selected_method="Report Printed Recommendation",
                recommendation_mode="SOIL_HEALTH_CARD",
                recommendation_type="SOIL_HEALTH_CARD",
                recommendation_source=req.printed_source or "Uploaded Soil Health Card",
                verification_status="SOIL_HEALTH_CARD_PRINTED",
                is_verified_rule=True,
                is_provisional=False,
                n_req_kg_per_ha=n_ha,
                net_n_kg_per_ha=n_ha,
                p2o5_req_kg_per_ha=p2o5_ha,
                net_p2o5_kg_per_ha=p2o5_ha,
                k2o_req_kg_per_ha=k2o_ha,
                net_k2o_kg_per_ha=k2o_ha,
                n_req_kg_per_acre=n_acre,
                p2o5_req_kg_per_acre=p2o5_acre,
                k2o_req_kg_per_acre=k2o_acre,
                farm_area_hectares=farm_area_ha,
                farm_area_original=farm_area,
                farm_area_unit_original=farm_area_unit,
                total_n_req_kg=total_n,
                total_farm_n_kg=total_n,
                total_p2o5_req_kg=total_p2o5,
                total_farm_p2o5_kg=total_p2o5,
                total_k2o_req_kg=total_k2o,
                total_farm_k2o_kg=total_k2o,
                calculation_method="Copied from Official Soil Health Card",
                calculation_details={
                    "source": "Uploaded Soil Health Card",
                    "printed_rates": {
                        "N": n_acre,
                        "P2O5": p2o5_acre,
                        "K2O": k2o_acre,
                        "unit": "kg/acre"
                    },
                    "converted_per_ha_rates": {
                        "N": n_ha,
                        "P2O5": p2o5_ha,
                        "K2O": k2o_ha,
                        "unit": "kg/ha"
                    },
                    "farm_area": farm_area,
                    "farm_area_unit": farm_area_unit,
                    "farm_totals_kg": {
                        "N": total_n,
                        "P2O5": total_p2o5,
                        "K2O": total_k2o
                    }
                },
                units={
                    "per_ha": "kg/ha",
                    "per_acre": "kg/acre",
                    "total": "kg",
                    "area": farm_area_unit
                },
                source_title=req.printed_source or "Uploaded Soil Health Card",
                derivation_explanation=f"Copied directly from the printed fertilizer recommendation section of the farmer's uploaded Soil Health Card ({n_acre:.1f} N, {p2o5_acre:.1f} P₂O₅, {k2o_acre:.1f} K₂O {rate_unit}) and scaled accurately to your confirmed farm area ({farm_area} {farm_area_unit}).",
                authoritative_reference={
                    "title": req.printed_source or "Uploaded Soil Health Card",
                    "verification_status": "SOIL_HEALTH_CARD_PRINTED",
                    "source": "Report Printed Recommendation Table"
                },
                warnings=[]
            )

        # =====================================================================
        # MODE 2: Calculated Agronomic Recommendation
        # =====================================================================

        # 1. Resolve Phase 4 Rule
        rule = None
        phase4_resp = None

        if req.phase4_result:
            p4_status = req.phase4_result.get("status")
            if p4_status in ("UNSUPPORTED_CROP", "UNSUPPORTED_SOIL_SERIES", "NO_MATCHING_RULE"):
                return NutrientCalculationResponse(
                    status=p4_status,
                    crop=req.crop or "",
                    farm_area_hectares=convert_area_to_hectares(req.farm_area or 1.0, req.farm_area_unit or "hectare"),
                    validation_errors=req.phase4_result.get("warnings") or [f"Rule selection failed with status {p4_status}."]
                )
            rule_id = req.phase4_result.get("selected_rule_id")
            if rule_id:
                for r in self.registry.get_all_rules():
                    if r["rule_id"] == rule_id:
                        rule = r
                        break

        if not rule and req.selected_rule_id:
            for r in self.registry.get_all_rules():
                if r["rule_id"] == req.selected_rule_id:
                    rule = r
                    break

        if not rule:
            if not req.crop:
                return NutrientCalculationResponse(
                    status=UNSUPPORTED_CROP,
                    validation_errors=["Either 'selected_rule_id' or 'crop' must be provided."]
                )

            p4_req = RuleSelectionRequest(
                crop=req.crop,
                variety=None,
                district=None,
                soil_series=req.soil_series,
                season=req.season,
                irrigation_method=req.irrigation_method,
                target_yield=req.target_yield,
                recommendation_type=req.recommendation_type,
                soil_values={
                    "nitrogen": req.soil_nitrogen,
                    "phosphorus": req.soil_phosphorus,
                    "potassium": req.soil_potassium,
                    "phosphorus_method": req.soil_phosphorus_method
                } if req.soil_nitrogen is not None or req.soil_phosphorus is not None else None
            )
            phase4_resp = self.rule_selection_service.select_rule(p4_req)

            if phase4_resp.status == "UNSUPPORTED_CROP":
                return NutrientCalculationResponse(
                    status=UNSUPPORTED_CROP,
                    crop=req.crop,
                    warnings=phase4_resp.warnings
                )

            if phase4_resp.status in ("NEEDS_MORE_INPUT", "UNSUPPORTED_SOIL_SERIES", "NO_MATCHING_RULE"):
                return NutrientCalculationResponse(
                    status=MISSING_INPUTS if phase4_resp.status == "NEEDS_MORE_INPUT" else VALIDATION_ERROR,
                    crop=req.crop,
                    selected_rule_id=phase4_resp.selected_rule_id,
                    missing_inputs=phase4_resp.missing_inputs,
                    warnings=phase4_resp.warnings
                )

            if phase4_resp.status in ("PENDING_VERIFICATION", "PENDING_AGRONOMIC_VALIDATION", "SOURCE_NOT_VERIFIED"):
                if not req.allow_unverified:
                    return NutrientCalculationResponse(
                        status=UNVERIFIED_RULE,
                        crop=req.crop,
                        selected_rule_id=phase4_resp.selected_rule_id,
                        recommendation_type="PROVISIONAL_UNVERIFIED",
                        verification_status=phase4_resp.verification_status,
                        is_verified_rule=False,
                        is_provisional=True,
                        warnings=phase4_resp.warnings + ["This rule has not yet been agronomically validated. A confirmed soil-specific recommendation is unavailable."],
                        validation_errors=[f"Rule '{phase4_resp.selected_rule_id}' has not yet been agronomically validated. A confirmed soil-specific recommendation is unavailable."]
                    )

            rule_id = phase4_resp.selected_rule_id
            for r in self.registry.get_all_rules():
                if r["rule_id"] == rule_id:
                    rule = r
                    break

        if not rule:
            return NutrientCalculationResponse(
                status=CALCULATION_FAILED,
                crop=req.crop,
                validation_errors=["Could not locate selected agronomic rule in registry."]
            )

        # Check Crop Compatibility with selected rule
        if req.crop and rule.get("crop") and req.crop.strip().lower() != rule["crop"].strip().lower():
            return NutrientCalculationResponse(
                status=INVALID_RULE_FOR_CROP,
                crop=req.crop,
                selected_rule_id=rule["rule_id"],
                validation_errors=[
                    f"Selected rule '{rule['rule_id']}' is for crop '{rule['crop']}', but requested crop is '{req.crop}'."
                ]
            )

        # 2. Check Rule Verification Status
        v_status = rule.get("verification_status", "PENDING_VERIFICATION")
        is_verified = (v_status == "VERIFIED")

        if not is_verified and not req.allow_unverified:
            return NutrientCalculationResponse(
                status=UNVERIFIED_RULE,
                crop=rule["crop"],
                selected_rule_id=rule["rule_id"],
                selected_method=rule.get("recommendation_method"),
                recommendation_type="PROVISIONAL_UNVERIFIED",
                verification_status=v_status,
                is_verified_rule=False,
                is_provisional=True,
                warnings=[
                    f"Rule '{rule['rule_id']}' is marked as '{v_status}' and cannot be used for production NPK calculations.",
                    "This rule has not yet been agronomically validated. A confirmed soil-specific recommendation is unavailable."
                ],
                validation_errors=[f"Rule '{rule['rule_id']}' has not yet been agronomically validated. A confirmed soil-specific recommendation is unavailable."]
            )

        # 3. Extract and Validate Input Values and Units
        crop_name = rule["crop"]
        rec_method = rule["recommendation_method"]

        # Validate Soil Phosphorus Method
        p_method = req.soil_phosphorus_method or "Olsen"
        if p_method not in ("Olsen", "Bray"):
            validation_errors.append(f"Invalid phosphorus test method '{p_method}'. Must be 'Olsen' or 'Bray'.")

        # Normalize Soil Test Values
        sn, sp, sk = None, None, None
        try:
            if req.soil_nitrogen is not None:
                sn = normalize_soil_nutrient_value(req.soil_nitrogen, req.soil_nitrogen_unit or "kg/ha")
            else:
                missing_inputs.append("soil_nitrogen")
        except ValueError as e:
            validation_errors.append(str(e))

        try:
            if req.soil_phosphorus is not None:
                p_unit = (req.soil_phosphorus_unit or "kg/ha").strip().lower()
                is_p2o5 = "p2o5" in p_unit
                clean_unit = p_unit.replace("_p2o5", "").replace("p2o5", "").strip() or "kg/ha"
                sp_raw = normalize_soil_nutrient_value(req.soil_phosphorus, clean_unit)
                sp = round(convert_oxide_to_elemental(sp_raw, "P"), 4) if is_p2o5 else sp_raw
            else:
                missing_inputs.append("soil_phosphorus")
        except ValueError as e:
            validation_errors.append(str(e))

        try:
            if req.soil_potassium is not None:
                k_unit = (req.soil_potassium_unit or "kg/ha").strip().lower()
                is_k2o = "k2o" in k_unit
                clean_unit = k_unit.replace("_k2o", "").replace("k2o", "").strip() or "kg/ha"
                sk_raw = normalize_soil_nutrient_value(req.soil_potassium, clean_unit)
                sk = round(convert_oxide_to_elemental(sk_raw, "K"), 4) if is_k2o else sk_raw
            else:
                missing_inputs.append("soil_potassium")
        except ValueError as e:
            validation_errors.append(str(e))

        # Check STCR specific required inputs
        target_yield = None
        if req.target_yield is not None:
            try:
                target_yield = convert_target_yield_to_tonnes_per_ha(req.target_yield, req.target_yield_unit or "t/ha")
            except ValueError as e:
                validation_errors.append(str(e))

        target_range = rule.get("target_yield_range")

        if rec_method.startswith("STCR"):
            if target_yield is None:
                if "target_yield" not in missing_inputs:
                    missing_inputs.append("target_yield")
            elif target_range:
                min_y, max_y = target_range.get("min"), target_range.get("max")
                if min_y is not None and target_yield < min_y:
                    validation_errors.append(f"Target yield {target_yield:.2f} t/ha is below documented range ({min_y}-{max_y} t/ha).")
                if max_y is not None and target_yield > max_y:
                    validation_errors.append(f"Target yield {target_yield:.2f} t/ha exceeds documented range ({min_y}-{max_y} t/ha).")

        # Validate Farm Area if provided
        farm_area_ha = None
        farm_area_val = None
        farm_area_unit_str = req.farm_area_unit or "hectare"
        if req.farm_area is not None:
            try:
                farm_area_val = float(req.farm_area)
                farm_area_ha = convert_area_to_hectares(farm_area_val, farm_area_unit_str)
            except ValueError as e:
                validation_errors.append(str(e))

        if validation_errors:
            return NutrientCalculationResponse(
                status=VALIDATION_ERROR,
                crop=crop_name,
                selected_rule_id=rule["rule_id"],
                verification_status=v_status,
                is_verified_rule=is_verified,
                validation_errors=validation_errors
            )

        if missing_inputs:
            return NutrientCalculationResponse(
                status=MISSING_INPUTS,
                crop=crop_name,
                selected_rule_id=rule["rule_id"],
                verification_status=v_status,
                is_verified_rule=is_verified,
                missing_inputs=missing_inputs
            )

        # 4. Perform Calculation based on Recommendation Method
        n_req, p2o5_req, k2o_req = 0.0, 0.0, 0.0
        calc_details: Dict[str, Any] = {
            "method": rec_method,
            "rule_id": rule["rule_id"],
            "verification_status": v_status,
        }

        if rec_method.startswith("STCR"):
            stcr_coeffs = rule.get("stcr_coefficients")
            if not stcr_coeffs or not all(k in stcr_coeffs for k in ("N", "P2O5", "K2O")):
                return NutrientCalculationResponse(
                    status=CALCULATION_FAILED,
                    crop=crop_name,
                    selected_rule_id=rule["rule_id"],
                    validation_errors=["STCR coefficients are missing or incomplete in rule definition."]
                )

            # N, P2O5, K2O calculation with FYM scaling
            fym_applied = float(req.fym_applied_t_per_ha) if req.fym_applied_t_per_ha is not None else 12.5
            fym_factor = max(0.0, fym_applied / 12.5) if 12.5 > 0 else 1.0

            n_c = stcr_coeffs["N"]
            fym_credit_n = round(n_c.get("c_fym", 0.0) * min(1.0, fym_factor), 2)
            raw_n = n_c["a"] * target_yield - n_c["b_soil"] * sn - fym_credit_n
            n_req = round(max(0.0, raw_n), 2)

            p_c = stcr_coeffs["P2O5"]
            fym_credit_p = round(p_c.get("c_fym", 0.0) * min(1.0, fym_factor), 2)
            raw_p = p_c["a"] * target_yield - p_c["b_soil"] * sp - fym_credit_p
            p2o5_req = round(max(0.0, raw_p), 2)

            k_c = stcr_coeffs["K2O"]
            fym_credit_k = round(k_c.get("c_fym", 0.0) * min(1.0, fym_factor), 2)
            raw_k = k_c["a"] * target_yield - k_c["b_soil"] * sk - fym_credit_k
            k2o_req = round(max(0.0, raw_k), 2)

            clamping_notes: List[str] = []
            if raw_n < 0:
                note = f"Calculated Nitrogen requirement was negative ({raw_n:.2f} kg/ha) because initial soil Nitrogen test level or FYM contribution satisfies target yield requirement. Clamped to 0.0 kg/ha (maintenance dose / no additional chemical N needed per TNAU STCR principles)."
                clamping_notes.append(note)
                warnings.append(note)
            if raw_p < 0:
                note = f"Calculated Phosphorus requirement was negative ({raw_p:.2f} kg/ha) because initial soil Phosphorus test level or FYM contribution satisfies target yield requirement. Clamped to 0.0 kg/ha (maintenance dose / no additional chemical P2O5 needed per TNAU STCR principles)."
                clamping_notes.append(note)
                warnings.append(note)
            if raw_k < 0:
                note = f"Calculated Potassium requirement was negative ({raw_k:.2f} kg/ha) because initial soil Potassium test level or FYM contribution satisfies target yield requirement. Clamped to 0.0 kg/ha (maintenance dose / no additional chemical K2O needed per TNAU STCR principles)."
                clamping_notes.append(note)
                warnings.append(note)

            calc_details.update({
                "formula_N": f"{n_c['a']} * T - {n_c['b_soil']} * SN - {fym_credit_n}",
                "formula_P2O5": f"{p_c['a']} * T - {p_c['b_soil']} * SP - {fym_credit_p}",
                "formula_K2O": f"{k_c['a']} * T - {k_c['b_soil']} * SK - {fym_credit_k}",
                "fym_applied_t_per_ha": fym_applied,
                "fym_credit_kg_per_ha": {"N": fym_credit_n, "P2O5": fym_credit_p, "K2O": fym_credit_k},
                "raw_calculated_rates_kg_per_ha": {
                    "N": round(raw_n, 2),
                    "P2O5": round(raw_p, 2),
                    "K2O": round(raw_k, 2),
                },
                "clamping_notes": clamping_notes,
                "inputs_used": {
                    "target_yield": target_yield,
                    "soil_N_kg_per_ha": sn,
                    "soil_P_kg_per_ha": sp,
                    "soil_K_kg_per_ha": sk,
                    "phosphorus_method": p_method,
                    "fym_applied_t_per_ha": fym_applied
                }
            })

        elif rec_method in ("TNAU-SOIL-TEST", "TNAU-BLANKET"):
            blanket_rdf = rule.get("blanket_rdf_kg_per_ha", {"N": 150.0, "P2O5": 50.0, "K2O": 50.0})
            adj_factors = rule.get("rating_adjustment_factors", {"low": 1.25, "medium": 1.00, "high": 0.75})

            n_class = classify("nitrogen", sn, "kg/ha")
            p_class = classify("phosphorus", sp, "kg/ha", p_method)
            k_class = classify("potassium", sk, "kg/ha")

            factor_n = adj_factors.get(n_class.lower(), 1.00)
            factor_p = adj_factors.get(p_class.lower(), 1.00)
            factor_k = adj_factors.get(k_class.lower(), 1.00)

            n_req = round(max(0.0, blanket_rdf["N"] * factor_n), 2)
            p2o5_req = round(max(0.0, blanket_rdf["P2O5"] * factor_p), 2)
            k2o_req = round(max(0.0, blanket_rdf["K2O"] * factor_k), 2)

            calc_details.update({
                "blanket_rdf": blanket_rdf,
                "soil_ratings": {
                    "nitrogen": {"value": sn, "status": n_class, "multiplier": factor_n},
                    "phosphorus": {"value": sp, "status": p_class, "multiplier": factor_p, "method": p_method},
                    "potassium": {"value": sk, "status": k_class, "multiplier": factor_k}
                }
            })

        else:
            return NutrientCalculationResponse(
                status=CALCULATION_FAILED,
                crop=crop_name,
                selected_rule_id=rule["rule_id"],
                validation_errors=[f"Unsupported recommendation method '{rec_method}'."]
            )

        # 5. Farm Area Total Calculations (Centralized & without double conversion)
        total_n, total_p2o5, total_k2o = None, None, None
        if farm_area_val is not None:
            total_n = round(calculate_farm_total_nutrient(n_req, "kg/ha", farm_area_val, farm_area_unit_str), 2)
            total_p2o5 = round(calculate_farm_total_nutrient(p2o5_req, "kg/ha", farm_area_val, farm_area_unit_str), 2)
            total_k2o = round(calculate_farm_total_nutrient(k2o_req, "kg/ha", farm_area_val, farm_area_unit_str), 2)

        n_req_acre = round(convert_kg_per_ha_to_kg_per_acre(n_req), 2)
        p2o5_req_acre = round(convert_kg_per_ha_to_kg_per_acre(p2o5_req), 2)
        k2o_req_acre = round(convert_kg_per_ha_to_kg_per_acre(k2o_req), 2)

        resp_status = CALCULATION_SUCCESS if is_verified else PENDING_AGRONOMIC_VALIDATION
        rec_type = rule.get("recommendation_type") or ("GENERAL_BLANKET" if rule.get("recommendation_method") in ("TNAU-BLANKET", "TNAU-SOIL-TEST") else "SOIL_SPECIFIC_STCR")
        if not is_verified:
            rec_type = "PROVISIONAL_UNVERIFIED"
            warnings.append(f"Rule '{rule['rule_id']}' is marked as '{v_status}' (not an authoritative STCR calibration).")
            warnings.append("This rule has not yet been agronomically validated. A confirmed soil-specific recommendation is unavailable.")

        # Soil nutrient status and interpretation against verified TNAU thresholds
        n_class = classify("nitrogen", sn, "kg/ha") or "Unknown"
        p_class = classify("phosphorus", sp, "kg/ha", p_method) or "Unknown"
        k_class = classify("potassium", sk, "kg/ha") or "Unknown"

        soil_nutrient_status = {
            "nitrogen": {
                "value": req.soil_nitrogen,
                "unit": req.soil_nitrogen_unit or "kg/ha",
                "value_kg_per_ha": sn,
                "status": "Deficient" if n_class == "Low" else ("Sufficient" if n_class == "Medium" else "Excessive"),
                "rating": n_class,
                "interpretation_threshold": "Low < 280 kg/ha, Medium 280-450 kg/ha, High > 450 kg/ha (TNAU)"
            },
            "phosphorus": {
                "value": req.soil_phosphorus,
                "unit": req.soil_phosphorus_unit or "kg/ha",
                "value_kg_per_ha": sp,
                "method": p_method,
                "status": "Deficient" if p_class == "Low" else ("Sufficient" if p_class == "Medium" else "Excessive"),
                "rating": p_class,
                "interpretation_threshold": "Olsen: Low < 11 kg/ha, Medium 11-22 kg/ha, High > 22 kg/ha (TNAU)" if p_method == "Olsen" else "Bray: Low < 24.2 kg/ha, Medium 24.2-49.7 kg/ha, High > 49.7 kg/ha (TNAU)"
            },
            "potassium": {
                "value": req.soil_potassium,
                "unit": req.soil_potassium_unit or "kg/ha",
                "value_kg_per_ha": sk,
                "status": "Excessive" if k_class == "High" else ("Sufficient" if k_class == "Medium" else "Deficient"),
                "rating": k_class,
                "interpretation_threshold": "Low < 118 kg/ha, Medium 118-280 kg/ha, High > 280 kg/ha (TNAU)"
            }
        }
        if req.organic_carbon is not None:
            try:
                oc_val = float(req.organic_carbon)
                oc_class = classify("organic_carbon", oc_val, "%")
                soil_nutrient_status["organic_carbon"] = {
                    "value": oc_val,
                    "unit": "%",
                    "status": "Deficient" if oc_class == "Low" else ("Sufficient" if oc_class == "Medium" else "High"),
                    "rating": oc_class,
                    "interpretation_threshold": "Low < 0.50 %, Medium 0.50-0.75 %, High > 0.75 % (TNAU)"
                }
            except Exception:
                pass
        if req.ph is not None:
            try:
                ph_val = float(req.ph)
                ph_status = "Acidic" if ph_val < 6.5 else ("Alkaline / Calcareous" if ph_val > 7.8 else "Neutral")
                soil_nutrient_status["ph"] = {
                    "value": ph_val,
                    "unit": None,
                    "status": ph_status,
                    "rating": ph_status,
                    "interpretation_threshold": "Acidic < 6.5, Neutral 6.5-7.8, Alkaline > 7.8"
                }
            except Exception:
                pass
        if req.ec is not None:
            try:
                ec_val = float(req.ec)
                ec_status = "Critical (Saline)" if ec_val >= 1.0 else "Normal (Non-saline)"
                soil_nutrient_status["ec"] = {
                    "value": ec_val,
                    "unit": "dS/m",
                    "status": ec_status,
                    "rating": ec_status,
                    "interpretation_threshold": "Normal < 1.0 dS/m, Saline >= 1.0 dS/m"
                }
            except Exception:
                pass

        if rec_method.startswith("STCR"):
            soil_series_name = rule.get("soil_series", ["designated"])[0] if rule.get("soil_series") else "designated"
            derivation_explanation = (
                f"Calculated using authoritative TNAU STCR-IPNS targeted yield calibration for {crop_name} "
                f"on {soil_series_name} soil series at target yield {target_yield:.1f} t/ha. "
                f"Formulas: FN = {n_c['a']}×T - {n_c['b_soil']}×SN - {fym_credit_n:.1f}; "
                f"FP₂O₅ = {p_c['a']}×T - {p_c['b_soil']}×SP - {fym_credit_p:.1f}; "
                f"FK₂O = {k_c['a']}×T - {k_c['b_soil']}×SK - {fym_credit_k:.1f}. "
                f"Initial soil test values ({sn:.1f} N, {sp:.1f} P, {sk:.1f} K kg/ha) and organic manure ({fym_applied:.1f} t/ha FYM) "
                f"are deducted from crop uptake to compute the net chemical fertilizer requirement."
            )
        elif rec_method in ("TNAU-SOIL-TEST", "TNAU-BLANKET"):
            derivation_explanation = (
                f"Calculated from official TNAU Crop Production Guide 2020 blanket schedule ({blanket_rdf['N']}:{blanket_rdf['P2O5']}:{blanket_rdf['K2O']} kg/ha) "
                f"adjusted by laboratory soil test ratings: Nitrogen is {n_class} (×{factor_n:.2f}), "
                f"Phosphorus is {p_class} (×{factor_p:.2f}), Potassium is {k_class} (×{factor_k:.2f})."
            )
        else:
            derivation_explanation = f"Calculated using verified TNAU agronomic rule {rule['rule_id']}."

        authoritative_reference = {
            "title": rule.get("source_title", "TNAU Agronomic Guideline"),
            "url": rule.get("source_url"),
            "section_or_page": rule.get("source_page_or_section"),
            "equation_or_dose_reference": rule.get("equation_or_dose_reference"),
            "verification_status": v_status,
            "applicability_notes": rule.get("applicability_notes")
        }

        return NutrientCalculationResponse(
            status=resp_status,
            crop=crop_name,
            selected_rule_id=rule["rule_id"],
            selected_method=rec_method,
            calculation_method=rec_method,
            recommendation_mode="CALCULATED_AGRONOMIC",
            recommendation_type=rec_type,
            recommendation_source=rule.get("source_title", "TNAU Agronomic Guideline"),
            verification_status=v_status,
            is_verified_rule=is_verified,
            is_provisional=(not is_verified),
            n_req_kg_per_ha=n_req,
            net_n_kg_per_ha=n_req,
            p2o5_req_kg_per_ha=p2o5_req,
            net_p2o5_kg_per_ha=p2o5_req,
            k2o_req_kg_per_ha=k2o_req,
            net_k2o_kg_per_ha=k2o_req,
            n_req_kg_per_acre=n_req_acre,
            p2o5_req_kg_per_acre=p2o5_req_acre,
            k2o_req_kg_per_acre=k2o_req_acre,
            farm_area_hectares=farm_area_ha,
            farm_area_original=farm_area_val,
            farm_area_unit_original=farm_area_unit_str,
            total_n_req_kg=total_n,
            total_farm_n_kg=total_n,
            total_p2o5_req_kg=total_p2o5,
            total_farm_p2o5_kg=total_p2o5,
            total_k2o_req_kg=total_k2o,
            total_farm_k2o_kg=total_k2o,
            calculation_details=calc_details,
            units={
                "per_ha": "kg/ha",
                "per_acre": "kg/acre",
                "total": "kg",
                "area": farm_area_unit_str
            },
            source_title=rule.get("source_title"),
            source_url=rule.get("source_url"),
            source_page_or_section=rule.get("source_page_or_section"),
            soil_nutrient_status=soil_nutrient_status,
            derivation_explanation=derivation_explanation,
            authoritative_reference=authoritative_reference,
            warnings=warnings,
            missing_inputs=[],
            validation_errors=[]
        )


def calculate_nutrient_requirement(req: NutrientCalculationRequest) -> NutrientCalculationResponse:
    service = NutrientCalculationService()
    return service.calculate(req)
