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
    farm_area: Optional[float] = Field(None, description="Farm area numeric value")
    farm_area_unit: Optional[str] = Field(None, description="Farm area unit e.g. acre, ha")
    allowed_fertilizers: Optional[List[str]] = Field(None, description="List of product IDs to consider")
    strategy: Optional[str] = Field("MIN_COST", description="Optimization strategy e.g. MIN_COST")
    phase5_result: Optional[Dict[str, Any]] = Field(None, description="Direct Phase 5 output payload")
    is_verified_rule: Optional[bool] = Field(None, description="Whether rule was verified")
    verification_status: Optional[str] = Field(None, description="Verification status e.g. PENDING_AGRONOMIC_VALIDATION")
    allow_unverified: bool = Field(False, description="Whether unverified rule calculation is permitted as provisional")
    allow_fractional_bags: bool = Field(False, description="Whether fractional bag / loose fertilizer application is permitted (ideal for smallholders)")
    max_surplus_factor: Optional[float] = Field(None, description="Optional upper bound factor on nutrient oversupply (e.g. 1.5 for max 50% surplus)")
    custom_prices: Optional[Dict[str, float]] = Field(None, description="Custom local bag prices keyed by product ID (e.g. {'UREA': 280.0, 'DAP': 1400.0})")


class FertilizerProductRecommendation(BaseModel):
    product_id: str
    product_name: str
    name: Optional[str] = None
    category: str
    quantity_kg: float
    bags: Any = Field(..., description="Commercial whole bags (int) or fractional bags (float) for smallholders")
    bag_size_kg: float
    price_per_bag_inr: float
    total_cost_inr: float
    quantity_per_ha_kg: Optional[float] = Field(None, description="Recommended quantity per hectare in kg")
    total_farm_quantity_kg: Optional[float] = Field(None, description="Total recommended quantity for the whole farm in kg")
    application_timing: Optional[str] = Field(None, description="Agronomic timing and split application stages")
    price_source: Optional[str] = None
    price_effective_date: Optional[str] = None


class NutrientBalanceDetail(BaseModel):
    required_kg: float
    supplied_kg: float
    surplus_kg: float
    surplus_pct: Optional[float] = Field(0.0, description="Percentage surplus relative to target requirement")


class SplitApplicationStage(BaseModel):
    stage_name: str
    timing: str
    n_pct: float
    p2o5_pct: float
    k2o_pct: float
    products: Dict[str, float] = Field(default_factory=dict, description="Product quantities in kg for this split stage")


class FertilizerOptimizationResponse(BaseModel):
    status: str = Field(..., description="OPTIMIZATION_SUCCESS, PROVISIONAL_UNVERIFIED, BLOCKED_UNVERIFIED_RULE, FEASIBLE, INFEASIBLE, VALIDATION_ERROR")
    crop: Optional[str] = None
    farm_area_hectares: float = 1.0
    total_cost_inr: float = 0.0
    optimization_method: str = "SciPy Mixed-Integer Linear Programming (HiGHS MILP)"
    is_verified: bool = Field(True, description="True if based on verified agronomic rule")
    is_provisional: bool = Field(False, description="True if provisional/unverified")
    recommendation_type: str = Field("SOIL_SPECIFIC_STCR", description="Recommendation type")
    recommended_products: List[FertilizerProductRecommendation] = Field(default_factory=list)
    nutrient_balance: Dict[str, NutrientBalanceDetail] = Field(default_factory=dict)
    nutrient_surplus_kg: Dict[str, float] = Field(default_factory=dict, description="Nutrient surplus in kg (supplied - required)")
    has_surplus: bool = Field(False, description="Whether any nutrient has a positive surplus")
    surplus_summary: Optional[str] = Field(None, description="Clear agronomic description of surplus")
    custom_prices_applied: bool = Field(False, description="True if farmer custom local prices were used")
    prices_last_updated: Optional[str] = Field("2026-10-22", description="Date fertilizer price registry was last updated")
    rules_last_updated: Optional[str] = Field("2026-10-22", description="Date agronomic rules were last updated")
    split_application_schedule: List[SplitApplicationStage] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)
