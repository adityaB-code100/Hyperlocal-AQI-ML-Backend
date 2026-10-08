import pytest
from pathlib import Path
from app.services.map_service import mapgenerator

def test_missing_city_no_keyerror(tmp_path):
    """TEST 6: Map generation must not raise KeyError when cities are missing from the input."""
    # Only supply Mumbai; Nanded, Pune, Nagpur, Nashik are missing
    partial_aqi = {
        "Mumbai": 115
    }
    # This must succeed without throwing KeyError
    m = mapgenerator("01-10-2026", partial_aqi, output_dir=tmp_path)
    assert m is not None
    out_file = tmp_path / "map01-10-2026.html"
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "Mumbai" in content

def test_none_and_invalid_aqi_handling(tmp_path):
    """TEST 5 & 6 variant: None or non-numeric AQI values do not crash map generation."""
    data = {
        "Mumbai": None,
        "Pune": "InvalidAQI",
        "Nagpur": 88
    }
    m = mapgenerator("02-10-2026", data, output_dir=tmp_path)
    assert m is not None
    out_file = tmp_path / "map02-10-2026.html"
    assert out_file.exists()

def test_completely_empty_city_data(tmp_path):
    """Empty AQI dict must render default map with No Data for all cities."""
    m = mapgenerator("03-10-2026", {}, output_dir=tmp_path)
    assert m is not None
    out_file = tmp_path / "map03-10-2026.html"
    assert out_file.exists()
