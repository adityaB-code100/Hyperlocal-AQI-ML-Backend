import pytest
from unittest.mock import patch, MagicMock
import pandas as pd
from tests.test_database import MockDB, MockClient
from scripts.run_pipeline import run_pipeline

def test_pipeline_orchestration():
    """Verify that the full pipeline executes all steps and updates all collections."""
    mock_db = MockDB()
    mock_client = MockClient(mock_db)

    # Mock predictions returning sample data for each city
    mock_df = pd.DataFrame({
        "Timestamp": ["01-10-2026 10:00"],
        "PM2.5": [50.0],
        "PM10": [100.0],
        "NO2": [30.0],
        "SO2": [20.0],
        "Predicted_AQI": [110]
    })

    with patch("scripts.add_raw_data.get_data_by_date", return_value=mock_df):
        with patch("app.services.processing_service.mapgenerator", return_value=None):
            success = run_pipeline(start_date="01-10-2026", days=1, client=mock_client)
            assert success is True

    # 1. Verify aqi_records has documents for 01-10-2026
    aqi_records = mock_db["aqi_records"].docs
    assert len(aqi_records) > 0
    assert any(doc.get("date") == "01-10-2026" for doc in aqi_records)

    # 2. Verify processed_data has documents
    processed_docs = mock_db["processed_data"].docs
    assert len(processed_docs) > 0

    # 3. Verify monthly_aqi has October 2026 entry
    monthly_docs = mock_db["monthly_aqi"].docs
    assert any(doc.get("month") == "2026-10" for doc in monthly_docs)
