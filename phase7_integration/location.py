"""
Location and Reverse Geocoding Service for Tamil Nadu Agriculture.
Validates farm coordinates, resolves administrative locations (District, Taluk, Village)
via real reverse geocoding with fallbacks, and manages verified district coordinates.
"""

import json
import logging
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Bounding box for Tamil Nadu, India
TN_LAT_MIN = 8.0
TN_LAT_MAX = 13.6
TN_LON_MIN = 76.2
TN_LON_MAX = 80.4

# Verified district centroid coordinates across all 38 districts of Tamil Nadu
TN_DISTRICT_COORDINATES: Dict[str, Tuple[float, float]] = {
    "Thanjavur": (10.7870, 79.1378),
    "Tiruvarur": (10.7725, 79.6365),
    "Nagapattinam": (10.7656, 79.8424),
    "Mayiladuthurai": (11.1075, 79.6524),
    "Cuddalore": (11.7480, 79.7714),
    "Coimbatore": (11.0168, 76.9558),
    "Tiruppur": (11.1085, 77.3411),
    "Erode": (11.3410, 77.7172),
    "Salem": (11.6643, 78.1460),
    "Namakkal": (11.2189, 78.1674),
    "Dharmapuri": (12.1357, 78.1585),
    "Krishnagiri": (12.5186, 78.2137),
    "Tiruchirappalli": (10.7905, 78.7047),
    "Trichy": (10.7905, 78.7047),
    "Karur": (10.9601, 78.0766),
    "Perambalur": (11.2333, 78.8833),
    "Ariyalur": (11.1401, 79.0786),
    "Pudukkottai": (10.3797, 78.8208),
    "Madurai": (9.9252, 78.1198),
    "Dindigul": (10.3673, 77.9803),
    "Theni": (10.0104, 77.4768),
    "Virudhunagar": (9.5680, 77.9624),
    "Sivaganga": (9.8433, 78.4809),
    "Ramanathapuram": (9.3639, 78.8395),
    "Tirunelveli": (8.7139, 77.7567),
    "Tenkasi": (8.9594, 77.3149),
    "Thoothukudi": (8.7642, 78.1348),
    "Kanniyakumari": (8.0883, 77.5385),
    "Nilgiris": (11.4102, 76.6950),
    "Vellore": (12.9165, 79.1325),
    "Ranipet": (12.9272, 79.3330),
    "Tirupathur": (12.4925, 78.5678),
    "Tiruvannamalai": (12.2253, 79.0747),
    "Viluppuram": (11.9401, 79.4861),
    "Kallakurichi": (11.7383, 78.9639),
    "Kancheepuram": (12.8342, 79.7036),
    "Chengalpattu": (12.6841, 79.9836),
    "Tiruvallur": (13.1231, 79.9120),
    "Chennai": (13.0827, 80.2707),
}


def is_in_tamil_nadu(lat: float, lon: float) -> bool:
    """Validate whether coordinates fall inside Tamil Nadu geographic boundary."""
    return (TN_LAT_MIN <= lat <= TN_LAT_MAX) and (TN_LON_MIN <= lon <= TN_LON_MAX)


def get_district_coordinates(district: str) -> Tuple[float, float]:
    """Return representative (lat, lon) for a Tamil Nadu district."""
    norm = district.strip().title()
    if norm in TN_DISTRICT_COORDINATES:
        return TN_DISTRICT_COORDINATES[norm]
    for d, coords in TN_DISTRICT_COORDINATES.items():
        if d.lower() == norm.lower():
            return coords
    # Default to Thanjavur (Cauvery Delta center)
    return TN_DISTRICT_COORDINATES["Thanjavur"]


def reverse_geocode_coordinates(lat: float, lon: float) -> Dict[str, Any]:
    """
    Resolve GPS latitude and longitude into administrative fields:
    State, District, Taluk, Village/City.
    Queries BigDataCloud client API with Nominatim fallback.
    """
    if not is_in_tamil_nadu(lat, lon):
        logger.warning(f"Coordinates ({lat}, {lon}) are outside Tamil Nadu geographic bounds.")

    district = None
    taluk = None
    village = None
    state = "Tamil Nadu"

    import httpx

    # 1. Query BigDataCloud reverse geocode client API
    try:
        url = f"https://api.bigdatacloud.net/data/reverse-geocode-client?latitude={lat}&longitude={lon}&localityLanguage=en"
        headers = {"User-Agent": "TNFertilizerOptimizer/1.0"}
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                state = data.get("principalSubdivision") or state
                village = data.get("locality") or data.get("city")

                # Parse admin hierarchy
                admin_list = data.get("localityInfo", {}).get("administrative", [])
                for item in admin_list:
                    name = item.get("name", "")
                    desc = item.get("description", "").lower()
                    order = item.get("order", 0)
                    if "district" in desc or "district" in name.lower() or order == 9:
                        district = name.replace(" district", "").replace(" District", "").replace(" taluk", "").replace(" Taluk", "").strip()
                    elif "taluk" in desc or "taluk" in name.lower():
                        taluk = name.replace(" taluk", "").replace(" Taluk", "").strip()
                    elif order == 10 and not village:
                        village = name
    except Exception as e:
        logger.warning(f"BigDataCloud reverse geocode failed: {e}. Trying OpenStreetMap Nominatim.")

    # 2. Fallback to OpenStreetMap Nominatim if district not resolved
    if not district:
        try:
            url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}"
            headers = {"User-Agent": "TNFertilizerOptimizer/1.0 (agri-research)"}
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code == 200:
                    data = resp.json()
                    addr = data.get("address", {})
                    state = addr.get("state") or state
                    district = addr.get("state_district") or addr.get("county")
                    if district:
                        district = district.replace(" District", "").replace(" district", "").strip()
                    taluk = addr.get("county") or addr.get("suburb") or taluk
                    village = addr.get("village") or addr.get("town") or addr.get("suburb") or village
        except Exception as e:
            logger.warning(f"Nominatim reverse geocode failed: {e}")

    # 3. If district still unknown, find nearest district centroid
    if not district:
        min_dist = float("inf")
        nearest_d = "Thanjavur"
        for d, (d_lat, d_lon) in TN_DISTRICT_COORDINATES.items():
            dist = (lat - d_lat) ** 2 + (lon - d_lon) ** 2
            if dist < min_dist:
                min_dist = dist
                nearest_d = d
        district = nearest_d

    # Normalize district to matching TN district key
    for known in TN_DISTRICT_COORDINATES.keys():
        if known.lower() == district.lower():
            district = known
            break

    return {
        "latitude": round(lat, 5),
        "longitude": round(lon, 5),
        "state": state,
        "district": district,
        "taluk": taluk,
        "village": village,
        "is_in_tamil_nadu": is_in_tamil_nadu(lat, lon),
        "source": "live_reverse_geocoding"
    }
