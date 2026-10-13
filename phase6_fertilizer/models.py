"""
Pydantic schemas for Phase 6 Fertilizer Type, Quantity, and Cost Optimization Engine.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class FertilizerOptimizationRequest(BaseModel):
    n_req_kg: Optional[float] = Field(None, description="Target Nitrogen requirement in kg")
    p2o5_req_kg: Optional[float] = Field(None, description="Target P2O5 requirement in kg")
    k2o_req_kg: Optional[float] = Field(None, description="Target K2O requirement in kg")
    crop: Optional[str] = Field(None, description="Crop name for split schedule generation")
    farm_area_hectares: Optional[float] = Field(1.0, description="Farm area in hectares")
    allowed_fertilizers: Optional[List[str]] = Field(None, description="List of product IDs to consider")
    strategy: Optional[str] = Field("MIN_COST", description="Optimization strategy e.g. MIN_COST")
    phase5_result: Optional[Dict[str, Any]] = Field(None, description="Direct Phase 5 output payload")


class FertilizerProductRecommendation(BaseModel):
    product_id: str
    product_name: str
    name: Optional[str] = None
    category: str
    quantity_kg: float
    bags: int
    bag_size_kg: float
    price_per_bag_inr: float
    total_cost_inr: float


class NutrientBalanceDetail(BaseModel):
    required_kg: float
    supplied_kg: float
    surplus_kg: float


class SplitApplicationStage(BaseModel):
    stage_name: str
    timing: str
    n_pct: float
    p2o5_pct: float
    k2o_pct: float
    products: Dict[str, float] = Field(default_factory=dict, description="Product quantities in kg for this split stage")


class FertilizerOptimizationResponse(BaseModel):
    status: str = Field(..., description="OPTIMIZATION_SUCCESS, FEASIBLE, INFEASIBLE, VALIDATION_ERROR")
    crop: Optional[str] = None
    farm_area_hectares: float = 1.0
    total_cost_inr: float = 0.0
    optimization_method: str = "Continuous LP (SciPy HiGHS) with Ceiling Bag Rounding"
    recommended_products: List[FertilizerProductRecommendation] = Field(default_factory=list)
    nutrient_balance: Dict[str, NutrientBalanceDetail] = Field(default_factory=dict)
    split_application_schedule: List[SplitApplicationStage] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)
