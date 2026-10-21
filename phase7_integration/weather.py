"""
Live Agro-Weather Guidance Service for Fertilizer Application Timing (Phase 7).
Uses Open-Meteo real-time weather and forecast APIs with SQLite caching
and agronomically verified fertilizer scheduling rules.
"""

import json
import logging
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

import os
from phase3_soil import db
from .location import get_district_coordinates, is_in_tamil_nadu

logger = logging.getLogger(__name__)

CACHE_TTL_SECONDS = 1800  # 30 minutes cache
DEFAULT_RAIN_THRESHOLD_MM = float(os.environ.get("FERTILIZER_RAIN_THRESHOLD_MM", "5.0"))

# Open-Meteo Weather interpretation codes (WMO)
WMO_WEATHER_CODES = {
    0: ("Clear Sky", "தெளிவான வானம்"),
    1: ("Mainly Clear", "முக்கியமாக தெளிவான வானம்"),
    2: ("Partly Cloudy", "பகுதி மேகமூட்டம்"),
    3: ("Overcast", "முழு மேகமூட்டம்"),
    45: ("Foggy", "பனிமூட்டம்"),
    48: ("Depositing Rime Fog", "பனி படலம்"),
    51: ("Light Drizzle", "லேசான தூறல்"),
    53: ("Moderate Drizzle", "மிதமான தூறல்"),
    55: ("Dense Drizzle", "அடர்ந்த தூறல்"),
    61: ("Slight Rain", "லேசான மழை"),
    63: ("Moderate Rain", "மிதமான மழை"),
    65: ("Heavy Rain", "கனமழை"),
    80: ("Slight Rain Showers", "லேசான மழைச்சாரல்"),
    81: ("Moderate Rain Showers", "மிதமான மழைச்சாரல்"),
    82: ("Violent Rain Showers", "பலத்த மழைச்சாரல்"),
    95: ("Thunderstorm", "இடியுடன் கூடிய மழை"),
}


def _interpret_wmo(code: int) -> Tuple[str, str]:
    return WMO_WEATHER_CODES.get(code, ("Fair Weather", "நல்ல வானிலை"))


def _fetch_open_meteo(lat: float, lon: float) -> Dict[str, Any]:
    """Fetch live observations and 7-day forecast from Open-Meteo."""
    params = {
        "latitude": f"{lat:.4f}",
        "longitude": f"{lon:.4f}",
        "current": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code",
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,precipitation_probability_max,weather_code",
        "timezone": "auto"
    }
    url = f"https://api.open-meteo.com/v1/forecast?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "TNFertilizerOptimizer/1.0 (agri-weather)"})
    with urllib.request.urlopen(req, timeout=8) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_cached_weather(cache_key: str) -> Optional[Dict[str, Any]]:
    """Retrieve non-expired cached weather from SQLite."""
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    try:
        with db.connect() as con:
            row = con.execute(
                "SELECT * FROM weather_cache WHERE cache_key = ? AND expires_at > ?",
                (cache_key, now_iso)
            ).fetchone()
            if row:
                return {
                    "current": json.loads(row["current_json"]),
                    "forecast": json.loads(row["forecast_json"]),
                    "observation_time": row["observation_time"],
                    "source": row["source"],
                    "is_cached": True,
                    "district": row["district"]
                }
    except Exception as e:
        logger.warning(f"Failed to read weather cache: {e}")
    return None


def _get_stale_cached_weather(cache_key: str) -> Optional[Dict[str, Any]]:
    """Retrieve any existing cached weather from SQLite even if expired (for offline fallback)."""
    try:
        with db.connect() as con:
            row = con.execute(
                "SELECT * FROM weather_cache WHERE cache_key = ? ORDER BY created_at DESC LIMIT 1",
                (cache_key,)
            ).fetchone()
            if row:
                return {
                    "current": json.loads(row["current_json"]),
                    "forecast": json.loads(row["forecast_json"]),
                    "observation_time": row["observation_time"],
                    "source": row["source"],
                    "district": row["district"]
                }
    except Exception as e:
        logger.warning(f"Failed to read stale weather cache: {e}")
    return None


