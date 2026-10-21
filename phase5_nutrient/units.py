"""
Unit conversions and validation for Phase 5 NPK calculation engine.
Handles farm area unit conversions, target yield normalization,
and soil nutrient unit and elemental/oxide form conversions.
"""

from typing import Tuple

# Canonical, authoritative area conversion constants
HA_TO_ACRE = 2.4710538147
ACRE_TO_HA = 0.4046856422
CENT_TO_HA = 0.004046856422

SUPPORTED_AREA_UNITS = {
    "hectare": 1.0,
    "hectares": 1.0,
    "ha": 1.0,
    "acre": ACRE_TO_HA,
    "acres": ACRE_TO_HA,
    "cent": CENT_TO_HA,
    "cents": CENT_TO_HA,
    "sq_meter": 0.0001,
    "sq.m": 0.0001,
    "m2": 0.0001,
    "square_meters": 0.0001,
}

SUPPORTED_NUTRIENT_UNITS = {
    "kg/ha": 1.0,
    "kg_per_ha": 1.0,
    "kg/acre": HA_TO_ACRE,       # 1 kg/acre = 2.4710538147 kg/ha
    "kg_per_acre": HA_TO_ACRE,
    "mg/kg": 2.24,               # Standard agronomic depth conversion: 1 mg/kg (ppm) = 2.24 kg/ha
    "ppm": 2.24,
}

SUPPORTED_YIELD_UNITS = {
    "t/ha": 1.0,
    "tonnes/ha": 1.0,
    "tonne/ha": 1.0,
    "ton/ha": 1.0,
    "q/ha": 0.1,             # 1 quintal = 100 kg = 0.1 tonne
    "quintal/ha": 0.1,
    "quintals/ha": 0.1,
    "kg/ha": 0.001,          # 1 kg = 0.001 tonne
}

# Stoichiometric Conversion Factors between Elemental and Oxide Forms
P_TO_P2O5 = 2.29137   # Molecular weight ratio P2O5 / 2P = 141.94 / 61.94
P2O5_TO_P = 0.43642   # 1 / 2.29137
K_TO_K2O = 1.2046     # Molecular weight ratio K2O / 2K = 94.20 / 78.20
K2O_TO_K = 0.83015    # 1 / 1.2046


def convert_acre_to_hectare(acre: float) -> float:
    """Converts acres to hectares using standard 0.4046856422 factor."""
    if acre is None or isinstance(acre, bool):
        raise ValueError("Acre value must be a numeric value.")
    return float(acre) * ACRE_TO_HA


def convert_hectare_to_acre(ha: float) -> float:
    """Converts hectares to acres using standard 2.4710538147 factor."""
    if ha is None or isinstance(ha, bool):
        raise ValueError("Hectare value must be a numeric value.")
    return float(ha) * HA_TO_ACRE


def convert_kg_per_acre_to_kg_per_ha(kg_per_acre: float) -> float:
    """Converts nutrient rate in kg/acre to kg/ha (kg/acre / 0.4046856422)."""
    if kg_per_acre is None or isinstance(kg_per_acre, bool):
        raise ValueError("Nutrient rate must be a numeric value.")
    return float(kg_per_acre) / ACRE_TO_HA


def convert_kg_per_ha_to_kg_per_acre(kg_per_ha: float) -> float:
    """Converts nutrient rate in kg/ha to kg/acre (kg/ha * 0.4046856422)."""
    if kg_per_ha is None or isinstance(kg_per_ha, bool):
        raise ValueError("Nutrient rate must be a numeric value.")
    return float(kg_per_ha) * ACRE_TO_HA


def calculate_farm_total_nutrient(
    rate: float,
    rate_unit: str,
    farm_area: float,
    farm_area_unit: str
) -> float:
    """
    Calculates total kg required for a given farm area without double-converting.
    
    If rate is in kg/acre and area is in acres:
        farm_total = rate * farm_area
    If rate is in kg/ha and area is in hectares:
        farm_total = rate * farm_area
    If rate is in kg/ha and area is in acres:
        farm_total = rate * (farm_area * ACRE_TO_HA)
    If rate is in kg/acre and area is in hectares:
        farm_total = rate * (farm_area * HA_TO_ACRE)
    """
    if rate is None or farm_area is None:
        raise ValueError("Rate and farm area must be numeric.")
    r_val = float(rate)
    a_val = float(farm_area)
    r_u = (rate_unit or "kg/ha").strip().lower().replace(" ", "_")
    a_u = (farm_area_unit or "hectare").strip().lower().replace(" ", "_")

    is_rate_acre = "acre" in r_u
    is_area_acre = "acre" in a_u

    if is_rate_acre and is_area_acre:
        return r_val * a_val
    elif not is_rate_acre and not is_area_acre:
        # rate in kg/ha, area in ha (or cents normalized to ha)
        area_ha = a_val * SUPPORTED_AREA_UNITS.get(a_u, 1.0)
        return r_val * area_ha
    elif is_rate_acre and not is_area_acre:
        area_acres = a_val * (HA_TO_ACRE if a_u in ("ha", "hectare", "hectares") else (SUPPORTED_AREA_UNITS.get(a_u, 1.0) * HA_TO_ACRE))
        return r_val * area_acres
    else:
        # rate in kg/ha, area in acres
        area_ha = a_val * ACRE_TO_HA
        return r_val * area_ha


