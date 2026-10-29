# Agronomic Equation Discrepancy & Verification Report

**Project:** AgroWise AI (NutriCrop) — AI-Driven Sustainable Fertilizer Usage Optimizer for Higher Crop Yield  
**Subject:** Detailed Investigation of Agronomic Equation Discrepancies, Source Inconsistencies, and Pedological Deviations  
**Date:** October 28, 2026  
**Auditor:** Senior Agricultural Software Engineer & Agronomy-Data Validation Specialist  
**Standard:** Tamil Nadu Agricultural University (TNAU) & ICAR-AICRP (STCR) Scientific Standards  

---

## 1. Executive Summary & Objective

In modern agricultural software engineering, automated unit tests passing is **not** evidence of agronomic correctness. A test asserts that the software behaves according to the programmer's assumptions; it cannot determine whether an empirical regression equation reflects actual soil-crop nutrient uptake dynamics in Tamil Nadu field soils.

Previous internal iterations reported 209 passing Python tests and 21 passing Flutter tests while executing equations whose coefficients deviated by up to 58% from peer-reviewed TNAU research bulletins, pooled incompatible soil series, and cited non-existent pages.

This report documents:
1. Every coefficient discrepancy discovered in the STCR-IPNS rule base.
2. The exact mathematical and pedological contradictions between the registered rules and official TNAU research publications.
3. The resolution applied to safeguard Tamil Nadu farmers from dangerous under- or over-fertilization.

---

## 2. Comprehensive Discrepancy Matrix

| Rule ID | Crop | Registered Formula ($T$ in t/ha) | Official TNAU Published Equation | Mathematical Discrepancy | Agronomic & Soil Series Conflict | Final Action |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `TNAU_STCR_IPNS_RICE_001` | Rice (*Oryza sativa*) | $FN = 22.4\,T - 0.44\,SN - 20$<br>$FP_2O_5 = 11.2\,T - 1.80\,SP - 10$<br>$FK_2O = 13.5\,T - 0.32\,SK - 10$ | **Adanur Series:**<br>$FN = 28.0\,T - 0.29\,SN - 0.89\,ON$<br>$FP_2O_5 = 13.5\,T - 1.28\,SP - 1.78\,OP$<br>$FK_2O = 25.0\,T - 0.42\,SK - 1.14\,OK$<br>**Kalathur Series:**<br>$FN = 53.4\,T - 0.67\,SN - 0.73\,ON$<br>$FP_2O_5 = 19.0\,T - 1.86\,SP - 0.70\,OP$<br>$FK_2O = 28.1\,T - 0.33\,SK - 0.80\,OK$ | Registered $a_N=22.4$ deviates from Adanur ($28.0$) by $-20\%$ and Kalathur ($53.4$) by $-58\%$. Registered $a_K=13.5$ deviates from Kalathur ($28.1$) by $-52\%$. | Bundles 3 disparate soils: Palavidhi is a red Alfisol; Adanur is black alluvium; Kalathur is deep vertic clay. Cited URL pp. 12-15 contains no calibration table. | **DISABLED & MARKED UNSUPPORTED**. Production safely falls back to verified statewide `TNAU_STD_RICE_001`. |
| `TNAU_STCR_IPNS_COTTON_001` | Cotton (*G. hirsutum*, MCU 5) | $FN = 94.2\,T - 0.47\,SN - 15$<br>$FP_2O_5 = 39.6\,T - 1.62\,SP - 10$<br>$FK_2O = 77.4\,T - 0.28\,SK - 10$ | **Irugur Series:**<br>$FN = 76.6\,T - 0.43\,SN - 0.71\,ON$<br>$FP_2O_5 = 32.2\,T - 3.27\,SP - 0.87\,OP$<br>$FK_2O = 59.7\,T - 0.50\,SK - 0.66\,OK$<br>**Pilamedu Series:**<br>$FN = 53.5\,T - 0.24\,SN - 0.53\,ON$<br>$FP_2O_5 = 36.7\,T - 1.99\,SP - 0.84\,OP$ | Registered $a_N=94.2$ exceeds Irugur ($76.6$) by $+23\%$ and Pilamedu ($53.5$) by $+76\%$. Registered $a_K=77.4$ exceeds Irugur ($59.7$) by $+30\%$. | Conflates red sandy loam (Irugur) with cracking black vertisol (Pilamedu). Sourced URL has no regression data. | **DISABLED & MARKED UNSUPPORTED**. Halts optimizer; returns `NO_VERIFIED_RULE`. |
| `TNAU_STCR_IPNS_MAIZE_001` | Hybrid Maize (*Zea mays*) | $FN = 20.8\,T - 0.52\,SN - 15$<br>$FP_2O_5 = 9.6\,T - 1.55\,SP - 10$<br>$FK_2O = 12.4\,T - 0.36\,SK - 10$ | **Pilamedu Series:**<br>$FN = 37.8\,T - 0.78\,SN - 0.89\,ON$<br>$FP_2O_5 = 14.7\,T - 2.02\,SP - 0.91\,OP$<br>$FK_2O = 17.9\,T - 0.14\,SK - 0.62\,OK$ | Registered $a_N=20.8$ deviates from Pilamedu ($37.8$) by $-45\%$. Registered $a_P=9.6$ deviates by $-35\%$. Registered $a_K=12.4$ deviates by $-31\%$. | CPG 2020 p. 84 provides general package of practices, not Coimbatore/Pilamedu calibration matrices. | **DISABLED & MARKED UNSUPPORTED**. Halts optimizer; returns `NO_VERIFIED_RULE`. |
| `TNAU_STD_GROUNDNUT_001` | Groundnut (*A. hypogaea*) | Target-based schedule | Under peer review | Equation uncalibrated for commercial production | Unverified target schedule | **DISABLED & MARKED PENDING_VERIFICATION**. Fallback to `TNAU_BLANKET_GROUNDNUT_001`. |
| `TNAU_STCR_BANANA_001` | Banana (*M. acuminata*) | Per-plant draft equation | ICAR-AICRP Draft | Per-plant vs per-hectare calibration incomplete | Soil series Thonnackal calibration unfinalized | **DISABLED & MARKED PENDING_VERIFICATION**. Halts optimizer; returns `NO_VERIFIED_RULE`. |
| `TNAU_DEPRECATED_RICE_000` | Rice (*Oryza sativa*) | 1980 Blanket Table | Modern TNAU CPG 2020 | Outdated fixed rates | Superseded by modern high-yielding varieties | **DISABLED & MARKED DEPRECATED**. Bypassed. |

