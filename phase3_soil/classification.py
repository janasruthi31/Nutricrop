"""TNAU soil-status classification (Low / Medium / High). STATUS ONLY - never a fertilizer dose."""
from .tnau_reference import TNAU_RATINGS


def _rate(value, low, high):
    if value < low:
        return "Low"
    if value > high:
        return "High"
    return "Medium"


def classify(field, value, unit, method=None):
    """Return 'Low' | 'Medium' | 'High' or None when no applicable TNAU threshold (unit/method mismatch, unsupported field)."""
    if value is None or field not in TNAU_RATINGS:
        return None
    ref = TNAU_RATINGS[field]
    if unit != ref["unit"]:
        return None  # e.g. mg/kg values are NOT converted to kg/ha, so they are not classified
    if field == "phosphorus":
        if method not in ("Olsen", "Bray"):
            return None  # never guess Olsen vs Bray
        t = ref[method]
        return _rate(value, t["low"], t["high"])
    return _rate(value, ref["low"], ref["high"])
