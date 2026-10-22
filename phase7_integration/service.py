"""
Master Pipeline Orchestrator Service (Phase 7).
Chains Phase 4 Rule Selection -> Phase 5 NPK Calculation -> Phase 6 LP Optimization -> Phase 2 Yield Model -> Phase 7 Weather Guidance.
Supports dual recommendation modes:
  1. 'SOIL_HEALTH_CARD': Copied directly from printed soil health card recommendations and scaled accurately.
  2. 'CALCULATED_AGRONOMIC': Computed from verified TNAU STCR / soil-test equations.
"""

from typing import Any, Dict, Optional
from agronomy.service import RuleSelectionService, RuleSelectionRequest
from phase5_nutrient.service import NutrientCalculationService, NutrientCalculationRequest
from phase6_fertilizer.service import FertilizerOptimizerService
from phase6_fertilizer.models import FertilizerOptimizationRequest, FertilizerOptimizationResponse
from phase7_integration.weather import get_weather_guidance
from predict_yield import predict_district_yield


class FullRecommendationService:
    def __init__(self):
        self.rule_service = RuleSelectionService()
        self.nutrient_service = NutrientCalculationService()
        self.fertilizer_service = FertilizerOptimizerService()

    def generate_full_recommendation(self, req: Dict[str, Any]) -> Dict[str, Any]:
        crop = req.get("crop", "Rice")
        district = req.get("district", "Thanjavur")
        soil_series = req.get("soil_series")
        season = req.get("season", "Kharif")
        irrigation = req.get("irrigation_method", "Irrigated")
        target_yield = req.get("target_yield", 6.0)

        # Support loading verified measurements from confirmed soil profile
        profile_id = req.get("soil_profile_id")
        soil_n = req.get("soil_nitrogen")
        soil_p = req.get("soil_phosphorus")
        soil_k = req.get("soil_potassium")
        p_method = req.get("soil_phosphorus_method", "Olsen")

        # Recommendation mode: 'SOIL_HEALTH_CARD' or 'CALCULATED_AGRONOMIC'
        rec_mode = req.get("recommendation_mode", "CALCULATED_AGRONOMIC")
        printed_n = req.get("printed_n_rate")
        printed_p = req.get("printed_p2o5_rate")
        printed_k = req.get("printed_k2o_rate")
        printed_unit = req.get("printed_rate_unit", "kg/acre")
        printed_source = req.get("printed_source", "Uploaded Soil Health Card")

        farm_area = req.get("farm_area")
        farm_area_unit = req.get("farm_area_unit")

        variety = req.get("variety")

        # Check if printed_recommendation passed directly or inside soil_profile
        prec_direct = req.get("printed_recommendation") or (req.get("soil_profile") or {}).get("printed_recommendation")
        if prec_direct and isinstance(prec_direct, dict):
            if printed_n is None:
                printed_n = prec_direct.get("n_kg_per_acre") or prec_direct.get("nitrogen_kg_per_acre") or prec_direct.get("n") or prec_direct.get("nitrogen")
            if printed_p is None:
                printed_p = prec_direct.get("p2o5_kg_per_acre") or prec_direct.get("p2o5") or prec_direct.get("phosphorus")
            if printed_k is None:
                printed_k = prec_direct.get("k2o_kg_per_acre") or prec_direct.get("k2o") or prec_direct.get("potassium")
            if not req.get("printed_rate_unit") and prec_direct.get("unit"):
                printed_unit = prec_direct.get("unit")
            if not req.get("printed_source") and prec_direct.get("source"):
                printed_source = prec_direct.get("source")

        # Units for soil nutrient status
        soil_n_unit = req.get("soil_nitrogen_unit")
        soil_p_unit = req.get("soil_phosphorus_unit")
        soil_k_unit = req.get("soil_potassium_unit")

        # Support extracting verified measurements directly from soil_profile dict if provided
        p_dict = req.get("soil_profile")
        if p_dict and isinstance(p_dict, dict):
            if not crop and p_dict.get("crop"):
                crop = p_dict.get("crop")
            if not district and p_dict.get("district"):
                district = p_dict.get("district")
            if soil_n is None and p_dict.get("nitrogen") is not None:
                soil_n = p_dict["nitrogen"].get("value") if isinstance(p_dict["nitrogen"], dict) else p_dict.get("nitrogen")
                if not soil_n_unit and isinstance(p_dict["nitrogen"], dict):
                    soil_n_unit = p_dict["nitrogen"].get("unit")
            if soil_p is None and p_dict.get("phosphorus") is not None:
                soil_p = p_dict["phosphorus"].get("value") if isinstance(p_dict["phosphorus"], dict) else p_dict.get("phosphorus")
                if isinstance(p_dict["phosphorus"], dict):
                    p_method = p_dict["phosphorus"].get("method", p_method)
                    if not soil_p_unit:
                        soil_p_unit = p_dict["phosphorus"].get("unit")
            if soil_k is None and p_dict.get("potassium") is not None:
                soil_k = p_dict["potassium"].get("value") if isinstance(p_dict["potassium"], dict) else p_dict.get("potassium")
                if not soil_k_unit and isinstance(p_dict["potassium"], dict):
                    soil_k_unit = p_dict["potassium"].get("unit")
            if farm_area is None and p_dict.get("farm_area"):
                farm_area = p_dict.get("farm_area")
            if farm_area_unit is None and p_dict.get("farm_area_unit"):
                farm_area_unit = p_dict.get("farm_area_unit")
            if req.get("organic_carbon") is None and p_dict.get("organic_carbon") is not None:
                req["organic_carbon"] = p_dict["organic_carbon"].get("value") if isinstance(p_dict["organic_carbon"], dict) else p_dict.get("organic_carbon")
            if req.get("ph") is None and p_dict.get("ph") is not None:
                req["ph"] = p_dict["ph"].get("value") if isinstance(p_dict["ph"], dict) else p_dict.get("ph")
            if req.get("ec") is None and p_dict.get("ec") is not None:
                req["ec"] = p_dict["ec"].get("value") if isinstance(p_dict["ec"], dict) else p_dict.get("ec")

        if profile_id:
            try:
                from phase3_soil import db
                import json
                with db.connect() as con:
                    row = con.execute("SELECT profile_json FROM soil_profiles WHERE soil_profile_id = ?", (profile_id,)).fetchone()
                    if row:
                        p_data = json.loads(row["profile_json"])
                        if not crop and p_data.get("crop"):
                            crop = p_data.get("crop")
                        if not district and p_data.get("district"):
                            district = p_data.get("district")
                        if soil_n is None and p_data.get("nitrogen"):
                            soil_n = p_data["nitrogen"].get("value")
                            if not soil_n_unit:
                                soil_n_unit = p_data["nitrogen"].get("unit")
                        if soil_p is None and p_data.get("phosphorus"):
                            soil_p = p_data["phosphorus"].get("value")
                            p_method = p_data["phosphorus"].get("method", p_method)
                            if not soil_p_unit:
                                soil_p_unit = p_data["phosphorus"].get("unit")
                        if soil_k is None and p_data.get("potassium"):
                            soil_k = p_data["potassium"].get("value")
                            if not soil_k_unit:
                                soil_k_unit = p_data["potassium"].get("unit")
                        if farm_area is None and p_data.get("farm_area"):
                            farm_area = p_data.get("farm_area")
                        if farm_area_unit is None and p_data.get("farm_area_unit"):
                            farm_area_unit = p_data.get("farm_area_unit")
                        if req.get("organic_carbon") is None and p_data.get("organic_carbon"):
                            req["organic_carbon"] = p_data["organic_carbon"].get("value")
                        if req.get("ph") is None and p_data.get("ph"):
                            req["ph"] = p_data["ph"].get("value")
                        if req.get("ec") is None and p_data.get("ec"):
                            req["ec"] = p_data["ec"].get("value")
                        
                        # Load printed recommendations if available
                        if p_data.get("printed_recommendation"):
                            prec = p_data["printed_recommendation"]
                            if printed_n is None:
                                printed_n = prec.get("nitrogen_kg_per_acre") or prec.get("n") or prec.get("nitrogen")
                            if printed_p is None:
                                printed_p = prec.get("p2o5_kg_per_acre") or prec.get("p2o5") or prec.get("phosphorus")
                            if printed_k is None:
                                printed_k = prec.get("k2o_kg_per_acre") or prec.get("k2o") or prec.get("potassium")
                            if not req.get("printed_rate_unit") and prec.get("unit"):
                                printed_unit = prec.get("unit")
            except Exception:
                pass

        if farm_area is None:
            farm_area = 1.0
        if farm_area_unit is None:
            farm_area_unit = "hectare"

        fym_applied = req.get("fym_applied_t_per_ha")
        organic_carbon = req.get("organic_carbon")
        soil_ph = req.get("ph")
        soil_ec = req.get("ec")

        target_yield_unit = req.get("target_yield_unit", "t/ha")

        # Step 1: Rule Selection (Phase 4)
        p4_req = RuleSelectionRequest(
            crop=crop,
            district=district,
            soil_series=soil_series,
            season=season,
            irrigation_method=irrigation,
            target_yield=target_yield,
            recommendation_type=req.get("recommendation_type"),
            soil_values={
                "nitrogen": soil_n,
                "phosphorus": soil_p,
                "potassium": soil_k,
                "phosphorus_method": p_method
            } if soil_n is not None or soil_p is not None or soil_k is not None else None
        )
        p4_res = self.rule_service.select_rule(p4_req)

        # Step 2: NPK Requirement Calculation (Phase 5)
        # allow_unverified is False by default to strictly enforce agronomic validation!
        allow_unverified = req.get("allow_unverified", False)

        p5_req = NutrientCalculationRequest(
            crop=crop,
            variety=variety,
            selected_rule_id=p4_res.selected_rule_id,
            target_yield=target_yield,
            target_yield_unit=target_yield_unit,
            soil_nitrogen=soil_n,
            soil_nitrogen_unit=soil_n_unit or "kg/ha",
            soil_phosphorus=soil_p,
            soil_phosphorus_unit=soil_p_unit or "kg/ha",
            soil_potassium=soil_k,
            soil_potassium_unit=soil_k_unit or "kg/ha",
            soil_phosphorus_method=p_method,
            organic_carbon=organic_carbon,
            ph=soil_ph,
            ec=soil_ec,
            fym_applied_t_per_ha=fym_applied,
            farm_area=farm_area,
            farm_area_unit=farm_area_unit,
            phase4_result=p4_res.model_dump(),
            recommendation_mode=rec_mode,
            recommendation_type=req.get("recommendation_type"),
            printed_n_rate=printed_n,
            printed_p2o5_rate=printed_p,
            printed_k2o_rate=printed_k,
            printed_rate_unit=printed_unit,
            printed_source=printed_source,
            allow_unverified=allow_unverified
        )
        p5_res = self.nutrient_service.calculate(p5_req)

        # Step 3: Fertilizer Optimization (Phase 6)
        if p5_res.status in ("MISSING_INPUTS", "VALIDATION_ERROR", "UNSUPPORTED_CROP", "UNSUPPORTED_SOIL_SERIES", "NO_MATCHING_RULE", "CALCULATION_FAILED"):
            # Do not fabricate or optimize fertilizer when required soil test inputs are missing or invalid
            p6_res = FertilizerOptimizationResponse(
                status=p5_res.status,
                crop=crop,
                farm_area_hectares=p5_res.farm_area_hectares or 1.0,
                total_cost_inr=0.0,
                is_verified=False,
                is_provisional=False,
                recommended_products=[],
                warnings=p5_res.warnings,
                validation_errors=p5_res.validation_errors or ["Fertilizer recommendation cannot yet be calculated reliably due to missing or invalid soil data."]
            )
        else:
            p6_req = FertilizerOptimizationRequest(
                crop=crop,
                phase5_result=p5_res.model_dump(),
                allow_unverified=allow_unverified
            )
            p6_res = self.fertilizer_service.optimize(p6_req)

        # Step 4: District Yield Model Prediction (Phase 2)
        yield_pred = None
        try:
            area_ha = p5_res.farm_area_hectares or 1.0
            yield_kg_per_ha = predict_district_yield(district, crop, season)
            est_prod_tonnes = round((yield_kg_per_ha / 1000.0) * area_ha, 2)
            yield_pred = {
                "estimated_production_tonnes": est_prod_tonnes,
                "estimated_yield_kg_per_ha": round(yield_kg_per_ha, 2),
                "crop": crop,
                "district": district,
                "scope": "District-Level Yield Benchmark (Phase 2 Model)"
            }
        except Exception as e:
            yield_pred = {"error": f"Yield prediction model error: {str(e)}"}

        # Step 5: Agro-Weather Guidance (Phase 7)
        lat = req.get("latitude")
        lon = req.get("longitude")
        weather_res = get_weather_guidance(district=district, lat=lat, lon=lon)

        # Determine overall status and verification flags
        if p5_res.status in ("MISSING_INPUTS", "VALIDATION_ERROR", "UNSUPPORTED_CROP", "UNSUPPORTED_SOIL_SERIES", "NO_MATCHING_RULE", "CALCULATION_FAILED"):
            final_status = p5_res.status
            final_is_verified = False
            final_rec_type = "UNAVAILABLE"
            status_message = "Recommendation cannot yet be calculated reliably. " + "; ".join(p5_res.validation_errors or ["Please check soil data."])
        elif p4_res.status in ("PENDING_VERIFICATION", "PENDING_AGRONOMIC_VALIDATION") or not p5_res.is_verified_rule:
            if rec_mode != "SOIL_HEALTH_CARD":
                if allow_unverified and p4_res.status in ("PENDING_VERIFICATION", "PENDING_AGRONOMIC_VALIDATION"):
                    final_status = "PROVISIONAL_PENDING_VALIDATION"
                    final_rec_type = "PROVISIONAL_UNVERIFIED"
                elif p6_res.status in ("BLOCKED_UNVERIFIED_RULE", "PENDING_AGRONOMIC_VALIDATION"):
                    final_status = p6_res.status
                    final_rec_type = "PROVISIONAL_UNVERIFIED"
                else:
                    final_status = "SUCCESS" if p6_res.status in ("OPTIMIZATION_SUCCESS", "PROVISIONAL_UNVERIFIED") else p6_res.status
                    final_rec_type = "PROVISIONAL"
                final_is_verified = False
                status_message = "This recommendation is based on PROVISIONAL agronomic rules pending official TNAU verification."
            else:
                final_status = "SUCCESS"
                final_is_verified = True
                final_rec_type = "SOIL_HEALTH_CARD"
                status_message = None
        else:
            final_status = "SUCCESS" if p6_res.status == "OPTIMIZATION_SUCCESS" else p6_res.status
            final_is_verified = True
            final_rec_type = p5_res.recommendation_type or p4_res.recommendation_type or "SOIL_SPECIFIC_STCR"
            status_message = None

        return {
            "status": final_status,
            "is_verified": final_is_verified,
            "is_provisional": not final_is_verified,
            "recommendation_type": final_rec_type,
            "crop": crop,
            "district": district,
            "recommendation_mode": p5_res.recommendation_mode,
            "rule_selection": p4_res.model_dump(),
            "nutrient_requirements": p5_res.model_dump(),
            "fertilizer_plan": p6_res.model_dump(),
            "soil_nutrient_status": p5_res.soil_nutrient_status,
            "derivation_explanation": p5_res.derivation_explanation,
            "authoritative_reference": p5_res.authoritative_reference,
            "message": status_message,
            "warnings": ([status_message] if status_message and status_message not in p6_res.warnings else []) + p6_res.warnings,
            "district_yield_prediction": yield_pred,
            "weather_guidance": weather_res
        }


def get_full_recommendation(payload: Dict[str, Any]) -> Dict[str, Any]:
    service = FullRecommendationService()
    return service.generate_full_recommendation(payload)
