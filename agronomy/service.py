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
NO_MATCHING_RULE = "NO_MATCHING_RULE"
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
                warnings=[f"Crop '{crop_input}' is not supported by the agronomic rule database."]
            )

        # Canonical crop display name
        canonical_crop = crop_rules[0]["crop"]

        # Check soil series compatibility specifically
        req_soil_series = (req.soil_series or "").strip()
        all_crop_soil_series: Set[str] = set()
        for r in crop_rules:
            if r.get("soil_series"):
                for ss in r["soil_series"]:
                    all_crop_soil_series.add(ss.lower())

        # If user supplied a soil series, check if any rule for this crop supports it
        if req_soil_series and all_crop_soil_series and req_soil_series.lower() not in all_crop_soil_series:
            stcr_rules = [r for r in crop_rules if r["recommendation_method"].startswith("STCR")]
            if stcr_rules and not any(r.get("soil_series") is None for r in crop_rules):
                return RuleSelectionResponse(
                    status=UNSUPPORTED_SOIL_SERIES,
                    crop=canonical_crop,
                    warnings=[f"Soil series '{req_soil_series}' is not supported for crop '{canonical_crop}'."]
                )

        valid_candidates: List[Tuple[int, dict, List[str]]] = []
        pending_candidates: List[dict] = []

        req_irrigation = (req.irrigation_method or "").strip().lower()
        req_season = (req.season or "").strip().lower()
        req_target_yield = req.target_yield

        for r in crop_rules:
            rule_status = r.get("verification_status", "UNSUPPORTED")

            if rule_status == "UNSUPPORTED":
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

            if rule_status == "PENDING_VERIFICATION":
                pending_candidates.append(r)
                continue

            # Check missing inputs for this rule
            missing: List[str] = []
            required_inputs = r.get("required_soil_inputs", [])

            soil_vals = req.soil_values
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
                if not getattr(soil_vals, "phosphorus_method", None):
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

            if missing_inputs:
                return RuleSelectionResponse(
                    status=NEEDS_MORE_INPUT,
                    selected_rule_id=best_rule["rule_id"],
                    crop=canonical_crop,
                    recommendation_method=best_rule["recommendation_method"],
                    applicable_soil_series=best_rule.get("soil_series"),
                    applicable_season=best_rule.get("season"),
                    irrigation_method=best_rule.get("irrigation_method"),
                    required_inputs=best_rule.get("required_soil_inputs", []),
                    source_title=best_rule.get("source_title"),
                    source_url=best_rule.get("source_url"),
                    source_page_or_section=best_rule.get("source_page_or_section"),
                    verification_status=best_rule.get("verification_status"),
                    applicability_notes=best_rule.get("applicability_notes"),
                    missing_inputs=missing_inputs,
                    warnings=[f"Missing mandatory input(s) for selected rule {best_rule['rule_id']}: {', '.join(missing_inputs)}"]
                )

            # All required inputs present and rule verified!
            return RuleSelectionResponse(
                status=RULE_SELECTED,
                selected_rule_id=best_rule["rule_id"],
                crop=canonical_crop,
                recommendation_method=best_rule["recommendation_method"],
                applicable_soil_series=best_rule.get("soil_series"),
                applicable_season=best_rule.get("season"),
                irrigation_method=best_rule.get("irrigation_method"),
                required_inputs=best_rule.get("required_soil_inputs", []),
                source_title=best_rule.get("source_title"),
                source_url=best_rule.get("source_url"),
                source_page_or_section=best_rule.get("source_page_or_section"),
                verification_status=best_rule.get("verification_status"),
                applicability_notes=best_rule.get("applicability_notes"),
                missing_inputs=[],
                warnings=warnings
            )

        # If no verified candidates, check pending candidates
        if pending_candidates:
            p_rule = pending_candidates[0]
            return RuleSelectionResponse(
                status=PENDING_VERIFICATION,
                selected_rule_id=p_rule["rule_id"],
                crop=canonical_crop,
                recommendation_method=p_rule.get("recommendation_method"),
                applicable_soil_series=p_rule.get("soil_series"),
                applicable_season=p_rule.get("season"),
                irrigation_method=p_rule.get("irrigation_method"),
                required_inputs=p_rule.get("required_soil_inputs", []),
                source_title=p_rule.get("source_title"),
                source_url=p_rule.get("source_url"),
                source_page_or_section=p_rule.get("source_page_or_section"),
                verification_status="PENDING_VERIFICATION",
                applicability_notes=p_rule.get("applicability_notes"),
                warnings=[f"Rule '{p_rule['rule_id']}' matches inputs but is pending verification and cannot be used for production recommendations."]
            )

        # No matching rule found
        return RuleSelectionResponse(
            status=NO_MATCHING_RULE,
            crop=canonical_crop,
            warnings=["No matching verified agronomic rule found for the provided cultivation parameters."]
        )


def select_rule(req: RuleSelectionRequest) -> RuleSelectionResponse:
    service = RuleSelectionService()
    return service.select_rule(req)