def _save_cached_weather(cache_key: str, lat: float, lon: float, district: str, current: Dict[str, Any], forecast: Dict[str, Any], obs_time: str):
    """Save live weather to SQLite with expiration timestamp."""
    now_ts = time.time()
    now_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_ts))
    exp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now_ts + CACHE_TTL_SECONDS))
    try:
        with db.connect() as con:
            con.execute(
                """INSERT OR REPLACE INTO weather_cache
                   (cache_key, latitude, longitude, district, current_json, forecast_json, observation_time, source, created_at, expires_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, 'Open-Meteo API', ?, ?)""",
                (cache_key, lat, lon, district, json.dumps(current), json.dumps(forecast), obs_time, now_iso, exp_iso)
            )
    except Exception as e:
        logger.warning(f"Failed to write weather cache: {e}")


def get_live_weather(lat: Optional[float] = None, lon: Optional[float] = None, district: Optional[str] = None) -> Dict[str, Any]:
    """
    Get live weather observation and forecast.
    Uses farm coordinates if provided; otherwise resolves district centroid.
    Resilient: Falls back to stale cache or explicit unavailable state on API/network failure.
    """
    d_norm = district.strip().title() if district else "Thanjavur"
    if lat is None or lon is None:
        lat, lon = get_district_coordinates(d_norm)

    cache_key = f"{lat:.3f}_{lon:.3f}"
    cached = _get_cached_weather(cache_key)
    if cached:
        return {
            "status": "SUCCESS",
            "latitude": lat,
            "longitude": lon,
            "district": d_norm,
            "is_cached": True,
            "is_stale": False,
            "source": "Open-Meteo (Cached)",
            "observation_time": cached["observation_time"],
            "current": cached["current"],
            "forecast": cached["forecast"]
        }

    # Fetch fresh from Open-Meteo with network resilience
    try:
        raw = _fetch_open_meteo(lat, lon)
        curr = raw.get("current", {})
        daily = raw.get("daily", {})

        w_code = curr.get("weather_code", 0)
        cond_en, cond_ta = _interpret_wmo(w_code)

        current_data = {
            "temperature_c": curr.get("temperature_2m"),
            "relative_humidity_pct": curr.get("relative_humidity_2m"),
            "precipitation_mm": curr.get("precipitation", 0.0),
            "wind_speed_kmh": curr.get("wind_speed_10m", 0.0),
            "weather_code": w_code,
            "condition_en": cond_en,
            "condition_ta": cond_ta,
            "observation_time": curr.get("time", time.strftime("%Y-%m-%dT%H:%M"))
        }

        forecast_days = []
        times = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precip_sums = daily.get("precipitation_sum", [])
        precip_probs = daily.get("precipitation_probability_max", [])
        codes = daily.get("weather_code", [])

        for i in range(len(times)):
            c_en, c_ta = _interpret_wmo(codes[i] if i < len(codes) else 0)
            forecast_days.append({
                "date": times[i],
                "temp_max_c": max_temps[i] if i < len(max_temps) else None,
                "temp_min_c": min_temps[i] if i < len(min_temps) else None,
                "precipitation_mm": precip_sums[i] if i < len(precip_sums) else 0.0,
                "precipitation_probability_pct": precip_probs[i] if i < len(precip_probs) else 0,
                "condition_en": c_en,
                "condition_ta": c_ta
            })

        forecast_data = {
            "days": forecast_days,
            "rainfall_next_24h_mm": forecast_days[0]["precipitation_mm"] if forecast_days else 0.0,
            "rainfall_next_48h_mm": (forecast_days[0]["precipitation_mm"] + (forecast_days[1]["precipitation_mm"] if len(forecast_days) > 1 else 0.0)) if forecast_days else 0.0,
        }

        _save_cached_weather(cache_key, lat, lon, d_norm, current_data, forecast_data, current_data["observation_time"])

        return {
            "status": "SUCCESS",
            "latitude": lat,
            "longitude": lon,
            "district": d_norm,
            "is_cached": False,
            "is_stale": False,
            "source": "Open-Meteo API (Live)",
            "observation_time": current_data["observation_time"],
            "current": current_data,
            "forecast": forecast_data
        }
    except Exception as e:
        logger.warning(f"Live Open-Meteo fetch failed ({e}). Checking stale cache for {d_norm}...")
        stale = _get_stale_cached_weather(cache_key)
        if stale:
            return {
                "status": "SUCCESS",
                "latitude": lat,
                "longitude": lon,
                "district": d_norm,
                "is_cached": True,
                "is_stale": True,
                "source": "Open-Meteo (Stale Cache Fallback)",
                "observation_time": stale["observation_time"],
                "current": stale["current"],
                "forecast": stale["forecast"]
            }

        return {
            "status": "WEATHER_UNAVAILABLE",
            "latitude": lat,
            "longitude": lon,
            "district": d_norm,
            "is_cached": False,
            "is_stale": False,
            "source": "Offline Fallback",
            "observation_time": time.strftime("%Y-%m-%dT%H:%M"),
            "current": {
                "temperature_c": None,
                "relative_humidity_pct": None,
                "precipitation_mm": None,
                "wind_speed_kmh": None,
                "weather_code": 0,
                "condition_en": "Unavailable",
                "condition_ta": "கிடைக்கவில்லை",
                "observation_time": time.strftime("%Y-%m-%dT%H:%M")
            },
            "forecast": {
                "days": [],
                "rainfall_next_24h_mm": 0.0,
                "rainfall_next_48h_mm": 0.0
            },
            "error_detail": str(e)
        }


