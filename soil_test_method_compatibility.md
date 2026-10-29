# Soil Phosphorus Test-Method Compatibility & Chemical Extraction Handling
**Project:** AgroWise AI (NutriCrop) — AI-Driven Sustainable Fertilizer Usage Optimizer  
**Domain:** Soil Phosphorus Chemical Extractants (Olsen vs. Bray-1) & Agronomic Rule Compatibility  
**Date:** October 2026  
**Status:** COMPLETE & ENFORCED  

---

## 1. Agronomic & Chemical Foundations

Soil test phosphorus (P) is an **empirical chemical extraction index**, not an absolute measurement of total elemental phosphorus in the soil profile. The quantity of orthophosphate ($H_2PO_4^-$ / $HPO_4^{2-}$) dissolved into an extracting solution depends fundamentally on the solution's pH, chelating ligands, fluoride activity, ionic strength, and soil-solution contact dynamics:

1. **Olsen Extraction (0.5 M $NaHCO_3$, pH 8.5):**
   - **Target Soil Reaction:** Neutral, calcareous, and alkaline soils ($\text{pH} \ge 6.5$).
   - **Mechanism:** Bicarbonate decreases calcium activity via $CaCO_3$ precipitation, driving the dissolution of calcium phosphates (dicalcium phosphate, tricalcium phosphate, octacalcium phosphate). The high pH suppresses aluminum and iron activity.
   - **TNAU STCR Calibration:** All TNAU STCR-IPNS equations in Tamil Nadu (Rice, Cotton, Maize) and the statewide rating adjustment table for Rice are calibrated **exclusively using the Olsen-P extraction method**.

2. **Bray-1 Extraction ($0.03\text{ N }NH_4F + 0.025\text{ N }HCl$, pH ~2.6):**
   - **Target Soil Reaction:** Acidic soils ($\text{pH} < 6.5$).
   - **Mechanism:** Dilute hydrochloric acid dissolves active aluminum and iron phosphates, while fluoride ($F^-$) complexes $Al^{3+}$ and $Fe^{3+}$ in solution to prevent rapid re-precipitation of dissolved phosphate.
   - **Calcareous Invalidation:** In neutral or alkaline soils with free calcium carbonate ($CaCO_3$), the fluoride ion precipitates with calcium ($CaF_2$), consuming the extractant and yielding spuriously low, meaningless phosphorus readings.

---

## 2. Prohibition of Generic Bray-to-Olsen Conversion Factors

### 2.1 The Myth of the "Universal Conversion Factor"
In unvalidated agricultural software, developers frequently attempt to bridge soil test methods by applying arbitrary multipliers, such as:
$$\text{Olsen-P} = \text{Bray-1 P} \times 0.5 \quad \text{or} \quad \text{Olsen-P} = \frac{\text{Bray-1 P}}{1.8}$$
**AgroWise AI strictly prohibits and eliminates all generic conversion factors.**

### 2.2 Agronomic Reasons Generic Conversions Cause Crop Failure:
1. **Soil-Specific Mineralogy:** The ratio of Bray-1 to Olsen extractable P varies from $0.2$ to $3.5$ depending on clay mineralogy, organic matter content, soil buffer power, and free iron/aluminum oxide ratios.
2. **Pedological Divergence in Tamil Nadu:**
   - Cauvery Delta alluvium (Palavidhi/Adanur/Kalathur) has neutral-to-alkaline pH ($7.2 - 8.2$) and high base saturation. Bray-1 extractant undergoes immediate fluoride neutralization.
   - Nilgiris or Western Ghats lateritic soils have acidic pH ($4.5 - 5.5$) with high iron/aluminum fixation where Olsen extraction is ineffective.
3. **Severe Fertilizer Dosing Errors:** Applying an uncalibrated $0.5$ multiplier to a Bray-1 value of $24\text{ kg/ha}$ fabricates an Olsen-P of $12\text{ kg/ha}$ (Low), causing the recommendation engine to prescribe excess diammonium phosphate (DAP) or single superphosphate (SSP). In alkaline soils, this wastes farmer capital and induces zinc deficiency; in sensitive pulse soils, it leads to toxic salt index and root burn.

---

## 3. Implementation of Soil-Test Method Compatibility Engine

### 3.1 Method Preservation in Soil Profiles
When an automated OCR scan or farmer confirmation extracts phosphorus data:
- The extracted value ($P$), unit (e.g. $\text{kg/ha}$, $\text{kg/acre}$, $\text{ppm}$), and **chemical method** (`Olsen` or `Bray`) are preserved verbatim in the `soil_profile` document and SQLite database.
- The system never silently alters the method tag or converts the numeric reading using an unvalidated multiplier.

### 3.2 Rule Compatibility Matrix

