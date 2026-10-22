"""
FastAPI router for Phase 7: Weather Guidance, Location Services, and Master Integration API.
Endpoints:
  GET  /api/weather/current
  GET  /api/weather/forecast
  GET  /api/weather/guidance
  GET  /api/location/reverse-geocode
  GET  /api/fertilizer/prices
  POST /api/full-recommendation
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Body, HTTPException, Query
from phase3_soil import db
from .location import reverse_geocode_coordinates, is_in_tamil_nadu
from .service import get_full_recommendation
from .weather import get_live_weather, get_weather_guidance

integration_router = APIRouter(tags=["phase7-integration"])


@integration_router.get("/api/weather/current")
def get_current_weather_endpoint(
    lat: Optional[float] = Query(None, description="Latitude coordinate"),
    lon: Optional[float] = Query(None, description="Longitude coordinate"),
    district: Optional[str] = Query(None, description="District name in Tamil Nadu")
) -> Dict[str, Any]:
    """Returns real-time weather observations from Open-Meteo for the farm location."""
    res = get_live_weather(lat=lat, lon=lon, district=district)
    return {
        "status": res.get("status", "SUCCESS"),
        "latitude": res["latitude"],
        "longitude": res["longitude"],
        "district": res["district"],
        "observation_time": res["observation_time"],
        "is_cached": res.get("is_cached", False),
        "is_stale": res.get("is_stale", False),
        "source": res["source"],
        "current": res["current"]
    }


@integration_router.get("/api/weather/forecast")
def get_weather_forecast_endpoint(
    lat: Optional[float] = Query(None, description="Latitude coordinate"),
    lon: Optional[float] = Query(None, description="Longitude coordinate"),
    district: Optional[str] = Query(None, description="District name in Tamil Nadu")
) -> Dict[str, Any]:
    """Returns 7-day daily forecast and precipitation probabilities for the farm location."""
    res = get_live_weather(lat=lat, lon=lon, district=district)
    return {
        "status": res.get("status", "SUCCESS"),
        "latitude": res["latitude"],
        "longitude": res["longitude"],
        "district": res["district"],
        "observation_time": res["observation_time"],
        "is_cached": res.get("is_cached", False),
        "is_stale": res.get("is_stale", False),
        "source": res["source"],
        "forecast": res["forecast"]
    }


@integration_router.get("/api/weather/guidance")
def weather_guidance_endpoint(
    district: Optional[str] = Query(None, description="District name in Tamil Nadu"),
    lat: Optional[float] = Query(None, description="Latitude coordinate"),
    lon: Optional[float] = Query(None, description="Longitude coordinate"),
    rain_threshold_mm: Optional[float] = Query(None, description="Configurable rainfall threshold in mm for spray/fertilizer advisory")
) -> Dict[str, Any]:
    """Returns weather advisory and fertilizer application timing guidance for a district or coordinates."""
    return get_weather_guidance(district=district, lat=lat, lon=lon, rain_threshold_mm=rain_threshold_mm)


@integration_router.get("/api/location/reverse-geocode")
def reverse_geocode_endpoint(
    lat: float = Query(..., description="Latitude coordinate"),
    lon: float = Query(..., description="Longitude coordinate")
) -> Dict[str, Any]:
    """Resolves device GPS coordinates to Tamil Nadu administrative district, taluk, and village."""
    if not (-90.0 <= lat <= 90.0) or not (-180.0 <= lon <= 180.0):
        raise HTTPException(status_code=400, detail="Invalid coordinates: latitude must be [-90, 90] and longitude [-180, 180].")
    return reverse_geocode_coordinates(lat=lat, lon=lon)


@integration_router.get("/api/fertilizer/prices")
def get_fertilizer_prices_endpoint() -> List[Dict[str, Any]]:
    """Returns verified fertilizer prices with traceability (source, NBS subsidy schedule, effective date)."""
    with db.connect() as con:
        rows = con.execute("SELECT * FROM fertilizer_prices ORDER BY category, name").fetchall()
        return [dict(r) for r in rows]


@integration_router.post("/api/full-recommendation")
def full_recommendation_endpoint(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """
    End-to-End Master Pipeline:
    Executes Phase 4 Rule Selection -> Phase 5 NPK Calculation -> Phase 6 LP Fertilizer Optimization -> Phase 2 District Yield Prediction -> Phase 7 Weather Guidance.
    """
    return get_full_recommendation(payload)


@integration_router.post("/api/voice/tamil-summary")
def get_tamil_voice_summary_endpoint(payload: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """
    Generates conversational Tamil speech synthesis script for the recommendation result (Task 4b).
    Enables smallholder farmers to listen to the recommendation in clear spoken Tamil.
    """
    crop = payload.get("crop", "பயிர்")
    district = payload.get("district", "தமிழ்நாடு")
    p6 = payload.get("fertilizer_plan") or {}
    products = p6.get("recommended_products") or []
    cost = float(p6.get("total_cost_inr", 0.0))

    crop_ta = {
        "rice": "நெல்",
        "cotton": "பருத்தி",
        "cotton (lint)": "பருத்தி",
        "sugarcane": "கரும்பு",
        "groundnut": "நிலக்கடலை",
        "blackgram": "உளுந்து",
        "maize": "மக்காச்சோளம்",
        "ragi": "கேழ்வரகு",
    }.get(str(crop).lower().strip(), crop)

    prods_ta = []
    for p in products:
        p_name = p.get("product_name") or p.get("name") or p.get("product_id")
        bags = p.get("bags")
        p_upper = str(p_name).upper()
        if "UREA" in p_upper:
            p_ta_name = "யூரியா"
        elif "DAP" in p_upper:
            p_ta_name = "டிஏபி (DAP)"
        elif "MOP" in p_upper or "POTASH" in p_upper:
            p_ta_name = "பொட்டாஷ் (MOP)"
        elif "SSP" in p_upper:
            p_ta_name = "சூப்பர் பாஸ்பேட்"
        else:
            p_ta_name = p_name
        prods_ta.append(f"{p_ta_name} {bags} மூட்டை")

    prods_sentence = ", ".join(prods_ta) if prods_ta else "உரத் தேவை இல்லை"

    script = (
        f"வணக்கம் உழவரே! உங்கள் {district} மாவட்ட {crop_ta} பயிருக்கான உகந்த உரப் பரிந்துரை இதுவாகும். "
        f"பரிந்துரைக்கப்பட்ட உரங்கள்: {prods_sentence}. "
        f"உத்தேச மொத்த உரச் செலவு ரூபாய் {cost:,.0f}. "
        f"அடிஉரங்களை விதைப்பின் போது இடவும். யூரியாவை பிரித்து மேலுரமாக இடவும். "
        f"இறுதி முடிவுக்கு உங்கள் பகுதி வட்டார வேளாண்மை அலுவலரை அணுகவும்."
    )

    return {
        "status": "SUCCESS",
        "crop": crop,
        "crop_tamil": crop_ta,
        "district": district,
        "tamil_speech_script": script,
        "total_cost_inr": cost,
        "audio_available": True,
        "voice_locale": "ta-IN",
        "disclaimer_ta": "இப்பரிந்துரை தமிழ்நாடு வேளாண்மைப் பல்கலைக்கழக வழிகாட்டுதலின்படி கணக்கிடப்பட்டது."
    }
