"""
Linear Programming Optimizer Service for Phase 6 Fertilizer Selection and Cost Minimization.
Uses scipy.optimize.linprog to formulate cost-minimization optimization.
"""

import math
from typing import Any, Dict, List, Optional
import numpy as np
from scipy.optimize import linprog

from .catalog import get_fertilizer_catalog
from .models import (
    FertilizerOptimizationRequest,
    FertilizerOptimizationResponse,
    FertilizerProductRecommendation,
    NutrientBalanceDetail,
    SplitApplicationStage,
)

OPTIMIZATION_SUCCESS = "OPTIMIZATION_SUCCESS"
FEASIBLE = "FEASIBLE"
INFEASIBLE = "INFEASIBLE"
VALIDATION_ERROR = "VALIDATION_ERROR"


class FertilizerOptimizerService:
    def __init__(self):
        self.catalog = get_fertilizer_catalog()

    def optimize(self, req: FertilizerOptimizationRequest) -> FertilizerOptimizationResponse:
        warnings: List[str] = []
        validation_errors: List[str] = []

        # Extract target nutrient requirements from Phase 5 output or direct inputs
        n_req, p2o5_req, k2o_req = None, None, None
        crop = req.crop
        area_ha = req.farm_area_hectares or 1.0

        if req.phase5_result:
            if req.phase5_result.get("total_n_req_kg") is not None:
                n_req = req.phase5_result.get("total_n_req_kg")
                p2o5_req = req.phase5_result.get("total_p2o5_req_kg")
                k2o_req = req.phase5_result.get("total_k2o_req_kg")
                if req.phase5_result.get("farm_area_hectares"):
                    area_ha = req.phase5_result.get("farm_area_hectares")
            elif req.phase5_result.get("n_req_kg_per_ha") is not None:
                n_req = req.phase5_result.get("n_req_kg_per_ha") * area_ha
                p2o5_req = req.phase5_result.get("p2o5_req_kg_per_ha") * area_ha
                k2o_req = req.phase5_result.get("k2o_req_kg_per_ha") * area_ha

            if not crop:
                crop = req.phase5_result.get("crop")

        if n_req is None:
            n_req = req.n_req_kg
        if p2o5_req is None:
            p2o5_req = req.p2o5_req_kg
        if k2o_req is None:
            k2o_req = req.k2o_req_kg

        # Validation of input nutrient requirements
        if n_req is None or p2o5_req is None or k2o_req is None:
            validation_errors.append("Target nutrient requirements (N, P2O5, K2O in kg) must be provided.")
        else:
            try:
                n_req = float(n_req)
                p2o5_req = float(p2o5_req)
                k2o_req = float(k2o_req)
            except (ValueError, TypeError):
                validation_errors.append("Nutrient requirements must be valid numbers.")

        if area_ha <= 0:
            validation_errors.append("Farm area in hectares must be greater than 0.")

        if validation_errors:
            return FertilizerOptimizationResponse(
                status=VALIDATION_ERROR,
                crop=crop,
                farm_area_hectares=area_ha,
                validation_errors=validation_errors
            )

        # Filter candidate fertilizers if allowed list is specified
        candidates = self.catalog
        if req.allowed_fertilizers:
            allowed_set = {a.upper() for a in req.allowed_fertilizers}
            candidates = [p for p in candidates if p["id"].upper() in allowed_set]

        if not candidates:
            return FertilizerOptimizationResponse(
                status=VALIDATION_ERROR,
                crop=crop,
                farm_area_hectares=area_ha,
                validation_errors=["No allowed fertilizer products available for optimization."]
            )

        num_vars = len(candidates)
        # Objective vector c: price per kg in INR
        c = np.array([p["price_per_kg_inr"] for p in candidates])

        # Inequality constraints: A_ub * x <= b_ub
        # We need:
        #  sum(n_pct/100 * x_i) >= n_req   => sum(-n_pct/100 * x_i) <= -n_req
        #  sum(p_pct/100 * x_i) >= p2o5_req => sum(-p_pct/100 * x_i) <= -p2o5_req
        #  sum(k_pct/100 * x_i) >= k2o_req  => sum(-k_pct/100 * x_i) <= -k2o_req
        A_ub = []
        b_ub = []

        if n_req > 0:
            A_ub.append([-p["n_pct"] / 100.0 for p in candidates])
            b_ub.append(-n_req)
        if p2o5_req > 0:
            A_ub.append([-p["p2o5_pct"] / 100.0 for p in candidates])
            b_ub.append(-p2o5_req)
        if k2o_req > 0:
            A_ub.append([-p["k2o_pct"] / 100.0 for p in candidates])
            b_ub.append(-k2o_req)

        # Bounds: x_i >= 0
        bounds = [(0, None) for _ in range(num_vars)]

        if not A_ub:
            # Zero nutrient requirement requested
            return FertilizerOptimizationResponse(
                status=OPTIMIZATION_SUCCESS,
                crop=crop,
                farm_area_hectares=area_ha,
                total_cost_inr=0.0,
                recommended_products=[],
                nutrient_balance={
                    "nitrogen": NutrientBalanceDetail(required_kg=0.0, supplied_kg=0.0, surplus_kg=0.0),
                    "phosphorus_p2o5": NutrientBalanceDetail(required_kg=0.0, supplied_kg=0.0, surplus_kg=0.0),
                    "potassium_k2o": NutrientBalanceDetail(required_kg=0.0, supplied_kg=0.0, surplus_kg=0.0),
                },
                warnings=["Nutrient requirement is 0 kg. No fertilizer application required."]
            )

        # Run Linear Programming solver
        res = linprog(c, A_ub=np.array(A_ub), b_ub=np.array(b_ub), bounds=bounds, method="highs")

        if not res.success:
            return FertilizerOptimizationResponse(
                status=INFEASIBLE,
                crop=crop,
                farm_area_hectares=area_ha,
                validation_errors=["Optimization failed to find a feasible fertilizer combination satisfying nutrient constraints."]
            )

        sol_x = res.x
        product_recs: List[FertilizerProductRecommendation] = []
        total_cost = 0.0

        supplied_n, supplied_p2o5, supplied_k2o = 0.0, 0.0, 0.0
        bag_supplied_n, bag_supplied_p2o5, bag_supplied_k2o = 0.0, 0.0, 0.0

        for i, qty in enumerate(sol_x):
            if qty > 0.01:  # Filter out near-zero products
                p = candidates[i]
                qty_kg = round(float(qty), 2)
                bags = math.ceil(qty_kg / p["bag_size_kg"])
                cost = round(bags * p["price_per_bag_inr"], 2)
                total_cost += cost

                supplied_n += qty_kg * (p["n_pct"] / 100.0)
                supplied_p2o5 += qty_kg * (p["p2o5_pct"] / 100.0)
                supplied_k2o += qty_kg * (p["k2o_pct"] / 100.0)

                bag_kg = bags * p["bag_size_kg"]
                bag_supplied_n += bag_kg * (p["n_pct"] / 100.0)
                bag_supplied_p2o5 += bag_kg * (p["p2o5_pct"] / 100.0)
                bag_supplied_k2o += bag_kg * (p["k2o_pct"] / 100.0)

                product_recs.append(FertilizerProductRecommendation(
                    product_id=p["id"],
                    product_name=p["name"],
                    name=p["name"],
                    category=p["category"],
                    quantity_kg=qty_kg,
                    bags=bags,
                    bag_size_kg=p["bag_size_kg"],
                    price_per_bag_inr=p["price_per_bag_inr"],
                    total_cost_inr=cost
                ))

        # Rigorous post-rounding validation: ensure whole bags fulfill required nutrients
        if (n_req > 0 and bag_supplied_n + 1e-4 < n_req) or \
           (p2o5_req > 0 and bag_supplied_p2o5 + 1e-4 < p2o5_req) or \
           (k2o_req > 0 and bag_supplied_k2o + 1e-4 < k2o_req):
            return FertilizerOptimizationResponse(
                status=INFEASIBLE,
                crop=crop,
                farm_area_hectares=area_ha,
                validation_errors=["Ceiling bag rounding violated nutrient requirements. Recommendation rejected as infeasible."]
            )

        supplied_n = round(supplied_n, 2)
        supplied_p2o5 = round(supplied_p2o5, 2)
        supplied_k2o = round(supplied_k2o, 2)

        nutrient_balance = {
            "nitrogen": NutrientBalanceDetail(
                required_kg=round(n_req, 2),
                supplied_kg=supplied_n,
                surplus_kg=round(max(0.0, supplied_n - n_req), 2)
            ),
            "phosphorus_p2o5": NutrientBalanceDetail(
                required_kg=round(p2o5_req, 2),
                supplied_kg=supplied_p2o5,
                surplus_kg=round(max(0.0, supplied_p2o5 - p2o5_req), 2)
            ),
            "potassium_k2o": NutrientBalanceDetail(
                required_kg=round(k2o_req, 2),
                supplied_kg=supplied_k2o,
                surplus_kg=round(max(0.0, supplied_k2o - k2o_req), 2)
            )
        }

        # Generate split application schedule
        split_schedule = self._generate_split_schedule(crop or "General", product_recs)

        return FertilizerOptimizationResponse(
            status=OPTIMIZATION_SUCCESS,
            crop=crop,
            farm_area_hectares=area_ha,
            total_cost_inr=round(total_cost, 2),
            recommended_products=product_recs,
            nutrient_balance=nutrient_balance,
            split_application_schedule=split_schedule,
            warnings=warnings
        )

    def _generate_split_schedule(
        self, crop_name: str, products: List[FertilizerProductRecommendation]
    ) -> List[SplitApplicationStage]:
        """Generates standard TNAU crop split application schedules."""
        c_norm = crop_name.lower()
        stages: List[SplitApplicationStage] = []

        if "rice" in c_norm or "paddy" in c_norm:
            stages = [
                SplitApplicationStage(
                    stage_name="Basal Application",
                    timing="At Sowing / Transplanting",
                    n_pct=50.0, p2o5_pct=100.0, k2o_pct=50.0,
                    products=self._allocate_split(products, n_factor=0.50, p_factor=1.00, k_factor=0.50)
                ),
                SplitApplicationStage(
                    stage_name="Active Tillering",
                    timing="21-25 days after transplanting (DAT)",
                    n_pct=25.0, p2o5_pct=0.0, k2o_pct=25.0,
                    products=self._allocate_split(products, n_factor=0.25, p_factor=0.00, k_factor=0.25)
                ),
                SplitApplicationStage(
                    stage_name="Panicle Initiation",
                    timing="40-45 days after transplanting (DAT)",
                    n_pct=25.0, p2o5_pct=0.0, k2o_pct=25.0,
                    products=self._allocate_split(products, n_factor=0.25, p_factor=0.00, k_factor=0.25)
                )
            ]
        elif "cotton" in c_norm:
            stages = [
                SplitApplicationStage(
                    stage_name="Basal Application",
                    timing="At Sowing",
                    n_pct=50.0, p2o5_pct=100.0, k2o_pct=50.0,
                    products=self._allocate_split(products, n_factor=0.50, p_factor=1.00, k_factor=0.50)
                ),
                SplitApplicationStage(
                    stage_name="Square Formation",
                    timing="45 days after sowing (DAS)",
                    n_pct=25.0, p2o5_pct=0.0, k2o_pct=25.0,
                    products=self._allocate_split(products, n_factor=0.25, p_factor=0.00, k_factor=0.25)
                ),
                SplitApplicationStage(
                    stage_name="Boll Formation",
                    timing="75 days after sowing (DAS)",
                    n_pct=25.0, p2o5_pct=0.0, k2o_pct=25.0,
                    products=self._allocate_split(products, n_factor=0.25, p_factor=0.00, k_factor=0.25)
                )
            ]
        else:
            # Default 2-split schedule for pulses / general crops
            stages = [
                SplitApplicationStage(
                    stage_name="Basal Application",
                    timing="At Sowing / Planting",
                    n_pct=50.0, p2o5_pct=100.0, k2o_pct=50.0,
                    products=self._allocate_split(products, n_factor=0.50, p_factor=1.00, k_factor=0.50)
                ),
                SplitApplicationStage(
                    stage_name="Top Dressing",
                    timing="30-35 days after sowing",
                    n_pct=50.0, p2o5_pct=0.0, k2o_pct=50.0,
                    products=self._allocate_split(products, n_factor=0.50, p_factor=0.00, k_factor=0.50)
                )
            ]

        return stages

    def _allocate_split(
        self, products: List[FertilizerProductRecommendation], n_factor: float, p_factor: float, k_factor: float
    ) -> Dict[str, float]:
        res: Dict[str, float] = {}
        for p in products:
            if p.category.startswith("Straight Nitrogenous"):
                res[p.product_id] = round(p.quantity_kg * n_factor, 2)
            elif p.category.startswith("Straight Potassic"):
                res[p.product_id] = round(p.quantity_kg * k_factor, 2)
            elif "Phosphatic" in p.category or "Complex" in p.category:
                res[p.product_id] = round(p.quantity_kg * p_factor, 2)
            else:
                res[p.product_id] = round(p.quantity_kg * n_factor, 2)
        return res


def optimize_fertilizer_plan(req: FertilizerOptimizationRequest) -> FertilizerOptimizationResponse:
    service = FertilizerOptimizerService()
    return service.optimize(req)