def convert_area_to_hectares(area: float, unit: str) -> float:
    """Converts farm area to hectares. Raises ValueError if invalid area or unit."""
    if area is None or isinstance(area, bool):
        raise ValueError("Farm area must be a numeric value.")
    try:
        val = float(area)
    except (ValueError, TypeError):
        raise ValueError(f"Farm area '{area}' is not a valid number.")

    if val <= 0:
        raise ValueError(f"Farm area must be greater than 0, got {val}.")

    u_norm = (unit or "hectare").strip().lower().replace(" ", "_")
    if u_norm not in SUPPORTED_AREA_UNITS:
        raise ValueError(
            f"Unsupported farm area unit '{unit}'. Supported units: {', '.join(sorted(set(SUPPORTED_AREA_UNITS.keys())))}"
        )

    return val * SUPPORTED_AREA_UNITS[u_norm]


def convert_target_yield_to_tonnes_per_ha(yield_val: float, unit: str = "t/ha") -> float:
    """Converts target yield to tonnes per hectare (t/ha). Supports t/ha, q/ha, and kg/ha."""
    if yield_val is None or isinstance(yield_val, bool):
        raise ValueError("Target yield must be a numeric value.")
    try:
        val = float(yield_val)
    except (ValueError, TypeError):
        raise ValueError(f"Target yield '{yield_val}' is not a valid number.")

    if val <= 0:
        raise ValueError(f"Target yield must be greater than 0, got {val}.")

    u_norm = (unit or "t/ha").strip().lower().replace(" ", "_")
    if u_norm not in SUPPORTED_YIELD_UNITS:
        raise ValueError(
            f"Unsupported target yield unit '{unit}'. Supported units: {', '.join(sorted(set(SUPPORTED_YIELD_UNITS.keys())))}"
        )

    return val * SUPPORTED_YIELD_UNITS[u_norm]


def normalize_soil_nutrient_value(value: float, unit: str) -> float:
    """Normalizes soil nutrient test value to kg/ha. Raises ValueError if unit is unsupported."""
    if value is None or isinstance(value, bool):
        raise ValueError("Nutrient value must be numeric.")
    try:
        val = float(value)
    except (ValueError, TypeError):
        raise ValueError(f"Nutrient value '{value}' is not a valid number.")

    if val < 0:
        raise ValueError(f"Nutrient value cannot be negative, got {val}.")

    u_norm = (unit or "kg/ha").strip().lower().replace(" ", "_")
    if u_norm not in SUPPORTED_NUTRIENT_UNITS:
        raise ValueError(
            f"Unsupported soil nutrient unit '{unit}'. Supported units: {', '.join(sorted(set(SUPPORTED_NUTRIENT_UNITS.keys())))}"
        )

    return val * SUPPORTED_NUTRIENT_UNITS[u_norm]


def convert_elemental_to_oxide(value: float, nutrient: str) -> float:
    """Converts elemental nutrient (P or K) to its oxide form (P2O5 or K2O)."""
    n = nutrient.strip().upper()
    if n in ("P", "PHOSPHORUS"):
        return value * P_TO_P2O5
    elif n in ("K", "POTASSIUM"):
        return value * K_TO_K2O
    return value


def convert_oxide_to_elemental(value: float, nutrient: str) -> float:
    """Converts oxide nutrient (P2O5 or K2O) to its elemental form (P or K)."""
    n = nutrient.strip().upper()
    if n in ("P2O5", "P", "PHOSPHORUS"):
        return value * P2O5_TO_P
    elif n in ("K2O", "K", "POTASSIUM"):
        return value * K2O_TO_K
    return value
