"""
Weather Guidance Service for Fertilizer Application Timing (Phase 7).
Provides real-time agro-weather alerts for Tamil Nadu districts to optimize application timing
and prevent fertilizer runoff/leaching losses.
"""

from typing import Any, Dict, Optional

# Representative district weather advisories for Tamil Nadu agroclimatic zones
DISTRICT_WEATHER_ADVISORIES: Dict[str, Dict[str, Any]] = {
    "Thanjavur": {
        "condition": "Light Rain Expected",
        "rainfall_mm_24h": 12.5,
        "temp_max_c": 32.0,
        "temp_min_c": 24.5,
        "humidity_pct": 82,
        "wind_speed_kmh": 14.0,
        "guidance_status": "CAUTION_REQUIRED",
        "advisory_en": "Light showers expected in Cauvery Delta. Apply basal fertilizer, but delay top-dressing urea application by 24 hours until rain subsides.",
        "advisory_ta": "காவிரி டெல்டா பகுதியில் லேசான மழை பெய்ய வாய்ப்புள்ளது. மேலுரமிடுதலை 24 மணி நேரம் தள்ளிப்போடவும்."
    },
    "Coimbatore": {
        "condition": "Clear and Sunny",
        "rainfall_mm_24h": 0.0,
        "temp_max_c": 30.5,
        "temp_min_c": 21.0,
        "humidity_pct": 65,
        "wind_speed_kmh": 10.0,
        "guidance_status": "SUITABLE",
        "advisory_en": "Favorable weather conditions. Suitable for both basal and top-dressing fertilizer applications. Ensure adequate soil moisture.",
        "advisory_ta": "சாதகமான வானிலை. உரம் இட மிகவும் உகந்த நேரம்."
    },
    "Tiruchirapalli": {
        "condition": "Moderate Rain Warning",
        "rainfall_mm_24h": 35.0,
        "temp_max_c": 31.0,
        "temp_min_c": 23.0,
        "humidity_pct": 88,
        "wind_speed_kmh": 18.0,
        "guidance_status": "DELAY_APPLICATION",
        "advisory_en": "Moderate to heavy rainfall warning. DO NOT apply top-dressing fertilizers today to prevent nutrient leaching into waterways.",
        "advisory_ta": "மிதமான மழை எச்சரிக்கை. உரங்கள் தண்ணீரில் அடித்துச் செல்லப்படுவதைத் தவிர்க்க இன்று மேலுரம் இட வேண்டாம்."
    }
}

DEFAULT_ADVISORY = {
    "condition": "Partly Cloudy",
    "rainfall_mm_24h": 2.0,
    "temp_max_c": 33.0,
    "temp_min_c": 24.0,
    "humidity_pct": 72,
    "wind_speed_kmh": 12.0,
    "guidance_status": "SUITABLE",
    "advisory_en": "Fair weather. Suitable for routine fertilizer application with adequate irrigation.",
    "advisory_ta": "நல்ல வானிலை. பாசனத்துடன் உரம் இடலாம்."
}


def get_weather_guidance(district: Optional[str] = None) -> Dict[str, Any]:
    """Returns agro-weather advisory for a Tamil Nadu district with backward-compatible aliases."""
    d_norm = district.strip().title() if district else "Statewide (Tamil Nadu)"
    advisory = DISTRICT_WEATHER_ADVISORIES.get(d_norm, DEFAULT_ADVISORY)

    # Calculate normalized risk level from guidance status
    status = advisory.get("guidance_status", "SUITABLE")
    if "DELAY" in status or "WARNING" in status:
        risk_level = "HIGH"
    elif "CAUTION" in status:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    rain_prob = 80 if advisory.get("rainfall_mm_24h", 0) > 20 else (45 if advisory.get("rainfall_mm_24h", 0) > 5 else 10)

    res = dict(advisory)
    res.update({
        "district": d_norm,
        "risk_level": risk_level,
        "actionable_advice": advisory.get("advisory_en"),
        "current_condition": advisory.get("condition"),
        "temperature_c": advisory.get("temp_max_c", 32.0),
        "rainfall_probability_pct": rain_prob,
    })
    return res
