import os
import pytest
from predict_yield import predict_district_yield, MODEL, META


def test_01_model_and_metadata_artifacts_exist():
    assert os.path.exists(MODEL), f"Model artifact missing at {MODEL}"
    assert os.path.exists(META), f"Metadata artifact missing at {META}"


def test_02_predict_district_yield_valid_input():
    yield_kg_ha = predict_district_yield(district="Thanjavur", crop="Rice", season="Kharif", year=2024)
    assert isinstance(yield_kg_ha, float)
    assert yield_kg_ha > 0.0, "District yield prediction should be positive"


def test_03_predict_district_yield_case_insensitive():
    y1 = predict_district_yield(district="thanjavur", crop="rice", season="kharif")
    y2 = predict_district_yield(district="Thanjavur", crop="Rice", season="Kharif")
    assert y1 == y2, "Normalization should produce identical predictions regardless of case"


def test_04_predict_yield_does_not_mutate_npk_requirements():
    from phase5_nutrient.service import NutrientCalculationService
    from phase5_nutrient.models import NutrientCalculationRequest

    req = NutrientCalculationRequest(
        crop="Rice",
        soil_series="Palavidhi",
        season="Kharif",
        irrigation_method="Irrigated",
        target_yield=5.0,
        soil_nitrogen=280.0,
        soil_phosphorus=18.0,
        soil_potassium=160.0,
        soil_phosphorus_method="Olsen",
        farm_area=2.5,
        farm_area_unit="acre"
    )
    srv = NutrientCalculationService()
    res1 = srv.calculate(req)

    # Invoke ML model prediction
    _ = predict_district_yield(district="Thanjavur", crop="Rice")

    res2 = srv.calculate(req)
    assert res1.n_req_kg_per_ha == res2.n_req_kg_per_ha
    assert res1.p2o5_req_kg_per_ha == res2.p2o5_req_kg_per_ha
    assert res1.k2o_req_kg_per_ha == res2.k2o_req_kg_per_ha


def test_05_unsupported_district_rejected():
    with pytest.raises(ValueError) as exc:
        predict_district_yield(district="NonExistentDistrict", crop="Rice")
    assert "not supported by the district yield benchmark model" in str(exc.value)


def test_06_unsupported_crop_rejected():
    with pytest.raises(ValueError) as exc:
        predict_district_yield(district="Thanjavur", crop="DragonFruit")
    assert "not supported by the district yield benchmark model" in str(exc.value)


def test_07_negative_rainfall_rejected():
    with pytest.raises(ValueError) as exc:
        predict_district_yield(district="Thanjavur", crop="Rice", rain_swm=-50.0)
    assert "cannot be negative" in str(exc.value)


def test_08_nine_feature_schema_consistency():
    import json
    meta = json.load(open(META, "r", encoding="utf-8"))
    features = meta["features"]
    assert len(features) == 9, f"Expected 9 features, got {len(features)}: {features}"
    expected_features = [
        "District", "Crop", "Season", "Year",
        "Rain_SWM_mm", "Rain_NEM_mm", "Rain_Winter_mm",
        "Rain_HotWeather_mm", "Rain_Annual_mm"
    ]
    assert features == expected_features, "Feature order or naming mismatch"

