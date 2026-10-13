"""
Phase 6: Fertilizer Type, Quantity, and Cost Optimization Engine.
Uses Linear Programming (scipy.optimize.linprog) to optimize fertilizer selection and minimize cost.
"""

from .service import optimize_fertilizer_plan, FertilizerOptimizerService

__all__ = ["optimize_fertilizer_plan", "FertilizerOptimizerService"]
