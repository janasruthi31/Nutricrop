"""
Pydantic schemas for Phase 5 NPK Nutrient Requirement Calculation Engine.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class NutrientCalculationRequest(BaseModel):
    crop: Optional[str] = Field(None, description="Crop name e.g. Rice, Cotton (lint), Blackgram")
    selected_rule_id: Optional[str] = Field(None, description="Phase 4 rule ID e.g. TNAU_STCR_IPNS_RICE_001")
    soil_series: Optional[str] = Field(None, description="Soil series name e.g. Palavidhi, Irugur")
    season: Optional[str] = Field(None, description="Season e.g. Kharif, Rabi, Samba")
    irrigation_method: Optional[str] = Field(None, description="Irrigated or Rainfed")
    target_yield: Optional[Any] = Field(None, description="Target yield in t/ha")
    soil_nitrogen: Optional[Any] = Field(None, description="Soil available N")
    soil_nitrogen_unit: Optional[str] = Field("kg/ha", description="Unit for soil N")
    soil_phosphorus: Optional[Any] = Field(None, description="Soil available P")
    soil_phosphorus_unit: Optional[str] = Field("kg/ha", description="Unit for soil P")
    soil_phosphorus_method: Optional[str] = Field("Olsen", description="Olsen or Bray")
    soil_potassium: Optional[Any] = Field(None, description="Soil available K")
    soil_potassium_unit: Optional[str] = Field("kg/ha", description="Unit for soil K")
    organic_carbon: Optional[Any] = Field(None, description="Organic Carbon %")
    fym_applied_t_per_ha: Optional[Any] = Field(None, description="FYM applied in t/ha (default 12.5 for IPNS)")
    farm_area: Optional[Any] = Field(None, description="Farm area size")
    farm_area_unit: Optional[str] = Field("hectare", description="hectare, acre, cent, sq_meter")
    phase4_result: Optional[Dict[str, Any]] = Field(None, description="Direct Phase 4 selection output")


class NutrientCalculationResponse(BaseModel):
    status: str = Field(..., description="CALCULATION_SUCCESS, UNVERIFIED_RULE, MISSING_INPUTS, VALIDATION_ERROR, UNSUPPORTED_CROP, CALCULATION_FAILED")
    crop: Optional[str] = None
    selected_rule_id: Optional[str] = None
    selected_method: Optional[str] = None
    n_req_kg_per_ha: Optional[float] = Field(None, description="Nitrogen requirement in kg/ha")
    p2o5_req_kg_per_ha: Optional[float] = Field(None, description="Phosphorus requirement as P2O5 in kg/ha")
    k2o_req_kg_per_ha: Optional[float] = Field(None, description="Potassium requirement as K2O in kg/ha")
    farm_area_hectares: Optional[float] = Field(None, description="Farm area in hectares")
    total_n_req_kg: Optional[float] = Field(None, description="Total N requirement for farm area in kg")
    total_p2o5_req_kg: Optional[float] = Field(None, description="Total P2O5 requirement for farm area in kg")
    total_k2o_req_kg: Optional[float] = Field(None, description="Total K2O requirement for farm area in kg")
    calculation_details: Dict[str, Any] = Field(default_factory=dict)
    units: Dict[str, str] = Field(default_factory=lambda: {"per_ha": "kg/ha", "total": "kg", "area": "hectare"})
    source_title: Optional[str] = None
    source_url: Optional[str] = None
    source_page_or_section: Optional[str] = None
    warnings: List[str] = Field(default_factory=list)
    missing_inputs: List[str] = Field(default_factory=list)
    validation_errors: List[str] = Field(default_factory=list)
