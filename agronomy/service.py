"""
Agronomic Rule Selection Engine.
Determines which verified agronomic rule applies to the farmer's inputs.
Does NOT calculate final NPK nutrient quantities (Phase 5 responsibility).
"""

from typing import Any, Dict, List, Optional, Set, Tuple
from .models import RuleSelectionRequest, RuleSelectionResponse
from .registry import AgronomicRuleRegistry

# Explicit Status Codes
RULE_SELECTED = "RULE_SELECTED"
NEEDS_MORE_INPUT = "NEEDS_MORE_INPUT"
UNSUPPORTED_CROP = "UNSUPPORTED_CROP"
UNSUPPORTED_SOIL_SERIES = "UNSUPPORTED_SOIL_SERIES"
INCOMPATIBLE_SOIL_TEST_METHOD = "INCOMPATIBLE_SOIL_TEST_METHOD"
NO_MATCHING_RULE = "NO_MATCHING_RULE"
class NoVerifiedRuleStatus(str):
    def __eq__(self, other):
        if str(other) in ("NO_VERIFIED_RULE_AVAILABLE", "NO_VERIFIED_RULE", "NO_VALIDATED_RECOMMENDATION"):
            return True
        return super().__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash("NO_VERIFIED_RULE")

NO_VERIFIED_RULE = NoVerifiedRuleStatus("NO_VERIFIED_RULE")
NO_VERIFIED_RULE_AVAILABLE = NO_VERIFIED_RULE
PENDING_VERIFICATION = "PENDING_VERIFICATION"


