"""
Unit conversions and validation for Phase 5 NPK calculation engine.
Handles farm area unit conversions and soil test unit normalization.
"""

from typing import Tuple

SUPPORTED_AREA_UNITS = {
    "hectare": 1.0,
    "hectares": 1.0,
    "ha": 1.0,
    "acre": 0.404686,
    "acres": 0.404686,
    "cent": 0.00404686,
    "cents": 0.00404686,
    "sq_meter": 0.0001,
    "sq.m": 0.0001,
    "m2": 0.0001,
    "square_meters": 0.0001,
}

SUPPORTED_NUTRIENT_UNITS = {
    "kg/ha": 1.0,
    "kg_per_ha": 1.0,
    "mg/kg": 2.24,  # Standard agronomic depth conversion: 1 mg/kg (ppm) = 2.24 kg/ha
    "ppm": 2.24,
}


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
