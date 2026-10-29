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
    custom_prices: Optional[Dict[str, Any]] = Field(None, description="Custom local bag prices keyed by product ID (e.g. {'UREA': 280.0, 'DAP': 1400.0})")
    prohibited_combinations: Optional[List[List[str]]] = Field(None, description="Custom list of prohibited product ID pairs")


class FertilizerProductRecommendation(BaseModel):
    product_id: str
    product_name: str
    name: Optional[str] = None
    category: str
    quantity_kg: float
    bags: Any = Field(..., description="Commercial whole bags (int) or fractional bags (float) for smallholders")
    whole_bags: Optional[int] = Field(None, description="Whole commercial bags (integer)")
    loose_kg: Optional[float] = Field(None, description="Loose quantity in kg beyond whole bags")
    bag_size_kg: float
    price_per_bag_inr: Optional[float] = None
    total_cost_inr: Optional[float] = None
    quantity_per_ha_kg: Optional[float] = Field(None, description="Recommended quantity per hectare in kg")
    total_farm_quantity_kg: Optional[float] = Field(None, description="Total recommended quantity for the whole farm in kg")
    nutrient_contributions: Dict[str, float] = Field(default_factory=dict, description="Nutrient contributions in kg: N, P2O5, K2O")
    selection_rationale: Optional[str] = Field(None, description="Agronomic rationale for selecting this product")
    why_recommended: Optional[str] = Field(None, description="Detailed explanation of why this fertilizer was recommended")
    why_recommended_ta: Optional[str] = Field(None, description="Tamil explanation of why this fertilizer was recommended")
    application_timing: Optional[str] = Field(None, description="Agronomic timing and split application stages")
    price_source: Optional[str] = None
    price_effective_date: Optional[str] = None
    price_basis: Optional[str] = Field(None, description="e.g. Statutory Subsidized MRP, Official Controlled Price, Dealer Quotation")
    pricing_mechanism: Optional[str] = Field(None, description="OFFICIAL_CONTROLLED_PRICE, SUBSIDY_RELATED_PRICE, DEALER_QUOTATION, NONE")
    price_status: Optional[str] = Field("VERIFIED", description="VERIFIED, COST_UNAVAILABLE, EXPIRED, CONFLICTING")


class NutrientBalanceDetail(BaseModel):
    required_kg: float
    supplied_kg: float
    surplus_kg: float
    deficit_kg: Optional[float] = Field(0.0, description="Nutrient deficit in kg if target could not be met")
    surplus_pct: Optional[float] = Field(0.0, description="Percentage surplus relative to target requirement")


class SplitApplicationStage(BaseModel):
    stage_name: str
    timing: str
    n_pct: float
    p2o5_pct: float
    k2o_pct: float
    products: Dict[str, float] = Field(default_factory=dict, description="Product quantities in kg for this split stage")


class FertilizerOptimizationResponse(BaseModel):
    status: str = Field(..., description="OPTIMIZATION_SUCCESS, NO_FEASIBLE_SOLUTION, INFEASIBLE, PROVISIONAL_UNVERIFIED, BLOCKED_UNVERIFIED_RULE, VALIDATION_ERROR")
    crop: Optional[str] = None
    farm_area_hectares: float = 1.0
    total_cost_inr: Optional[float] = 0.0
    total_cost_status: Optional[str] = Field("AVAILABLE", description="AVAILABLE, COST_UNAVAILABLE, PARTIAL")
    optimization_method: str = "SciPy Mixed-Integer Linear Programming (HiGHS MILP)"
    is_verified: bool = Field(True, description="True if based on verified agronomic rule")
    is_provisional: bool = Field(False, description="True if provisional/unverified")
    recommendation_type: str = Field("SOIL_SPECIFIC_STCR", description="Recommendation type")
    recommended_products: List[FertilizerProductRecommendation] = Field(default_factory=list)
    nutrient_balance: Dict[str, NutrientBalanceDetail] = Field(default_factory=dict)
    nutrient_surplus_kg: Dict[str, float] = Field(default_factory=dict, description="Nutrient surplus in kg (supplied - required)")
    nutrient_deficit_kg: Dict[str, float] = Field(default_factory=dict, description="Nutrient deficit in kg (required - supplied)")
    has_surplus: bool = Field(False, description="Whether any nutrient has a positive surplus")
    has_deficit: bool = Field(False, description="Whether any nutrient has an unmet deficit")
    surplus_summary: Optional[str] = Field(None, description="Clear agronomic description of surplus")
    custom_prices_applied: bool = Field(False, description="True if farmer custom local prices were used")
    price_data_timestamp: Optional[str] = Field("2026-10-22", description="Timestamp of retail price dataset")
    prices_last_updated: Optional[str] = Field("2026-10-22", description="Date fertilizer price registry was last updated")
    rules_last_updated: Optional[str] = Field("2026-10-22", description="Date agronomic rules were last updated")
    agronomic_rule_source: Optional[str] = Field(None, description="Authoritative rule source e.g. TNAU CPG 2020 / ICAR-STCR")
    optimizer_rationale: Optional[str] = Field(None, description="Summary explanation of cost and packaging trade-offs")
    limiting_constraint: Optional[str] = Field(None, description="Limiting agronomic or packaging constraint if infeasible")
    package_rounding_effects: Optional[Dict[str, Any]] = Field(None, description="Breakdown of discrete packaging rounding vs continuous requirement")
    prohibited_combinations_detected: List[str] = Field(default_factory=list, description="Incompatible fertilizer combinations detected")
    split_application_schedule: List[SplitApplicationStage] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)
