import pytest
from app.utils.pollutant_utils import (
    normalize_pollutant_name,
    filter_off,
    classify_pollutants
)

def test_pm25_normalization():
    """TEST 7: PM2.5 normalization with Unicode subscript and variants."""
    assert normalize_pollutant_name("PM₂.₅") == "PM2.5"
    assert normalize_pollutant_name("pm2.5") == "PM2.5"
    assert normalize_pollutant_name("PM2.5") == "PM2.5"
    assert normalize_pollutant_name("PM2.5 (ug/m³)") == "PM2.5"

def test_no2_normalization():
    """TEST 8: NO2 normalization with Unicode subscript."""
    assert normalize_pollutant_name("NO₂") == "NO2"
    assert normalize_pollutant_name("no2") == "NO2"
    assert normalize_pollutant_name("NO2") == "NO2"

def test_so2_normalization():
    """TEST 9: SO2 normalization with Unicode subscript."""
    assert normalize_pollutant_name("SO₂") == "SO2"
    assert normalize_pollutant_name("so2") == "SO2"
    assert normalize_pollutant_name("SO2") == "SO2"

def test_o3_normalization():
    """TEST 10: O3 and Ozone normalization."""
    assert normalize_pollutant_name("O₃") == "O3"
    assert normalize_pollutant_name("o3") == "O3"
    assert normalize_pollutant_name("Ozone") == "O3"
    assert normalize_pollutant_name("ozone") == "O3"

def test_additional_pollutants_normalization():
    """Verify PM10, NH3, CO, and Pb normalization."""
    assert normalize_pollutant_name("PM₁₀") == "PM10"
    assert normalize_pollutant_name("NH₃") == "NH3"
    assert normalize_pollutant_name("CO (mg/m³)") == "CO"
    assert normalize_pollutant_name("lead") == "Pb"

def test_filter_off():
    """Verify filter_off normalizes keys and filters non-pollutants."""
    data = {
        "PM₂.₅": 45,
        "NO₂": 22,
        "SO₂": 15,
        "Unknown_Param": 999
    }
    filtered = filter_off(data)
    assert "PM2.5" in filtered
    assert "NO2" in filtered
    assert "SO2" in filtered
    assert "Unknown_Param" not in filtered

def test_classify_pollutants():
    """Verify pollutant classification into AQI status levels."""
    data = {
        "PM2.5": 30.0,   # 50% of 60 standard -> Good
        "NO2": 80.0,     # 100% of 80 standard -> Satisfactory
        "SO2": 170.0,    # > 200% -> Poor
        "CO": None       # None should be skipped
    }
    classifications = classify_pollutants(data)
    names = [c["name"] for c in classifications]
    assert "PM2.5" in names
    assert "NO2" in names
    assert "SO2" in names
    assert "CO" not in names

    pm_entry = next(c for c in classifications if c["name"] == "PM2.5")
    assert pm_entry["status"] == "Good"
    assert pm_entry["percentage"] == 50.0

    no2_entry = next(c for c in classifications if c["name"] == "NO2")
    assert no2_entry["status"] == "Satisfactory"
    assert no2_entry["percentage"] == 100.0
