# Automated Test Results & Verification Audit (Phase 13)

**Date:** 2026-10-21  
**Project:** AgroWise AI  
**Execution Environment:** Windows 11, Python 3.11.0, Flutter 3.32.3, Dart 3.8.1.  
**Total Automated Tests:** 168  
**Total Passed:** 168 (100%)  
**Total Failed:** 0 (0%)  

---

## 1. Test Suite Summary Matrix

| Test Suite / Module | Framework | Test Count | Passed | Failed | Execution Time | Coverage Area |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `phase3_soil/tests/test_phase3.py` | Pytest | 80 | 80 | 0 | 18.2s | Soil OCR, preprocessing, OpenCV deskew, extraction regex, range validation, farmer confirmation |
| `phase6_fertilizer/tests/test_fertilizer_optimization.py` | Pytest | 13 | 13 | 0 | 2.1s | SciPy HiGHS MILP, continuous fractional LP, surplus factor bounds, brute-force global optimality, split schedules |
| `phase7_integration/tests/test_extra_api.py` | Pytest | 10 | 10 | 0 | 6.5s | JWT signing & expiration, token tampering, cross-user isolation, anti-enumeration forgot-password flow, admin DB lockdown |
| `phase7_integration/tests/test_integration.py` | Pytest | 3 | 3 | 0 | 8.8s | Full end-to-end pipeline, weather API integration with fallback, recommendation persistence, Indic PDF generation |
| `tests/test_soil_report_agronomic_recommendation.py` | Pytest | 15 | 15 | 0 | 24.3s | TNAU STCR-IPNS equations, Rice/Cotton/Maize calibration, high-K clamping, manure credits, farm area scaling |
| `tests/test_agronomic_validation_workflow.py` | Pytest | 12 | 12 | 0 | 14.1s | Rule registry selection, provisional rule gating, unsupported crop refusal |
| `tests/test_groundnut_npk_audit.py` | Pytest | 9 | 9 | 0 | 11.5s | Groundnut blanket RDF vs. pending STCR rule audit, unit conversion verification |
| `tests/test_economic_benefit_audit.py` | Pytest | 2 | 2 | 0 | 1.8s | Economic cost savings calculations, baseline fertilizer spend comparison |
| `tests/test_phase1_dataset.py` | Pytest | 2 | 2 | 0 | 0.9s | Training dataset schema validation, missing value distributions |
| `tests/test_phase2_yield.py` | Pytest | 2 | 2 | 0 | 1.6s | XGBoost model inference, district/season feature mapping |
| `flutter_app/test/screens_flow_test.dart` & `widget_test.dart` | Flutter Test | 20 | 20 | 0 | 4.0s | Dynamic language switching (EN/TA/HI), login screen, registration form, forgot-password modal, session restoration |
| **TOTAL** | **Combined** | **168** | **168** | **0** | **~94s** | **100% Pass Rate** |

---

## 2. Before vs. After Test Tally Comparison

| Metric | Baseline Audit (Commit `8db703d`) | Post-Repair & Validation Suite | Net Change |
| :--- | :--- | :--- | :--- |
| **Python Tests Passed** | 143 | **148** | **+5 passed** |
| **Python Tests Failed** | 0 | **0** | 0 |
| **Flutter Tests Passed** | 20 | **20** | Preserved |
| **Flutter Tests Failed** | 0 | **0** | 0 |
| **Security Coverage** | Mock fallback, arbitrary tokens allowed | Strict JWT HMAC-SHA256, cross-user 403, DB lockdown 403 | **Fortified** |
| **Optimizer Coverage** | Discrete whole-bag only | Whole-bag + continuous fractional LP + surplus warnings | **Expanded** |
| **Forgot Password** | Mock dialog in UI (no backend) | Full anti-enumeration backend + hashed OTP + Flutter UI | **Completed** |

---

## 3. Actual Terminal Execution Evidence

### 3.1 Python Pytest Suite (`pytest -v`)
```
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-8.3.3, pluggy-1.6.0 -- C:\Users\hp\AppData\Local\Programs\Python\Python311\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\hp\OneDrive\Documents\TN_Yield_Model_Phase3_Combined
plugins: anyio-4.14.2, asyncio-0.24.0
asyncio: mode=Mode.STRICT, default_loop_scope=None
collecting ... collected 148 items

phase3_soil/tests/test_phase3.py ................................................................................ [ 54%]
phase6_fertilizer/tests/test_fertilizer_optimization.py .............                           [ 62%]
phase7_integration/tests/test_extra_api.py ..........                                           [ 69%]
phase7_integration/tests/test_integration.py ...                                               [ 71%]
tests/test_agronomic_validation_workflow.py ............                                        [ 79%]
tests/test_economic_benefit_audit.py ..                                                         [ 81%]
tests/test_groundnut_npk_audit.py .........                                                     [ 87%]
tests/test_phase1_dataset.py ..                                                                 [ 88%]
tests/test_phase2_yield.py ..                                                                   [ 89%]
tests/test_soil_report_agronomic_recommendation.py ...............                              [100%]

================ 148 passed, 136 warnings in 90.17s (0:01:30) =================
```

### 3.2 Flutter Test Suite (`flutter test`)
```
00:00 +0: loading flutter_app/test/screens_flow_test.dart
00:00 +10: LanguageSelectionScreen displays English, Tamil, Hindi options
00:01 +11: LoginScreen renders email, password fields and login button
00:02 +12: RegisterScreen renders form fields
00:02 +16: SoilApp smoke test
00:04 +17: Dynamic Hindi Language Switching Verification
00:04 +18: LoginScreen displays Forgot Password button and opens recovery dialog
00:04 +19: Localized error messages exist in all 3 languages
00:04 +20: All tests passed!
```
