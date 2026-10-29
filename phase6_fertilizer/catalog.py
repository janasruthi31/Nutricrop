"""
Commercial Fertilizer Catalog and Price Registry for Tamil Nadu.
Contains verified nutrient compositions (% N, P2O5, K2O), bag sizes, and retail prices in INR.
"""

import json
import os
from typing import Any, Dict, List, Optional

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_PRICES_JSON_PATH = os.path.join(_BASE_DIR, "data", "agronomy", "fertilizer_prices.json")

CATALOG_LAST_UPDATED = "2026-10-22"

# Default fallback catalog
_DEFAULT_CATALOG: List[Dict[str, Any]] = [
    {
        "id": "UREA",
        "name": "Neem Coated Urea",
        "category": "Straight Nitrogenous",
        "n_pct": 46.0,
        "p2o5_pct": 0.0,
        "k2o_pct": 0.0,
        "bag_size_kg": 45.0,
        "price_per_bag_inr": 266.50,
        "price_per_kg_inr": 5.92,
        "currency": "INR",
        "package_unit": "bag",
        "price_basis": "Statutory Subsidized Maximum Retail Price (Statutory MRP)",
        "pricing_mechanism": "OFFICIAL_CONTROLLED_PRICE",
        "price_status": "VERIFIED",
        "source": "Department of Fertilizers, Ministry of Chemicals & Fertilizers, GoI (Statutory MRP notification)",
        "effective_date": "2024-04-01",
        "last_updated": "2026-10-22",
        "verification_status": "VERIFIED",
        "description": "Standard Nitrogen source (46% N)"
    },
    {
        "id": "DAP",
        "name": "Di-Ammonium Phosphate (DAP)",
        "category": "Complex / Phosphatic",
        "n_pct": 18.0,
        "p2o5_pct": 46.0,
        "k2o_pct": 0.0,
        "bag_size_kg": 50.0,
        "price_per_bag_inr": 1350.00,
        "price_per_kg_inr": 27.00,
        "currency": "INR",
        "package_unit": "bag",
        "price_basis": "Nutrient Based Subsidy (NBS) Policy Subsidized MRP",
        "pricing_mechanism": "SUBSIDY_RELATED_PRICE",
        "price_status": "VERIFIED",
        "source": "Department of Fertilizers, GoI (Nutrient Based Subsidy Notification 2024-25)",
        "effective_date": "2024-04-01",
        "last_updated": "2026-10-22",
        "verification_status": "VERIFIED",
        "description": "High Phosphorus complex (18% N, 46% P2O5)"
    },
    {
        "id": "MOP",
        "name": "Muriate of Potash (MOP)",
        "category": "Straight Potassic",
        "n_pct": 0.0,
        "p2o5_pct": 0.0,
        "k2o_pct": 60.0,
        "bag_size_kg": 50.0,
        "price_per_bag_inr": 1700.00,
        "price_per_kg_inr": 34.00,
        "currency": "INR",
        "package_unit": "bag",
        "price_basis": "Nutrient Based Subsidy (NBS) Policy Subsidized MRP",
        "pricing_mechanism": "SUBSIDY_RELATED_PRICE",
        "price_status": "VERIFIED",
        "source": "Department of Fertilizers, GoI (NBS Subsidy Schedule for Potassic Fertilizers)",
        "effective_date": "2024-04-01",
        "last_updated": "2026-10-22",
        "verification_status": "VERIFIED",
        "description": "Potassium source (60% K2O)"
    },
    {
        "id": "SSP",
        "name": "Single Super Phosphate (SSP)",
        "category": "Straight Phosphatic",
        "n_pct": 0.0,
        "p2o5_pct": 16.0,
        "k2o_pct": 0.0,
        "bag_size_kg": 50.0,
        "price_per_bag_inr": 600.00,
        "price_per_kg_inr": 12.00,
        "currency": "INR",
        "package_unit": "bag",
        "price_basis": "State Cooperative Subsidized Retail Price / NBS Schedule",
        "pricing_mechanism": "SUBSIDY_RELATED_PRICE",
        "price_status": "VERIFIED",
        "source": "Tamil Nadu Cooperative Marketing Federation (TANFED) / NBS Price Schedule",
        "effective_date": "2024-04-01",
        "last_updated": "2026-10-22",
        "verification_status": "VERIFIED",
        "description": "Phosphorus source with Sulphur (16% P2O5)"
    },
    {
        "id": "COMPLEX_20_20_0",
        "name": "Complex 20:20:0:0 (Ammonium Phosphate Sulphate)",
        "category": "Complex",
        "n_pct": 20.0,
        "p2o5_pct": 20.0,
        "k2o_pct": 0.0,
        "bag_size_kg": 50.0,
        "price_per_bag_inr": 1250.00,
        "price_per_kg_inr": 25.00,
        "currency": "INR",
        "package_unit": "bag",
        "price_basis": "State Cooperative Complex Fertilizer Retail Rate",
        "pricing_mechanism": "SUBSIDY_RELATED_PRICE",
        "price_status": "VERIFIED",
        "source": "TANFED Commercial Price Schedule 2024",
        "effective_date": "2024-04-01",
        "last_updated": "2026-10-22",
        "verification_status": "VERIFIED",
        "description": "Balanced NP complex (20% N, 20% P2O5)"
    },
    {
        "id": "COMPLEX_17_17_17",
        "name": "Complex 17:17:17",
        "category": "Complex NPK",
        "n_pct": 17.0,
        "p2o5_pct": 17.0,
        "k2o_pct": 17.0,
        "bag_size_kg": 50.0,
        "price_per_bag_inr": 1450.00,
        "price_per_kg_inr": 29.00,
        "currency": "INR",
        "package_unit": "bag",
        "price_basis": "State Cooperative Complex Fertilizer Retail Rate",
        "pricing_mechanism": "SUBSIDY_RELATED_PRICE",
        "price_status": "VERIFIED",
        "source": "TANFED Commercial Price Schedule 2024",
        "effective_date": "2024-04-01",
        "last_updated": "2026-10-22",
        "verification_status": "VERIFIED",
        "description": "Equal ratio NPK complex (17-17-17)"
    }
]

def _load_catalog() -> tuple[List[Dict[str, Any]], str]:
    if os.path.exists(_PRICES_JSON_PATH):
        try:
            with open(_PRICES_JSON_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("products", _DEFAULT_CATALOG), data.get("last_updated", CATALOG_LAST_UPDATED)
        except Exception:
            pass
    return _DEFAULT_CATALOG, CATALOG_LAST_UPDATED

_loaded_catalog, CATALOG_LAST_UPDATED = _load_catalog()
FERTILIZER_CATALOG: List[Dict[str, Any]] = _loaded_catalog


def get_fertilizer_catalog() -> List[Dict[str, Any]]:
    return [dict(p) for p in FERTILIZER_CATALOG]


def get_catalog_last_updated() -> str:
    return CATALOG_LAST_UPDATED
