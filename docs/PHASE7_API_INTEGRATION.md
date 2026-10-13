# Phase 7 — Weather Service & Master Pipeline Integration Documentation

## 1. Overview
Phase 7 integrates weather guidance advisories (`phase7_integration/weather.py`) and orchestrates all sub-engines into a unified master recommendation pipeline (`phase7_integration/service.py`).

## 2. Orchestration Sequence
```
Client Request (Crop, District, Soil Test Values, Farm Area, Target Yield)
   │
   ├──> 1. Soil Profile Confirmation / Extraction Check
   │
   ├──> 2. Phase 4: Agronomic Rule Selection Engine
   │       └── Selects verified TNAU STCR / Soil-Test Rule
   │
   ├──> 3. Phase 5: NPK Calculation Engine
   │       └── Calculates exact N, P2O5, K2O requirements (kg/ha and total farm)
   │
   ├──> 4. Phase 6: LP Fertilizer Cost Optimizer
   │       └── Determines minimum cost fertilizer mix, commercial bag counts, and split schedule
   │
   ├──> 5. Phase 2: District Yield Benchmark Model (XGBoost)
   │       └── Predicts expected district benchmark yield (t/ha)
   │
   ├──> 6. Weather Advisory Engine
   │       └── Generates rainfall warnings & application timing advisories
   │
   └──> Final Consolidated Recommendation Response
```

## 3. Endpoints & Schemas
- `GET /api/weather/guidance?district={district}`
  - Returns: Current weather advisories, rainfall risks, and fertilizer application guidance.
- `POST /api/full-recommendation`
  - Accepts: Complete request containing soil profile, target crop, district, season, irrigation, farm area, target yield.
  - Returns: Consolidated recommendation including rule metadata, NPK requirements, fertilizer mix, cost breakdown, split schedules, weather guidance, and yield benchmark.

## 4. Integration Guardrails & Resilience
- **Isolated Weather Failure:** If the weather provider is offline or times out, the service returns `weather_guidance.status = "UNAVAILABLE"` with a warning, preserving 100% of the soil fertilizer recommendation.
- **Isolated ML Failure:** If XGBoost prediction fails or district data is uncalibrated, `district_yield_prediction.status = "UNAVAILABLE"` is returned, leaving agronomic dosing intact.