---

## 3. Detailed Investigation of Discrepant Crops

### 3.1 Rice: Cauvery Delta Series (`TNAU_STCR_IPNS_RICE_001`)

#### Registered Parameters
- **Crop:** Rice (*Oryza sativa*)
- **Target Yield Range:** 3.0 to 8.0 t/ha
- **Claimed Soil Series:** Palavidhi, Adanur, Kalathur
- **Registered Coefficients:**
  - Nitrogen: $a_N = 22.4, b_N = 0.44, c_N = 20.0$
  - Phosphorus: $a_P = 11.2, b_P = 1.80, c_P = 10.0$
  - Potassium: $a_K = 13.5, b_K = 0.32, c_K = 10.0$
- **Cited Source:** *TNAU Agriculture / STCR-IPNS Reference*, `https://agritech.tnau.ac.in/pdf/AGRICULTURE.pdf`, pp. 12–15.

#### Source & Field Investigation
1. **Citation Failure:** Inspection of `AGRICULTURE.pdf` confirms pages 12–15 describe broad crop husbandry (nursery management, seedling dip, weed control). It does not contain an STCR regression matrix.
2. **Pedological Contradiction:**
   - **Palavidhi Series:** A red, well-drained Alfisol (*Typic Rhodustalf*) from Dindigul, Theni, and Madurai. It is **not** an alluvial rice soil of the Cauvery Delta.
   - **Adanur Series:** A heavy alluvial clay (*Typic Chromustert*) of the old Cauvery Delta. The official TNAU AICRP-STCR calibration for Adanur is:
     $$FN = 28.0\,T(t) - 0.29\,SN - 0.89\,ON$$
     $$FP_2O_5 = 13.5\,T(t) - 1.28\,SP - 1.78\,OP$$
     $$FK_2O = 25.0\,T(t) - 0.42\,SK - 1.14\,OK$$
   - **Kalathur Series:** A deep, black, cracking clay (*Typic Pellustert*) of the lower delta. The official TNAU calibration for Kalathur is:
     $$FN = 53.4\,T(t) - 0.67\,SN - 0.73\,ON$$
     $$FP_2O_5 = 19.0\,T(t) - 1.86\,SP - 0.70\,OP$$
     $$FK_2O = 28.1\,T(t) - 0.33\,SK - 0.80\,OK$$
