# Phase 4 — Agronomic Rule Database & Selection Validation

## 1. Overview
Phase 4 maintains the verified agronomic rule registry (`data/agronomy/tnau_stcr_rules.json`) and source traceability log (`data/agronomy/source_registry.csv`). It implements the deterministic rule selection engine for Tamil Nadu crops.

## 2. Mandatory Rules Enforced
1. **Source Verification:** Only rules marked `VERIFIED` in `tnau_stcr_rules.json` with valid source citations in `source_registry.csv` can generate fertilizer recommendations.
2. **Precedence Hierarchy:**
   - **Rank 1:** Verified `STCR-IPNS` rule (Soil Test Crop Response with Integrated Plant Nutrient System using FYM/Organic Manure).
   - **Rank 2:** Verified `STCR-NPK` rule (Soil Test Crop Response linear targeted yield formula).
   - **Rank 3:** Standard `TNAU-SOIL-TEST` rating-based adjustment recommendation.
3. **Hard Applicability Matching:** Crop name, irrigation status, season, target yield range, soil series, and phosphorus test method must match exactly. Rules are never selected based solely on partial crop string matching.

## 3. Data Schemas & Structure
- **Rule Storage:** `data/agronomy/tnau_stcr_rules.json`
- **Source Traceability:** `data/agronomy/source_registry.csv`
- **Selection Engine:** `agronomy/selector.py`
- **API Endpoint:** `POST /api/agronomy/select-rule`

## 4. Verification Test Suite Results
- `test_01_exact_stcr_rule_match`: PASSED
- `test_02_unverified_rule_rejection`: PASSED
- `test_03_unsupported_crop_returns_unsupported`: PASSED
- `test_04_target_yield_out_of_range`: PASSED
- `test_05_olsen_vs_bray_method_guard`: PASSED
- Total Phase 4 Test Pass Rate: 100% (14/14 tests passing).
