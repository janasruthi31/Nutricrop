# Final Equation Change Summary & Implementation Rationale

**Project:** AgroWise AI (NutriCrop) — AI-Driven Sustainable Fertilizer Usage Optimizer for Higher Crop Yield  
**Date:** October 28, 2026  
**Auditor:** Senior Agricultural Software Engineer & Agronomy-Data Validation Specialist  
**Status:** COMPLETED & PRODUCTION-READY  

---

## 1. Overview & Change Rationale

This document summarizes the architectural and code changes made to enforce agronomic safety and eliminate unverified empirical equations from generating production recommendations.

In accordance with strict agronomic safety guidelines:
1. **Never Invent Agricultural Equations:** No equation or coefficient may be guessed or extrapolated.
2. **Production Gating:** Any equation lacking verified source evidence or exhibiting soil series calibration discrepancies must be disabled.
3. **No Silent Fallbacks to Unverified Rules:** When an STCR rule is unsupported, fall back only to a verified standard recommendation if documented conditions are satisfied (e.g. Rice falling back to `TNAU_STD_RICE_001`). If no verified rule exists (e.g. Cotton, Maize), halt calculation with `NO_VERIFIED_RULE`.
4. **Commercial Optimization Halting:** When no verified agronomic rule is available, the fertilizer purchase optimizer must NOT recommend chemical fertilizer purchases.

---

## 2. Inventory of Modified Files

### 2.1 Agronomic Rule Registry: `data/agronomy/tnau_stcr_rules.json`

| Rule ID | Prior Status | New Verification Status | `is_enabled` | `is_verified` | Rationale |
| :--- | :--- | :--- | :---: | :---: | :--- |
| `TNAU_STCR_IPNS_RICE_001` | PROVISIONAL / VERIFIED | `UNSUPPORTED` | `false` | `false` | Registered coefficients ($22.4, 11.2, 13.5$) contradict published TNAU Delta alluvium calibrations (Adanur $28.0, 13.5, 25.0$; Kalathur $53.4, 19.0, 28.1$). Palavidhi is an uncalibrated Alfisol. |
| `TNAU_STCR_IPNS_COTTON_001` | PROVISIONAL / VERIFIED | `UNSUPPORTED` | `false` | `false` | Registered coefficients ($94.2, 39.6, 77.4$) contradict published Irugur ($76.6, 32.2, 59.7$) and Pilamedu ($53.5, 36.7$) calibrations. Pooling red sandy loam with cracking vertisol is unvalidated. |
| `TNAU_STCR_IPNS_MAIZE_001` | PROVISIONAL / VERIFIED | `UNSUPPORTED` | `false` | `false` | Registered coefficients ($20.8, 9.6, 12.4$) contradict published Pilamedu calibration ($37.8, 14.7, 17.9$). CPG 2020 p. 84 does not calibrate a joint equation. |
| `TNAU_STD_RICE_001` | VERIFIED | `VERIFIED` | `true` | `true` | Authoritative standard RDF ($150:50:50\text{ kg/ha}$) with verified TNAU soil rating table. Production fallback for irrigated rice. |
| `TNAU_STD_BLACKGRAM_RF_001` | VERIFIED | `VERIFIED` | `true` | `true` | Verified rainfed blanket RDF ($20:40:20\text{ kg/ha}$) supported by TNAU CPG 2020 Pulses Chapter p. 64. |
| `TNAU_BLANKET_GROUNDNUT_001` | VERIFIED | `VERIFIED` | `true` | `true` | Verified blanket RDF ($25:50:75\text{ kg/ha}$) supported by TNAU CPG 2020 Oilseeds Section p. 112. |
| `TNAU_STD_SUGARCANE_001` | VERIFIED | `VERIFIED` | `true` | `true` | Verified blanket RDF ($275:62.5:112.5\text{ kg/ha}$) supported by TNAU CPG 2020 p. 150. |
| `TNAU_STD_GROUNDNUT_001` | PROVISIONAL | `PENDING_VERIFICATION` | `false` | `false` | Uncalibrated targeted yield schedule under peer review. Disabled in production. |
| `TNAU_STCR_BANANA_001` | PROVISIONAL | `PENDING_VERIFICATION` | `false` | `false` | Draft per-plant equation under calibration. Disabled in production. |
| `TNAU_DEPRECATED_RICE_000` | UNSUPPORTED | `DEPRECATED` | `false` | `false` | Obsolete 1980 advisory table superseded by modern CPG. Disabled. |

---

### 2.2 Agronomic Rule Selection Service: `agronomy/service.py`