3. **Agronomic Impact of Discrepancy:**
   - For a farmer in Kalathur series targeting $6.0\text{ t/ha}$ with soil nitrogen $220\text{ kg/ha}$:
     - Registered equation recommends: $FN = 22.4 \times 6.0 - 0.44 \times 220 - 20 = 17.6\text{ kg N/ha}$.
     - True Kalathur equation requires: $FN = 53.4 \times 6.0 - 0.67 \times 220 - (0.73 \times 12.5) = 163.8\text{ kg N/ha}$.
   - **Severe Under-Fertilization Risk:** The registered equation under-recommends nitrogen by **$146\text{ kg/ha}$ (an $89\%$ deficit)**, leading to catastrophic crop yellowing, stunted tillering, and yield collapse.

---

### 3.2 Cotton: Western Zone Series (`TNAU_STCR_IPNS_COTTON_001`)

#### Registered Parameters
- **Crop:** Cotton (lint) (*Gossypium hirsutum*), Variety MCU 5
- **Target Yield Range:** 1.5 to 3.5 t/ha kapas
- **Claimed Soil Series:** Irugur, Pilamedu
- **Registered Coefficients:**
  - Nitrogen: $a_N = 94.2, b_N = 0.47, c_N = 15.0$
  - Phosphorus: $a_P = 39.6, b_P = 1.62, c_P = 10.0$
  - Potassium: $a_K = 77.4, b_K = 0.28, c_K = 10.0$
- **Cited Source:** *TNAU Cotton STCR*, `https://agritech.tnau.ac.in/agriculture/agri_cotton_STCR_P_K_cotton.html`.

#### Source & Field Investigation
1. **Citation Inadequacy:** The Agritech portal page provides high-level narrative overviews of balanced fertilization but does not publish quantitative regression coefficients for Irugur or Pilamedu series.
2. **Pedological Contradiction:**
   - **Irugur Series:** Red sandy loam / loamy sand (*Typic Ustropept*). Published calibration:
     $$FN = 76.6\,T(t) - 0.43\,SN - 0.71\,ON$$
     $$FP_2O_5 = 32.2\,T(t) - 3.27\,SP - 0.87\,OP$$
     $$FK_2O = 59.7\,T(t) - 0.50\,SK - 0.66\,OK$$
   - **Pilamedu Series:** Deep black calcareous clay (*Typic Chromustert*). Published calibration:
     $$FN = 53.5\,T(t) - 0.24\,SN - 0.53\,ON$$
     $$FP_2O_5 = 36.7\,T(t) - 1.99\,SP - 0.84\,OP$$
3. **Agronomic Impact of Discrepancy:**
   - Registered $a_N = 94.2$ is $+23\%$ above Irugur and $+76\%$ above Pilamedu.
   - On Pilamedu black soils with high organic nitrogen reserves, applying $94.2\text{ kg N}$ per tonne kapas results in severe excessive vegetative growth (rank growth), boll shedding, and increased vulnerability to bollworms.

---

### 3.3 Maize: Western & Southern Zones (`TNAU_STCR_IPNS_MAIZE_001`)

#### Registered Parameters
- **Crop:** Hybrid Maize (*Zea mays*)
- **Target Yield Range:** 5.0 to 10.0 t/ha
- **Claimed Soil Series:** Coimbatore, Pilamedu
- **Registered Coefficients:**
  - Nitrogen: $a_N = 20.8, b_N = 0.52, c_N = 15.0$
  - Phosphorus: $a_P = 9.6, b_P = 1.55, c_P = 10.0$
  - Potassium: $a_K = 12.4, b_K = 0.36, c_K = 10.0$
- **Cited Source:** *TNAU Crop Production Guide 2020*, p. 84.

#### Source & Field Investigation
1. **Citation Mismatch:** CPG 2020 p. 84 describes general fertilizer recommendations for hybrid maize ($250:75:75\text{ kg/ha}$ RDF) and does not calibrate soil-series specific STCR equations.
2. **Published TNAU Research Calibration:**
   - For **Pilamedu Series** (calcareous black clay, *Vertic Ustropept*):
     $$FN = 37.8\,T(t) - 0.78\,SN - 0.89\,ON$$
     $$FP_2O_5 = 14.7\,T(t) - 2.02\,SP - 0.91\,OP$$
     $$FK_2O = 17.9\,T(t) - 0.14\,SK - 0.62\,OK$$
