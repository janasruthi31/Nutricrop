# Phase 8 — Comprehensive Testing, QA, and Deployment Guide

## 1. Test Architecture & Coverage
The project includes a 3-level verification test suite built with `pytest` and Python `unittest`.

### Suite Structure
1. `phase3_soil/tests/test_phase3.py` (32 tests):
   - Document upload (JPEG, PNG, PDF), binary sniffing, size limits.
   - Text extraction, unit normalization, Olsen vs Bray P validation, privacy, audit persistence.
2. `phase5_nutrient/tests/test_npk_calculation.py` (14 tests):
   - STCR targeted yield linear equations, soil-test adjustment tables, acre to hectare conversions.
   - Unit validation, per-hectare vs total farm quantities, missing target yield validation.
3. `phase6_fertilizer/tests/test_fertilizer_optimization.py` (6 tests):
   - LP cost minimization, bag rounding, 100% nutrient sufficiency re-verification, restricted catalog.
4. `phase7_integration/tests/test_integration.py` (3 tests):
   - Weather guidance endpoint, master pipeline orchestrator, full recommendation API.
5. `agronomy/tests/test_agronomy_rules.py` (13 tests):
   - Agronomic rule matching, precedence logic, verified status enforcement, unsupported crop handling.

## 2. Test Execution Command
```bash
pytest -v agronomy/tests phase3_soil/tests phase5_nutrient/tests phase6_fertilizer/tests phase7_integration/tests
```

**Overall Results:**
- **Total Executed Tests:** 68
- **Passed:** 68 (100% pass rate)
- **Failed:** 0

## 3. Production Deployment Guide
### Backend FastAPI Server
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start server via Uvicorn:
   ```bash
   uvicorn phase3_soil.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```
3. API documentation accessible at `http://localhost:8000/docs`.

### Flutter Mobile App (`flutter_app/`)
1. Ensure Flutter SDK is installed.
2. Run static analysis & build:
   ```bash
   cd flutter_app
   flutter analyze
   flutter build apk --release
   ```