def get_weather_guidance(district: Optional[str] = None, lat: Optional[float] = None, lon: Optional[float] = None, rain_threshold_mm: Optional[float] = None) -> Dict[str, Any]:
    """
    Returns agro-weather advisory for fertilizer application timing.
    Combines live Open-Meteo observations and forecast with TNAU scheduling rules.
    """
    try:
        weather = get_live_weather(lat, lon, district)
        d_norm = weather.get("district", district or "Thanjavur")
        rain_threshold = rain_threshold_mm if rain_threshold_mm is not None else DEFAULT_RAIN_THRESHOLD_MM

        if weather.get("status") == "WEATHER_UNAVAILABLE" or weather.get("current", {}).get("temperature_c") is None:
            return {
                "status": "WEATHER_UNAVAILABLE",
                "district": d_norm,
                "latitude": weather.get("latitude"),
                "longitude": weather.get("longitude"),
                "guidance_status": "WEATHER_UNAVAILABLE",
                "risk_level": "UNKNOWN",
                "advisory_en": "Live weather service is currently unreachable. Soil-based fertilizer recommendations remain fully active.",
                "advisory_ta": "வானிலை தகவலைப் பெற முடியவில்லை. மண் சார்ந்த உரப் பரிந்துரைகள் வழக்கம் போல் செயல்படுகின்றன.",
                "actionable_advice": "Weather service temporarily offline. Rely on soil-based recommendations.",
                "condition": "Unavailable",
                "current_condition": "Unavailable",
                "condition_ta": "கிடைக்கவில்லை",
                "temperature_c": None,
                "temp_max_c": None,
                "humidity_pct": None,
                "rainfall_mm_24h": None,
                "rainfall_probability_pct": None,
                "wind_speed_kmh": None,
                "observation_time": weather.get("observation_time", time.strftime("%Y-%m-%dT%H:%M")),
                "is_cached": False,
                "data_source": "Offline Fallback",
                "rain_threshold_mm": rain_threshold,
                "forecast_disclaimer": "Weather forecast guidance provides general advisory timing based on meteorological projections and is not a guaranteed micro-climate prediction.",
                "error_detail": weather.get("error_detail", "Live weather service unreachable")
            }

        curr = weather["current"]
        fc = weather["forecast"]
        rain_24h = fc.get("rainfall_next_24h_mm", 0.0)
        rain_48h = fc.get("rainfall_next_48h_mm", 0.0)
        wind = curr.get("wind_speed_kmh", 0.0)
        temp = curr.get("temperature_c", 30.0)
        humidity = curr.get("relative_humidity_pct", 70)
        cond_en = curr.get("condition_en", "Clear")
        cond_ta = curr.get("condition_ta", "தெளிவான வானிலை")
        is_cached = weather.get("is_cached", False)
        source = weather.get("source", "Open-Meteo")

        # Agronomic evaluation of fertilizer timing
        if rain_24h >= 25.0:
            status = "DELAY_APPLICATION"
            risk_level = "HIGH"
            adv_en = f"Heavy rain forecast ({rain_24h:.1f} mm in 24h). Delay top-dressing urea or water-soluble fertilizers to prevent leaching and surface runoff. Note: Meteorological forecasts carry uncertainty."
            adv_ta = f"கனமழை வாய்ப்புள்ளது ({rain_24h:.1f} மிமீ). உரங்கள் நீரில் கரைந்து வீணாவதைத் தடுக்க மேலுரமிடுதலை தள்ளிப்போடவும்."
        elif rain_24h >= rain_threshold:
            status = "CAUTION_REQUIRED"
            risk_level = "MEDIUM"
            adv_en = f"Rainfall expected ({rain_24h:.1f} mm in 24h exceeds configurable threshold of {rain_threshold:.1f} mm). General guidance: Basal fertilizer application acceptable, but postpone top-dressing urea until showers subside. Note: Meteorological forecasts carry uncertainty."
            adv_ta = f"மிதமான மழை எதிர்பார்க்கப்படுகிறது ({rain_24h:.1f} மிமீ). அடிஉரம் இடலாம்; ஆனால் யூரியா மேலுரமிடுதலை மழை நின்றபின் மேற்கொள்ளவும்."
        elif wind > 20.0:
            status = "CAUTION_REQUIRED"
            risk_level = "MEDIUM"
            adv_en = f"High wind speeds ({wind:.1f} km/h). Avoid foliar micronutrient or pesticide spraying to avoid drift losses. Soil application is suitable."
            adv_ta = f"காற்று வேகம் அதிகமாக உள்ளது ({wind:.1f} கிமீ/மணி). இலைவழி தெளிப்பைத் தவிர்க்கவும். மண்ணில் உரம் இடலாம்."
        elif temp > 38.0:
            status = "CAUTION_REQUIRED"
            risk_level = "MEDIUM"
            adv_en = f"High ambient temperature ({temp:.1f}°C). Apply fertilizers during early morning or late evening with adequate irrigation to avoid volatilization."
            adv_ta = f"அதிக வெப்பம் ({temp:.1f}°C). அதிகாலை அல்லது மாலையில் பாசனத்துடன் உரம் இடவும்."
        else:
            status = "SUITABLE"
            risk_level = "LOW"
            adv_en = f"Favorable weather conditions ({cond_en}, {temp:.1f}°C, rainfall {rain_24h:.1f} mm). Suitable for both basal and top-dressing applications."
            adv_ta = f"உரம் இட சாதகமான வானிலை ({cond_ta}, {temp:.1f}°C). அடிஉரம் மற்றும் மேலுரம் இரண்டையும் இடலாம்."

        rain_prob = 0
        if fc.get("days"):
            rain_prob = fc["days"][0].get("precipitation_probability_pct", 0)

        return {
            "status": "SUCCESS",
            "district": d_norm,
            "latitude": weather["latitude"],
            "longitude": weather["longitude"],
            "guidance_status": status,
            "risk_level": risk_level,
            "advisory_en": adv_en,
            "advisory_ta": adv_ta,
            "actionable_advice": adv_en,
            "condition": cond_en,
            "current_condition": cond_en,
            "condition_ta": cond_ta,
            "temp_max_c": temp,
            "temperature_c": temp,
            "humidity_pct": humidity,
            "rainfall_mm_24h": rain_24h,
            "rainfall_probability_pct": rain_prob,
            "wind_speed_kmh": wind,
            "observation_time": weather["observation_time"],
            "is_cached": is_cached,
            "data_source": source,
            "rain_threshold_mm": rain_threshold,
            "forecast_disclaimer": "Weather forecast guidance provides general advisory timing based on meteorological projections and is not a guaranteed micro-climate prediction.",
            "forecast_days": fc.get("days", [])
        }
    except Exception as e:
        logger.error(f"Live weather lookup failed: {e}")
        # Never fabricate weather data when API fails: return explicit unavailable state
        return {
            "status": "WEATHER_UNAVAILABLE",
            "district": district or "Tamil Nadu",
            "guidance_status": "WEATHER_UNAVAILABLE",
            "risk_level": "UNKNOWN",
            "advisory_en": "Live weather service is currently unreachable. Soil-based fertilizer recommendations remain fully active.",
            "advisory_ta": "வானிலை தகவலைப் பெற முடியவில்லை. மண் சார்ந்த உரப் பரிந்துரைகள் வழக்கம் போல் செயல்படுகின்றன.",
            "actionable_advice": "Weather service temporarily offline. Rely on soil-based recommendations.",
            "condition": "Unavailable",
            "current_condition": "Unavailable",
            "temperature_c": None,
            "humidity_pct": None,
            "rainfall_mm_24h": None,
            "rainfall_probability_pct": None,
            "wind_speed_kmh": None,
            "is_cached": False,
            "data_source": "Offline Fallback",
            "error_detail": str(e)
        }
