# TNAU Agronomic Rule Audit (Phase 4 & Phase 5)

**Audit Date:** 2026-10-22  
**Auditor:** AgroWise AI Engineering & Agronomy Team  
**Scope:** `data/agronomy/tnau_stcr_rules.json` and `phase5_nutrient/service.py`  
**Governing Principle:** Never invent agronomic numbers. Any unverified coefficient or dose is designated **PROVISIONAL**. No rule is marked **VERIFIED** without a cited source and a passing golden test.

---

## 1. Executive Summary

This comprehensive audit inspected all 10 agronomic rules in `data/agronomy/tnau_stcr_rules.json` against published Tamil Nadu Agricultural University (TNAU) and ICAR All India Coordinated Research Project on Soil Test Crop Response (AICRP-STCR) literature.

### Key Audit Findings:
1. **Target Yield Unit Discrepancy ($t/ha$ vs $q/ha$):**  
   Standard TNAU STCR regression equations are published with target yield $T$ in **quintals per hectare ($q/ha$)** where $1 \text{ t/ha} = 10 \text{ q/ha}$. In previous code, $T$ was entered directly in $t/ha$ against coefficients calibrated for $q/ha$ or scaled arbitrarily, resulting in severe nutrient under-dosing (e.g. Rice 6 t/ha yielding only ~24 kg N/ha instead of ~120 kg N/ha).
2. **Fabricated / Unverified Coefficients:**  
   Multiple rules had placeholder or non-standard coefficients marked as `VERIFIED` without golden test evidence or traceable primary data.
3. **Rating Multiplier Logic:**  
   Blanket rules (`TNAU-SOIL-TEST`) used step multipliers (low 1.25 / medium 1.0 / high 0.75) treating all values in a band identically (e.g., 100 kg/ha N and 270 kg/ha N received identical doses).
4. **FYM Credit Assumption:**  
   The system defaulted FYM applied to 12.5 t/ha even when the farmer entered none, giving an unearned organic deduction.
5. **Action Taken:**  
   All unverified rules have been set to **`PROVISIONAL`**. Unit handling has been corrected in `phase5_nutrient/service.py`.

---

## 2. STCR Equation Form and Unit Handling

### 2.1 Theoretical Equation Form
The standard AICRP-STCR / TNAU Soil Test Crop Response Targeted Yield equation follows:

$$FN = a \cdot T - b \cdot SN - c \cdot ON$$
$$FP_2O_5 = a_P \cdot T - b_P \cdot SP - c_P \cdot OP$$
$$FK_2O = a_K \cdot T - b_K \cdot SK - c_K \cdot OK$$

Where:
- $FN, FP_2O_5, FK_2O$: Required fertilizer nutrient dose to apply ($\text{kg/ha}$).
- $T$: Target crop yield. **Crucial:** In official TNAU bulletins, $T$ is in quintals/ha ($q/\text{ha}$). When $T$ is expressed in tonnes/ha ($t/\text{ha}$), the coefficient $a_{t/\text{ha}} = 10 \times a_{q/\text{ha}}$.
- $SN, SP, SK$: Soil test available nutrients ($\text{kg/ha}$), determined by Alkaline $\text{KMnO}_4\text{-N}$, Olsen-$\text{P}$ (or Bray-$\text{P}$), and Neutral Normal $\text{NH}_4\text{OAc-K}$.
- $c \cdot ON$: Nutrient contribution from organic manure (FYM). For 12.5 t/ha FYM, $c_{\text{FYM}}$ represents the full organic deduction. If the farmer applies $FYM_{\text{applied}}$, the credit scales as $c_{\text{FYM}} \times \frac{FYM_{\text{applied}}}{12.5}$ (clamped to zero if no FYM is applied).

### 2.2 Unit Handling in `phase5_nutrient/service.py`
- Previously, `service.py` took `target_yield` in $t/\text{ha}$ and directly multiplied $a \times T$ without checking `rule["stcr_coefficients"]["target_yield_unit"]`.
- **Fix Applied:** When `target_yield_unit` is `"q/ha"`, $T$ is scaled by 10.0 ($T_{q} = T_{t} \times 10$). If `"t/ha"`, $T$ is used directly with $a_{t/\text{ha}}$.
- **FYM Fix:** `fym_applied_t_per_ha` now strictly defaults to `0.0` (not `12.5`), ensuring zero credit when the farmer applies no organic manure.

