"""
Pydantic schemas for Phase 4: Agronomic Rule Selection.
"""
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field


class SoilValuesInput(BaseModel):
    nitrogen: Optional[float] = Field(None, description="Soil N in kg/ha")
    phosphorus: Optional[float] = Field(None, description="Soil P in kg/ha")
    potassium: Optional[float] = Field(None, description="Soil K in kg/ha")
    ph: Optional[float] = Field(None, description="Soil pH")
    organic_carbon: Optional[float] = Field(None, description="Organic Carbon in %")
    phosphorus_method: Optional[str] = Field(None, description="Olsen or Bray")


class TargetYieldRange(BaseModel):
    min: float
    max: float
    unit: str = "t/ha"


class RuleSelectionRequest(BaseModel):
    crop: str = Field(..., description="Crop name e.g. Rice, Cotton (lint), Blackgram")
    variety: Optional[str] = Field(None, description="Crop variety e.g. MCU 5, ADT 36")
    district: Optional[str] = Field(None, description="District name in Tamil Nadu")
    soil_series: Optional[str] = Field(None, description="Soil series name e.g. Palavidhi, Irugur")
    season: Optional[str] = Field(None, description="Cultivation season e.g. Kharif, Rabi, Samba, Rainfed")
    irrigation_method: Optional[str] = Field(None, description="Irrigated or Rainfed")
    target_yield: Optional[float] = Field(None, description="Target yield in t/ha")
    soil_values: Optional[SoilValuesInput] = Field(None, description="Soil test values")


class AgronomicRule(BaseModel):
    rule_id: str
    crop: str
    variety: Optional[str] = None
    soil_series: Optional[List[str]] = None
    district: Optional[List[str]] = None
    season: Optional[List[str]] = None
    irrigation_method: str
    recommendation_method: str
    target_yield_range: Optional[TargetYieldRange] = None
    required_soil_inputs: List[str]
    required_units: Dict[str, str]
    equation_or_dose_reference: str
    source_title: str
    source_url: str
    source_page_or_section: str
    verification_status: str
    applicability_notes: str


class RuleSelectionResponse(BaseModel):
    status: str = Field(..., description="Status e.g. RULE_SELECTED, NEEDS_MORE_INPUT, UNSUPPORTED_CROP, UNSUPPORTED_SOIL_SERIES, NO_MATCHING_RULE, PENDING_VERIFICATION")
    selected_rule_id: Optional[str] = None
    crop: Optional[str] = None
    recommendation_method: Optional[str] = None
    applicable_soil_series: Optional[List[str]] = None
    applicable_season: Optional[Union[List[str], str]] = None
    irrigation_method: Optional[str] = None
    required_inputs: List[str] = Field(default_factory=list)
    source_title: Optional[str] = None
    source_url: Optional[str] = None
    source_page_or_section: Optional[str] = None
    verification_status: Optional[str] = None
    applicability_notes: Optional[str] = None
    missing_inputs: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
