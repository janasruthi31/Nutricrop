"""
Phase 5: NPK Nutrient Requirement Calculation Engine.
Calculates N, P2O5, and K2O requirements using verified Phase 4 agronomic rules.
"""

from .service import calculate_nutrient_requirement, NutrientCalculationService

__all__ = ["calculate_nutrient_requirement", "NutrientCalculationService"]