- **Added Constant:** `NO_VERIFIED_RULE = "NO_VERIFIED_RULE"`.
- **Production Eligibility Filter:** In `select_rule()`, candidate rules with `is_enabled == False`, `is_verified == False`, or `verification_status != "VERIFIED"` are filtered out of production matching.
- **Strict Error Code:** If no verified candidate rule matches the query conditions or if an unverified STCR equation was explicitly requested, the service returns:
  ```python
  RuleSelectionResult(
      rule=None,
      status=NO_VERIFIED_RULE,
      error_code="NO_VERIFIED_RULE",
      actionable_message="No verified agronomic recommendation is currently available for this crop/soil combination in the official TNAU database. Please consult your local TNAU Krishi Vigyan Kendra (KVK)."
  )
  ```

---

### 2.3 Nutrient Calculation Service: `phase5_nutrient/service.py`

- **Added Constant:** `NO_VERIFIED_RULE = "NO_VERIFIED_RULE"`.
- **Pre-Execution Safety Intercept:** If Phase 4 rule selection returned `NO_VERIFIED_RULE`, Phase 5 immediately returns a zeroed requirement response with status `NO_VERIFIED_RULE` and appends explanatory warnings.
- **Gating Parameter (`allow_unverified`):**
  - By default (`allow_unverified=False`), selecting an unverified or disabled rule halts with status `NO_VERIFIED_RULE`.
  - When `allow_unverified=True` (used strictly for mathematical auditing and research calibration), Phase 5 computes the formula but sets `is_verified_rule=False` and attaches explicit warnings.

---

### 2.4 Commercial Integration & Optimizer Service: `phase7_integration/service.py`

- **Optimizer Bypassing:** When Phase 5 returns `status == "NO_VERIFIED_RULE"`:
  ```python
  if nutrient_resp.status == NO_VERIFIED_RULE:
      final_status = "NO_VERIFIED_RULE"
      final_is_verified = False
      final_rec_type = "UNAVAILABLE"
      # Fertilizer optimizer halted
      recommended_products = []
      total_cost_inr = 0.0
  ```
- **Farmer Safety Guarantee:** Prevents generating commercial fertilizer purchase plans when agronomic nutrient targets are unvalidated.

---

### 2.5 Flutter Mobile Application: `flutter_app/lib/screens/npk_requirement_screen.dart`

- **Visual Safety Banner:** Added conditional rendering when `status == "NO_VERIFIED_RULE"`:
  - Renders a warning card styled with an alert icon and amber border.
  - States: *"No Verified Agronomic Rule Available — A verified soil-specific agronomic recommendation is currently unavailable for this crop/soil series combination. Please consult your local TNAU Krishi Vigyan Kendra (KVK)."*
  - Replaces purchase calculation buttons with safe advisory messages.

---

### 2.6 Test Suites

1. **`tests/test_final_equation_audit_safety.py` (New):**
   - 11 dedicated regression tests verifying registry states, rice fallback to standard RDF, cotton/maize rejection with `NO_VERIFIED_RULE`, optimizer halting, and safety gating. (11/11 passed).
2. **`tests/test_nutrient_equations_audit.py` (Updated):**
   - Updated audit scenarios to pass `allow_unverified=True` for mathematical audit checks and verify verified standard fallback `TNAU_STD_RICE_001` in end-to-end API response. (11/11 passed).
3. **`tests/test_phase1_dataset.py` (Updated):**
   - Included `"DEPRECATED"` in rule registry status verification. (3/3 passed).

---

## 3. Summary of System Behavior Post-Change

```
Farmer Request
      │
      ▼
Rule Selection (agronomy/service.py)
      │
      ├─► Rice (Statewide / Cauvery Delta) ──► Disabled STCR bypassed ──► Uses TNAU_STD_RICE_001 (VERIFIED) ──► Calculates RDF
      │
      ├─► Blackgram (Rainfed) ─────────────► Uses TNAU_STD_BLACKGRAM_RF_001 (VERIFIED) ──────────────────────► Calculates RDF
      │
      ├─► Groundnut ───────────────────────► Uses TNAU_BLANKET_GROUNDNUT_001 (VERIFIED) ─────────────────────► Calculates RDF
      │
      ├─► Sugarcane (Plant Cane) ──────────► Uses TNAU_STD_SUGARCANE_001 (VERIFIED) ─────────────────────────► Calculates RDF
      │
      └─► Cotton / Maize / Banana ────────► No verified rule available ──► Returns NO_VERIFIED_RULE ──────────► Halts Optimizer
                                                                                                               (Products: [], Cost: 0)
```
