"""
Safe unit handling. Only EXACT, assumption-free conversions are performed:
  ppm (soil, mass basis) -> mg/kg        (identical quantity)
  g/kg  -> %        for organic carbon   (1 % = 10 g/kg)
  uS/cm -> dS/m                          (1 dS/m = 1000 uS/cm);  mmhos/cm and mS/cm == dS/m
NEVER done: mg/kg <-> kg/ha (needs soil depth + bulk density), Olsen P <-> Bray P, N/P/K between any
other units. Unrecognised units are returned as None so callers flag them instead of guessing.
"""
import re

_UNIT_ALIASES = {
    "kg/ha": "kg/ha", "kgha-1": "kg/ha", "kgha": "kg/ha", "kg/hectare": "kg/ha", "kgperha": "kg/ha", "kg/hec": "kg/ha",
    "mg/kg": "mg/kg", "mgkg-1": "mg/kg", "mgkg": "mg/kg", "mg/kgsoil": "mg/kg",
    "ppm": "ppm", "%": "%", "percent": "%", "percentage": "%", "per cent": "%", "percentage(%)": "%",
    "(%)": "%", "(oc%)": "%", "oc%": "%",
    "g/kg": "g/kg", "gkg-1": "g/kg",
    "ds/m": "dS/m", "dsm-1": "dS/m", "ds/cm": None, "mmhos/cm": "dS/m", "mmho/cm": "dS/m", "ms/cm": "dS/m",
    "(ds/m)": "dS/m",
    "us/cm": "uS/cm", "µs/cm": "uS/cm", "μs/cm": "uS/cm", "umhos/cm": "uS/cm", "μmhos/cm": "uS/cm",
    "kg/acre": "kg/acre", "kg/ac": "kg/acre", "lb/acre": "lb/acre", "lbs/acre": "lb/acre",
    "கிலோ/ஏக்கர்": "kg/acre", "கிலோ/ஹெக்டேர்": "kg/ha", "கிலோ/ஏக்": "kg/acre",
    "(கிலோ/ஏக்கர்)": "kg/acre", "கிலோ/ஏக்கர்": "kg/acre",
}


def canonical_unit_token(raw):
    """Return a recognised unit token (possibly one we cannot safely convert, e.g. kg/acre) or None."""
    if raw is None:
        return None
    s = str(raw).strip().lower().replace(" ", "").replace("\u00b5", "µ").replace("^-1", "-1").replace("⁻¹", "-1")
    s = s.rstrip(".,;:")
    if s in _UNIT_ALIASES:
        return _UNIT_ALIASES[s]
    s2 = re.sub(r"[()\[\]]", "", s)
    return _UNIT_ALIASES.get(s2)


def normalize_value_unit(field, value, raw_unit):
    """
    Returns (value, unit, note, original_unit). `unit` is None if unknown/unsafe; `note` explains an exact conversion.
    Values are only changed by exact/standard conversions.
    """
    tok = canonical_unit_token(raw_unit)
    if tok is None:
        return value, None, None, raw_unit
    if tok == "ppm":
        return value, "mg/kg", "ppm treated as mg/kg (identical for soil mass basis)", raw_unit
    if tok == "g/kg" and field == "organic_carbon" and value is not None:
        return round(value / 10.0, 6), "%", "g/kg converted to % (1 % = 10 g/kg)", raw_unit
    if tok == "uS/cm" and field == "ec" and value is not None:
        return round(value / 1000.0, 6), "dS/m", "uS/cm converted to dS/m (/1000)", raw_unit
    if tok == "kg/acre":
        return value, "kg/acre", None, raw_unit
    return value, tok, None, raw_unit
