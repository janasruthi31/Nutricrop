# Agronomic Rules and Parameters Requiring Official Primary Sourcing

**Authority:** AgroWise AI Agronomic Governance  
**Policy:** Zero invented numbers. Any unverified coefficient or parameter remains **PROVISIONAL** until verified against official TNAU/ICAR literature with a passing golden test.

---

## 1. Rules Currently Designated as PROVISIONAL

| Rule ID | Crop | Soil Series / Tract | Current Status | Required Primary Source Document / Action |
|:---|:---|:---|:---|:---|
| `TNAU_STCR_IPNS_RICE_001` | Rice | Palavidhi / Adanur / Kalathur | **PROVISIONAL** | Primary AICRP-STCR / TNAU calibration bulletin table for Cauvery Delta series (Adanur & Kalathur series coefficients). |
| `TNAU_STCR_IPNS_COTTON_001` | Cotton (lint) | Irugur / Pilamedu | **PROVISIONAL** | Official TNAU Coimbatore STCR bulletin for MCU 5 cotton equations across black soil tracts. |
| `TNAU_STCR_IPNS_MAIZE_001` | Maize | Coimbatore / Pilamedu | **PROVISIONAL** | Official TNAU CPG 2020 hybrid maize multi-location regression parameters for red sandy loam. |
| `TNAU_STD_RICE_001` | Rice | General Tamil Nadu | **PROVISIONAL** | Continuous soil test adjustment equation or official TNAU rating band boundaries. |
| `TNAU_STD_SUGARCANE_001` | Sugarcane | General Tamil Nadu | **PROVISIONAL** | Sourced STCR equations for plant vs ratoon sugarcane in Western and Cauvery tracts. |
| `TNAU_STCR_BANANA_001` | Banana (Grand Naine) | Alluvial Tracts | **PROVISIONAL** | Multi-location trial calibration data from NRCB / TNAU. |

---

## 2. Information Needed from Domain Expert / User

To promote any of the above PROVISIONAL rules to **VERIFIED**:
1. Provide the exact TNAU / ICAR publication title, publication year, chapter, and page number.
2. Provide a worked reference example (Soil test N, P, K in kg/ha, target yield in q/ha or t/ha, FYM applied in t/ha, and exact calculated N, P2O5, K2O fertilizer requirements).
3. antigravity will add a corresponding test in `phase5_nutrient/tests/test_golden_stcr.py`. Once the golden test passes, the rule status will be marked **VERIFIED**.