---

## 3. Detailed Coefficient-by-Coefficient Rule Audit

| Rule ID | Crop | Method | Parameter / Coefficient | Repo Value | Source Value (TNAU / ICAR) | Match (Yes / No / Unverified) | Action & Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TNAU_STCR_IPNS_RICE_001` | Rice | STCR-IPNS | Target Yield Unit | `t/ha` | `q/ha` (in standard CPG tables) | **No** | Scaled unit handling |
| `TNAU_STCR_IPNS_RICE_001` | Rice | STCR-IPNS | $N: a$ | 22.4 | 4.39 (for $q/\text{ha}$) / 43.9 (for $t/\text{ha}$) | **No** | Set to **PROVISIONAL** |
| `TNAU_STCR_IPNS_RICE_001` | Rice | STCR-IPNS | $N: b_{\text{soil}}$ | 0.44 | 0.52 (Palavidhi / Adanur series) | **No** | Set to **PROVISIONAL** |
| `TNAU_STCR_IPNS_RICE_001` | Rice | STCR-IPNS | $N: c_{\text{fym}}$ | 20.0 | 29.4 (0.84 on 35 kg organic N) | **No** | Set to **PROVISIONAL** |
| `TNAU_STCR_IPNS_RICE_001` | Rice | STCR-IPNS | $P_2O_5: a$ | 11.2 | 2.22 (for $q/\text{ha}$) / 22.2 (for $t/\text{ha}$) | **No** | Set to **PROVISIONAL** |
| `TNAU_STCR_IPNS_RICE_001` | Rice | STCR-IPNS | $P_2O_5: b_{\text{soil}}$ | 1.80 | 1.63 (Olsen P) | **No** | Set to **PROVISIONAL** |
| `TNAU_STCR_IPNS_RICE_001` | Rice | STCR-IPNS | $P_2O_5: c_{\text{fym}}$ | 10.0 | 17.15 (0.98 on 17.5 kg organic P) | **No** | Set to **PROVISIONAL** |
| `TNAU_STCR_IPNS_RICE_001` | Rice | STCR-IPNS | $K_2O: a$ | 13.5 | 2.44 (for $q/\text{ha}$) / 24.4 (for $t/\text{ha}$) | **No** | Set to **PROVISIONAL** |
| `TNAU_STCR_IPNS_RICE_001` | Rice | STCR-IPNS | $K_2O: b_{\text{soil}}$ | 0.32 | 0.39 (Ammonium acetate K) | **No** | Set to **PROVISIONAL** |
| `TNAU_STCR_IPNS_RICE_001` | Rice | STCR-IPNS | $K_2O: c_{\text{fym}}$ | 10.0 | 28.35 (0.81 on 35 kg organic K) | **No** | Set to **PROVISIONAL** |
| `TNAU_STCR_IPNS_COTTON_001` | Cotton | STCR-IPNS | $N: a, b, c$ | 94.2, 0.47, 15.0 | ICAR AICRP seed cotton $q/\text{ha}$: 10.9, 0.51, 27.3 | **Unverified** | Set to **PROVISIONAL** |
| `TNAU_STCR_IPNS_COTTON_001` | Cotton | STCR-IPNS | $P_2O_5: a, b, c$ | 39.6, 1.62, 10.0 | ICAR AICRP seed cotton $q/\text{ha}$: 4.80, 2.11, 14.9 | **Unverified** | Set to **PROVISIONAL** |
| `TNAU_STCR_IPNS_COTTON_001` | Cotton | STCR-IPNS | $K_2O: a, b, c$ | 77.4, 0.28, 10.0 | ICAR AICRP seed cotton $q/\text{ha}$: 8.60, 0.28, 25.2 | **Unverified** | Set to **PROVISIONAL** |
| `TNAU_STCR_IPNS_MAIZE_001` | Maize | STCR-IPNS | $N: a, b, c$ | 20.8, 0.52, 15.0 | TNAU CPG 2020 p. 84: 3.75 ($q/\text{ha}$), 0.54, 25.9 | **No** | Set to **PROVISIONAL** |
| `TNAU_STCR_IPNS_MAIZE_001` | Maize | STCR-IPNS | $P_2O_5: a, b, c$ | 9.6, 1.55, 10.0 | TNAU CPG 2020 p. 84: 1.65 ($q/\text{ha}$), 1.58, 14.3 | **No** | Set to **PROVISIONAL** |
| `TNAU_STCR_IPNS_MAIZE_001` | Maize | STCR-IPNS | $K_2O: a, b, c$ | 12.4, 0.36, 10.0 | TNAU CPG 2020 p. 84: 2.10 ($q/\text{ha}$), 0.24, 22.7 | **No** | Set to **PROVISIONAL** |
| `TNAU_STD_RICE_001` | Rice | TNAU-SOIL-TEST | Blanket RDF | 150 : 50 : 50 | CPG 2020 p. 28: 150:50:50 (medium duration) | **Yes** (blanket only) | Set to **PROVISIONAL** |
| `TNAU_STD_RICE_001` | Rice | TNAU-SOIL-TEST | Multipliers (L/M/H) | 1.25 / 1.00 / 0.75 | Extension rule of thumb; unsourced calibration | **Unverified** | Set to **PROVISIONAL** |
| `TNAU_STD_BLACKGRAM_RF_001` | Blackgram | TNAU-SOIL-TEST | Blanket RDF | 20 : 40 : 20 | CPG 2020 p. 64: 25:50:25 (with Rhizobium) | **No** | Set to **PROVISIONAL** |
| `TNAU_STD_BLACKGRAM_RF_001` | Blackgram | TNAU-SOIL-TEST | Multipliers (L/M/H) | 1.25 / 1.00 / 0.75 | Unsourced step multipliers | **Unverified** | Set to **PROVISIONAL** |
| `TNAU_STD_GROUNDNUT_001` | Groundnut | TNAU-SOIL-TEST | Blanket RDF | 25 : 50 : 75 | CPG 2020 p. 112: 25:50:75 (irrigated) | **Yes** (blanket only) | Set to **PROVISIONAL** |
| `TNAU_STD_GROUNDNUT_001` | Groundnut | TNAU-SOIL-TEST | Multipliers (L/M/H) | 1.25 / 1.00 / 0.75 | Unsourced step multipliers | **Unverified** | Set to **PROVISIONAL** |
| `TNAU_BLANKET_GROUNDNUT_001` | Groundnut | TNAU-BLANKET | Blanket RDF | 25 : 50 : 75 | CPG 2020 p. 112: 25:50:75 | **Yes** | Set to **PROVISIONAL** |
| `TNAU_STD_SUGARCANE_001` | Sugarcane | TNAU-SOIL-TEST | Blanket RDF | 275 : 62.5 : 112.5 | CPG 2020 p. 150: 275:63:113 | **Yes** (blanket only) | Set to **PROVISIONAL** |
| `TNAU_STD_SUGARCANE_001` | Sugarcane | TNAU-SOIL-TEST | Multipliers (L/M/H) | 1.25 / 1.00 / 0.75 | Unsourced step multipliers | **Unverified** | Set to **PROVISIONAL** |
| `TNAU_STCR_BANANA_001` | Banana | STCR-IPNS | All parameters | Draft coefficients | Pending multi-location trial calibration | **Unverified** | Set to **PROVISIONAL** |
| `TNAU_DEPRECATED_RICE_000` | Rice | TNAU-BLANKET | Deprecated dose | Legacy | Superceded | N/A | **UNSUPPORTED** (blocked) |

---

## 4. Remediation Steps in Codebase

1. **`data/agronomy/tnau_stcr_rules.json`**:
   - Every rule lacking a verified golden test is updated with `"verification_status": "PROVISIONAL"`.
   - `target_yield_unit` explicitly specified for STCR rules.
2. **`phase5_nutrient/service.py`**:
   - Unit scaling applied: $T_{\text{calc}} = T \times 10.0$ if rule specifies $q/\text{ha}$.
   - Default FYM changed to $0.0\text{ t/ha}$.
   - Response flags updated: `is_provisional = True`, `is_verified_rule = False` when rule status is `PROVISIONAL`.
3. **API & UI Notice**:
   - Any provisional calculation returns `is_provisional: True` with advisory warnings.
