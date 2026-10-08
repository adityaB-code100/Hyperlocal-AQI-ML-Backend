import pytest
from app.services.processing_service import compute_seven_day_metrics
from app.utils.date_utils import next_seven_days, next_days, parse_date

def test_seven_day_average():
    """TEST 1: Seven-day average calculation matches mathematical formula."""
    records = [
        ("01-10-2026", 100),
        ("02-10-2026", 120),
        ("03-10-2026", 80),
        ("04-10-2026", 90),
        ("05-10-2026", 110),
        ("06-10-2026", 100),
        ("07-10-2026", 70)
    ]
    avg, worst_val, worst_date, best_val, best_date = compute_seven_day_metrics(records)
    # Expected average: (100+120+80+90+110+100+70) / 7 = 670 / 7 = 95.714285...
    assert round(avg, 2) == 95.71
    assert worst_val == 120
    assert worst_date == "02-10-2026"
    assert best_val == 70
    assert best_date == "07-10-2026"

def test_missing_aqi_date_alignment():
    """TEST 2: Verify date/value relationships remain aligned when values are missing."""
    records = [
        ("01-10-2026", 100),
        ("02-10-2026", 120),
        ("03-10-2026", None),  # Missing day
        ("04-10-2026", 90)
    ]
    avg, worst_val, worst_date, best_val, best_date = compute_seven_day_metrics(records)
    # Expected average: (100 + 120 + 90) / 3 = 103.33
    assert round(avg, 2) == 103.33
    assert worst_val == 120
    assert worst_date == "02-10-2026"
    assert best_val == 90
    assert best_date == "04-10-2026"

def test_duplicate_aqi_deterministic_dates():
    """TEST 3: Duplicate AQI values do not overwrite dates and pick first deterministic occurrence."""
    records = [
        ("01-10-2026", 100),
        ("02-10-2026", 150),
        ("03-10-2026", 100)
    ]
    avg, worst_val, worst_date, best_val, best_date = compute_seven_day_metrics(records)
    assert avg == round((100 + 150 + 100) / 3, 2)
    assert worst_val == 150
    assert worst_date == "02-10-2026"
    # Lowest is 100, occurring on both Oct 1 and Oct 3. Must pick first occurrence.
    assert best_val == 100
    assert best_date == "01-10-2026"

def test_empty_data():
    """TEST 4: Empty data must not crash and should return None metrics."""
    avg, worst_val, worst_date, best_val, best_date = compute_seven_day_metrics([])
    assert avg is None
    assert worst_val is None
    assert worst_date is None
    assert best_val is None
    assert best_date is None

def test_none_and_nan_aqi():
    """TEST 5: None and NaN values are skipped safely."""
    records = [
        ("01-10-2026", None),
        ("02-10-2026", float("nan")),
        ("03-10-2026", 85.0)
    ]
    avg, worst_val, worst_date, best_val, best_date = compute_seven_day_metrics(records)
    assert avg == 85.0
    assert worst_val == 85.0
    assert worst_date == "03-10-2026"
    assert best_val == 85.0
    assert best_date == "03-10-2026"

def test_seven_day_helper_returns_exactly_seven_days():
    """TEST 12: next_seven_days must return exactly 7 consecutive formatted dates."""
    dates = next_seven_days("01-10-2026")
    assert len(dates) == 7
    assert dates[0] == "01-10-2026"
    assert dates[1] == "02-10-2026"
    assert dates[6] == "07-10-2026"

    # Also test YYYY-MM-DD format input
    dates_iso = next_seven_days("2026-10-01")
    assert len(dates_iso) == 7
    assert dates_iso[0] == "01-10-2026"
    assert dates_iso[6] == "07-10-2026"
