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

        soil_n = req.get("soil_nitrogen", 220.0)
        soil_p = req.get("soil_phosphorus", 16.0)
        soil_k = req.get("soil_potassium", 190.0)
        p_method = req.get("soil_phosphorus_method", "Olsen")

        farm_area = req.get("farm_area", 1.0)
        farm_area_unit = req.get("farm_area_unit", "hectare")

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
            }
        )
        p4_res = self.rule_service.select_rule(p4_req)

        # Step 2: NPK Requirement Calculation (Phase 5)
        p5_req = NutrientCalculationRequest(
            crop=crop,
            selected_rule_id=p4_res.selected_rule_id,
            target_yield=target_yield,
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
        weather_res = get_weather_guidance(district)

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
