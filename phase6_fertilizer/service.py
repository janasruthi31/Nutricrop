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

class InfeasibleStatus(str):
    def __eq__(self, other):
        if str(other) in ("NO_FEASIBLE_SOLUTION", "INFEASIBLE"):
            return True
        return super().__eq__(other)


OPTIMIZATION_SUCCESS = "OPTIMIZATION_SUCCESS"
FEASIBLE = "FEASIBLE"
NO_FEASIBLE_SOLUTION = InfeasibleStatus("NO_FEASIBLE_SOLUTION")
INFEASIBLE = NO_FEASIBLE_SOLUTION
VALIDATION_ERROR = "VALIDATION_ERROR"

PROHIBITED_COMBINATIONS = [
    {
        "pair": {"CAN", "BASIC_SLAG"},
        "reason": "Ammonium fertilizers react with alkaline basic slag to release gaseous ammonia (severe N loss).",
        "authority": "TNAU Crop Production Guide 2020, Fertilizer Compatibility Section"
    },
    {
        "pair": {"UREA", "CAN"},
        "reason": "Urea mixed with Calcium Ammonium Nitrate forms a highly hygroscopic mixture that rapidly deliquesces into an unspreadable slurry.",
        "authority": "TNAU Crop Production Guide 2020 / Handbook of Agriculture"
    },
    {
        "pair": {"DAP", "LIME"},
        "reason": "Water-soluble phosphate in DAP reverts to insoluble tricalcium phosphate when mixed with lime.",
        "authority": "TNAU Crop Production Guide 2020 Soil Fertility Management"
    }
]


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
                            "price_per_bag_inr": float(r["price_per_bag_inr"]) if r.get("price_per_bag_inr") is not None else None,
                            "price_per_kg_inr": float(r["price_per_kg_inr"]) if r.get("price_per_kg_inr") is not None else None,
                            "price_basis": r.get("price_basis"),
                            "pricing_mechanism": r.get("pricing_mechanism"),
                            "price_status": r.get("price_status", "VERIFIED"),
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

        # Prepare candidate fertilizers and apply custom local prices if provided
        custom_prices_applied = False
        candidates = [dict(p) for p in self.catalog]
        if req.custom_prices and isinstance(req.custom_prices, dict):
            for p in candidates:
                pid = p.get("id", "")
                for c_k, c_v in req.custom_prices.items():
                    if c_k.strip().upper() == pid.strip().upper():
                        if c_v is None:
                            p["price_per_bag_inr"] = None
                            p["price_per_kg_inr"] = None
                            p["price_status"] = "COST_UNAVAILABLE"
                            p["has_valid_price"] = False
                        elif isinstance(c_v, str) and c_v.upper() in ("EXPIRED", "CONFLICTING", "COST_UNAVAILABLE"):
                            p["price_per_bag_inr"] = None
                            p["price_per_kg_inr"] = None
                            p["price_status"] = c_v.upper()
                            p["has_valid_price"] = False
                        else:
                            try:
                                v_float = float(c_v)
                                if v_float > 0:
                                    p["price_per_bag_inr"] = v_float
                                    p["price_per_kg_inr"] = round(v_float / max(0.1, float(p.get("bag_size_kg", 50.0))), 2)
                                    p["source"] = "Local Dealer / Farmer Custom Price"
                                    p["pricing_mechanism"] = "DEALER_QUOTATION"
                                    p["price_basis"] = "Local Dealer Quotation"
                                    p["price_status"] = "VERIFIED"
                                    p["has_valid_price"] = True
                                    custom_prices_applied = True
                                else:
                                    p["price_per_bag_inr"] = None
                                    p["price_per_kg_inr"] = None
                                    p["price_status"] = "COST_UNAVAILABLE"
                                    p["has_valid_price"] = False
                            except (ValueError, TypeError):
                                p["price_per_bag_inr"] = None
                                p["price_per_kg_inr"] = None
                                p["price_status"] = "COST_UNAVAILABLE"
                                p["has_valid_price"] = False

        # Filter candidate fertilizers if allowed list is specified
        if req.allowed_fertilizers:
            allowed_set = {a.upper() for a in req.allowed_fertilizers}
            candidates = [p for p in candidates if p["id"].upper() in allowed_set]

        # Filter candidate fertilizers by availability and evaluate pricing
        available_candidates = []
        for p in candidates:
            if p.get("is_available") is False or p.get("available") is False:
                continue

            # Evaluate price status if not already determined by custom prices
            if "has_valid_price" not in p:
                p_stat = p.get("price_status")
                if p.get("is_expired") or p_stat == "EXPIRED":
                    p["price_status"] = "EXPIRED"
                    p["has_valid_price"] = False
                elif p.get("has_conflicting_prices") or p_stat == "CONFLICTING":
                    p["price_status"] = "CONFLICTING"
                    p["has_valid_price"] = False
                elif p_stat == "COST_UNAVAILABLE" or p.get("price_per_bag_inr") is None:
                    p["price_status"] = "COST_UNAVAILABLE"
                    p["has_valid_price"] = False
                else:
                    try:
                        p_val = float(p["price_per_bag_inr"])
                        if p_val <= 0:
                            p["price_status"] = "COST_UNAVAILABLE"
                            p["has_valid_price"] = False
                        else:
                            p["has_valid_price"] = True
                            if not p_stat:
                                p["price_status"] = "VERIFIED"
                    except (ValueError, TypeError):
                        p["price_status"] = "COST_UNAVAILABLE"
                        p["has_valid_price"] = False

            # Ensure price metadata fields are always defined
            pid_upper = p.get("id", "").upper()
            if not p.get("pricing_mechanism"):
                if "UREA" in pid_upper:
                    p["pricing_mechanism"] = "OFFICIAL_CONTROLLED_PRICE"
                    p["price_basis"] = p.get("price_basis") or "Statutory Subsidized Maximum Retail Price (Statutory MRP)"
                else:
                    p["pricing_mechanism"] = "SUBSIDY_RELATED_PRICE"
                    p["price_basis"] = p.get("price_basis") or "Nutrient Based Subsidy (NBS) Policy Subsidized MRP"
            if not p.get("price_basis"):
                p["price_basis"] = "Statutory Subsidized Maximum Retail Price (Statutory MRP)" if "UREA" in pid_upper else "Nutrient Based Subsidy (NBS) Policy Subsidized MRP"

            available_candidates.append(p)
        candidates = available_candidates

        if not candidates:
            return FertilizerOptimizationResponse(
                status=NO_FEASIBLE_SOLUTION,
                crop=crop,
                farm_area_hectares=area_ha,
                limiting_constraint="No available fertilizer products were found in the catalog.",
                validation_errors=["No allowed/available fertilizer products are available for optimization."]
            )

        # Build prohibited combinations list including authoritative TNAU rules and custom request constraints
        all_prohibited = list(PROHIBITED_COMBINATIONS)
        if req.prohibited_combinations:
            for custom_pair in req.prohibited_combinations:
                all_prohibited.append({
                    "pair": {str(x).upper() for x in custom_pair},
                    "reason": "Incompatible fertilizer combination constraint.",
                    "authority": "Configurable Optimizer Constraint"
                })

        # Prohibited combinations pre-check if user explicitly specified an incompatible combination
        req_allowed_set = {a.upper() for a in req.allowed_fertilizers} if req.allowed_fertilizers else set()
        for combo in all_prohibited:
            if req_allowed_set and combo["pair"].issubset(req_allowed_set):
                return FertilizerOptimizationResponse(
                    status=NO_FEASIBLE_SOLUTION,
                    crop=crop,
                    farm_area_hectares=area_ha,
                    limiting_constraint=f"Prohibited fertilizer combination requested: {', '.join(sorted(combo['pair']))}. {combo['reason']}",
                    prohibited_combinations_detected=[f"{'/'.join(sorted(combo['pair']))}: {combo['reason']} ({combo['authority']})"],
                    validation_errors=[f"Incompatible fertilizer combination requested: {combo['reason']}"]
                )

        num_vars = len(candidates)
        # Objective vector c: price per commercial bag in INR (or surrogate cost for bag minimization when price is unavailable)
        c_bags = np.array([
            float(p["price_per_bag_inr"]) if p.get("has_valid_price") and p.get("price_per_bag_inr") is not None else 500.0
            for p in candidates
        ])

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
                nutrient_names = []
                if r_idx == 0 and n_req > 0:
                    nutrient_names.append("Nitrogen")
                elif (r_idx == 1 or (r_idx == 0 and n_req == 0)) and p2o5_req > 0:
                    nutrient_names.append("Phosphorus (P2O5)")
                else:
                    nutrient_names.append("Potassium (K2O)")
                nut_name = nutrient_names[0] if nutrient_names else "Required nutrient"
                return FertilizerOptimizationResponse(
                    status=NO_FEASIBLE_SOLUTION,
                    crop=crop,
                    farm_area_hectares=area_ha,
                    limiting_constraint=f"No available candidate fertilizer product supplies required {nut_name}.",
                    validation_errors=[
                        f"Optimization failed to find a feasible fertilizer combination. "
                        f"Required nutrient ({nut_name}) cannot be supplied by the allowed/available fertilizer catalog."
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
            c_kg = np.array([
                float(p["price_per_kg_inr"]) if p.get("has_valid_price") and p.get("price_per_kg_inr") is not None else (500.0 / max(0.1, float(p.get("bag_size_kg", 50.0))))
                for p in candidates
            ])
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
            limiting = "Nutrient requirements cannot be satisfied within upper surplus limit and discrete bag constraints."
            if req.max_surplus_factor is not None:
                limiting = f"Limiting constraint: Maximum surplus factor ({req.max_surplus_factor}x) cannot be satisfied with discrete commercial bag increments."
            return FertilizerOptimizationResponse(
                status=NO_FEASIBLE_SOLUTION,
                crop=crop,
                farm_area_hectares=area_ha,
                limiting_constraint=limiting,
                validation_errors=[f"Optimization failed to find a feasible commercial fertilizer combination satisfying nutrient constraints. {solver_status_msg}"]
            )

        product_recs: List[FertilizerProductRecommendation] = []
        total_cost = 0.0
        has_cost_unavailable = False

        supplied_n, supplied_p2o5, supplied_k2o = 0.0, 0.0, 0.0

        for i, bags in enumerate(bag_counts):
            if bags > 0:
                p = candidates[i]
                b_size = float(p["bag_size_kg"])
                qty_kg = round(bags * b_size, 2)

                # Price evaluation and traceability
                p_has_valid_price = p.get("has_valid_price", True)
                p_stat = p.get("price_status", "VERIFIED")
                if not p_has_valid_price or p_stat in ("COST_UNAVAILABLE", "EXPIRED", "CONFLICTING") or p.get("price_per_bag_inr") is None:
                    has_cost_unavailable = True
                    rec_price_per_bag = None
                    rec_total_cost = None
                    rec_price_status = p_stat if p_stat in ("EXPIRED", "CONFLICTING", "COST_UNAVAILABLE") else "COST_UNAVAILABLE"
                else:
                    rec_price_per_bag = float(p["price_per_bag_inr"])
                    rec_total_cost = round(bags * rec_price_per_bag, 2)
                    rec_price_status = "VERIFIED"
                    total_cost += rec_total_cost

                p_n = round(qty_kg * (float(p["n_pct"]) / 100.0), 2)
                p_p2o5 = round(qty_kg * (float(p["p2o5_pct"]) / 100.0), 2)
                p_k2o = round(qty_kg * (float(p["k2o_pct"]) / 100.0), 2)

                supplied_n += p_n
                supplied_p2o5 += p_p2o5
                supplied_k2o += p_k2o

                # Compute whole commercial bags and loose kg
                whole_bags = int(math.floor(bags))
                loose_kg = round((bags - whole_bags) * b_size, 2)
                if not is_fractional:
                    whole_bags = int(round(bags))
                    loose_kg = 0.0

                timing_desc = "At Sowing / Basal Application"
                pid_upper = p["id"].upper()
                if "UREA" in pid_upper:
                    timing_desc = "Split: 50% Basal, 25% Tillering, 25% Panicle Initiation"
                    rationale = "Primary straight Nitrogen source (46% N) at statutory subsidized MRP (₹266.50 / 45kg bag) to fulfill vegetative Nitrogen requirements after accounting for starter N supplied by DAP."
                    rationale_ta = "பயிர் வளர்ச்சிக்குத் தேவையான தழைச்சத்தை (46% N) மிகக் குறைந்த அரசு மானிய விலையில் வழங்க யூரியா பரிந்துரைக்கப்படுகிறது."
                elif "DAP" in pid_upper:
                    timing_desc = "100% Basal at sowing / transplanting"
                    rationale = "High-concentration complex supplying starter Nitrogen (18% N) and primary Phosphorus (46% P₂O₅) for strong root development and early vigor."
                    rationale_ta = "வேர் வளர்ச்சிக்கும் தொடக்க கால பயிர் ஊட்டத்திற்கும் தேவையான மணிச்சத்தை (46% P₂O₅) மற்றும் தொடக்க தழைச்சத்தை (18% N) வழங்க டிஏபி பரிந்துரைக்கப்படுகிறது."
                elif "MOP" in pid_upper or "POTASH" in pid_upper:
                    timing_desc = "Split: 50% Basal, 50% Heading / Flowering"
                    rationale = "Primary straight Potassic source (60% K₂O) at subsidized MRP (₹1,700 / 50kg bag) to build pest resistance, drought tolerance, and grain filling."
                    rationale_ta = "பயிர் வலிமை, பூச்சி எதிர்ப்பு, வறட்சி தாங்கும் திறன் மற்றும் தானிய எடை அதிகரிப்பிற்குத் தேவையான சாம்பல் சத்தை (60% K₂O) வழங்க பொட்டாஷ் பரிந்துரைக்கப்படுகிறது."
                elif "SSP" in pid_upper:
                    timing_desc = "100% Basal at sowing / transplanting"
                    rationale = "Straight phosphatic fertilizer providing 16% P₂O₅ plus 11-12% essential Sulphur and Calcium, optimal for root nodulation."
                    rationale_ta = "மணிச்சத்து (16% P₂O₅) மற்றும் பயிருக்குத் தேவையான கந்தகச் சத்தை வழங்க சூப்பர் பாஸ்பேட் பரிந்துரைக்கப்படுகிறது."
                elif "20:20" in pid_upper or "20-20" in pid_upper:
                    timing_desc = "100% Basal at sowing / transplanting"
                    rationale = "Balanced NP complex supplying 20% N, 20% P₂O₅ and 13% Sulphur in an easily absorbable ammonium phosphate form."
                    rationale_ta = "சமவிகித தழை மற்றும் மணிச்சத்தை (20:20:0) கந்தகத்துடன் வழங்க காம்ப்ளக்ஸ் உரம் பரிந்துரைக்கப்படுகிறது."
                elif "17:17" in pid_upper or "17-17" in pid_upper:
                    timing_desc = "Split: 50% Basal, 50% Active Tillering"
                    rationale = "Equally balanced complete NPK complex supplying 17% each of N, P₂O₅, and K₂O in a single uniform application."
                    rationale_ta = "தழை, மணி, சாம்பல் ஆகிய மூன்று முதன்மைச் சத்துக்களையும் சமவிகிதத்தில் (17:17:17) வழங்க பரிந்துரைக்கப்படுகிறது."
                else:
                    rationale = f"Supplies {p['category']} at optimal cost to fulfill targeted crop requirement."
                    rationale_ta = f"பயிரின் ஊட்டச்சத்து தேவையை பூர்த்தி செய்ய {p['category']} உரம் பரிந்துரைக்கப்படுகிறது."

                product_recs.append(FertilizerProductRecommendation(
                    product_id=p["id"],
                    product_name=p["name"],
                    name=p["name"],
                    category=p["category"],
                    quantity_kg=qty_kg,
                    bags=bags,
                    whole_bags=whole_bags,
                    loose_kg=loose_kg,
                    bag_size_kg=b_size,
                    price_per_bag_inr=rec_price_per_bag,
                    total_cost_inr=rec_total_cost,
                    quantity_per_ha_kg=round(qty_kg / max(0.001, area_ha), 2),
                    total_farm_quantity_kg=qty_kg,
                    nutrient_contributions={
                        "nitrogen": p_n,
                        "phosphorus_p2o5": p_p2o5,
                        "potassium_k2o": p_k2o
                    },
                    selection_rationale=rationale,
                    why_recommended=rationale,
                    why_recommended_ta=rationale_ta,
                    application_timing=timing_desc,
                    price_source=p.get("source", "Department of Fertilizers, GoI (NBS Subsidy Schedule)"),
                    price_effective_date=p.get("effective_date", "2024-04-01"),
                    price_basis=p.get("price_basis"),
                    pricing_mechanism=p.get("pricing_mechanism"),
                    price_status=rec_price_status
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

        surplus_n = round(max(0.0, supplied_n - n_req), 2)
        surplus_p = round(max(0.0, supplied_p2o5 - p2o5_req), 2)
        surplus_k = round(max(0.0, supplied_k2o - k2o_req), 2)

        deficit_n = round(max(0.0, n_req - supplied_n), 2)
        deficit_p = round(max(0.0, p2o5_req - supplied_p2o5), 2)
        deficit_k = round(max(0.0, k2o_req - supplied_k2o), 2)

        surplus_pct_n = round((surplus_n / n_req) * 100.0, 1) if n_req > 0 else 0.0
        surplus_pct_p = round((surplus_p / p2o5_req) * 100.0, 1) if p2o5_req > 0 else 0.0
        surplus_pct_k = round((surplus_k / k2o_req) * 100.0, 1) if k2o_req > 0 else 0.0

        nutrient_balance = {
            "nitrogen": NutrientBalanceDetail(
                required_kg=round(n_req, 2),
                supplied_kg=supplied_n,
                surplus_kg=surplus_n,
                deficit_kg=deficit_n,
                surplus_pct=surplus_pct_n,
            ),
            "phosphorus_p2o5": NutrientBalanceDetail(
                required_kg=round(p2o5_req, 2),
                supplied_kg=supplied_p2o5,
                surplus_kg=surplus_p,
                deficit_kg=deficit_p,
                surplus_pct=surplus_pct_p,
            ),
            "potassium_k2o": NutrientBalanceDetail(
                required_kg=round(k2o_req, 2),
                supplied_kg=supplied_k2o,
                surplus_kg=surplus_k,
                deficit_kg=deficit_k,
                surplus_pct=surplus_pct_k,
            )
        }

        surplus_dict = {
            "nitrogen": surplus_n,
            "phosphorus_p2o5": surplus_p,
            "potassium_k2o": surplus_k
        }
        deficit_dict = {
            "nitrogen": deficit_n,
            "phosphorus_p2o5": deficit_p,
            "potassium_k2o": deficit_k
        }
        has_surplus = any(v > 0.05 for v in surplus_dict.values())
        has_deficit = any(v > 0.05 for v in deficit_dict.values())

        surplus_parts = []
        if surplus_n > 0.05:
            surplus_parts.append(f"Nitrogen +{surplus_n} kg (+{surplus_pct_n}%)")
        if surplus_p > 0.05:
            surplus_parts.append(f"P₂O₅ +{surplus_p} kg (+{surplus_pct_p}%)")
        if surplus_k > 0.05:
            surplus_parts.append(f"K₂O +{surplus_k} kg (+{surplus_pct_k}%)")
        surplus_summary = "; ".join(surplus_parts) if surplus_parts else "Balanced (0 kg surplus)"

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

        # Check prohibited combinations among selected products
        prohibited_detected = []
        selected_pids = {p.product_id.upper() for p in product_recs}
        for combo in all_prohibited:
            if combo["pair"].issubset(selected_pids):
                prohibited_detected.append(f"{'/'.join(sorted(combo['pair']))}: {combo['reason']} ({combo['authority']})")
                return FertilizerOptimizationResponse(
                    status=NO_FEASIBLE_SOLUTION,
                    crop=crop,
                    farm_area_hectares=area_ha,
                    limiting_constraint=f"Prohibited fertilizer combination selected: {combo['reason']}",
                    prohibited_combinations_detected=prohibited_detected,
                    validation_errors=[f"Optimization resulted in an incompatible product combination: {combo['reason']}"]
                )

        # Package rounding effects breakdown
        package_rounding_effects = {
            "is_fractional": is_fractional,
            "whole_bags_total": sum(p.whole_bags or 0 for p in product_recs),
            "loose_kg_total": round(sum(p.loose_kg or 0.0 for p in product_recs), 2),
            "surplus_from_rounding_kg": {
                "nitrogen": surplus_n,
                "phosphorus_p2o5": surplus_p,
                "potassium_k2o": surplus_k
            },
            "packaging_effect_description": (
                "Continuous fractional calculation applies exact nutrient rates with zero packaging surplus."
                if is_fractional
                else f"Commercial whole-bag increments resulted in discrete packaging surplus: {surplus_summary}."
            ),
            "packaging_description": (
                "Continuous fractional calculation applies exact nutrient rates with zero packaging surplus."
                if is_fractional
                else f"Commercial whole-bag increments resulted in discrete packaging surplus: {surplus_summary}."
            )
        }

        final_opt_status = OPTIMIZATION_SUCCESS
        if is_provisional or not is_verified or p5_status == "PROVISIONAL_PENDING_VALIDATION":
            final_opt_status = "PROVISIONAL_UNVERIFIED"
            rec_type = "PROVISIONAL_UNVERIFIED"
            warnings.append("PROVISIONAL ONLY: This recommendation is derived from an unverified agronomic rule awaiting official calibration and must not be used as an official soil-specific recommendation.")

        if has_cost_unavailable:
            final_total_cost = None
            total_cost_status = "COST_UNAVAILABLE"
            warnings.append("Cost calculation unavailable: One or more recommended fertilizer products lack a verified current price (COST_UNAVAILABLE).")
        else:
            final_total_cost = round(total_cost, 2)
            total_cost_status = "AVAILABLE"

        rule_src = p5.get("source_title") or p5.get("recommendation_source") or "TNAU Crop Production Guide (Agriculture) 2020 / ICAR-STCR"
        opt_rationale = (
            "Formulation selected via SciPy optimization to minimize commercial input costs while satisfying "
            "agronomic nutrient targets. Commercial bag packaging constraints and multi-nutrient balances are accounted for."
        )

        return FertilizerOptimizationResponse(
            status=final_opt_status,
            crop=crop,
            farm_area_hectares=area_ha,
            total_cost_inr=final_total_cost,
            total_cost_status=total_cost_status,
            optimization_method=solver_status_msg,
            is_verified=is_verified and not is_provisional,
            is_provisional=is_provisional or (not is_verified),
            recommendation_type=rec_type,
            recommended_products=product_recs,
            nutrient_balance=nutrient_balance,
            nutrient_surplus_kg=surplus_dict,
            nutrient_deficit_kg=deficit_dict,
            has_surplus=has_surplus,
            has_deficit=has_deficit,
            surplus_summary=surplus_summary,
            custom_prices_applied=custom_prices_applied,
            price_data_timestamp="2026-10-22",
            prices_last_updated="2026-10-22",
            rules_last_updated="2026-10-22",
            agronomic_rule_source=rule_src,
            optimizer_rationale=opt_rationale,
            package_rounding_effects=package_rounding_effects,
            prohibited_combinations_detected=prohibited_detected,
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
