"""
FastAPI router for Phase 7: Weather Guidance and Master Integration API.
Endpoints:
  GET  /api/weather/guidance?district=...
  POST /api/full-recommendation
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Body, Query
from .service import get_full_recommendation
from .weather import get_weather_guidance

integration_router = APIRouter(tags=["phase7-integration"])


@integration_router.get("/api/weather/guidance")
def weather_guidance_endpoint(district: Optional[str] = Query(None, description="District name in Tamil Nadu")) -> Dict[str, Any]:
    """Returns weather advisory and fertilizer application timing guidance for a district."""
    return get_weather_guidance(district)


@integration_router.post("/api/full-recommendation")
def full_recommendation_endpoint(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """
    End-to-End Master Pipeline:
    Executes Phase 4 Rule Selection -> Phase 5 NPK Calculation -> Phase 6 LP Fertilizer Optimization -> Phase 2 District Yield Prediction -> Phase 7 Weather Guidance.
    """
    return get_full_recommendation(payload)
