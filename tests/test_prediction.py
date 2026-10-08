import pytest
import pandas as pd
from pathlib import Path
from models.prediction_model import predict_aqi_from_csv

def test_prediction_output_structure(tmp_path):
    """TEST 14: Verify valid input produces expected output structure with Predicted_AQI column."""
    # Create a minimal synthetic training CSV
    train_csv = tmp_path / "mock_train.csv"
    train_data = pd.DataFrame({
        "Timestamp": ["01-10-2026 10:00", "01-10-2026 11:00", "01-10-2026 12:00"],
        "PM2.5": [55.0, 60.0, 65.0],
        "PM10": [110.0, 115.0, 120.0],
        "NO2": [25.0, 28.0, 30.0],
        "AQI": [110, 120, 130]
    })
    train_data.to_csv(train_csv, index=False)

    # Create input DataFrame
    input_data = pd.DataFrame({
        "Timestamp": ["02-10-2026 09:00", "02-10-2026 10:00"],
        "PM2.5": [58.0, 62.0],
        "PM10": [112.0, 118.0],
        "NO2": [26.0, 29.0]
    })

    result_df = predict_aqi_from_csv(train_csv, input_data)
    assert "Predicted_AQI" in result_df.columns
    assert len(result_df) == 2
    assert all(isinstance(val, (int, float)) for val in result_df["Predicted_AQI"])
    assert all(val >= 0 for val in result_df["Predicted_AQI"])

def test_prediction_empty_input(tmp_path):
    """Empty input DataFrame should return gracefully without unhandled exception."""
    train_csv = tmp_path / "mock_train.csv"
    pd.DataFrame({"PM2.5": [50], "AQI": [100]}).to_csv(train_csv, index=False)

    empty_input = pd.DataFrame()
    res = predict_aqi_from_csv(train_csv, empty_input)
    assert res.empty
    assert "Predicted_AQI" in res.columns
