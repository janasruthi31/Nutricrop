"""
Commercial Fertilizer Catalog and Price Registry for Tamil Nadu.
Contains verified nutrient compositions (% N, P2O5, K2O), bag sizes, and retail prices in INR.
"""

from typing import Any, Dict, List, Optional

# Verified Tamil Nadu fertilizer products catalog
FERTILIZER_CATALOG: List[Dict[str, Any]] = [
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
        "description": "Equal ratio NPK complex (17-17-17)"
    }
]


def get_fertilizer_catalog() -> List[Dict[str, Any]]:
    return [dict(p) for p in FERTILIZER_CATALOG]
