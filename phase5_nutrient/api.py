"""
FastAPI router for Phase 5: NPK Nutrient Requirement Calculation Engine.
Endpoint: POST /api/nutrient-requirement/calculate
"""

from fastapi import APIRouter, Body, HTTPException
from .models import NutrientCalculationRequest, NutrientCalculationResponse
from .service import NutrientCalculationService

nutrient_router = APIRouter(prefix="/api/nutrient-requirement", tags=["phase5-nutrient"])
_service = NutrientCalculationService()


@nutrient_router.post("/calculate", response_model=NutrientCalculationResponse)
def calculate_nutrient_endpoint(request: NutrientCalculationRequest = Body(...)) -> NutrientCalculationResponse:
    """
    Calculates exact Nitrogen (N), Phosphorus (P2O5), and Potassium (K2O) nutrient requirements in kg/ha
    and farm-total kg using verified Phase 4 agronomic rules.
    Does NOT output fertilizer product bag quantities (Phase 6).
    """
    try:
        response = _service.calculate(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal nutrient calculation error: {str(e)}")
