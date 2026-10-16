"""
Fertilizer Whole-Bag Optimization Module (Phase 6).
Provides the Mixed-Integer Linear Programming (MILP) cost optimizer
and scheduler interfaces for commercial fertilizer product selection.
"""

from .service import FertilizerOptimizerService, optimize_fertilizer_plan
from .models import (
    FertilizerOptimizationRequest,
    FertilizerOptimizationResponse,
    FertilizerProductRecommendation,
    NutrientBalanceDetail,
    SplitApplicationStage,
)
from .catalog import FERTILIZER_CATALOG, get_fertilizer_catalog

__all__ = [
    "FertilizerOptimizerService",
    "optimize_fertilizer_plan",
    "FertilizerOptimizationRequest",
    "FertilizerOptimizationResponse",
    "FertilizerProductRecommendation",
    "NutrientBalanceDetail",
    "SplitApplicationStage",
    "FERTILIZER_CATALOG",
    "get_fertilizer_catalog",
]
