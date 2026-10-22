"""
Pydantic schemas for Phase 5 NPK Nutrient Requirement Calculation Engine.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class PreviousFertilizerItem(BaseModel):
    product: str = Field(..., description="Commercial fertilizer product name or ID e.g. DAP, Urea, MOP, SSP")
    quantity: float = Field(..., description="Quantity applied")
    unit: str = Field("kg", description="Unit of quantity: kg, bags, tonnes, kg/acre, kg/ha")
    months_ago: Optional[float] = Field(None, description="Months elapsed since application")


class NutrientCalculationRequest(BaseModel):
    crop: Optional[str] = Field(None, description="Crop name e.g. Rice, Cotton (lint), Blackgram, Groundnut")
    variety: Optional[str] = Field(None, description="Crop variety e.g. ADT 43, MCU 5, CO 51")
    selected_rule_id: Optional[str] = Field(None, description="Phase 4 rule ID e.g. TNAU_STCR_IPNS_RICE_001, TNAU_STD_GROUNDNUT_001")
    soil_series: Optional[str] = Field(None, description="Soil series name e.g. Palavidhi, Irugur")
    season: Optional[str] = Field(None, description="Season e.g. Kharif, Rabi, Samba")
    irrigation_method: Optional[str] = Field(None, description="Irrigated or Rainfed")
    target_yield: Optional[Any] = Field(None, description="Target yield")
    target_yield_unit: Optional[str] = Field("t/ha", description="Target yield unit: t/ha, q/ha, quintal/ha, kg/ha")
    soil_nitrogen: Optional[Any] = Field(None, description="Soil available N (soil-test status)")
    soil_nitrogen_unit: Optional[str] = Field("kg/ha", description="Unit for soil N")
    soil_phosphorus: Optional[Any] = Field(None, description="Soil available P (soil-test status)")
    soil_phosphorus_unit: Optional[str] = Field("kg/ha", description="Unit for soil P")
    soil_phosphorus_method: Optional[str] = Field("Olsen", description="Olsen or Bray")
    soil_potassium: Optional[Any] = Field(None, description="Soil available K (soil-test status)")
    soil_potassium_unit: Optional[str] = Field("kg/ha", description="Unit for soil K")
    organic_carbon: Optional[Any] = Field(None, description="Organic Carbon %")
    ph: Optional[Any] = Field(None, description="Soil pH value")
    ec: Optional[Any] = Field(None, description="Electrical Conductivity in dS/m")
    zinc: Optional[Any] = Field(None, description="Available Zinc in ppm / mg/kg")
    sulphur: Optional[Any] = Field(None, description="Available Sulphur in ppm / mg/kg")
    boron: Optional[Any] = Field(None, description="Available Boron in ppm / mg/kg")
    fym_applied_t_per_ha: Optional[Any] = Field(0.0, description="FYM applied in t/ha (default 0.0)")
    farm_area: Optional[Any] = Field(None, description="Farm area size")
    farm_area_unit: Optional[str] = Field("hectare", description="hectare, acre, cent, sq_meter")
    phase4_result: Optional[Dict[str, Any]] = Field(None, description="Direct Phase 4 selection output")

    # Previous agronomic history inputs
    previous_crop: Optional[str] = Field(None, description="Previous crop grown e.g. Blackgram, Groundnut, Rice, Green Manure")
    previous_fertilizers: Optional[List[PreviousFertilizerItem]] = Field(default_factory=list, description="List of previous fertilizers applied")

    # Dual recommendation mode parameters
    recommendation_mode: Optional[str] = Field("CALCULATED_AGRONOMIC", description="'SOIL_HEALTH_CARD' or 'CALCULATED_AGRONOMIC'")
    printed_n_rate: Optional[float] = Field(None, description="Printed Nitrogen recommendation from soil health card")
    printed_p2o5_rate: Optional[float] = Field(None, description="Printed P2O5 recommendation from soil health card")
    printed_k2o_rate: Optional[float] = Field(None, description="Printed K2O recommendation from soil health card")
    printed_rate_unit: Optional[str] = Field("kg/acre", description="Unit of printed recommendation (default kg/acre)")
    printed_source: Optional[str] = Field("Uploaded Soil Health Card", description="Label of source document")
    allow_unverified: Optional[bool] = Field(False, description="Allow calculation for unverified rule with unverified status flag")
    recommendation_type: Optional[str] = Field(None, description="'SOIL_SPECIFIC_STCR', 'GENERAL_BLANKET', 'SOIL_HEALTH_CARD', 'PROVISIONAL_UNVERIFIED'")



class NutrientCalculationResponse(BaseModel):
    status: str = Field(..., description="CALCULATION_SUCCESS, UNVERIFIED_RULE, PENDING_AGRONOMIC_VALIDATION, MISSING_INPUTS, VALIDATION_ERROR, UNSUPPORTED_CROP, CALCULATION_FAILED")
    crop: Optional[str] = None
    selected_rule_id: Optional[str] = None
    selected_method: Optional[str] = None
    recommendation_mode: str = Field("CALCULATED_AGRONOMIC", description="'SOIL_HEALTH_CARD' or 'CALCULATED_AGRONOMIC'")
    recommendation_type: str = Field("SOIL_SPECIFIC_STCR", description="'SOIL_SPECIFIC_STCR', 'GENERAL_BLANKET', 'SOIL_HEALTH_CARD', 'PROVISIONAL_UNVERIFIED'")
    recommendation_source: Optional[str] = None
    verification_status: Optional[str] = None
    is_verified_rule: bool = False
    is_provisional: bool = False

    # Confidence and fallback labels (Task 2a)
    confidence: Optional[str] = Field("high", description="'high' for soil-specific STCR, 'lower' for general blanket fallback")
    confidence_label: Optional[str] = Field(None, description="'General recommendation (lower confidence)' or 'Soil-specific STCR (high confidence)'")

    # Recommended Range (Task 2c)
    recommended_range_kg_per_ha: Optional[Dict[str, Any]] = Field(None, description="Recommended min/max range per nutrient in kg/ha")
    recommended_range_kg_per_acre: Optional[Dict[str, Any]] = Field(None, description="Recommended min/max range per nutrient in kg/acre")
    blanket_comparison: Optional[Dict[str, Any]] = Field(None, description="Comparison with official TNAU blanket dose and >50% deviation warnings")

    # Micronutrient Advisory (Task 2d)
    micronutrient_advisory: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = Field(default_factory=dict, description="Zinc, Sulphur, and Boron advisory based on TNAU critical limits")

    # Per-hectare rates
    n_req_kg_per_ha: Optional[float] = Field(None, description="Nitrogen requirement in kg/ha")
    net_n_kg_per_ha: Optional[float] = Field(None, description="Nitrogen requirement in kg/ha (alias)")
    p2o5_req_kg_per_ha: Optional[float] = Field(None, description="Phosphorus requirement as P2O5 in kg/ha")
    net_p2o5_kg_per_ha: Optional[float] = Field(None, description="Phosphorus requirement as P2O5 in kg/ha (alias)")
    k2o_req_kg_per_ha: Optional[float] = Field(None, description="Potassium requirement as K2O in kg/ha")
    net_k2o_kg_per_ha: Optional[float] = Field(None, description="Potassium requirement as K2O in kg/ha (alias)")

    # Per-acre rates
    n_req_kg_per_acre: Optional[float] = Field(None, description="Nitrogen requirement in kg/acre")
    p2o5_req_kg_per_acre: Optional[float] = Field(None, description="Phosphorus requirement as P2O5 in kg/acre")
    k2o_req_kg_per_acre: Optional[float] = Field(None, description="Potassium requirement as K2O in kg/acre")

    # Farm area details
    farm_area_hectares: Optional[float] = Field(None, description="Farm area in hectares")
    farm_area_original: Optional[float] = Field(None, description="Original farm area value entered by farmer")
    farm_area_unit_original: Optional[str] = Field(None, description="Original farm area unit (e.g. acre, hectare)")

    # Farm total requirements
    total_n_req_kg: Optional[float] = Field(None, description="Total N requirement for farm area in kg")
    total_farm_n_kg: Optional[float] = Field(None, description="Total N requirement for farm area in kg (alias)")
    total_p2o5_req_kg: Optional[float] = Field(None, description="Total P2O5 requirement for farm area in kg")
    total_farm_p2o5_kg: Optional[float] = Field(None, description="Total P2O5 requirement for farm area in kg (alias)")
    total_k2o_req_kg: Optional[float] = Field(None, description="Total K2O requirement for farm area in kg")
    total_farm_k2o_kg: Optional[float] = Field(None, description="Total K2O requirement for farm area in kg (alias)")

    calculation_method: Optional[str] = Field(None, description="Method name alias")
    calculation_details: Dict[str, Any] = Field(default_factory=dict)
    units: Dict[str, str] = Field(default_factory=lambda: {"per_ha": "kg/ha", "per_acre": "kg/acre", "total": "kg", "area": "hectare"})
    source_title: Optional[str] = None
    source_url: Optional[str] = None
    source_page_or_section: Optional[str] = None
    soil_nutrient_status: Optional[Dict[str, Any]] = Field(default=None, description="Soil test nutrient status (Deficient / Sufficient / Excessive) against verified TNAU thresholds")
    derivation_explanation: Optional[str] = Field(default=None, description="Human-readable step-by-step agronomic explanation of how requirements were derived")
    authoritative_reference: Optional[Dict[str, Any]] = Field(default=None, description="Official reference citation, source document, title, and URL")

    # Agronomic Breakdown per nutrient
    previous_crop: Optional[str] = None
    crop_requirement_kg_per_ha: Optional[Dict[str, float]] = None
    soil_supply_kg_per_ha: Optional[Dict[str, float]] = None
    fym_credit_kg_per_ha: Optional[Dict[str, float]] = None
    previous_crop_credit_kg_per_ha: Optional[Dict[str, float]] = None
    previous_fertilizer_residual_kg_per_ha: Optional[Dict[str, float]] = None
    nutrient_breakdown: Optional[Dict[str, Any]] = None

    warnings: List[str] = Field(default_factory=list)
    missing_inputs: List[str] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)