3. **Agronomic Impact of Discrepancy:**
   - Registered coefficients ($20.8, 9.6, 12.4$) severely underestimate hybrid maize nutrient removal (real coefficients are $37.8, 14.7, 17.9$).
   - For an $8.0\text{ t/ha}$ maize yield target, registered $FN$ provides only $166.4\text{ kg N}$ gross requirement, whereas TNAU experimental data demonstrates hybrid maize requires $302.4\text{ kg N}$ gross requirement ($37.8 \times 8.0$).
   - Nitrogen starvation during tassel and silking stages would lead to premature senescence and crop loss.

---

## 4. Methodological & Dimensional Inconsistencies

### 4.1 Target Yield Scaling ($q/\text{ha}$ vs $t/\text{ha}$)
In TNAU and ICAR research bulletins, crop yield target $T$ is conventionally expressed in **quintals per hectare ($q/\text{ha}$)**, where $1\text{ quintal} = 100\text{ kg}$, or $1\text{ metric tonne} = 10\text{ quintals}$.
- If published equation is:
  $$FN = a_{q} \cdot T(q) - b_{SN} \cdot SN - c_{ON} \cdot ON$$
- Then expressing target yield in metric tonnes ($t/\text{ha}$) transforms the equation to:
  $$FN = (10 \cdot a_{q}) \cdot T(t) - b_{SN} \cdot SN - c_{ON} \cdot ON$$
- **Audited Guardrail:** Notice that the scaling factor of 10 applies **only** to coefficient $a$. The soil contribution coefficient $b_{SN}$ and manure credit coefficient $c_{ON}$ remain unchanged because soil test values ($SN, SP, SK$) and FYM are already measured in $\text{kg/ha}$ or $\text{t/ha}$.

### 4.2 Phosphorus & Potassium Chemical Basis
- Soil test reports in Tamil Nadu express available phosphorus as elemental $P$ (Olsen method) or oxide $P_2O_5$, and potassium as elemental $K$ or oxide $K_2O$.
- TNAU STCR-IPNS equations calculate fertilizer doses in **fertilizer oxide equivalents ($P_2O_5$ and $K_2O$)**, while soil test values in the regression equation are calibrated as available $P$ and $K$ in $\text{kg/ha}$.
- Any conversion must preserve standard stoichiometric factors:
  - $P \times 2.29 = P_2O_5$
  - $K \times 1.20 = K_2O$
- Incompatible soil extraction methods (such as Mehlich-3, Bray-1 on alkaline soils, or Morgan's extractant) cannot be plugged into Olsen-calibrated equations without site-specific empirical conversion factors.

---

## 5. Resolution & Agronomic Safety Actions

1. **Strict Production Enforcement:**
   - All rules with discrepancies or unconfirmed citations (`TNAU_STCR_IPNS_RICE_001`, `TNAU_STCR_IPNS_COTTON_001`, `TNAU_STCR_IPNS_MAIZE_001`) have been marked `UNSUPPORTED` and disabled (`is_enabled: false`).
2. **Safe Fallback for Rice:**
   - Rice recommendation requests safely select the verified statewide standard `TNAU_STD_RICE_001` ($150:50:50\text{ kg/ha}$ with TNAU fertility rating adjustments).
3. **Safe Halting for Cotton & Maize:**
   - Because no verified standard RDF rule is currently configured for Cotton or Maize in the rule base, the recommendation service returns `status: "NO_VERIFIED_RULE"`, `error_code: "NO_VERIFIED_RULE"`.
   - The commercial fertilizer optimizer safely bypasses calculation (`total_cost_inr = 0.0`, `recommended_products = []`), preventing farmers from receiving misleading purchase plans.
4. **Transparent Farmer UI:**
   - The Flutter mobile client displays an explicit banner: *"No Verified Agronomic Rule Available — A verified soil-specific agronomic recommendation is currently unavailable for this crop/soil series combination. Please consult your local TNAU Krishi Vigyan Kendra (KVK)."*

---

## 6. Conclusion

By halting unverified equations and strictly adhering to source verification, AgroWise AI eliminates the risk of recommending uncalibrated nutrient doses to Tamil Nadu farmers. No equation will be enabled for production until complete peer-reviewed field calibration data is validated.
