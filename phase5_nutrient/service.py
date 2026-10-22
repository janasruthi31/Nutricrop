"""
Nutrient Requirement Calculation Engine Service (Phase 5).
Calculates exact N, P2O5, and K2O nutrient requirements using verified Phase 4 agronomic rules
OR copies and scales printed fertilizer recommendations from uploaded Soil Health Cards.
Does NOT calculate final fertilizer product quantities (Phase 6 responsibility).
"""

import json
import os
from typing import Any, Dict, List, Optional, Tuple
from agronomy.registry import AgronomicRuleRegistry
from agronomy.service import RuleSelectionService, RuleSelectionRequest
from phase3_soil.classification import classify
from .models import NutrientCalculationRequest, NutrientCalculationResponse, PreviousFertilizerItem
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
        self.crop_credits_data = self._load_previous_crop_credits()
        self.micronutrients_data = self._load_micronutrient_thresholds()

    def _load_previous_crop_credits(self) -> Dict[str, Any]:
        """Loads verified previous crop credits and fertilizer residual parameters."""
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "agronomy", "previous_crop_credits.json"))
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _load_micronutrient_thresholds(self) -> Dict[str, Any]:
        """Loads verified TNAU secondary and micronutrient thresholds (CPG 2020)."""
        path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "agronomy", "micronutrient_thresholds.json"))
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    @staticmethod
    def interpolate_soil_rating_multiplier(nutrient: str, value: Optional[float], method: str = "Olsen") -> float:
        """
        Interpolates soil-test rating multiplier continuously across TNAU rating bands.
        Replaces discrete step multipliers (1.25, 1.00, 0.75) so different soil values produce different doses.

        TNAU Rating Bands (CPG 2020 / phase3_soil/classification.py):
        - Nitrogen (kg/ha): Low < 280, Medium 280-450, High > 450
        - Phosphorus Olsen (kg/ha): Low < 11.0, Medium 11.0-22.0, High > 22.0
        - Phosphorus Bray (kg/ha): Low < 24.2, Medium 24.2-49.7, High > 49.7
        - Potassium (kg/ha): Low < 118, Medium 118-280, High > 280

        Multiplier curves:
        - Low: smoothly decreases from 1.30 down to 1.05 at low cutoff
        - Medium: smoothly decreases from 1.05 down to 0.95 at high cutoff (midpoint = 1.00)
        - High: smoothly decreases below 0.95 down to 0.50 floor for excessive soils
        """
        if value is None:
            return 1.0

        nut = nutrient.strip().lower()
        val = max(0.0, float(value))

        if nut in ("n", "nitrogen"):
            low_cut, high_cut = 280.0, 450.0
        elif nut in ("p", "phosphorus", "p2o5"):
            if method.strip().lower() == "bray":
                low_cut, high_cut = 24.2, 49.7
            else:
                low_cut, high_cut = 11.0, 22.0
        elif nut in ("k", "potassium", "k2o"):
            low_cut, high_cut = 118.0, 280.0
        else:
            return 1.0

        if val < low_cut:
            # Low band: 1.30 at val=0 down to 1.05 at val=low_cut
            return round(1.30 - (val / low_cut) * 0.25, 3)
        elif val <= high_cut:
            # Medium band: 1.05 at low_cut down to 0.95 at high_cut (centered at 1.00)
            frac = (val - low_cut) / (high_cut - low_cut)
            return round(1.05 - frac * 0.10, 3)
        else:
            # High band: 0.95 down to 0.50 floor
            excess = val - high_cut
            return round(max(0.50, 0.95 - (excess / high_cut) * 0.25), 3)

    def _evaluate_micronutrients(
        self,
        zinc: Optional[float],
        sulphur: Optional[float],
        boron: Optional[float],
    ) -> Dict[str, Any]:
        """
        Evaluates soil test Zinc, Sulphur, and Boron against verified TNAU critical limits:
        - Zinc: < 1.2 ppm (DTPA-Zn) -> 25 kg ZnSO4/ha (10 kg/acre)
        - Sulphur: < 10.0 ppm (CaCl2-S) -> 200 kg Gypsum/ha (80 kg/acre)
        - Boron: < 0.5 ppm (Hot Water B) -> 10 kg Borax/ha (4 kg/acre)
        """
        micros = self.micronutrients_data.get("micronutrients", {})
        advisory: Dict[str, Any] = {}

        if zinc is not None:
            z_spec = micros.get("zinc", {})
            crit = float(z_spec.get("critical_limit", 1.2))
            is_def = float(zinc) < crit
            rec = z_spec.get("recommendations", {}).get("deficient" if is_def else "sufficient", {})
            advisory["zinc"] = {
                "nutrient": "Zinc (Zn)",
                "value_ppm": float(zinc),
                "critical_limit_ppm": crit,
                "status": "Deficient" if is_def else "Sufficient",
                "is_deficient": is_def,
                "advisory": rec.get("advisory"),
                "product": rec.get("product"),
                "dose_kg_per_ha": rec.get("dose_kg_per_ha", 0.0),
                "dose_kg_per_acre": rec.get("dose_kg_per_acre", 0.0),
                "application_method": rec.get("application_method"),
                "caution": rec.get("caution"),
                "source": z_spec.get("interpretation", {}).get("citation", "TNAU CPG 2020 p. 18")
            }

        if sulphur is not None:
            s_spec = micros.get("sulphur", {})
            crit = float(s_spec.get("critical_limit", 10.0))
            is_def = float(sulphur) < crit
            rec = s_spec.get("recommendations", {}).get("deficient" if is_def else "sufficient", {})
            advisory["sulphur"] = {
                "nutrient": "Sulphur (S)",
                "value_ppm": float(sulphur),
                "critical_limit_ppm": crit,
                "status": "Deficient" if is_def else "Sufficient",
                "is_deficient": is_def,
                "advisory": rec.get("advisory"),
                "product": rec.get("product"),
                "dose_kg_per_ha": rec.get("dose_kg_per_ha", 0.0),
                "dose_kg_per_acre": rec.get("dose_kg_per_acre", 0.0),
                "application_method": rec.get("application_method"),
                "caution": rec.get("caution"),
                "source": s_spec.get("interpretation", {}).get("citation", "TNAU CPG 2020 p. 19")
            }

        if boron is not None:
            b_spec = micros.get("boron", {})
            crit = float(b_spec.get("critical_limit", 0.5))
            is_def = float(boron) < crit
            rec = b_spec.get("recommendations", {}).get("deficient" if is_def else "sufficient", {})
            advisory["boron"] = {
                "nutrient": "Boron (B)",
                "value_ppm": float(boron),
                "critical_limit_ppm": crit,
                "status": "Deficient" if is_def else "Sufficient",
                "is_deficient": is_def,
                "advisory": rec.get("advisory"),
                "product": rec.get("product"),
                "dose_kg_per_ha": rec.get("dose_kg_per_ha", 0.0),
                "dose_kg_per_acre": rec.get("dose_kg_per_acre", 0.0),
                "application_method": rec.get("application_method"),
                "caution": rec.get("caution"),
                "source": b_spec.get("interpretation", {}).get("citation", "TNAU CPG 2020 p. 20")
            }

        return advisory

    def _compare_with_blanket_dose(
        self,
        crop: str,
        calc_n_ha: float,
        calc_p2o5_ha: float,
        calc_k2o_ha: float,
    ) -> Tuple[Dict[str, Any], List[str]]:
        """
        Compares calculated STCR net dose with official TNAU blanket recommendation.
        Flags warnings if calculated dose deviates > 50% from the standard blanket dose.
        """
        blanket_benchmarks = {
            "rice": {"N": 150.0, "P2O5": 50.0, "K2O": 50.0, "citation": "TNAU CPG 2020 p. 28"},
            "groundnut": {"N": 25.0, "P2O5": 50.0, "K2O": 75.0, "citation": "TNAU CPG 2020 p. 112"},
            "blackgram": {"N": 25.0, "P2O5": 50.0, "K2O": 25.0, "citation": "TNAU CPG 2020 p. 64"},
            "sugarcane": {"N": 275.0, "P2O5": 62.5, "K2O": 112.5, "citation": "TNAU CPG 2020 p. 150"},
            "maize": {"N": 250.0, "P2O5": 75.0, "K2O": 75.0, "citation": "TNAU CPG 2020 p. 80"},
            "cotton (lint)": {"N": 80.0, "P2O5": 40.0, "K2O": 40.0, "citation": "TNAU CPG 2020 p. 132"},
            "cotton": {"N": 80.0, "P2O5": 40.0, "K2O": 40.0, "citation": "TNAU CPG 2020 p. 132"},
        }
        c_low = crop.strip().lower()
        b_data = None
        for k, v in blanket_benchmarks.items():
            if k == c_low or k in c_low or c_low in k:
                b_data = v
                break

        if not b_data:
            return {}, []

        warnings: List[str] = []
        comparison: Dict[str, Any] = {
            "crop": crop,
            "source": b_data.get("citation"),
            "nutrients": {}
        }
        nutrients = [("N", calc_n_ha), ("P2O5", calc_p2o5_ha), ("K2O", calc_k2o_ha)]
        for name, calc_val in nutrients:
            b_val = float(b_data.get(name, 0.0))
            diff = abs(calc_val - b_val)
            pct = round((diff / b_val * 100.0) if b_val > 0 else 0.0, 1)
            is_large_dev = pct > 50.0
            comparison["nutrients"][name] = {
                "blanket_rdf_kg_per_ha": b_val,
                "calculated_net_dose_kg_per_ha": calc_val,
                "difference_pct": pct,
                "deviates_over_50_pct": is_large_dev
            }
            if is_large_dev:
                warnings.append(
                    f"Calculated {name} recommendation ({calc_val:.1f} kg/ha) differs by {pct:.0f}% from standard TNAU blanket dose ({b_val:.1f} kg/ha). "
                    "Significant adjustment is due to soil test levels and targeted yield calibration."
                )

        return comparison, warnings

    def _get_previous_crop_credit(self, previous_crop: Optional[str]) -> Dict[str, float]:
        """Returns N, P2O5, K2O biological credit in kg/ha for the previous crop."""
        if not previous_crop or previous_crop.strip().lower() in ("none", "fallow", "none / fallow", "none/fallow"):
            return {"N": 0.0, "P2O5": 0.0, "K2O": 0.0}

        credits_map = self.crop_credits_data.get("previous_crop_credits", {})
        c_low = previous_crop.strip().lower()

        for k, v in credits_map.items():
            if k.lower() == c_low or k.lower() in c_low or c_low in k.lower():
                return {
                    "N": float(v.get("n_credit_kg_per_ha", 0.0)),
                    "P2O5": float(v.get("p2o5_credit_kg_per_ha", 0.0)),
                    "K2O": float(v.get("k2o_credit_kg_per_ha", 0.0)),
                }

        return {"N": 0.0, "P2O5": 0.0, "K2O": 0.0}

    def _calculate_previous_fertilizer_residual(
        self,
        previous_fertilizers: Optional[List[Any]],
        farm_area_ha: float
    ) -> Dict[str, float]:
        """
        Calculates residual P2O5 and K2O carryover in kg/ha from previously applied fertilizers.
        Soluble N leaves negligible carryover in tropical soils (0.0).
        """
        if not previous_fertilizers:
            return {"N": 0.0, "P2O5": 0.0, "K2O": 0.0}

        nutrients_catalog = self.crop_credits_data.get("fertilizer_nutrient_content", {
            "UREA": {"n_pct": 46.0, "p2o5_pct": 0.0, "k2o_pct": 0.0, "bag_size_kg": 45.0},
            "DAP": {"n_pct": 18.0, "p2o5_pct": 46.0, "k2o_pct": 0.0, "bag_size_kg": 50.0},
            "MOP": {"n_pct": 0.0, "p2o5_pct": 0.0, "k2o_pct": 60.0, "bag_size_kg": 50.0},
            "SSP": {"n_pct": 0.0, "p2o5_pct": 16.0, "k2o_pct": 0.0, "bag_size_kg": 50.0},
            "COMPLEX_20_20_0": {"n_pct": 20.0, "p2o5_pct": 20.0, "k2o_pct": 0.0, "bag_size_kg": 50.0},
            "COMPLEX_17_17_17": {"n_pct": 17.0, "p2o5_pct": 17.0, "k2o_pct": 17.0, "bag_size_kg": 50.0},
        })

        rule_params = self.crop_credits_data.get("previous_fertilizer_residual_rules", {})
        recent_thresh = float(rule_params.get("recent_threshold_months", 6.0))
        p_res_frac = float(rule_params.get("recent_p2o5_residual_fraction", 0.15))
        k_res_frac = float(rule_params.get("recent_k2o_residual_fraction", 0.10))

        tot_res_n = 0.0
        tot_res_p = 0.0
        tot_res_k = 0.0
        effective_ha = max(0.01, farm_area_ha or 1.0)

        for item in previous_fertilizers:
            if isinstance(item, dict):
                p_name = str(item.get("product") or item.get("fertilizer_product") or "").strip()
                qty = float(item.get("quantity") or 0.0)
                unit = str(item.get("unit") or "kg").strip().lower()
                months_ago = item.get("months_ago")
                if months_ago is not None:
                    try:
                        months_ago = float(months_ago)
                    except (ValueError, TypeError):
                        months_ago = None
            elif hasattr(item, "product"):
                p_name = str(item.product).strip()
                qty = float(item.quantity or 0.0)
                unit = str(item.unit or "kg").strip().lower()
                months_ago = float(item.months_ago) if item.months_ago is not None else None
            else:
                continue

            if qty <= 0:
                continue

            # Identify fertilizer product
            p_upper = p_name.upper()
            matched_key = None
            for cat_key in nutrients_catalog.keys():
                if cat_key in p_upper or p_upper in cat_key:
                    matched_key = cat_key
                    break
            if not matched_key:
                if "UREA" in p_upper:
                    matched_key = "UREA"
                elif "DAP" in p_upper or "DI-AMMONIUM" in p_upper:
                    matched_key = "DAP"
                elif "MOP" in p_upper or "POTASH" in p_upper:
                    matched_key = "MOP"
                elif "SSP" in p_upper or "SUPER PHOSPHATE" in p_upper:
                    matched_key = "SSP"
                elif "20:20" in p_upper or "20-20" in p_upper:
                    matched_key = "COMPLEX_20_20_0"
                elif "17:17" in p_upper or "17-17" in p_upper:
                    matched_key = "COMPLEX_17_17_17"

            if not matched_key or matched_key not in nutrients_catalog:
                # Missing or unrecognized product treated as 0 deduction per requirements
                continue

            entry = nutrients_catalog[matched_key]
            bag_size = float(entry.get("bag_size_kg", 50.0))

            # Normalize quantity to kg per hectare
            if "acre" in unit:
                rate_kg_ha = convert_kg_per_acre_to_kg_per_ha(qty)
            elif "ha" in unit:
                rate_kg_ha = qty
            elif "bag" in unit:
                rate_kg_ha = (qty * bag_size) / effective_ha
            elif "tonne" in unit or "ton" in unit:
                rate_kg_ha = (qty * 1000.0) / effective_ha
            else:  # plain 'kg' on the whole farm
                rate_kg_ha = qty / effective_ha

            applied_n = rate_kg_ha * (float(entry.get("n_pct", 0.0)) / 100.0)
            applied_p = rate_kg_ha * (float(entry.get("p2o5_pct", 0.0)) / 100.0)
            applied_k = rate_kg_ha * (float(entry.get("k2o_pct", 0.0)) / 100.0)

            # Apply residual fraction based on elapsed time (recent within threshold)
            if months_ago is None or months_ago <= recent_thresh:
                tot_res_n += 0.0  # Synthetic N leaves zero residual in tropical soils
                tot_res_p += applied_p * p_res_frac
                tot_res_k += applied_k * k_res_frac

        return {
            "N": round(tot_res_n, 2),
            "P2O5": round(tot_res_p, 2),
            "K2O": round(tot_res_k, 2),
        }

    def _compare_with_printed_card(
        self,
        printed_n: Optional[float],
        printed_p2o5: Optional[float],
        printed_k2o: Optional[float],
        printed_unit: str,
        calc_n_ha: float,
        calc_p2o5_ha: float,
        calc_k2o_ha: float,
        calc_n_acre: float,
        calc_p2o5_acre: float,
        calc_k2o_acre: float,
    ) -> Dict[str, Any]:
        """
        Compares calculated agronomic need with Soil Health Card printed dose.
        Flags differences > 30% with clear warnings. Explicitly notes unprinted nutrients.
        """
        use_acre = "acre" in printed_unit.lower()
        unit_str = "kg/acre" if use_acre else "kg/ha"
        comp: Dict[str, Any] = {
            "has_printed_card": True,
            "unit": unit_str,
            "comparison": {},
            "warnings": []
        }
        nutrients = [
            ("N", printed_n, calc_n_acre if use_acre else calc_n_ha),
            ("P2O5", printed_p2o5, calc_p2o5_acre if use_acre else calc_p2o5_ha),
            ("K2O", printed_k2o, calc_k2o_acre if use_acre else calc_k2o_ha),
        ]
        for name, p_val, c_val in nutrients:
            if p_val is None:
                comp["comparison"][name] = {
                    "printed": "not printed on card",
                    "calculated": c_val,
                    "difference_pct": None,
                    "status": "NOT_PRINTED"
                }
            else:
                p_float = float(p_val)
                diff = abs(c_val - p_float)
                diff_pct = round((diff / p_float * 100.0) if p_float > 0 else 0.0, 1)
                is_flagged = diff_pct > 30.0
                comp["comparison"][name] = {
                    "printed": p_float,
                    "calculated": c_val,
                    "difference_pct": diff_pct,
                    "status": "DIFFERENCE_FLAGGED" if is_flagged else "CONSISTENT"
                }
                if is_flagged:
                    comp["warnings"].append(
                        f"Soil Health Card prints {name} {p_float:.1f} {unit_str}; calculated need is {c_val:.1f} {unit_str} "
                        f"(differs by {diff_pct:.0f}%). Soil-test calculation accounts for your target yield, soil test level, and previous crop credits."
                    )
        return comp

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

            n_is_printed = req.printed_n_rate is not None
            p_is_printed = req.printed_p2o5_rate is not None
            k_is_printed = req.printed_k2o_rate is not None

            n_val = float(req.printed_n_rate) if n_is_printed else 0.0
            p_val = float(req.printed_p2o5_rate) if p_is_printed else 0.0
            k_val = float(req.printed_k2o_rate) if k_is_printed else 0.0
            rate_unit = req.printed_rate_unit or "kg/acre"

            if not n_is_printed:
                warnings.append("Nitrogen (N) recommendation was not printed on the Soil Health Card.")
            if not p_is_printed:
                warnings.append("Phosphorus (P₂O₅) recommendation was not printed on the Soil Health Card.")
            if not k_is_printed:
                warnings.append("Potassium (K₂O) recommendation was not printed on the Soil Health Card.")

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
                        "N": n_acre if n_is_printed else "not printed on card",
                        "P2O5": p2o5_acre if p_is_printed else "not printed on card",
                        "K2O": k2o_acre if k_is_printed else "not printed on card",
                        "unit": rate_unit
                    },
                    "printed_status": {
                        "N": "PRINTED" if n_is_printed else "NOT_PRINTED",
                        "P2O5": "PRINTED" if p_is_printed else "NOT_PRINTED",
                        "K2O": "PRINTED" if k_is_printed else "NOT_PRINTED"
                    },
                    "converted_per_ha_rates": {
                        "N": n_ha if n_is_printed else "not printed on card",
                        "P2O5": p2o5_ha if p_is_printed else "not printed on card",
                        "K2O": k2o_ha if k_is_printed else "not printed on card",
                        "unit": "kg/ha"
                    },
                    "farm_area": farm_area,
                    "farm_area_unit": farm_area_unit,
                    "farm_totals_kg": {
                        "N": total_n if n_is_printed else 0.0,
                        "P2O5": total_p2o5 if p_is_printed else 0.0,
                        "K2O": total_k2o if k_is_printed else 0.0
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
                confidence="lower",
                confidence_label="Copied from Soil Health Card",
                recommended_range_kg_per_ha={"N": [n_ha, n_ha], "P2O5": [p2o5_ha, p2o5_ha], "K2O": [k2o_ha, k2o_ha]},
                recommended_range_kg_per_acre={"N": [n_acre, n_acre], "P2O5": [p2o5_acre, p2o5_acre], "K2O": [k2o_acre, k2o_acre]},
                warnings=warnings
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
        v_status = rule.get("verification_status", "PROVISIONAL")
        is_verified = (v_status == "VERIFIED")

        # Explicitly unsupported or unconfirmed pending rules are blocked unless allow_unverified is set
        if v_status in ("UNSUPPORTED", "PENDING_VERIFICATION", "PENDING_AGRONOMIC_VALIDATION") and not req.allow_unverified:
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

        # Check if this is a "No Soil Test" mode calculation (Task 3d)
        has_soil_inputs = (req.soil_nitrogen is not None or req.soil_phosphorus is not None or req.soil_potassium is not None)
        is_no_soil_test = (
            getattr(req, "no_soil_test", False) or
            req.recommendation_type == "NO_SOIL_TEST" or
            (not has_soil_inputs and (req.recommendation_type == "GENERAL_BLANKET" or rec_method in ("TNAU-BLANKET", "TNAU-SOIL-TEST")))
        )

        # Normalize Soil Test Values
        sn, sp, sk = None, None, None
        if not is_no_soil_test:
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
        else:
            sn, sp, sk = 0.0, 0.0, 0.0

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
        # 4. Perform Calculation based on Recommendation Method
        n_req, p2o5_req, k2o_req = 0.0, 0.0, 0.0
        req_n, req_p, req_k = 0.0, 0.0, 0.0
        soil_supply_n, soil_supply_p, soil_supply_k = 0.0, 0.0, 0.0
        fym_credit_n, fym_credit_p, fym_credit_k = 0.0, 0.0, 0.0
        prev_crop_n, prev_crop_p, prev_crop_k = 0.0, 0.0, 0.0
        prev_fert_n, prev_fert_p, prev_fert_k = 0.0, 0.0, 0.0
        raw_n, raw_p, raw_k = 0.0, 0.0, 0.0
        clamping_notes: List[str] = []

        calc_details: Dict[str, Any] = {
            "method": rec_method,
            "rule_id": rule["rule_id"],
            "verification_status": v_status,
        }

        # Calculate Previous Crop Biological Credits
        prev_crop_credits = self._get_previous_crop_credit(req.previous_crop)
        prev_crop_n = prev_crop_credits["N"]
        prev_crop_p = prev_crop_credits["P2O5"]
        prev_crop_k = prev_crop_credits["K2O"]

        # Calculate Previous Fertilizer Residual Carryover
        prev_fert_residuals = self._calculate_previous_fertilizer_residual(req.previous_fertilizers, farm_area_ha or 1.0)
        prev_fert_n = prev_fert_residuals["N"]
        prev_fert_p = prev_fert_residuals["P2O5"]
        prev_fert_k = prev_fert_residuals["K2O"]

        fym_applied = float(req.fym_applied_t_per_ha) if req.fym_applied_t_per_ha is not None else 0.0

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
            # Default FYM to 0.0 unless farmer specifically applied it
            fym_factor = max(0.0, fym_applied / 12.5) if 12.5 > 0 else 0.0

            # Target yield scaling: if rule expects q/ha, scale 1 t/ha = 10 q/ha
            rule_t_unit = (stcr_coeffs.get("target_yield_unit") or "t/ha").strip().lower()
            t_calc = target_yield * 10.0 if rule_t_unit in ("q/ha", "quintal/ha", "q") else target_yield

            n_c = stcr_coeffs["N"]
            req_n = round(n_c["a"] * t_calc, 2)
            soil_supply_n = round(n_c["b_soil"] * sn, 2)
            fym_credit_n = round(n_c.get("c_fym", 0.0) * min(1.0, fym_factor), 2)
            raw_n = req_n - soil_supply_n - fym_credit_n - prev_crop_n - prev_fert_n
            n_req = round(max(0.0, raw_n), 2)

            p_c = stcr_coeffs["P2O5"]
            req_p = round(p_c["a"] * t_calc, 2)
            soil_supply_p = round(p_c["b_soil"] * sp, 2)
            fym_credit_p = round(p_c.get("c_fym", 0.0) * min(1.0, fym_factor), 2)
            raw_p = req_p - soil_supply_p - fym_credit_p - prev_crop_p - prev_fert_p
            p2o5_req = round(max(0.0, raw_p), 2)

            k_c = stcr_coeffs["K2O"]
            req_k = round(k_c["a"] * t_calc, 2)
            soil_supply_k = round(k_c["b_soil"] * sk, 2)
            fym_credit_k = round(k_c.get("c_fym", 0.0) * min(1.0, fym_factor), 2)
            raw_k = req_k - soil_supply_k - fym_credit_k - prev_crop_k - prev_fert_k
            k2o_req = round(max(0.0, raw_k), 2)

            if raw_n < 0:
                note = f"Calculated Nitrogen requirement was negative ({raw_n:.2f} kg/ha) because initial soil test level ({sn:.1f} kg/ha), FYM ({fym_applied:.1f} t/ha), or previous credits satisfy target yield demand. Clamped to 0.0 kg/ha."
                clamping_notes.append(note)
                warnings.append(note)
            if raw_p < 0:
                note = f"Calculated Phosphorus requirement was negative ({raw_p:.2f} kg/ha) because initial soil test level ({sp:.1f} kg/ha), FYM, or previous credits satisfy target yield demand. Clamped to 0.0 kg/ha."
                clamping_notes.append(note)
                warnings.append(note)
            if raw_k < 0:
                note = f"Calculated Potassium requirement was negative ({raw_k:.2f} kg/ha) because initial soil test level ({sk:.1f} kg/ha), FYM, or previous credits satisfy target yield demand. Clamped to 0.0 kg/ha."
                clamping_notes.append(note)
                warnings.append(note)

            calc_details.update({
                "formula_N": f"{n_c['a']} * T - {n_c['b_soil']} * SN - {fym_credit_n} - {prev_crop_n} - {prev_fert_n}",
                "formula_P2O5": f"{p_c['a']} * T - {p_c['b_soil']} * SP - {fym_credit_p} - {prev_crop_p} - {prev_fert_p}",
                "formula_K2O": f"{k_c['a']} * T - {k_c['b_soil']} * SK - {fym_credit_k} - {prev_crop_k} - {prev_fert_k}",
                "target_yield_used": t_calc,
                "target_yield_unit_used": rule_t_unit,
                "fym_applied_t_per_ha": fym_applied,
                "fym_credit_kg_per_ha": {"N": fym_credit_n, "P2O5": fym_credit_p, "K2O": fym_credit_k},
                "previous_crop_credit_kg_per_ha": {"N": prev_crop_n, "P2O5": prev_crop_p, "K2O": prev_crop_k},
                "previous_fertilizer_residual_kg_per_ha": {"N": prev_fert_n, "P2O5": prev_fert_p, "K2O": prev_fert_k},
                "raw_calculated_rates_kg_per_ha": {
                    "N": round(raw_n, 2),
                    "P2O5": round(raw_p, 2),
                    "K2O": round(raw_k, 2),
                },
                "clamping_notes": clamping_notes,
                "inputs_used": {
                    "target_yield": target_yield,
                    "target_yield_unit": req.target_yield_unit or "t/ha",
                    "soil_N_kg_per_ha": sn,
                    "soil_P_kg_per_ha": sp,
                    "soil_K_kg_per_ha": sk,
                    "phosphorus_method": p_method,
                    "fym_applied_t_per_ha": fym_applied,
                    "previous_crop": req.previous_crop
                }
            })

        elif rec_method in ("TNAU-SOIL-TEST", "TNAU-BLANKET") or is_no_soil_test:
            blanket_rdf = rule.get("blanket_rdf_kg_per_ha", {"N": 150.0, "P2O5": 50.0, "K2O": 50.0})

            if is_no_soil_test:
                n_class, p_class, k_class = "Not Tested", "Not Tested", "Not Tested"
                factor_n, factor_p, factor_k = 1.0, 1.0, 1.0
                warnings.append(
                    "No soil test provided. Recommending official TNAU blanket dose. "
                    "We strongly recommend testing your field soil at your nearest Agricultural Extension Center (AEC) "
                    "or Krishi Vigyan Kendra (KVK) for precise fertilizer savings."
                )
            else:
                n_class = classify("nitrogen", sn, "kg/ha")
                p_class = classify("phosphorus", sp, "kg/ha", p_method)
                k_class = classify("potassium", sk, "kg/ha")

                factor_n = self.interpolate_soil_rating_multiplier("nitrogen", sn, p_method)
                factor_p = self.interpolate_soil_rating_multiplier("phosphorus", sp, p_method)
                factor_k = self.interpolate_soil_rating_multiplier("potassium", sk, p_method)

            req_n = round(blanket_rdf["N"] * factor_n, 2)
            req_p = round(blanket_rdf["P2O5"] * factor_p, 2)
            req_k = round(blanket_rdf["K2O"] * factor_k, 2)

            soil_supply_n, soil_supply_p, soil_supply_k = 0.0, 0.0, 0.0

            # Sourced FYM replacement in blanket mode: 1.5 kg N, 1.0 kg P2O5, 1.5 kg K2O per tonne
            fym_credit_n = round(min(req_n * 0.25, fym_applied * 1.5), 2)
            fym_credit_p = round(min(req_p * 0.25, fym_applied * 1.0), 2)
            fym_credit_k = round(min(req_k * 0.25, fym_applied * 1.5), 2)

            raw_n = req_n - fym_credit_n - prev_crop_n - prev_fert_n
            n_req = round(max(0.0, raw_n), 2)

            raw_p = req_p - fym_credit_p - prev_crop_p - prev_fert_p
            p2o5_req = round(max(0.0, raw_p), 2)

            raw_k = req_k - fym_credit_k - prev_crop_k - prev_fert_k
            k2o_req = round(max(0.0, raw_k), 2)

            if raw_n < 0:
                clamping_notes.append("Nitrogen clamped to 0.0 kg/ha.")
            if raw_p < 0:
                clamping_notes.append("Phosphorus clamped to 0.0 kg/ha.")
            if raw_k < 0:
                clamping_notes.append("Potassium clamped to 0.0 kg/ha.")

            calc_details.update({
                "blanket_rdf": blanket_rdf,
                "soil_ratings": {
                    "nitrogen": {"value": sn, "status": n_class, "multiplier": factor_n},
                    "phosphorus": {"value": sp, "status": p_class, "multiplier": factor_p, "method": p_method},
                    "potassium": {"value": sk, "status": k_class, "multiplier": factor_k}
                },
                "fym_credit_kg_per_ha": {"N": fym_credit_n, "P2O5": fym_credit_p, "K2O": fym_credit_k},
                "previous_crop_credit_kg_per_ha": {"N": prev_crop_n, "P2O5": prev_crop_p, "K2O": prev_crop_k},
                "previous_fertilizer_residual_kg_per_ha": {"N": prev_fert_n, "P2O5": prev_fert_p, "K2O": prev_fert_k},
                "raw_calculated_rates_kg_per_ha": {
                    "N": round(raw_n, 2),
                    "P2O5": round(raw_p, 2),
                    "K2O": round(raw_k, 2),
                },
                "clamping_notes": clamping_notes
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

        resp_status = PENDING_AGRONOMIC_VALIDATION if v_status in ("PENDING_AGRONOMIC_VALIDATION", "PENDING_VERIFICATION") else CALCULATION_SUCCESS
        rec_type = rule.get("recommendation_type") or ("GENERAL_BLANKET" if rule.get("recommendation_method") in ("TNAU-BLANKET", "TNAU-SOIL-TEST") else "SOIL_SPECIFIC_STCR")
        if not is_verified:
            rec_type = "PROVISIONAL"
            warnings.append(f"Rule '{rule['rule_id']}' is marked as {v_status} pending TNAU/KVK verification.")
            warnings.append("Recommendation is advisory and subject to field verification.")

        # Soil nutrient status and interpretation against verified TNAU thresholds
        if is_no_soil_test:
            n_class, p_class, k_class = "Not Tested", "Not Tested", "Not Tested"
            soil_nutrient_status = {
                "nitrogen": {
                    "value": None,
                    "unit": "kg/ha",
                    "value_kg_per_ha": None,
                    "status": "Not Tested",
                    "rating": "Not Tested",
                    "interpretation_threshold": "Not tested - standard TNAU blanket dose applied"
                },
                "phosphorus": {
                    "value": None,
                    "unit": "kg/ha",
                    "value_kg_per_ha": None,
                    "method": p_method,
                    "status": "Not Tested",
                    "rating": "Not Tested",
                    "interpretation_threshold": "Not tested - standard TNAU blanket dose applied"
                },
                "potassium": {
                    "value": None,
                    "unit": "kg/ha",
                    "value_kg_per_ha": None,
                    "status": "Not Tested",
                    "rating": "Not Tested",
                    "interpretation_threshold": "Not tested - standard TNAU blanket dose applied"
                }
            }
        else:
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

        # Compare with printed card if printed rates were provided on request
        card_comparison = None
        if req.printed_n_rate is not None or req.printed_p2o5_rate is not None or req.printed_k2o_rate is not None:
            card_comparison = self._compare_with_printed_card(
                printed_n=req.printed_n_rate,
                printed_p2o5=req.printed_p2o5_rate,
                printed_k2o=req.printed_k2o_rate,
                printed_unit=req.printed_rate_unit or "kg/acre",
                calc_n_ha=n_req,
                calc_p2o5_ha=p2o5_req,
                calc_k2o_ha=k2o_req,
                calc_n_acre=n_req_acre,
                calc_p2o5_acre=p2o5_req_acre,
                calc_k2o_acre=k2o_req_acre,
            )
            calc_details["card_printed_comparison"] = card_comparison
            if card_comparison.get("warnings"):
                warnings.extend(card_comparison["warnings"])

        crop_requirement_kg_per_ha = {"n": req_n, "p2o5": req_p, "k2o": req_k}
        soil_supply_kg_per_ha = {"n": soil_supply_n, "p2o5": soil_supply_p, "k2o": soil_supply_k}
        fym_credit_kg_per_ha = {"n": fym_credit_n, "p2o5": fym_credit_p, "k2o": fym_credit_k}
        previous_crop_credit_kg_per_ha = {"n": prev_crop_n, "p2o5": prev_crop_p, "k2o": prev_crop_k}
        previous_fertilizer_residual_kg_per_ha = {"n": prev_fert_n, "p2o5": prev_fert_p, "k2o": prev_fert_k}

        nutrient_breakdown = {
            "nitrogen": {
                "nutrient": "Nitrogen (N)",
                "crop_requirement_kg_per_ha": req_n,
                "soil_supply_kg_per_ha": soil_supply_n,
                "fym_credit_kg_per_ha": fym_credit_n,
                "previous_crop_credit_kg_per_ha": prev_crop_n,
                "previous_crop_credit": prev_crop_n,
                "previous_fertilizer_residual_kg_per_ha": prev_fert_n,
                "previous_fertilizer_residual": prev_fert_n,
                "final_net_dose_kg_per_ha": n_req,
                "final_net_dose_kg_per_acre": n_req_acre,
                "total_farm_dose_kg": total_n,
                "clamped_at_zero": raw_n < 0
            },
            "phosphorus": {
                "nutrient": "Phosphorus (P₂O₅)",
                "crop_requirement_kg_per_ha": req_p,
                "soil_supply_kg_per_ha": soil_supply_p,
                "fym_credit_kg_per_ha": fym_credit_p,
                "previous_crop_credit_kg_per_ha": prev_crop_p,
                "previous_crop_credit": prev_crop_p,
                "previous_fertilizer_residual_kg_per_ha": prev_fert_p,
                "previous_fertilizer_residual": prev_fert_p,
                "final_net_dose_kg_per_ha": p2o5_req,
                "final_net_dose_kg_per_acre": p2o5_req_acre,
                "total_farm_dose_kg": total_p2o5,
                "clamped_at_zero": raw_p < 0
            },
            "potassium": {
                "nutrient": "Potassium (K₂O)",
                "crop_requirement_kg_per_ha": req_k,
                "soil_supply_kg_per_ha": soil_supply_k,
                "fym_credit_kg_per_ha": fym_credit_k,
                "previous_crop_credit_kg_per_ha": prev_crop_k,
                "previous_crop_credit": prev_crop_k,
                "previous_fertilizer_residual_kg_per_ha": prev_fert_k,
                "previous_fertilizer_residual": prev_fert_k,
                "final_net_dose_kg_per_ha": k2o_req,
                "final_net_dose_kg_per_acre": k2o_req_acre,
                "total_farm_dose_kg": total_k2o,
                "clamped_at_zero": raw_k < 0
            }
        }
        nutrient_breakdown["N"] = nutrient_breakdown["nitrogen"]
        nutrient_breakdown["P2O5"] = nutrient_breakdown["phosphorus"]
        nutrient_breakdown["K2O"] = nutrient_breakdown["potassium"]

        if is_no_soil_test:
            derivation_explanation = (
                f"Calculated using standard TNAU blanket recommendation for {crop_name} without soil test adjustment (multipliers = 1.00). "
                f"Deductions for organic manure ({fym_credit_n:.1f} N) and previous crop credits ({prev_crop_n:.1f} N) applied."
            )
        elif rec_method.startswith("STCR"):
            soil_series_name = rule.get("soil_series", ["designated"])[0] if rule.get("soil_series") else "designated"
            derivation_explanation = (
                f"Calculated using authoritative TNAU STCR-IPNS targeted yield calibration for {crop_name} "
                f"on {soil_series_name} soil series at target yield {target_yield:.1f} t/ha. "
                f"Formulas: FN = {n_c['a']}×T - {n_c['b_soil']}×SN - {fym_credit_n:.1f} - {prev_crop_n:.1f} - {prev_fert_n:.1f}; "
                f"FP₂O₅ = {p_c['a']}×T - {p_c['b_soil']}×SP - {fym_credit_p:.1f} - {prev_crop_p:.1f} - {prev_fert_p:.1f}; "
                f"FK₂O = {k_c['a']}×T - {k_c['b_soil']}×SK - {fym_credit_k:.1f} - {prev_crop_k:.1f} - {prev_fert_k:.1f}. "
                f"Initial soil test values ({sn:.1f} N, {sp:.1f} P, {sk:.1f} K kg/ha), organic manure ({fym_applied:.1f} t/ha FYM), "
                f"previous crop ({req.previous_crop or 'None'}), and fertilizer residuals are accounted for."
            )
        elif rec_method in ("TNAU-SOIL-TEST", "TNAU-BLANKET"):
            derivation_explanation = (
                f"Calculated from official TNAU Crop Production Guide 2020 blanket schedule ({blanket_rdf['N']}:{blanket_rdf['P2O5']}:{blanket_rdf['K2O']} kg/ha) "
                f"adjusted by laboratory soil test ratings: Nitrogen is {n_class} (×{factor_n:.2f}), "
                f"Phosphorus is {p_class} (×{factor_p:.2f}), Potassium is {k_class} (×{factor_k:.2f}). "
                f"Deductions for organic manure ({fym_credit_n:.1f} N) and previous crop credits ({prev_crop_n:.1f} N) applied."
            )
        else:
            derivation_explanation = f"Calculated using verified TNAU agronomic rule {rule['rule_id']}."

        # Micronutrient advisory evaluation (Task 2d)
        micronutrient_advisory = self._evaluate_micronutrients(req.zinc, req.sulphur, req.boron)
        if micronutrient_advisory:
            calc_details["micronutrient_advisory"] = micronutrient_advisory
            for m_key, m_info in micronutrient_advisory.items():
                soil_nutrient_status[m_key] = {
                    "value": m_info["value_ppm"],
                    "unit": "ppm",
                    "status": m_info["status"],
                    "rating": m_info["status"],
                    "interpretation_threshold": f"Critical limit {m_info['critical_limit_ppm']} ppm ({m_info['source']})",
                    "advisory": m_info["advisory"]
                }

        # Blanket dose comparison & >50% deviation warning (Task 2c)
        blanket_comparison, b_warnings = self._compare_with_blanket_dose(crop_name, n_req, p2o5_req, k2o_req)
        if blanket_comparison:
            calc_details["blanket_comparison"] = blanket_comparison
            if b_warnings:
                warnings.extend(b_warnings)

        # Spatial sampling note (Task 2c)
        spatial_sampling_note = "Recommendation is valid for this sample; sample several spots of the field for representative accuracy."
        if spatial_sampling_note not in warnings:
            warnings.append(spatial_sampling_note)

        # Recommended ranges (+/- 10%) (Task 2c)
        rec_range_ha = {
            "N": [round(max(0.0, n_req * 0.9), 1), round(n_req * 1.1, 1)],
            "P2O5": [round(max(0.0, p2o5_req * 0.9), 1), round(p2o5_req * 1.1, 1)],
            "K2O": [round(max(0.0, k2o_req * 0.9), 1), round(k2o_req * 1.1, 1)],
        }
        rec_range_acre = {
            "N": [round(max(0.0, n_req_acre * 0.9), 1), round(n_req_acre * 1.1, 1)],
            "P2O5": [round(max(0.0, p2o5_req_acre * 0.9), 1), round(p2o5_req_acre * 1.1, 1)],
            "K2O": [round(max(0.0, k2o_req_acre * 0.9), 1), round(k2o_req_acre * 1.1, 1)],
        }

        # Confidence level (Task 2a & 3d)
        is_blanket = is_no_soil_test or rec_type == "GENERAL_BLANKET" or rec_method in ("TNAU-BLANKET", "TNAU-SOIL-TEST")
        confidence_val = "lower" if is_blanket else "high"
        confidence_lbl = "General recommendation (lower confidence)" if is_blanket else "Soil-specific calibration (high confidence)"

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
            confidence=confidence_val,
            confidence_label=confidence_lbl,
            recommended_range_kg_per_ha=rec_range_ha,
            recommended_range_kg_per_acre=rec_range_acre,
            blanket_comparison=blanket_comparison,
            micronutrient_advisory=micronutrient_advisory,
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
            previous_crop=req.previous_crop,
            crop_requirement_kg_per_ha=crop_requirement_kg_per_ha,
            soil_supply_kg_per_ha=soil_supply_kg_per_ha,
            fym_credit_kg_per_ha=fym_credit_kg_per_ha,
            previous_crop_credit_kg_per_ha=previous_crop_credit_kg_per_ha,
            previous_fertilizer_residual_kg_per_ha=previous_fertilizer_residual_kg_per_ha,
            nutrient_breakdown=nutrient_breakdown,
            card_comparison=card_comparison,
            card_printed_comparison=card_comparison,
            warnings=warnings,
            missing_inputs=[],
            validation_errors=[]
        )


def calculate_nutrient_requirement(req: NutrientCalculationRequest) -> NutrientCalculationResponse:
    service = NutrientCalculationService()
    return service.calculate(req)