| Agronomic Rule | Supported Phosphorus Methods | Handling of Olsen-P | Handling of Bray-1 P | Handling of Unknown / Missing Method |
| :--- | :--- | :--- | :--- | :--- |
| **Rice STCR-IPNS** (`TNAU_STCR_IPNS_RICE_001`) | `["Olsen"]` | **Compatible:** STCR equation executes with high confidence | **Incompatible:** Returns `INCOMPATIBLE_SOIL_TEST_METHOD`; optimizer halted | Returns `MISSING_INPUTS` with `error_code="MISSING_PHOSPHORUS_METHOD"` |
| **Cotton STCR-IPNS** (`TNAU_STCR_IPNS_COTTON_001`) | `["Olsen"]` | **Compatible:** STCR equation executes | **Incompatible:** Returns `INCOMPATIBLE_SOIL_TEST_METHOD`; optimizer halted | Returns `MISSING_INPUTS` with `error_code="MISSING_PHOSPHORUS_METHOD"` |
| **Maize STCR-IPNS** (`TNAU_STCR_IPNS_MAIZE_001`) | `["Olsen"]` | **Compatible:** STCR equation executes | **Incompatible:** Returns `INCOMPATIBLE_SOIL_TEST_METHOD`; optimizer halted | Returns `MISSING_INPUTS` with `error_code="MISSING_PHOSPHORUS_METHOD"` |
| **Rice Standard RDF** (`TNAU_STD_RICE_001`) | `["Olsen"]` | **Compatible:** Standard rating adjustment applied | **Incompatible:** Returns `INCOMPATIBLE_SOIL_TEST_METHOD` | Returns `MISSING_INPUTS` with `error_code="MISSING_PHOSPHORUS_METHOD"` |
| **Blackgram Rainfed RDF** (`TNAU_STD_BLACKGRAM_RF_001`) | `["Olsen", "Bray"]` | **Compatible:** Diagnostic fertility interpretation; fixed RDF ($20:40:20$) | **Compatible:** Diagnostic fertility interpretation; fixed RDF ($20:40:20$) | Returns `MISSING_INPUTS` with `error_code="MISSING_PHOSPHORUS_METHOD"` if soil P entered |
| **Groundnut Blanket RDF** (`TNAU_BLANKET_GROUNDNUT_001`) | `["Olsen", "Bray"]` | **Compatible:** Diagnostic fertility interpretation; fixed RDF ($25:50:75$) | **Compatible:** Diagnostic fertility interpretation; fixed RDF ($25:50:75$) | Returns `MISSING_INPUTS` with `error_code="MISSING_PHOSPHORUS_METHOD"` if soil P entered |
| **Sugarcane Standard RDF** (`TNAU_STD_SUGARCANE_001`) | `["Olsen", "Bray"]` | **Compatible:** Fixed statewide schedule ($275:62.5:112.5$) | **Compatible:** Fixed statewide schedule ($275:62.5:112.5$) | Returns `MISSING_INPUTS` with `error_code="MISSING_PHOSPHORUS_METHOD"` if soil P entered |

---

## 4. Error Codes, Actionable Messages & UI Guidance

### 4.1 Incompatible Method (`INCOMPATIBLE_SOIL_TEST_METHOD`)
When an uploaded report or farmer confirmation states Bray-1 phosphorus and the matching agronomic rule requires Olsen-P:
- **Status Code:** `200 OK` (agronomic payload contract).
- **Status Field:** `"INCOMPATIBLE_SOIL_TEST_METHOD"`.
- **Error Code:** `"INCOMPATIBLE_SOIL_TEST_METHOD"`.
- **Actionable Farmer Message:**
  > *"Your soil test report uses the 'Bray'-P test method. The selected agronomic rule is calibrated exclusively for Olsen-P (0.5 M NaHCO3, pH 8.5). Converting Bray-1 to Olsen-P using generic conversion factors is agronomically unvalidated and prohibited. Please confirm whether an Olsen-P test was performed or select a standard fertilizer recommendation."*
- **Safety Lockdown:** Commercial fertilizer bag optimizer is completely bypassed (`total_cost_inr = 0.0`, `recommended_products = []`), preventing uncalibrated fertilizer procurement.

### 4.2 Missing Method (`MISSING_INPUTS`)
When soil phosphorus is provided but the test method is omitted:
- **Status Field:** `"MISSING_INPUTS"`.
- **Error Code:** `"MISSING_PHOSPHORUS_METHOD"`.
- **Actionable Farmer Message:**
  > *"Phosphorus test method (Olsen or Bray-1) is required to determine fertilizer requirements. Please verify the method stated on your Soil Health Card (Olsen for neutral/alkaline soils, Bray for acidic soils). Do not guess."*
- **Missing Inputs List:** `["soil_phosphorus_method"]`.

### 4.3 Flutter UI Enhancements
1. **Confirmation Screen (`VerifyScreen`):**
   - Clearly exposes the Phosphorus Method dropdown (`Olsen` / `Bray-1`).
   - Displays clear explanatory guidance below the dropdown:  
     *“Confirm method from Soil Health Card (Olsen for neutral/alkaline, Bray for acidic). Do not guess.”*
   - Prevents blind guessing by requiring the farmer to check the physical card or select a blanket recommendation.
2. **NPK Requirement Screen (`NpkRequirementScreen`):**
   - Displays prominent amber alert banner if `status == "INCOMPATIBLE_SOIL_TEST_METHOD"` or `error_code == "MISSING_PHOSPHORUS_METHOD"`.
   - Explains that chemical extraction incompatibility prevents precision calculation without an Olsen soil test.
3. **Recommendation Screen (`FinalRecommendationScreen`):**
   - Displays clear, bulleted agronomic limitations under the Authoritative Reference section.
   - Shows supported phosphorus methods and explicit disclaimers regarding extraction validity.

---

## 5. Verification and Compliance

All compatibility rules have been verified through automated test suites in `tests/test_soil_series_and_methods.py`, `tests/test_agronomic_validation_workflow.py`, and `tests/test_soil_report_agronomic_recommendation.py`. Full integration with the Flutter client has been verified with 21 unit/widget tests passing.
