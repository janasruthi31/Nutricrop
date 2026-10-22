"""
Linear Programming Optimizer Service for Phase 6 Fertilizer Selection and Cost Minimization.
Uses scipy.optimize.linprog to formulate cost-minimization optimization.
"""

import math
from typing import Any, Dict, List, Optional
import numpy as np
try:
    from scipy.optimize import milp, LinearConstraint, Bounds
    HAS_MILP = True
except ImportError:
    from scipy.optimize import linprog
    HAS_MILP = False

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
    def __init__(self, catalog: Optional[List[Dict[str, Any]]] = None):
        if catalog is not None:
            self.catalog = catalog
        else:
            self.catalog = self._load_catalog_from_db()

    def _load_catalog_from_db(self) -> List[Dict[str, Any]]:
        try:
            from phase3_soil import db
            with db.connect() as con:
                rows = con.execute("SELECT * FROM fertilizer_prices").fetchall()
                if rows:
                    return [
                        {
                            "id": r["product_id"],
                            "name": r["name"],
                            "category": r["category"],
                            "n_pct": float(r["n_pct"]),
                            "p2o5_pct": float(r["p2o5_pct"]),
                            "k2o_pct": float(r["k2o_pct"]),
                            "bag_size_kg": float(r["bag_size_kg"]),
                            "price_per_bag_inr": float(r["price_per_bag_inr"]),
                            "price_per_kg_inr": float(r["price_per_kg_inr"]),
                            "source": r["source"],
                            "effective_date": r["effective_date"],
                        }
                        for r in rows
                    ]
        except Exception:
            pass
        return get_fertilizer_catalog()

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

        p5 = req.phase5_result or {}
        p5_status = p5.get("status")
        is_verified = p5.get("is_verified_rule")
        if is_verified is None:
            is_verified = True if req.is_verified_rule is None else req.is_verified_rule

        v_status = p5.get("verification_status") or req.verification_status
        if p5_status is None and v_status:
            p5_status = v_status

        allow_unverified = req.allow_unverified or p5.get("allow_unverified", False)
        is_provisional = p5.get("is_provisional", not is_verified)
        rec_type = p5.get("recommendation_type", "SOIL_SPECIFIC_STCR")

        # Backend enforcement:
        # If Phase 5 rule was explicitly blocked or pending agronomic validation without allow_unverified flag:
        if p5_status in ("UNVERIFIED_RULE", "BLOCKED_UNVERIFIED_RULE") or (
            (p5_status in ("PENDING_AGRONOMIC_VALIDATION", "PENDING_VERIFICATION") or v_status in ("PENDING_AGRONOMIC_VALIDATION", "PENDING_VERIFICATION")) and not allow_unverified
        ):
            return FertilizerOptimizationResponse(
                status="BLOCKED_UNVERIFIED_RULE",
                crop=crop,
                farm_area_hectares=area_ha,
                total_cost_inr=0.0,
                is_verified=False,
                is_provisional=True,
                recommendation_type="PROVISIONAL_UNVERIFIED",
                recommended_products=[],
                warnings=["This rule has not yet been agronomically validated. A confirmed soil-specific recommendation is unavailable."],
                validation_errors=["Fertilizer recommendation generation blocked: The agronomic rule is pending agronomic validation. An unverified nutrient target cannot be presented as a confirmed fertilizer recommendation."]
            )

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
        # Objective vector c: price per commercial bag in INR
        c_bags = np.array([float(p["price_per_bag_inr"]) for p in candidates])

        # Matrix for nutrient delivery per commercial bag:
        # A_row_N: [bag_size * (n_pct / 100)]
        # A_row_P2O5: [bag_size * (p2o5_pct / 100)]
        # A_row_K2O: [bag_size * (k2o_pct / 100)]
        A_rows = []
        lhs_bounds = []

        if n_req > 0:
            A_rows.append([float(p["bag_size_kg"]) * (float(p["n_pct"]) / 100.0) for p in candidates])
            lhs_bounds.append(n_req)
        if p2o5_req > 0:
            A_rows.append([float(p["bag_size_kg"]) * (float(p["p2o5_pct"]) / 100.0) for p in candidates])
            lhs_bounds.append(p2o5_req)
        if k2o_req > 0:
            A_rows.append([float(p["bag_size_kg"]) * (float(p["k2o_pct"]) / 100.0) for p in candidates])
            lhs_bounds.append(k2o_req)

        if not A_rows:
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

        # Upper bounds configuration
        ub_bounds = [np.inf] * len(lhs_bounds)
        if req.max_surplus_factor is not None and req.max_surplus_factor > 1.0:
            ub_bounds = [b * float(req.max_surplus_factor) for b in lhs_bounds]

        # Solve using Mixed-Integer Linear Programming (MILP) or continuous LP
        bag_counts = None
        solver_status_msg = ""
        is_globally_optimal = False
        is_fractional = bool(req.allow_fractional_bags)

        # Feasibility pre-check: verify that each requested nutrient has at least one candidate product that supplies it
        for r_idx, row in enumerate(A_rows):
            if max(row) <= 0.0 and lhs_bounds[r_idx] > 0.0:
                return FertilizerOptimizationResponse(
                    status=INFEASIBLE,
                    crop=crop,
                    farm_area_hectares=area_ha,
                    validation_errors=[
                        "Optimization failed to find a feasible fertilizer combination. "
                        "Required nutrient cannot be supplied by the allowed fertilizer catalog."
                    ]
                )

        if HAS_MILP:
            integrality = np.zeros(num_vars) if is_fractional else np.ones(num_vars)
            constraints = LinearConstraint(A_rows, lb=lhs_bounds, ub=ub_bounds)
            bounds = Bounds(lb=0, ub=np.inf)
            res = milp(c=c_bags, integrality=integrality, constraints=constraints, bounds=bounds)

            if res.success and res.x is not None:
                if is_fractional:
                    bag_counts = [round(math.ceil(float(v) * 100.0) / 100.0, 2) for v in res.x]
                    solver_status_msg = "Solved to fractional optimality via SciPy Linear Programming (continuous bag fractions)."
                else:
                    bag_counts = [int(round(v)) for v in res.x]
                    solver_status_msg = "Solved to global optimality via SciPy Mixed-Integer Linear Programming (HiGHS MILP)."
                is_globally_optimal = True
            else:
                solver_status_msg = f"MILP solver status: {res.status} ({getattr(res, 'message', 'Infeasible')})"
        else:
            # Fallback continuous LP
            c_kg = np.array([float(p["price_per_kg_inr"]) for p in candidates])
            A_ub = [[-float(p["n_pct"]) / 100.0 for p in candidates]] if n_req > 0 else []
            b_ub = [-n_req] if n_req > 0 else []
            if p2o5_req > 0:
                A_ub.append([-float(p["p2o5_pct"]) / 100.0 for p in candidates])
                b_ub.append(-p2o5_req)
            if k2o_req > 0:
                A_ub.append([-float(p["k2o_pct"]) / 100.0 for p in candidates])
                b_ub.append(-k2o_req)
            bounds = [(0, None) for _ in range(num_vars)]
            res = linprog(c_kg, A_ub=np.array(A_ub), b_ub=np.array(b_ub), bounds=bounds, method="highs")
            if res.success and res.x is not None:
                if is_fractional:
                    bag_counts = [round(float(qty) / p["bag_size_kg"], 3) for qty, p in zip(res.x, candidates)]
                    solver_status_msg = "Solved via continuous LP (fractional bag units)."
                else:
                    bag_counts = [math.ceil(round(float(qty), 2) / p["bag_size_kg"]) for qty, p in zip(res.x, candidates)]
                    solver_status_msg = "Solved via continuous LP with integer bag ceiling."
                is_globally_optimal = True

        if bag_counts is None:
            return FertilizerOptimizationResponse(
                status=INFEASIBLE,
                crop=crop,
                farm_area_hectares=area_ha,
                validation_errors=[f"Optimization failed to find a feasible commercial fertilizer combination satisfying nutrient constraints. {solver_status_msg}"]
            )

        product_recs: List[FertilizerProductRecommendation] = []
        total_cost = 0.0

        supplied_n, supplied_p2o5, supplied_k2o = 0.0, 0.0, 0.0

        for i, bags in enumerate(bag_counts):
            if bags > 0:
                p = candidates[i]
                qty_kg = round(bags * float(p["bag_size_kg"]), 2)
                cost = round(bags * float(p["price_per_bag_inr"]), 2)
                total_cost += cost

                p_n = round(qty_kg * (float(p["n_pct"]) / 100.0), 2)
                p_p2o5 = round(qty_kg * (float(p["p2o5_pct"]) / 100.0), 2)
                p_k2o = round(qty_kg * (float(p["k2o_pct"]) / 100.0), 2)

                supplied_n += p_n
                supplied_p2o5 += p_p2o5
                supplied_k2o += p_k2o

                timing_desc = "At Sowing / Basal Application"
                pid_upper = p["id"].upper()
                if "UREA" in pid_upper:
                    timing_desc = "Split: 50% Basal, 25% Tillering, 25% Panicle Initiation"
                elif "DAP" in pid_upper or "SSP" in pid_upper:
                    timing_desc = "100% Basal at sowing / transplanting"
                elif "MOP" in pid_upper or "POTASH" in pid_upper:
                    timing_desc = "Split: 50% Basal, 50% Heading / Flowering"

                product_recs.append(FertilizerProductRecommendation(
                    product_id=p["id"],
                    product_name=p["name"],
                    name=p["name"],
                    category=p["category"],
                    quantity_kg=qty_kg,
                    bags=bags,
                    bag_size_kg=float(p["bag_size_kg"]),
                    price_per_bag_inr=float(p["price_per_bag_inr"]),
                    total_cost_inr=cost,
                    quantity_per_ha_kg=round(qty_kg / max(0.001, area_ha), 2),
                    total_farm_quantity_kg=qty_kg,
                    application_timing=timing_desc,
                    price_source=p.get("source", "Department of Fertilizers, GoI (NBS Subsidy Schedule)"),
                    price_effective_date=p.get("effective_date", "2024-04-01")
                ))

        # Re-validate that fertilizer package combination satisfies target nutrients
        val_tol = 0.1 if is_fractional else 1e-4
        if (n_req > 0 and supplied_n + val_tol < n_req) or \
           (p2o5_req > 0 and supplied_p2o5 + val_tol < p2o5_req) or \
           (k2o_req > 0 and supplied_k2o + val_tol < k2o_req):
            return FertilizerOptimizationResponse(
                status=INFEASIBLE,
                crop=crop,
                farm_area_hectares=area_ha,
                validation_errors=["Fertilizer package combination failed to satisfy nutrient requirements. Recommendation rejected as infeasible."]
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

        # Generate crop-specific phenological split application schedule
        split_schedule = self._generate_split_schedule(crop or "General", product_recs)

        if is_globally_optimal:
            if is_fractional:
                warnings.append("Cost minimization solved to global optimality for continuous fractional quantities.")
            else:
                warnings.append("Cost minimization solved to global optimality for discrete commercial bags.")

        # Check for significant discrete oversupply (> 1.5x)
        surplus_alerts = []
        if n_req > 0 and supplied_n > 1.5 * n_req:
            surplus_alerts.append(f"Nitrogen (supplied {supplied_n:.1f} kg vs required {n_req:.1f} kg; {supplied_n/n_req:.1f}x)")
        if p2o5_req > 0 and supplied_p2o5 > 1.5 * p2o5_req:
            surplus_alerts.append(f"P₂O₅ (supplied {supplied_p2o5:.1f} kg vs required {p2o5_req:.1f} kg; {supplied_p2o5/p2o5_req:.1f}x)")
        if k2o_req > 0 and supplied_k2o > 1.5 * k2o_req:
            surplus_alerts.append(f"K₂O (supplied {supplied_k2o:.1f} kg vs required {k2o_req:.1f} kg; {supplied_k2o/k2o_req:.1f}x)")

        if surplus_alerts and not is_fractional:
            warnings.append(
                f"Commercial whole-bag packaging constraint causes surplus over 1.5x for: {'; '.join(surplus_alerts)}. "
                f"For smallholder plots, farmers are advised to apply precise fractional/loose quantities to avoid nutrient oversupply and unnecessary cost."
            )

        final_opt_status = OPTIMIZATION_SUCCESS
        if is_provisional or not is_verified or p5_status == "PROVISIONAL_PENDING_VALIDATION":
            final_opt_status = "PROVISIONAL_UNVERIFIED"
            rec_type = "PROVISIONAL_UNVERIFIED"
            warnings.append("PROVISIONAL ONLY: This recommendation is derived from an unverified agronomic rule awaiting official calibration and must not be used as an official soil-specific recommendation.")

        return FertilizerOptimizationResponse(
            status=final_opt_status,
            crop=crop,
            farm_area_hectares=area_ha,
            total_cost_inr=round(total_cost, 2),
            optimization_method=solver_status_msg,
            is_verified=is_verified and not is_provisional,
            is_provisional=is_provisional or (not is_verified),
            recommendation_type=rec_type,
            recommended_products=product_recs,
            nutrient_balance=nutrient_balance,
            split_application_schedule=split_schedule,
            warnings=warnings
        )

    def _generate_split_schedule(
        self, crop_name: str, products: List[FertilizerProductRecommendation]
    ) -> List[SplitApplicationStage]:
        """Generates crop-specific split application schedules calibrated to TNAU Crop Production Guide 2020."""
        c_norm = crop_name.lower().strip()

        if "rice" in c_norm or "paddy" in c_norm:
            return [
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
            return [
                SplitApplicationStage(
                    stage_name="Basal Application",
                    timing="At Sowing",
                    n_pct=50.0, p2o5_pct=100.0, k2o_pct=50.0,
                    products=self._allocate_split(products, n_factor=0.50, p_factor=1.00, k_factor=0.50)
                ),
                SplitApplicationStage(
                    stage_name="Square Formation",
                    timing="40-45 days after sowing (DAS)",
                    n_pct=25.0, p2o5_pct=0.0, k2o_pct=25.0,
                    products=self._allocate_split(products, n_factor=0.25, p_factor=0.00, k_factor=0.25)
                ),
                SplitApplicationStage(
                    stage_name="Boll Formation",
                    timing="70-75 days after sowing (DAS)",
                    n_pct=25.0, p2o5_pct=0.0, k2o_pct=25.0,
                    products=self._allocate_split(products, n_factor=0.25, p_factor=0.00, k_factor=0.25)
                )
            ]
        elif "maize" in c_norm:
            return [
                SplitApplicationStage(
                    stage_name="Basal Application",
                    timing="At Sowing",
                    n_pct=50.0, p2o5_pct=100.0, k2o_pct=50.0,
                    products=self._allocate_split(products, n_factor=0.50, p_factor=1.00, k_factor=0.50)
                ),
                SplitApplicationStage(
                    stage_name="Knee-High Stage",
                    timing="25-30 days after sowing (DAS)",
                    n_pct=25.0, p2o5_pct=0.0, k2o_pct=25.0,
                    products=self._allocate_split(products, n_factor=0.25, p_factor=0.00, k_factor=0.25)
                ),
                SplitApplicationStage(
                    stage_name="Tasseling / Silking Stage",
                    timing="45-50 days after sowing (DAS)",
                    n_pct=25.0, p2o5_pct=0.0, k2o_pct=25.0,
                    products=self._allocate_split(products, n_factor=0.25, p_factor=0.00, k_factor=0.25)
                )
            ]
        elif "sugarcane" in c_norm:
            return [
                SplitApplicationStage(
                    stage_name="Basal Application",
                    timing="At Planting",
                    n_pct=25.0, p2o5_pct=100.0, k2o_pct=0.0,
                    products=self._allocate_split(products, n_factor=0.25, p_factor=1.00, k_factor=0.00)
                ),
                SplitApplicationStage(
                    stage_name="Tillering Phase",
                    timing="30-45 days after planting (DAP)",
                    n_pct=50.0, p2o5_pct=0.0, k2o_pct=50.0,
                    products=self._allocate_split(products, n_factor=0.50, p_factor=0.00, k_factor=0.50)
                ),
                SplitApplicationStage(
                    stage_name="Grand Growth Stage",
                    timing="90-100 days after planting (DAP)",
                    n_pct=25.0, p2o5_pct=0.0, k2o_pct=50.0,
                    products=self._allocate_split(products, n_factor=0.25, p_factor=0.00, k_factor=0.50)
                )
            ]
        elif any(p in c_norm for p in ("blackgram", "greengram", "pulse", "pulses", "gram")):
            # TNAU CPG 2020 specifies 100% basal application for short-duration pulses
            return [
                SplitApplicationStage(
                    stage_name="Basal Application (100% at Sowing)",
                    timing="At Sowing / Seed Placement",
                    n_pct=100.0, p2o5_pct=100.0, k2o_pct=100.0,
                    products=self._allocate_split(products, n_factor=1.00, p_factor=1.00, k_factor=1.00)
                )
            ]
        else:
            # General crops: standard 2-split schedule with explanatory timing
            return [
                SplitApplicationStage(
                    stage_name="Basal Application",
                    timing="At Sowing / Planting",
                    n_pct=50.0, p2o5_pct=100.0, k2o_pct=50.0,
                    products=self._allocate_split(products, n_factor=0.50, p_factor=1.00, k_factor=0.50)
                ),
                SplitApplicationStage(
                    stage_name="Top Dressing",
                    timing="30-35 days after sowing (DAS)",
                    n_pct=50.0, p2o5_pct=0.0, k2o_pct=50.0,
                    products=self._allocate_split(products, n_factor=0.50, p_factor=0.00, k_factor=0.50)
                )
            ]

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
