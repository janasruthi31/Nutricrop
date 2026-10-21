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

    val_norm = value
    if unit in ("kg/acre", "kg/ac"):
        # Convert kg/acre to kg/ha for comparison against official TNAU ratings (1 ha = 2.4710538147 acres)
        val_norm = value * 2.4710538147
    elif unit != ref["unit"]:
        return None  # e.g. mg/kg values are NOT converted to kg/ha without soil bulk density

    if field == "phosphorus":
        if method not in ("Olsen", "Bray"):
            return None  # never guess Olsen vs Bray
        t = ref[method]
        return _rate(val_norm, t["low"], t["high"])
    return _rate(val_norm, ref["low"], ref["high"])

