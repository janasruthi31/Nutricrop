"""
FastAPI router for Phase 4: Agronomic Rule Database & Rule Selection Engine.
Endpoint: POST /api/agronomy/select-rule
"""

from fastapi import APIRouter, Body, HTTPException
from .models import RuleSelectionRequest, RuleSelectionResponse
from .service import RuleSelectionService

agronomy_router = APIRouter(prefix="/api/agronomy", tags=["phase4-agronomy"])
_service = RuleSelectionService()


@agronomy_router.post("/select-rule", response_model=RuleSelectionResponse)
def select_rule_endpoint(request: RuleSelectionRequest = Body(...)) -> RuleSelectionResponse:
    """
    Selects the applicable verified agronomic rule (TNAU/STCR/IPNS) based on crop,
    soil series, season, irrigation method, target yield, and soil test values.
    Does NOT calculate final NPK fertilizer requirements (Phase 5).
    """
    try:
        response = _service.select_rule(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal agronomy engine error: {str(e)}")
