"""Crop-name check against the crop list of the trained Phase 2 yield model (read-only; model untouched)."""
import json, os

_META = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models", "yield_prediction", "metadata.json")
_FALLBACK = ["Rice", "Maize", "Groundnut", "Sugarcane", "Cotton (lint)", "Ragi", "Banana", "Tomato", "Onion", "Turmeric"]


def _load():
    try:
        with open(_META, encoding="utf-8") as fh:
            return list(json.load(fh)["categories"]["Crop"])
    except (OSError, KeyError, ValueError):
        return _FALLBACK


CROPS = _load()


def known_crop(name):
    k = str(name).strip().lower()
    for c in CROPS:
        if c.lower() == k:
            return c
    return None
