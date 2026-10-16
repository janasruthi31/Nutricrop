"""
Master Pipeline Orchestrator Service (Phase 7).
Chains Phase 4 Rule Selection -> Phase 5 NPK Calculation -> Phase 6 LP Optimization -> Phase 2 Yield Model -> Phase 7 Weather Guidance.
"""

from typing import Any, Dict, Optional
from agronomy.service import RuleSelectionService, RuleSelectionRequest
from phase5_nutrient.service import NutrientCalculationService, NutrientCalculationRequest
from phase6_fertilizer.service import FertilizerOptimizerService, FertilizerOptimizationRequest
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
                        if soil_p is None and p_data.get("phosphorus"):
                            soil_p = p_data["phosphorus"].get("value")
                            p_method = p_data["phosphorus"].get("method", p_method)
                        if soil_k is None and p_data.get("potassium"):
                            soil_k = p_data["potassium"].get("value")
            except Exception:
                pass

        farm_area = req.get("farm_area", 1.0)
        farm_area_unit = req.get("farm_area_unit", "hectare")
        target_yield_unit = req.get("target_yield_unit", "t/ha")

        # Step 1: Rule Selection (Phase 4)
        p4_req = RuleSelectionRequest(
            crop=crop,
            district=district,
            soil_series=soil_series,
            season=season,
            irrigation_method=irrigation,
            target_yield=target_yield,
            soil_values={
                "nitrogen": soil_n,
                "phosphorus": soil_p,
                "potassium": soil_k,
                "phosphorus_method": p_method
            } if soil_n is not None or soil_p is not None or soil_k is not None else None
        )
        p4_res = self.rule_service.select_rule(p4_req)

        # Step 2: NPK Requirement Calculation (Phase 5)
        p5_req = NutrientCalculationRequest(
            crop=crop,
            selected_rule_id=p4_res.selected_rule_id,
            target_yield=target_yield,
            target_yield_unit=target_yield_unit,
            soil_nitrogen=soil_n,
            soil_phosphorus=soil_p,
            soil_potassium=soil_k,
            soil_phosphorus_method=p_method,
            farm_area=farm_area,
            farm_area_unit=farm_area_unit,
            phase4_result=p4_res.model_dump()
        )
        p5_res = self.nutrient_service.calculate(p5_req)

        # Step 3: Fertilizer Optimization (Phase 6)
        p6_req = FertilizerOptimizationRequest(
            crop=crop,
            phase5_result=p5_res.model_dump()
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

        return {
            "status": "SUCCESS" if p6_res.status == "OPTIMIZATION_SUCCESS" else p6_res.status,
            "crop": crop,
            "district": district,
            "rule_selection": p4_res.model_dump(),
            "nutrient_requirements": p5_res.model_dump(),
            "fertilizer_plan": p6_res.model_dump(),
            "district_yield_prediction": yield_pred,
            "weather_guidance": weather_res
        }


def get_full_recommendation(payload: Dict[str, Any]) -> Dict[str, Any]:
    service = FullRecommendationService()
    return service.generate_full_recommendation(payload)
