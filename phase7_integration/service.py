"""
Master Pipeline Orchestrator Service (Phase 7).
Chains Phase 4 Rule Selection -> Phase 5 NPK Calculation -> Phase 6 LP Optimization -> Phase 2 Yield Model -> Phase 7 Weather Guidance.
Supports dual recommendation modes:
  1. 'SOIL_HEALTH_CARD': Copied directly from printed soil health card recommendations and scaled accurately.
  2. 'CALCULATED_AGRONOMIC': Computed from verified TNAU STCR / soil-test equations.
"""

import hashlib
import json
import time
from typing import Any, Dict, Optional, Tuple
from agronomy.service import RuleSelectionService, RuleSelectionRequest
from phase5_nutrient.service import NutrientCalculationService, NutrientCalculationRequest
from phase6_fertilizer.service import FertilizerOptimizerService
from phase6_fertilizer.models import FertilizerOptimizationRequest, FertilizerOptimizationResponse
from phase7_integration.weather import get_weather_guidance
from predict_yield import predict_district_yield

_RECOMMENDATION_CACHE: Dict[str, Tuple[float, Dict[str, Any]]] = {}
_RECOMMENDATION_CACHE_TTL = 3 * 3600  # 3 hours (10800 seconds)


class FullRecommendationService:
    def __init__(self):
        self.rule_service = RuleSelectionService()
        self.nutrient_service = NutrientCalculationService()
        self.fertilizer_service = FertilizerOptimizerService()

    def generate_full_recommendation(self, req: Dict[str, Any]) -> Dict[str, Any]:
        # 3-hour recommendation caching by request payload hash
        cache_key = None
        if not req.get("no_cache"):
            try:
                # Deterministic hash of significant calculation parameters
                key_fields = {
                    "crop": req.get("crop"),
                    "district": req.get("district"),
                    "soil_series": req.get("soil_series"),
                    "season": req.get("season"),
                    "target_yield": req.get("target_yield"),
                    "soil_n": req.get("soil_nitrogen"),
                    "soil_p": req.get("soil_phosphorus"),
                    "soil_k": req.get("soil_potassium"),
                    "soil_phosphorus_method": req.get("soil_phosphorus_method"),
                    "farm_area": req.get("farm_area"),
                    "farm_area_unit": req.get("farm_area_unit"),
                    "previous_crop": req.get("previous_crop"),
                    "previous_fertilizers": req.get("previous_fertilizers"),
                    "fym": req.get("fym_applied_t_per_ha"),
                    "custom_prices": req.get("custom_prices"),
                    "allow_unverified": req.get("allow_unverified"),
                    "recommendation_mode": req.get("recommendation_mode"),
                    "recommendation_type": req.get("recommendation_type"),
                    "no_soil_test": req.get("no_soil_test"),
                }
                cache_key = hashlib.sha256(json.dumps(key_fields, sort_keys=True, default=str).encode("utf-8")).hexdigest()
                cached_entry = _RECOMMENDATION_CACHE.get(cache_key)
                if cached_entry:
                    exp_ts, cached_data = cached_entry
                    if time.time() < exp_ts:
                        res = dict(cached_data)
                        res["is_cached"] = True
                        return res
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning(f"Cache key computation error: {e}")
                cache_key = None

        crop = req.get("crop", "Rice")
        district = req.get("district", "Thanjavur")
        soil_series = req.get("soil_series")
        season = req.get("season", "Kharif")
        irrigation = req.get("irrigation_method", "Irrigated")
        crop_low = crop.strip().lower()
        if req.get("target_yield") is not None:
            target_yield = float(req.get("target_yield"))
        elif "cotton" in crop_low:
            target_yield = 2.5
        elif any(p in crop_low for p in ("blackgram", "greengram", "pulse", "pulses", "gram")):
            target_yield = 1.0
        elif "sugarcane" in crop_low:
            target_yield = 120.0
        elif "groundnut" in crop_low:
            target_yield = 2.2
        elif "maize" in crop_low:
            target_yield = 6.0
        else:
            target_yield = 6.0

        # Support loading verified measurements from confirmed soil profile
        profile_id = req.get("soil_profile_id")
        soil_n = req.get("soil_nitrogen")
        soil_p = req.get("soil_phosphorus")
        soil_k = req.get("soil_potassium")
        p_method = req.get("soil_phosphorus_method")

        # Recommendation mode: 'SOIL_HEALTH_CARD' or 'CALCULATED_AGRONOMIC'
        rec_mode = req.get("recommendation_mode", "CALCULATED_AGRONOMIC")
        printed_n = req.get("printed_n_rate")
        printed_p = req.get("printed_p2o5_rate")
        printed_k = req.get("printed_k2o_rate")
        printed_unit = req.get("printed_rate_unit", "kg/acre")
        printed_source = req.get("printed_source", "Uploaded Soil Health Card")

        farm_area = req.get("farm_area")
        farm_area_unit = req.get("farm_area_unit")

        variety = req.get("variety")

        # Check if printed_recommendation passed directly or inside soil_profile
        prec_direct = req.get("printed_recommendation") or (req.get("soil_profile") or {}).get("printed_recommendation")
        if prec_direct and isinstance(prec_direct, dict):
            if printed_n is None:
                printed_n = prec_direct.get("n_kg_per_acre") or prec_direct.get("nitrogen_kg_per_acre") or prec_direct.get("n") or prec_direct.get("nitrogen")
            if printed_p is None:
                printed_p = prec_direct.get("p2o5_kg_per_acre") or prec_direct.get("p2o5") or prec_direct.get("phosphorus")
            if printed_k is None:
                printed_k = prec_direct.get("k2o_kg_per_acre") or prec_direct.get("k2o") or prec_direct.get("potassium")
            if not req.get("printed_rate_unit") and prec_direct.get("unit"):
                printed_unit = prec_direct.get("unit")
            if not req.get("printed_source") and prec_direct.get("source"):
                printed_source = prec_direct.get("source")

        # Units for soil nutrient status
        soil_n_unit = req.get("soil_nitrogen_unit")
        soil_p_unit = req.get("soil_phosphorus_unit")
        soil_k_unit = req.get("soil_potassium_unit")

        # Support extracting verified measurements directly from soil_profile dict if provided
        p_dict = req.get("soil_profile")
        if p_dict and isinstance(p_dict, dict):
            if not crop and p_dict.get("crop"):
                crop = p_dict.get("crop")
            if not district and p_dict.get("district"):
                district = p_dict.get("district")
            if not soil_series and p_dict.get("soil_series"):
                soil_series = p_dict.get("soil_series")
            if soil_n is None and p_dict.get("nitrogen") is not None:
                soil_n = p_dict["nitrogen"].get("value") if isinstance(p_dict["nitrogen"], dict) else p_dict.get("nitrogen")
                if not soil_n_unit and isinstance(p_dict["nitrogen"], dict):
                    soil_n_unit = p_dict["nitrogen"].get("unit")
            if soil_p is None and p_dict.get("phosphorus") is not None:
                soil_p = p_dict["phosphorus"].get("value") if isinstance(p_dict["phosphorus"], dict) else p_dict.get("phosphorus")
                if isinstance(p_dict["phosphorus"], dict):
                    p_method = p_dict["phosphorus"].get("method", p_method)
                    if not soil_p_unit:
                        soil_p_unit = p_dict["phosphorus"].get("unit")
            if soil_k is None and p_dict.get("potassium") is not None:
                soil_k = p_dict["potassium"].get("value") if isinstance(p_dict["potassium"], dict) else p_dict.get("potassium")
                if not soil_k_unit and isinstance(p_dict["potassium"], dict):
                    soil_k_unit = p_dict["potassium"].get("unit")
            if farm_area is None and p_dict.get("farm_area"):
                farm_area = p_dict.get("farm_area")
            if farm_area_unit is None and p_dict.get("farm_area_unit"):
                farm_area_unit = p_dict.get("farm_area_unit")
            if req.get("organic_carbon") is None and p_dict.get("organic_carbon") is not None:
                req["organic_carbon"] = p_dict["organic_carbon"].get("value") if isinstance(p_dict["organic_carbon"], dict) else p_dict.get("organic_carbon")
            if req.get("ph") is None and p_dict.get("ph") is not None:
                req["ph"] = p_dict["ph"].get("value") if isinstance(p_dict["ph"], dict) else p_dict.get("ph")
            if req.get("ec") is None and p_dict.get("ec") is not None:
                req["ec"] = p_dict["ec"].get("value") if isinstance(p_dict["ec"], dict) else p_dict.get("ec")

        if profile_id:
            try:
                from phase3_soil import db
                with db.connect() as con:
                    row = con.execute("SELECT profile_json FROM soil_profiles WHERE soil_profile_id = ?", (profile_id,)).fetchone()
                    if row:
                        p_data = json.loads(row["profile_json"])
                        if not crop and p_data.get("crop"):
                            crop = p_data.get("crop")
                        if not district and p_data.get("district"):
                            district = p_data.get("district")
                        if not soil_series and p_data.get("soil_series"):
                            soil_series = p_data.get("soil_series")
                        if soil_n is None and p_data.get("nitrogen"):
                            soil_n = p_data["nitrogen"].get("value")
                            if not soil_n_unit:
                                soil_n_unit = p_data["nitrogen"].get("unit")
                        if soil_p is None and p_data.get("phosphorus"):
                            soil_p = p_data["phosphorus"].get("value")
                            p_method = p_data["phosphorus"].get("method", p_method)
                            if not soil_p_unit:
                                soil_p_unit = p_data["phosphorus"].get("unit")
                        if soil_k is None and p_data.get("potassium"):
                            soil_k = p_data["potassium"].get("value")
                            if not soil_k_unit:
                                soil_k_unit = p_data["potassium"].get("unit")
                        if farm_area is None and p_data.get("farm_area"):
                            farm_area = p_data.get("farm_area")
                        if farm_area_unit is None and p_data.get("farm_area_unit"):
                            farm_area_unit = p_data.get("farm_area_unit")
                        if req.get("organic_carbon") is None and p_data.get("organic_carbon"):
                            req["organic_carbon"] = p_data["organic_carbon"].get("value")
                        if req.get("ph") is None and p_data.get("ph"):
                            req["ph"] = p_data["ph"].get("value")
                        if req.get("ec") is None and p_data.get("ec"):
                            req["ec"] = p_data["ec"].get("value")
                        
                        # Load printed recommendations if available
                        if p_data.get("printed_recommendation"):
                            prec = p_data["printed_recommendation"]
                            if printed_n is None:
                                printed_n = prec.get("nitrogen_kg_per_acre") or prec.get("n") or prec.get("nitrogen")
                            if printed_p is None:
                                printed_p = prec.get("p2o5_kg_per_acre") or prec.get("p2o5") or prec.get("phosphorus")
                            if printed_k is None:
                                printed_k = prec.get("k2o_kg_per_acre") or prec.get("k2o") or prec.get("potassium")
                            if not req.get("printed_rate_unit") and prec.get("unit"):
                                printed_unit = prec.get("unit")
            except Exception:
                pass

        if farm_area is None:
            farm_area = 1.0
        if farm_area_unit is None:
            farm_area_unit = "hectare"

        fym_applied = req.get("fym_applied_t_per_ha")
        organic_carbon = req.get("organic_carbon")
        soil_ph = req.get("ph")
        soil_ec = req.get("ec")

        target_yield_unit = req.get("target_yield_unit", "t/ha")

        # Step 1: Rule Selection (Phase 4)
        p4_req = RuleSelectionRequest(
            crop=crop,
            district=district,
            soil_series=soil_series,
            season=season,
            irrigation_method=irrigation,
            target_yield=target_yield,
            recommendation_type=req.get("recommendation_type"),
            soil_values={
                "nitrogen": soil_n,
                "phosphorus": soil_p,
                "potassium": soil_k,
                "phosphorus_method": p_method
            } if soil_n is not None or soil_p is not None or soil_k is not None else None
        )
        p4_res = self.rule_service.select_rule(p4_req)

        # Step 2: NPK Requirement Calculation (Phase 5)
        # allow_unverified is False by default to strictly enforce agronomic validation!
        allow_unverified = req.get("allow_unverified", False)

        previous_crop = req.get("previous_crop")
        previous_fertilizers = req.get("previous_fertilizers") or []

        # If previous_fertilizers not explicitly in payload, auto-query authenticated farmer's history from database
        farmer_uid = req.get("user_id") or req.get("farmer_id")
        if not previous_fertilizers and farmer_uid:
            try:
                from phase3_soil import db
                with db.connect() as con:
                    rows = con.execute(
                        "SELECT * FROM farmer_fertilizer_history WHERE user_id = ? ORDER BY created_at DESC",
                        (farmer_uid,)
                    ).fetchall()
                    if rows:
                        previous_fertilizers = [
                            {
                                "product": r["fertilizer_product"],
                                "fertilizer_product": r["fertilizer_product"],
                                "product_grade": r["fertilizer_grade"] if "fertilizer_grade" in r.keys() else None,
                                "category": r["category"] if "category" in r.keys() else None,
                                "quantity": float(r["quantity"]),
                                "unit": r["unit"],
                                "bag_weight_kg": r["bag_weight_kg"] if "bag_weight_kg" in r.keys() and r["bag_weight_kg"] is not None else None,
                                "field_area": r["field_area"] if "field_area" in r.keys() and r["field_area"] is not None else None,
                                "field_area_unit": r["field_area_unit"] if "field_area_unit" in r.keys() and r["field_area_unit"] is not None else None,
                                "application_method": r["application_method"] if "application_method" in r.keys() else None,
                                "application_date": r["application_date"],
                                "crop_season": r["season"] if "season" in r.keys() else None,
                                "n_pct": r["n_pct"] if "n_pct" in r.keys() and r["n_pct"] is not None else None,
                                "p2o5_pct": r["p2o5_pct"] if "p2o5_pct" in r.keys() and r["p2o5_pct"] is not None else None,
                                "k2o_pct": r["k2o_pct"] if "k2o_pct" in r.keys() and r["k2o_pct"] is not None else None,
                            }
                            for r in rows
                        ]
            except Exception:
                pass

        zinc = req.get("zinc")
        sulphur = req.get("sulphur")
        boron = req.get("boron")

        p5_req = NutrientCalculationRequest(
            crop=crop,
            variety=variety,
            soil_series=soil_series,
            selected_rule_id=p4_res.selected_rule_id,
            target_yield=target_yield,
            target_yield_unit=target_yield_unit,
            soil_nitrogen=soil_n,
            soil_nitrogen_unit=soil_n_unit or "kg/ha",
            soil_phosphorus=soil_p,
            soil_phosphorus_unit=soil_p_unit or "kg/ha",
            soil_potassium=soil_k,
            soil_potassium_unit=soil_k_unit or "kg/ha",
            soil_phosphorus_method=p_method,
            organic_carbon=organic_carbon,
            ph=soil_ph,
            ec=soil_ec,
            zinc=zinc,
            sulphur=sulphur,
            boron=boron,
            fym_applied_t_per_ha=fym_applied,
            farm_area=farm_area,
            farm_area_unit=farm_area_unit,
            phase4_result=p4_res.model_dump(),
            previous_crop=previous_crop,
            previous_fertilizers=previous_fertilizers,
            recommendation_mode=rec_mode,
            recommendation_type=req.get("recommendation_type"),
            no_soil_test=req.get("no_soil_test", False) or (soil_n is None and soil_p is None and soil_k is None and req.get("recommendation_type") in ("GENERAL_BLANKET", "NO_SOIL_TEST")),
            printed_n_rate=printed_n,
            printed_p2o5_rate=printed_p,
            printed_k2o_rate=printed_k,
            printed_rate_unit=printed_unit,
            printed_source=printed_source,
            allow_unverified=allow_unverified
        )
        p5_res = self.nutrient_service.calculate(p5_req)

        # Step 3: Fertilizer Optimization (Phase 6)
        if p5_res.status in ("MISSING_INPUTS", "VALIDATION_ERROR", "UNSUPPORTED_CROP", "UNSUPPORTED_SOIL_SERIES", "INCOMPATIBLE_SOIL_TEST_METHOD", "NO_MATCHING_RULE", "NO_VERIFIED_RULE", "NO_VERIFIED_RULE_AVAILABLE", "CALCULATION_FAILED"):
            # Do not fabricate or optimize fertilizer when required soil test inputs are missing or invalid
            p6_res = FertilizerOptimizationResponse(
                status=p5_res.status,
                crop=crop,
                farm_area_hectares=p5_res.farm_area_hectares or 1.0,
                total_cost_inr=0.0,
                is_verified=False,
                is_provisional=False,
                recommended_products=[],
                warnings=p5_res.warnings,
                validation_errors=p5_res.validation_errors or ["Fertilizer recommendation cannot yet be calculated reliably due to missing or invalid soil data."]
            )
        else:
            p6_req = FertilizerOptimizationRequest(
                crop=crop,
                phase5_result=p5_res.model_dump(),
                allow_unverified=allow_unverified,
                custom_prices=req.get("custom_prices")
            )
            p6_res = self.fertilizer_service.optimize(p6_req)

        # Step 4: District Yield Model Prediction (Phase 2)
        yield_pred = None
        try:
            area_ha = p5_res.farm_area_hectares or 1.0
            yield_kg_per_ha = predict_district_yield(district, crop, season)
            est_prod_tonnes = round((yield_kg_per_ha / 1000.0) * area_ha, 2)
            yield_pred = {
                "status": "DISTRICT_BENCHMARK_ESTIMATE",
                "target_variable": "yield",
                "target_unit": "kg/ha",
                "target_definition": "Official district-average historical yield (Season & Crop Report Table V-A). NOT derived, NOT farm-specific.",
                "estimated_yield_kg_per_ha": round(yield_kg_per_ha, 2),
                "estimated_production_tonnes": est_prod_tonnes,
                "production_derivation": "Derived planning estimate: (yield_kg_per_ha / 1000.0) * farm_area_hectares",
                "crop": crop,
                "district": district,
                "season": season,
                "evaluation_metrics": {
                    "model": "XGBoostRegressor",
                    "MAE_kg_per_ha": 1706.3,
                    "RMSE_kg_per_ha": 3945.5,
                    "R2": 0.951,
                    "test_split": "chronological 80/20 held-out (1,739 rows)",
                },
                "scope": "district benchmark, not a prediction for your field",
                "label": "district benchmark, not a prediction for your field",
                "disclaimer": "Historical district benchmark, not a prediction for your field. Does not modify fertilizer recommendations.",
                "limitations": [
                    "District-level average estimate; not a farm-specific yield prediction.",
                    "Does not account for individual farm soil depth, microclimate, or management.",
                    "Completely independent of fertilizer recommendations; does not alter fertilizer doses."
                ]
            }
        except Exception as e:
            yield_pred = {
                "status": "NOT_VALIDATED",
                "target_variable": "yield",
                "target_unit": "kg/ha",
                "target_definition": "Official district-average historical yield (Season & Crop Report Table V-A).",
                "error": f"District yield benchmark unavailable: {str(e)}",
                "scope": "district benchmark, not a prediction for your field",
                "label": "district benchmark, not a prediction for your field",
                "disclaimer": "Yield benchmark is NOT VALIDATED for this crop/district combination."
            }

        # Step 5: Agro-Weather Guidance (Phase 7)
        lat = req.get("latitude")
        lon = req.get("longitude")
        weather_res = get_weather_guidance(district=district, lat=lat, lon=lon)

        # Determine overall status and verification flags
        if p5_res.status in ("MISSING_INPUTS", "VALIDATION_ERROR", "UNSUPPORTED_CROP", "UNSUPPORTED_SOIL_SERIES", "INCOMPATIBLE_SOIL_TEST_METHOD", "NO_MATCHING_RULE", "NO_VERIFIED_RULE", "NO_VERIFIED_RULE_AVAILABLE", "CALCULATION_FAILED"):
            final_status = p5_res.status
            final_is_verified = False
            final_rec_type = "UNAVAILABLE"
            status_message = p5_res.actionable_message or ("Recommendation cannot yet be calculated reliably. " + "; ".join(p5_res.validation_errors or ["Please check soil data."]))
        elif p4_res.status in ("PENDING_VERIFICATION", "PENDING_AGRONOMIC_VALIDATION") or not p5_res.is_verified_rule:
            if rec_mode != "SOIL_HEALTH_CARD":
                if allow_unverified and p4_res.status in ("PENDING_VERIFICATION", "PENDING_AGRONOMIC_VALIDATION"):
                    final_status = "PROVISIONAL_PENDING_VALIDATION"
                    final_rec_type = "PROVISIONAL_UNVERIFIED"
                elif p6_res.status in ("BLOCKED_UNVERIFIED_RULE", "PENDING_AGRONOMIC_VALIDATION"):
                    final_status = p6_res.status
                    final_rec_type = "PROVISIONAL_UNVERIFIED"
                else:
                    final_status = "SUCCESS" if p6_res.status in ("OPTIMIZATION_SUCCESS", "PROVISIONAL_UNVERIFIED") else p6_res.status
                    final_rec_type = "PROVISIONAL"
                final_is_verified = False
                status_message = "This recommendation is based on PROVISIONAL agronomic rules pending official TNAU verification."
            else:
                final_status = "SUCCESS"
                final_is_verified = True
                final_rec_type = "SOIL_HEALTH_CARD"
                status_message = None
        else:
            final_status = "SUCCESS" if p6_res.status == "OPTIMIZATION_SUCCESS" else p6_res.status
            final_is_verified = True
            final_rec_type = p5_res.recommendation_type or p4_res.recommendation_type or "SOIL_SPECIFIC_STCR"
            status_message = None

        all_warnings: list = []
        if status_message and status_message not in all_warnings:
            all_warnings.append(status_message)
        for w in (p4_res.warnings or []):
            if w not in all_warnings:
                all_warnings.append(w)
        for w in (p5_res.warnings or []):
            if w not in all_warnings:
                all_warnings.append(w)
        for w in (p6_res.warnings or []):
            if w not in all_warnings:
                all_warnings.append(w)

        # Weather timing warning if live weather is unavailable or historical normal
        if weather_res.get("guidance_status") == "UNKNOWN" or weather_res.get("status") == "UNKNOWN / HISTORICAL_NORMALS":
            weather_warn = "Timing warning: Live weather forecast is unavailable. Safe fertilizer application timing cannot be verified from historical normals alone. Check local weather before top-dressing."
            if weather_warn not in all_warnings:
                all_warnings.append(weather_warn)

        # Check test_date age (Task 3c)
        test_date = req.get("test_date") or (p_dict or {}).get("test_date")
        if test_date:
            try:
                import datetime
                td_dt = None
                td_str = str(test_date).strip()
                if "-" in td_str:
                    td_dt = datetime.date.fromisoformat(td_str[:10])
                elif "/" in td_str:
                    parts = td_str.split("/")
                    if len(parts) == 3:
                        if len(parts[0]) == 4:
                            td_dt = datetime.date(int(parts[0]), int(parts[1]), int(parts[2]))
                        elif len(parts[2]) == 4:
                            td_dt = datetime.date(int(parts[2]), int(parts[1]), int(parts[0]))
                if td_dt:
                    age_days = (datetime.date.today() - td_dt).days
                    if age_days > 365:
                        date_warn = f"Soil test date ({test_date}) is more than 1 year old ({age_days} days). Soil nutrient levels fluctuate over time; consider testing a fresh soil sample."
                        if date_warn not in all_warnings:
                            all_warnings.append(date_warn)
            except Exception:
                pass

        # Build Low NPK Highlights & Agronomic Impact Explanations
        low_nutrients_list = []
        n_stat = (p5_res.soil_nutrient_status or {}).get("nitrogen", {})
        p_stat = (p5_res.soil_nutrient_status or {}).get("phosphorus", {})
        k_stat = (p5_res.soil_nutrient_status or {}).get("potassium", {})

        n_val = soil_n if soil_n is not None else n_stat.get("value_kg_per_ha")
        p_val = soil_p if soil_p is not None else p_stat.get("value_kg_per_ha")
        k_val = soil_k if soil_k is not None else k_stat.get("value_kg_per_ha")

        if n_val is not None and (float(n_val) < 280.0 or n_stat.get("rating") == "Low"):
            low_nutrients_list.append({
                "nutrient": "Nitrogen",
                "symbol": "N",
                "value": float(n_val),
                "unit": "kg/ha",
                "rating": "Low",
                "status": "Deficient",
                "threshold": "Low (< 280 kg/ha)",
                "highlight_alert": f"Soil Nitrogen is LOW ({float(n_val):.1f} kg/ha < 280 kg/ha threshold).",
                "highlight_alert_ta": f"மண்ணில் தழைச்சத்து (N) குறைவாக உள்ளது ({float(n_val):.1f} kg/ha < 280 kg/ha).",
                "agronomic_explanation": "Because soil Nitrogen is deficient, the fertilizer nitrogen dose has been adjusted upwards (+10% to +25%) to build soil fertility and sustain tillering and vegetative growth.",
                "agronomic_explanation_ta": "மண் தழைச்சத்து குறைவாக உள்ளதால், மண் வளத்தை உயர்த்தவும் பயிர் வளர்ச்சியை பராமரிக்கவும் தழைச்சத்து உர அளவு அதிகரிக்கப்பட்டுள்ளது."
            })

        p_thresh = 11.0 if str(p_method).strip().lower() != "bray" else 24.2
        if p_val is not None and (float(p_val) < p_thresh or p_stat.get("rating") == "Low"):
            low_nutrients_list.append({
                "nutrient": "Phosphorus",
                "symbol": "P₂O₅",
                "value": float(p_val),
                "unit": "kg/ha",
                "rating": "Low",
                "status": "Deficient",
                "threshold": f"Low (< {p_thresh} kg/ha {p_method})",
                "highlight_alert": f"Soil Phosphorus is LOW ({float(p_val):.1f} kg/ha < {p_thresh} kg/ha {p_method}).",
                "highlight_alert_ta": f"மண்ணில் மணிச்சத்து (P) குறைவாக உள்ளது ({float(p_val):.1f} kg/ha < {p_thresh} kg/ha).",
                "agronomic_explanation": f"Because soil Phosphorus is deficient under the {p_method} test, phosphatic fertilizer is increased to ensure strong root establishment and early vegetative vigor.",
                "agronomic_explanation_ta": "மணிச்சத்து குறைவாக உள்ளதால் வேர் வளர்ச்சி மற்றும் ஆரம்பகால பயிர் ஊட்டத்தை உறுதி செய்ய பாஸ்பேட் உர அளவு அதிகரிக்கப்பட்டுள்ளது."
            })

        if k_val is not None and (float(k_val) < 118.0 or k_stat.get("rating") == "Low"):
            low_nutrients_list.append({
                "nutrient": "Potassium",
                "symbol": "K₂O",
                "value": float(k_val),
                "unit": "kg/ha",
                "rating": "Low",
                "status": "Deficient",
                "threshold": "Low (< 118 kg/ha)",
                "highlight_alert": f"Soil Potassium is LOW ({float(k_val):.1f} kg/ha < 118 kg/ha threshold).",
                "highlight_alert_ta": f"மண்ணில் சாம்பல் சத்து (K) குறைவாக உள்ளது ({float(k_val):.1f} kg/ha < 118 kg/ha).",
                "agronomic_explanation": "Because soil Potassium is deficient, potash application is increased to improve stem strength, drought resistance, and grain filling.",
                "agronomic_explanation_ta": "சாம்பல் சத்து குறைவாக உள்ளதால் தண்டு வலிமை, வறட்சி தாங்கும் திறன் மற்றும் தானிய எடையை அதிகரிக்க பொட்டாஷ் உர அளவு அதிகரிக்கப்பட்டுள்ளது."
            })

        has_low_nutrients = len(low_nutrients_list) > 0
        if has_low_nutrients:
            low_names = ", ".join(item["nutrient"] for item in low_nutrients_list)
            low_summary_en = f"Low Soil Nutrient Alert: {low_names} in your soil test are below the critical TNAU fertility threshold. Recommended fertilizer doses have been adjusted upwards to compensate for these deficiencies."
            low_summary_ta = f"மண் பரிசோதனை எச்சரிக்கை: உங்கள் மண்ணில் {low_names} ஊட்டச்சத்து(க்கள்) குறைவாக உள்ளன. இந்த குறைபாட்டை ஈடுசெய்ய பரிந்துரைக்கப்பட்ட உர அளவுகள் அதிகரிக்கப்பட்டுள்ளன."
        else:
            low_summary_en = "Soil fertility diagnostic: Primary nutrients (N, P, K) are in the Medium to High fertility range."
            low_summary_ta = "மண் வளப் பகுப்பாய்வு: முதன்மை ஊட்டச்சத்துக்கள் (N, P, K) போதுமான நடுத்தர/உயர் அளவில் உள்ளன."

        soil_fertility_highlights = {
            "has_low_nutrients": has_low_nutrients,
            "low_nutrients_count": len(low_nutrients_list),
            "low_nutrients": low_nutrients_list,
            "summary_en": low_summary_en,
            "summary_ta": low_summary_ta,
            "all_ratings": {
                "nitrogen": n_stat.get("rating", "Low" if (n_val is not None and float(n_val) < 280) else "Medium"),
                "phosphorus": p_stat.get("rating", "Low" if (p_val is not None and float(p_val) < p_thresh) else "Medium"),
                "potassium": k_stat.get("rating", "Low" if (k_val is not None and float(k_val) < 118) else "Medium"),
            }
        }

        res_payload = {
            "status": final_status,
            "is_verified": final_is_verified,
            "is_provisional": not final_is_verified,
            "recommendation_type": final_rec_type,
            "recommendation_category": p5_res.recommendation_category or p4_res.recommendation_category,
            "recommendation_type_label": p5_res.recommendation_type_label or p4_res.recommendation_type_label,
            "is_stcr_ipns": p5_res.is_stcr_ipns,
            "is_standard_rdf": p5_res.is_standard_rdf,
            "applicable_limitations": p5_res.applicable_limitations or p4_res.applicable_limitations,
            "supported_phosphorus_methods": p5_res.supported_phosphorus_methods or p4_res.supported_phosphorus_methods,
            "error_code": p5_res.error_code or p4_res.error_code,
            "actionable_message": p5_res.actionable_message or p4_res.actionable_message,
            "crop": crop,
            "district": district,
            "recommendation_mode": p5_res.recommendation_mode,
            "rule_selection": p4_res.model_dump(),
            "nutrient_requirements": p5_res.model_dump(),
            "fertilizer_plan": p6_res.model_dump(),
            "soil_fertility_highlights": soil_fertility_highlights,
            "low_nutrients_highlight": soil_fertility_highlights,
            "soil_nutrient_status": p5_res.soil_nutrient_status,
            "soil_test_summary": {
                "nitrogen_kg_per_ha": soil_n,
                "phosphorus_kg_per_ha": soil_p,
                "potassium_kg_per_ha": soil_k,
                "phosphorus_method": p_method,
                "phosphorus_test_method": p_method,
                "original_phosphorus_value": req.get("soil_phosphorus") or (p_dict.get("phosphorus") if p_dict else None),
                "original_phosphorus_unit": soil_p_unit or "kg/ha",
                "source_report": profile_id or (p_dict.get("sample_id") if p_dict else None) or "Soil Health Card",
                "sampling_date": test_date,
                "conversion_applied": False,
                "conversion_note": "No conversion factor applied between Olsen and Bray extraction methods. Agronomic rules match only natively calibrated test methods.",
                "ph": soil_ph,
                "ec": soil_ec,
                "organic_carbon_pct": organic_carbon,
                "zinc_ppm": zinc,
                "sulphur_ppm": sulphur,
                "boron_ppm": boron,
                "soil_series": soil_series
            },
            "previous_history_considered": {
                "previous_crop": previous_crop,
                "previous_fertilizers_count": len(previous_fertilizers),
                "previous_fertilizers": previous_fertilizers,
                "previous_crop_credit_kg_per_ha": p5_res.previous_crop_credit_kg_per_ha or {"N": 0.0, "P2O5": 0.0, "K2O": 0.0},
                "previous_fertilizer_residual_kg_per_ha": p5_res.previous_fertilizer_residual_kg_per_ha or {"N": 0.0, "P2O5": 0.0, "K2O": 0.0}
            },
            "agronomic_rule_source": p6_res.agronomic_rule_source or (p5_res.authoritative_reference.get("title") if p5_res.authoritative_reference else "TNAU Crop Production Guide 2020"),
            "source_information": p5_res.authoritative_reference or p4_res.source_title,
            "derivation_explanation": p5_res.derivation_explanation,
            "authoritative_reference": p5_res.authoritative_reference,
            "message": status_message,
            "warnings": all_warnings,
            "district_yield_prediction": yield_pred,
            "weather_guidance": weather_res,
            "nutrient_surplus_kg": p6_res.nutrient_surplus_kg,
            "nutrient_deficit_kg": p6_res.nutrient_deficit_kg,
            "has_surplus": p6_res.has_surplus,
            "has_deficit": p6_res.has_deficit,
            "surplus_summary": p6_res.surplus_summary,
            "custom_prices_applied": p6_res.custom_prices_applied,
            "prices_last_updated": p6_res.prices_last_updated or "2026-10-22",
            "rules_last_updated": p6_res.rules_last_updated or "2026-10-22",
            "data_source": weather_res.get("data_source", "live"),
            "is_cached": False,
            "total_cost_status": getattr(p6_res, "total_cost_status", "AVAILABLE") if (final_is_verified and p6_res.status == "OPTIMIZATION_SUCCESS") else "UNAVAILABLE",
            "unified_recommendation": {
                "status": final_status,
                "is_verified": final_is_verified,
                "priority_tier": getattr(p4_res, "priority_tier", 2 if getattr(p4_res, "is_standard_rdf", False) else 1),
                "rule_priority": getattr(p4_res, "rule_priority", "TNAU_SOIL_TEST" if getattr(p4_res, "is_standard_rdf", False) else "STCR_IPNS"),
                "selection_reason": getattr(p4_res, "selection_reason", p5_res.derivation_explanation),
                "fallback_applied": getattr(p4_res, "fallback_applied", False),
                "fallback_reason": getattr(p4_res, "fallback_reason", None),
                "provisional_rule_rejected": getattr(p4_res, "provisional_rule_rejected", None),
                "rule_id": p4_res.selected_rule_id or p5_res.selected_rule_id,
                "source_title": (p5_res.authoritative_reference.get("title") if p5_res.authoritative_reference else None) or p4_res.source_title or "TNAU Crop Production Guide 2020",
                "total_cost_inr": p6_res.total_cost_inr if (final_is_verified and p6_res.status == "OPTIMIZATION_SUCCESS" and getattr(p6_res, "total_cost_status", "AVAILABLE") != "COST_UNAVAILABLE") else None,
                "total_cost_status": getattr(p6_res, "total_cost_status", "AVAILABLE") if (final_is_verified and p6_res.status == "OPTIMIZATION_SUCCESS") else "UNAVAILABLE",
                "recommended_products": [p.model_dump() if hasattr(p, "model_dump") else p for p in p6_res.recommended_products] if (final_is_verified and p6_res.status == "OPTIMIZATION_SUCCESS") else [],
                "split_application_schedule": [s.model_dump() if hasattr(s, "model_dump") else s for s in p6_res.split_application_schedule] if (final_is_verified and p6_res.status == "OPTIMIZATION_SUCCESS") else [],
                "soil_fertility_highlights": soil_fertility_highlights,
                "low_nutrients_highlight": soil_fertility_highlights,
            },
        }

        if cache_key and final_status in ("SUCCESS", "PROVISIONAL_PENDING_VALIDATION"):
            _RECOMMENDATION_CACHE[cache_key] = (time.time() + _RECOMMENDATION_CACHE_TTL, res_payload)

        return res_payload


class UnifiedFertilizerRecommendationService(FullRecommendationService):
    """
    Unified Fertilizer Recommendation Service.
    Produces one simple, accurate, traceable fertilizer recommendation per farmer.
    Coordinates Phase 4 Rule Selection (3-Tier Priority Cascade) -> Phase 5 NPK Calculation ->
    Phase 6 LP Cost Optimization -> Phase 2 District Yield Benchmark -> Phase 7 Weather Guidance.
    """
    def generate_recommendation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self.generate_full_recommendation(payload)


def get_full_recommendation(payload: Dict[str, Any]) -> Dict[str, Any]:
    service = UnifiedFertilizerRecommendationService()
    return service.generate_full_recommendation(payload)
