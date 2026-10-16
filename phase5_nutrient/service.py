"""
Nutrient Requirement Calculation Engine Service (Phase 5).
Calculates exact N, P2O5, and K2O nutrient requirements using verified Phase 4 agronomic rules.
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
)

CALCULATION_SUCCESS = "CALCULATION_SUCCESS"
UNVERIFIED_RULE = "UNVERIFIED_RULE"
MISSING_INPUTS = "MISSING_INPUTS"
VALIDATION_ERROR = "VALIDATION_ERROR"
UNSUPPORTED_CROP = "UNSUPPORTED_CROP"
CALCULATION_FAILED = "CALCULATION_FAILED"


class NutrientCalculationService:
    def __init__(self, registry: Optional[AgronomicRuleRegistry] = None):
        self.registry = registry or AgronomicRuleRegistry()
        self.rule_selection_service = RuleSelectionService(self.registry)

    def calculate(self, req: NutrientCalculationRequest) -> NutrientCalculationResponse:
        validation_errors: List[str] = []
        missing_inputs: List[str] = []
        warnings: List[str] = []

        # 1. Resolve Phase 4 Rule
        rule = None
        phase4_resp = None

        if req.phase4_result:
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
            # Dynamically perform Phase 4 rule selection if not explicitly passed
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

            if phase4_resp.status == "PENDING_VERIFICATION":
                return NutrientCalculationResponse(
                    status=UNVERIFIED_RULE,
                    crop=req.crop,
                    selected_rule_id=phase4_resp.selected_rule_id,
                    warnings=phase4_resp.warnings
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

        # 2. Confirm VERIFIED status
        if rule.get("verification_status") != "VERIFIED":
            return NutrientCalculationResponse(
                status=UNVERIFIED_RULE,
                crop=rule["crop"],
                selected_rule_id=rule["rule_id"],
                warnings=[f"Rule '{rule['rule_id']}' is marked as '{rule.get('verification_status')}' and cannot be used for production NPK calculations."]
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
        if req.farm_area is not None:
            try:
                farm_area_ha = convert_area_to_hectares(req.farm_area, req.farm_area_unit or "hectare")
            except ValueError as e:
                validation_errors.append(str(e))

        if validation_errors:
            return NutrientCalculationResponse(
                status=VALIDATION_ERROR,
                crop=crop_name,
                selected_rule_id=rule["rule_id"],
                selected_method=rec_method,
                validation_errors=validation_errors
            )

        if missing_inputs:
            return NutrientCalculationResponse(
                status=MISSING_INPUTS,
                crop=crop_name,
                selected_rule_id=rule["rule_id"],
                selected_method=rec_method,
                missing_inputs=missing_inputs,
                warnings=[f"Missing mandatory inputs for rule calculation: {', '.join(missing_inputs)}"]
            )

        # 4. Perform Calculation
        n_req, p2o5_req, k2o_req = 0.0, 0.0, 0.0
        calc_details: Dict[str, Any] = {"method": rec_method}

        if rec_method.startswith("STCR"):
            stcr_coeffs = rule.get("stcr_coefficients")
            if not stcr_coeffs:
                return NutrientCalculationResponse(
                    status=CALCULATION_FAILED,
                    crop=crop_name,
                    selected_rule_id=rule["rule_id"],
                    validation_errors=["Rule is missing STCR equation coefficients."]
                )

            # N calculation
            n_c = stcr_coeffs["N"]
            raw_n = n_c["a"] * target_yield - n_c["b_soil"] * sn - n_c.get("c_fym", 0.0)
            n_req = round(max(0.0, raw_n), 2)

            # P2O5 calculation
            p_c = stcr_coeffs["P2O5"]
            raw_p = p_c["a"] * target_yield - p_c["b_soil"] * sp - p_c.get("c_fym", 0.0)
            p2o5_req = round(max(0.0, raw_p), 2)

            # K2O calculation
            k_c = stcr_coeffs["K2O"]
            raw_k = k_c["a"] * target_yield - k_c["b_soil"] * sk - k_c.get("c_fym", 0.0)
            k2o_req = round(max(0.0, raw_k), 2)

            calc_details.update({
                "formula_N": f"{n_c['a']} * T - {n_c['b_soil']} * SN - {n_c.get('c_fym', 0.0)}",
                "formula_P2O5": f"{p_c['a']} * T - {p_c['b_soil']} * SP - {p_c.get('c_fym', 0.0)}",
                "formula_K2O": f"{k_c['a']} * T - {k_c['b_soil']} * SK - {k_c.get('c_fym', 0.0)}",
                "inputs_used": {
                    "target_yield": target_yield,
                    "soil_N_kg_per_ha": sn,
                    "soil_P_kg_per_ha": sp,
                    "soil_K_kg_per_ha": sk,
                    "phosphorus_method": p_method
                }
            })

        elif rec_method == "TNAU-SOIL-TEST":
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

        # 5. Farm Area Total Calculations
        total_n, total_p2o5, total_k2o = None, None, None
        if farm_area_ha is not None:
            total_n = round(n_req * farm_area_ha, 2)
            total_p2o5 = round(p2o5_req * farm_area_ha, 2)
            total_k2o = round(k2o_req * farm_area_ha, 2)

        return NutrientCalculationResponse(
            status=CALCULATION_SUCCESS,
            crop=crop_name,
            selected_rule_id=rule["rule_id"],
            selected_method=rec_method,
            calculation_method=rec_method,
            n_req_kg_per_ha=n_req,
            net_n_kg_per_ha=n_req,
            p2o5_req_kg_per_ha=p2o5_req,
            net_p2o5_kg_per_ha=p2o5_req,
            k2o_req_kg_per_ha=k2o_req,
            net_k2o_kg_per_ha=k2o_req,
            farm_area_hectares=round(farm_area_ha, 4) if farm_area_ha is not None else None,
            total_n_req_kg=total_n,
            total_farm_n_kg=total_n,
            total_p2o5_req_kg=total_p2o5,
            total_farm_p2o5_kg=total_p2o5,
            total_k2o_req_kg=total_k2o,
            total_farm_k2o_kg=total_k2o,
            calculation_details=calc_details,
            units={
                "per_ha": "kg/ha",
                "total": "kg",
                "area": "hectare"
            },
            source_title=rule.get("source_title"),
            source_url=rule.get("source_url"),
            source_page_or_section=rule.get("source_page_or_section"),
            warnings=warnings,
            missing_inputs=[],
            validation_errors=[]
        )


def calculate_nutrient_requirement(req: NutrientCalculationRequest) -> NutrientCalculationResponse:
    service = NutrientCalculationService()
    return service.calculate(req)