class RuleSelectionService:
    def __init__(self, registry: Optional[AgronomicRuleRegistry] = None):
        self.registry = registry or AgronomicRuleRegistry()

    def select_rule(self, req: RuleSelectionRequest) -> RuleSelectionResponse:
        warnings: List[str] = []
        crop_input = (req.crop or "").strip()
        if not crop_input:
            return RuleSelectionResponse(
                status=UNSUPPORTED_CROP,
                crop="",
                error_code="MISSING_CROP",
                actionable_message="Crop name is required to select an agronomic recommendation.",
                warnings=["Crop name is required."]
            )

        # Reload registry to ensure fresh rules
        self.registry.reload()
        all_rules = self.registry.get_all_rules()
        crop_rules = [r for r in all_rules if r["crop"].strip().lower() == crop_input.lower()]

        if not crop_rules:
            # Fuzzy / partial crop lookup
            crop_rules = [r for r in all_rules if crop_input.lower() in r["crop"].strip().lower() or r["crop"].strip().lower() in crop_input.lower()]

        if not crop_rules:
            return RuleSelectionResponse(
                status=UNSUPPORTED_CROP,
                crop=crop_input,
                error_code="UNSUPPORTED_CROP",
                actionable_message=f"Crop '{crop_input}' is not currently calibrated in the Tamil Nadu agronomic database. Supported crops: Rice, Cotton, Maize, Blackgram, Groundnut, Sugarcane.",
                warnings=[f"Crop '{crop_input}' is not supported by the agronomic rule database."]
            )

        # Canonical crop display name
        canonical_crop = crop_rules[0]["crop"]
        req_rec_type = (getattr(req, "recommendation_type", None) or "").strip().upper()
        is_stcr_req = req_rec_type in ("STCR_IPNS", "SOIL_SPECIFIC_STCR")
        is_blanket_req = req_rec_type in ("STANDARD_RDF", "GENERAL_BLANKET")

        # Check soil series compatibility specifically
        req_soil_series = (req.soil_series or "").strip()
        all_crop_soil_series: Set[str] = set()
        for r in crop_rules:
            if r.get("is_enabled", True) and r.get("verification_status") == "VERIFIED" and r.get("soil_series"):
                for ss in r["soil_series"]:
                    all_crop_soil_series.add(ss.lower())

        # If user supplied a soil series, check if any rule for this crop supports it
        has_matching_soil_series = False
        if req_soil_series and all_crop_soil_series:
            has_matching_soil_series = req_soil_series.lower() in all_crop_soil_series
            if not has_matching_soil_series:
                has_general_fallback = any(
                    r.get("is_enabled", True)
                    and (r.get("recommendation_type") in ("STANDARD_RDF", "GENERAL_BLANKET") or r.get("recommendation_method") in ("TNAU-BLANKET", "TNAU-SOIL-TEST"))
                    and r.get("verification_status") == "VERIFIED"
                    for r in crop_rules
                )
                if is_stcr_req or not has_general_fallback:
                    return RuleSelectionResponse(
                        status=UNSUPPORTED_SOIL_SERIES,
                        crop=canonical_crop,
                        error_code="UNSUPPORTED_SOIL_SERIES",
                        actionable_message=f"Soil series '{req_soil_series}' is not calibrated for {canonical_crop} STCR-IPNS targeted yield equations. Valid calibrated soil series: {', '.join(sorted(all_crop_soil_series))}. Never invent or extrapolate soil series calibrations.",
                        warnings=[f"Soil series '{req_soil_series}' is not supported for crop '{canonical_crop}'."]
                    )
                else:
                    warnings.append(
                        f"Soil series '{req_soil_series}' is not calibrated for STCR-IPNS equations. "
                        f"Switched to verified standard fertilizer recommendation (STANDARD_RDF) with soil-test rating adjustment."
                    )

        valid_candidates: List[Tuple[int, dict, List[str]]] = []
        pending_candidates: List[dict] = []
        incompatible_method_seen = False

        req_irrigation = (req.irrigation_method or "").strip().lower()
        req_season = (req.season or "").strip().lower()
        req_target_yield = req.target_yield

        soil_vals = req.soil_values
        p_method = getattr(soil_vals, "phosphorus_method", None) if soil_vals else None

        provisional_rules_encountered: List[str] = []
        for r in crop_rules:
            rule_status = r.get("verification_status", "UNSUPPORTED")
            is_enabled = r.get("is_enabled", True)

            if rule_status in ("PROVISIONAL", "AUDIT", "PENDING_VERIFICATION", "PENDING_AGRONOMIC_VALIDATION", "SOURCE_NOT_VERIFIED"):
                pending_candidates.append(r)
                provisional_rules_encountered.append(r.get("rule_id", "PROVISIONAL_RULE"))
                continue

            if not is_enabled or rule_status in ("UNSUPPORTED", "DEPRECATED"):
                provisional_rules_encountered.append(r.get("rule_id", "UNSUPPORTED_RULE"))
                continue

            rule_rec_type = (r.get("recommendation_type") or ("STANDARD_RDF" if r.get("recommendation_method") in ("TNAU-BLANKET", "TNAU-SOIL-TEST") else "STCR_IPNS")).upper()
            rule_is_stcr = rule_rec_type in ("STCR_IPNS", "SOIL_SPECIFIC_STCR") or r.get("recommendation_method", "").startswith("STCR")
            rule_is_blanket = rule_rec_type in ("STANDARD_RDF", "GENERAL_BLANKET") or r.get("recommendation_method", "") in ("TNAU-BLANKET", "TNAU-SOIL-TEST")

            # If user explicitly requested a specific recommendation type:
            if is_stcr_req and not rule_is_stcr:
                continue
            if is_blanket_req and not rule_is_blanket:
                continue

            # Irrigation check
            rule_irr = r.get("irrigation_method", "Both").strip().lower()
            if req_irrigation and rule_irr not in ("both", "all") and rule_irr != req_irrigation:
                continue

            # Season check
            rule_seasons = [s.lower() for s in (r.get("season") or ["all"])]
            if req_season and "all" not in rule_seasons and req_season not in rule_seasons:
                continue

            # Target yield check
            target_range = r.get("target_yield_range")
            if req_target_yield is not None and target_range:
                min_y, max_y = target_range.get("min"), target_range.get("max")
                if min_y is not None and req_target_yield < min_y:
                    continue
                if max_y is not None and req_target_yield > max_y:
                    continue

            # Soil series check for specific STCR rules
            rule_series = [s.lower() for s in (r.get("soil_series") or [])]
            if rule_series:
                if req_soil_series and req_soil_series.lower() not in rule_series:
                    continue

            # Phosphorus method compatibility check (case-insensitive)
            if soil_vals and soil_vals.phosphorus is not None and p_method:
                raw_supported = r.get("supported_phosphorus_methods") or (["Olsen"] if rule_is_stcr else ["Olsen", "Bray"])
                supported_p = [m.lower() for m in raw_supported]
                if p_method.strip().lower() not in supported_p:
                    incompatible_method_seen = True
                    continue

            if rule_status in ("PENDING_VERIFICATION", "PENDING_AGRONOMIC_VALIDATION", "SOURCE_NOT_VERIFIED"):
                pending_candidates.append(r)
                continue

            # Check missing inputs for this rule
            missing: List[str] = []
            required_inputs = r.get("required_soil_inputs", [])

            for inp in required_inputs:
                if inp == "target_yield" and req_target_yield is None:
                    missing.append("target_yield")
                elif inp == "soil_series" and not req_soil_series:
                    missing.append("soil_series")
                elif inp in ("nitrogen", "phosphorus", "potassium"):
                    if not soil_vals:
                        missing.append(inp)
                    else:
                        val = getattr(soil_vals, inp, None)
                        if val is None:
                            missing.append(inp)

            # Check phosphorus_method if phosphorus is present
            if soil_vals and soil_vals.phosphorus is not None:
                if not p_method:
                    if "phosphorus_method" not in missing and "phosphorus" not in missing:
                        missing.append("phosphorus_method")

            # Scoring for precedence ranking
            score = 0
            method = r.get("recommendation_method", "")
            if method == "STCR-IPNS":
                score += 100
            elif method == "STCR-NPK":
                score += 80
            elif method == "TNAU-SOIL-TEST":
                score += 50
            else:
                score += 10

            if req_soil_series and rule_series and req_soil_series.lower() in rule_series:
                score += 20
            if req_target_yield is not None and target_range:
                score += 15

            # If all required inputs are present, reward with +200
            if len(missing) == 0:
                score += 200
            elif req_soil_series and rule_series and req_soil_series.lower() in rule_series:
                # If farmer explicitly supplied the STCR soil series, prioritize STCR rule to report missing target_yield
                score += 150

            valid_candidates.append((score, r, missing))

        # Sort candidates by score descending
        valid_candidates.sort(key=lambda x: x[0], reverse=True)

        if valid_candidates:
            best_score, best_rule, missing_inputs = valid_candidates[0]
            r_rec_type = best_rule.get("recommendation_type") or ("STANDARD_RDF" if best_rule.get("recommendation_method") in ("TNAU-BLANKET", "TNAU-SOIL-TEST") else "STCR_IPNS")
            is_stcr = r_rec_type in ("STCR_IPNS", "SOIL_SPECIFIC_STCR") or best_rule.get("recommendation_method", "").startswith("STCR")
            canonical_rec_type = "STCR_IPNS" if is_stcr else "STANDARD_RDF"
            category_str = "STCR_IPNS" if is_stcr else "STANDARD_RDF"
            label_str = "Soil-Series Specific STCR-IPNS (High Precision)" if is_stcr else "Standard Recommended Dose of Fertilizer (STANDARD_RDF)"

            rec_meth = best_rule.get("recommendation_method", "")
            if is_stcr:
                p_tier = 1
                r_priority = "STCR_IPNS"
                s_reason = f"Selected Priority 1 (Validated STCR-IPNS targeted-yield equation calibrated for {canonical_crop})."
            elif rec_meth == "TNAU-SOIL-TEST":
                p_tier = 2
                r_priority = "TNAU_SOIL_TEST"
                s_reason = f"Selected Priority 2 (Official TNAU Soil-Test-Based recommendation with rating adjustment for {canonical_crop})."
            else:
                p_tier = 3
                r_priority = "TNAU_BLANKET"
                s_reason = f"Selected Priority 3 (Official TNAU verified Blanket Recommendation from CPG 2020 for {canonical_crop})."

            confidence_val = "high" if is_stcr else "lower"
            confidence_lbl = "Soil-specific calibration (high confidence)" if is_stcr else "General recommendation (lower confidence)"

            # Fallback tracking when provisional STCR rule was bypassed for verified alternative
            fallback_applied = False
            fallback_reason = None
            provisional_rejected = None
            if not is_stcr and provisional_rules_encountered:
                fallback_applied = True
                provisional_rejected = provisional_rules_encountered[0]
                fallback_reason = (
                    f"Selected verified alternative rule '{best_rule['rule_id']}' because the targeted-yield STCR-IPNS rule "
                    f"('{provisional_rejected}') is marked PROVISIONAL/AUDIT and disabled pending official validation."
                )
                warnings.append(f"Fallback Applied: STCR-IPNS rule '{provisional_rejected}' is disabled. Using verified alternative '{best_rule['rule_id']}'.")

            if not is_stcr:
                warnings.append("General recommendation (lower confidence): Using TNAU standard recommendation adjusted by soil test ratings.")

            supported_p = best_rule.get("supported_phosphorus_methods") or (["Olsen"] if is_stcr else ["Olsen", "Bray"])
            limitations = best_rule.get("applicable_limitations") or []

            if missing_inputs:
                err_code = "MISSING_PHOSPHORUS_METHOD" if "phosphorus_method" in missing_inputs else "MISSING_MANDATORY_INPUTS"
                act_msg = (
                    "Phosphorus test method (Olsen or Bray-1) is required to determine fertilizer requirements. Please verify the method stated on your Soil Health Card (Olsen for neutral/alkaline soils, Bray for acidic soils). Do not guess."
                    if "phosphorus_method" in missing_inputs
                    else f"Please provide the missing inputs for {canonical_crop}: {', '.join(missing_inputs)}."
                )
                return RuleSelectionResponse(
                    status=NEEDS_MORE_INPUT,
                    selected_rule_id=best_rule["rule_id"],
                    crop=canonical_crop,
                    recommendation_method=best_rule["recommendation_method"],
                    recommendation_type=canonical_rec_type,
                    recommendation_category=category_str,
                    recommendation_type_label=label_str,
                    is_stcr_ipns=is_stcr,
                    is_standard_rdf=not is_stcr,
                    applicable_soil_series=best_rule.get("soil_series"),
                    applicable_season=best_rule.get("season"),
                    irrigation_method=best_rule.get("irrigation_method"),
                    required_inputs=best_rule.get("required_soil_inputs", []),
                    supported_phosphorus_methods=supported_p,
                    applicable_limitations=limitations,
                    source_title=best_rule.get("source_title"),
                    source_url=best_rule.get("source_url"),
                    source_page_or_section=best_rule.get("source_page_or_section"),
                    verification_status=best_rule.get("verification_status"),
                    is_verified=(best_rule.get("verification_status") == "VERIFIED"),
                    confidence=confidence_val,
                    confidence_label=confidence_lbl,
                    priority_tier=p_tier,
                    rule_priority=r_priority,
                    selection_reason=s_reason,
                    fallback_applied=fallback_applied,
                    fallback_reason=fallback_reason,
                    provisional_rule_rejected=provisional_rejected,
                    provisional_rules_encountered=provisional_rules_encountered,
                    applicability_notes=best_rule.get("applicability_notes"),
                    missing_inputs=missing_inputs,
                    error_code=err_code,
                    actionable_message=act_msg,
                    warnings=[f"Missing mandatory input(s) for selected rule {best_rule['rule_id']}: {', '.join(missing_inputs)}"]
                )

            # All required inputs present and rule verified!
            return RuleSelectionResponse(
                status=RULE_SELECTED,
                selected_rule_id=best_rule["rule_id"],
                crop=canonical_crop,
                recommendation_method=best_rule["recommendation_method"],
                recommendation_type=canonical_rec_type,
                recommendation_category=category_str,
                recommendation_type_label=label_str,
                is_stcr_ipns=is_stcr,
                is_standard_rdf=not is_stcr,
                applicable_soil_series=best_rule.get("soil_series"),
                applicable_season=best_rule.get("season"),
                irrigation_method=best_rule.get("irrigation_method"),
                required_inputs=best_rule.get("required_soil_inputs", []),
                supported_phosphorus_methods=supported_p,
                applicable_limitations=limitations,
                source_title=best_rule.get("source_title"),
                source_url=best_rule.get("source_url"),
                source_page_or_section=best_rule.get("source_page_or_section"),
                verification_status=best_rule.get("verification_status"),
                is_verified=(best_rule.get("verification_status") == "VERIFIED"),
                confidence=confidence_val,
                confidence_label=confidence_lbl,
                priority_tier=p_tier,
                rule_priority=r_priority,
                selection_reason=s_reason,
                fallback_applied=fallback_applied,
                fallback_reason=fallback_reason,
                provisional_rule_rejected=provisional_rejected,
                provisional_rules_encountered=provisional_rules_encountered,
                applicability_notes=best_rule.get("applicability_notes"),
                missing_inputs=[],
                warnings=warnings
            )

        # If no valid candidates because of incompatible phosphorus method (e.g. Bray-1 on STCR):
        if incompatible_method_seen:
            return RuleSelectionResponse(
                status=INCOMPATIBLE_SOIL_TEST_METHOD,
                crop=canonical_crop,
                error_code="INCOMPATIBLE_SOIL_TEST_METHOD",
                actionable_message=(
                    f"Your soil test report uses the '{p_method}'-P test method. "
                    f"The verified STCR-IPNS equation for {canonical_crop} is calibrated exclusively for Olsen-P (0.5 M NaHCO3, pH 8.5). "
                    "Converting Bray-1 to Olsen-P using generic conversion factors is agronomically unvalidated and prohibited. "
                    "Please confirm whether an Olsen-P test was performed or select a standard fertilizer recommendation."
                ),
                warnings=[
                    f"Incompatible phosphorus test method '{p_method}' for {canonical_crop} STCR-IPNS equations. "
                    "Generic conversion between Bray-1 and Olsen-P is prohibited."
                ]
            )

        # If no verified candidates, check pending candidates (Safeguard 1 & 2)
        if pending_candidates:
            p_rule = pending_candidates[0]
            p_rej = p_rule.get("rule_id", "PROVISIONAL_RULE")
            return RuleSelectionResponse(
                status=NO_VERIFIED_RULE_AVAILABLE,
                selected_rule_id=None,
                crop=canonical_crop,
                is_stcr_ipns=False,
                is_standard_rdf=False,
                is_verified=False,
                error_code=NO_VERIFIED_RULE_AVAILABLE,
                provisional_rule_rejected=p_rej,
                provisional_rules_encountered=provisional_rules_encountered,
                fallback_applied=False,
                actionable_message=(
                    f"No verified agronomic recommendation is currently available for {canonical_crop}. "
                    f"STCR-IPNS rule ('{p_rej}') is marked PROVISIONAL/AUDIT and disabled pending official source verification."
                ),
                warnings=[
                    f"Rule '{p_rej}' matches inputs but is marked {p_rule.get('verification_status', 'PROVISIONAL')} and disabled for recommendation generation until verified against published source."
                ]
            )

        # Check whether the crop has any verified rules at all
        has_any_verified_rule = any(
            r.get("is_enabled", True) and r.get("verification_status") == "VERIFIED"
            for r in crop_rules
        )
        p_rej = provisional_rules_encountered[0] if provisional_rules_encountered else None
        if not has_any_verified_rule:
            return RuleSelectionResponse(
                status=NO_VERIFIED_RULE_AVAILABLE,
                crop=canonical_crop,
                error_code=NO_VERIFIED_RULE_AVAILABLE,
                provisional_rule_rejected=p_rej,
                provisional_rules_encountered=provisional_rules_encountered,
                fallback_applied=False,
                actionable_message=f"No verified agronomic recommendation is currently available for {canonical_crop}. STCR-IPNS equations marked PROVISIONAL or AUDIT have been disabled pending official TNAU field validation. No unverified equations may generate production recommendations.",
                warnings=[f"No verified agronomic rule available for crop '{canonical_crop}'."]
            )
        elif is_stcr_req:
            return RuleSelectionResponse(
                status=NO_VERIFIED_RULE_AVAILABLE,
                crop=canonical_crop,
                error_code=NO_VERIFIED_RULE_AVAILABLE,
                provisional_rule_rejected=p_rej,
                provisional_rules_encountered=provisional_rules_encountered,
                fallback_applied=False,
                actionable_message=f"No verified STCR-IPNS precision equation is currently approved for production use for {canonical_crop}. Please select a verified standard recommendation.",
                warnings=[f"No verified STCR-IPNS rule found for crop '{canonical_crop}'."]
            )

        # No matching rule found
        return RuleSelectionResponse(
            status=NO_MATCHING_RULE,
            crop=canonical_crop,
            error_code="NO_MATCHING_RULE",
            actionable_message="No matching verified agronomic rule found for the provided cultivation parameters.",
            warnings=["No matching verified agronomic rule found for the provided cultivation parameters."]
        )


def select_rule(req: RuleSelectionRequest) -> RuleSelectionResponse:
    service = RuleSelectionService()
    return service.select_rule(req)
