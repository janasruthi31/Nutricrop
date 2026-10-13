"""
FastAPI router for Phase 6: Fertilizer Type, Quantity, and Cost Optimization Engine.
Endpoint: POST /api/fertilizer/optimize
"""

from fastapi import APIRouter, Body, HTTPException
from .models import FertilizerOptimizationRequest, FertilizerOptimizationResponse
from .service import FertilizerOptimizerService

fertilizer_router = APIRouter(prefix="/api/fertilizer", tags=["phase6-fertilizer"])
fertilizer_opt_router = APIRouter(prefix="/api/fertilizer-optimization", tags=["phase6-fertilizer"])
_service = FertilizerOptimizerService()


@fertilizer_router.post("/optimize", response_model=FertilizerOptimizationResponse)
@fertilizer_opt_router.post("/optimize", response_model=FertilizerOptimizationResponse)
def optimize_fertilizer_endpoint(request: FertilizerOptimizationRequest = Body(...)) -> FertilizerOptimizationResponse:
    """
    Minimizes fertilizer purchase cost using Linear Programming (scipy.optimize.linprog)
    to fulfill required N, P2O5, and K2O nutrient requirements.
    Generates product quantities in kg and commercial bags (45kg/50kg), nutrient surplus details,
    and split application schedules.
    """
    try:
        response = _service.optimize(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal fertilizer optimization error: {str(e)}")

