import pytest
import statistics
from unittest.mock import MagicMock
from app.database.repositories import (
    get_aqi_data,
    get_aqi_by_village,
    get_processed_data,
    save_aqi_records,
    save_processed_data
)
from scripts.save_average import calculate_and_store_monthly_mean_aqi

class MockCollection:
    def __init__(self):
        self.docs = []

    def find(self, query=None):
        return [dict(d) for d in self.docs]

    def find_one(self, query, projection=None):
        for doc in self.docs:
            match = True
            for k, v in query.items():
                if doc.get(k) != v:
                    match = False
                    break
            if match:
                res = dict(doc)
                if projection and "_id" in projection and projection["_id"] == 0:
                    res.pop("_id", None)
                return res
        return None

    def update_one(self, filter_query, update_query, upsert=False):
        matched = None
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in filter_query.items()):
                matched = doc
                break

        set_fields = update_query.get("$set", {})
        if matched is not None:
            for k, v in set_fields.items():
                if "." in k:
                    parts = k.split(".", 1)
                    if parts[0] not in matched or not isinstance(matched[parts[0]], dict):
                        matched[parts[0]] = {}
                    matched[parts[0]][parts[1]] = v
                else:
                    matched[k] = v
        elif upsert:
            new_doc = dict(filter_query)
            for k, v in set_fields.items():
                if "." in k:
                    parts = k.split(".", 1)
                    if parts[0] not in new_doc or not isinstance(new_doc[parts[0]], dict):
                        new_doc[parts[0]] = {}
                    new_doc[parts[0]][parts[1]] = v
                else:
                    new_doc[k] = v
            self.docs.append(new_doc)

class MockDB:
    def __init__(self):
        self.collections = {
            "aqi_records": MockCollection(),
            "processed_data": MockCollection(),
            "monthly_aqi": MockCollection()
        }

    def __getitem__(self, item):
        if item not in self.collections:
            self.collections[item] = MockCollection()
        return self.collections[item]

class MockClient:
    def __init__(self, db):
        self.db = db

    def __getitem__(self, item):
        return self.db

def test_mongodb_document_query_consistency():
    """TEST 13: Verify MongoDB schema consistency between writers and readers."""
    mock_db = MockDB()
    mock_client = MockClient(mock_db)

    # 1. Save records using repository (saves nested under data.Mumbai)
    records = [
        {"date": "01-10-2026", "Predicted_AQI": 115, "PM2.5": 42}
    ]
    save_aqi_records(records, "Mumbai", client=mock_client)

    # 2. Query for Mumbai specifically
    data_mumbai = get_aqi_data("01-10-2026", village="Mumbai", client=mock_client)
    assert data_mumbai is not None
    assert data_mumbai.get("Predicted_AQI") == 115
    assert data_mumbai.get("PM2.5") == 42

    # 3. Query all villages on that date
    data_all = get_aqi_data("01-10-2026", village=None, client=mock_client)
    assert "Mumbai" in data_all
    assert data_all["Mumbai"]["Predicted_AQI"] == 115

    # 4. Save and query processed_data (fixes legacy get_user schema mismatch)
    summary_data = {"avg_aqi_7_days": 110, "best_aqi": 80}
    save_processed_data("01-10-2026", "Mumbai", summary_data, client=mock_client)

    processed = get_processed_data("01-10-2026", village="Mumbai", client=mock_client)
    assert processed is not None
    assert processed["avg_aqi_7_days"] == 110

def test_monthly_average_idempotency():
    """
    TEST 11: Verify that monthly average calculation is strictly idempotent.
    Repeated runs with identical source data must produce identical averages,
    without drifting or averaging the average.
    """
    mock_db = MockDB()
    mock_client = MockClient(mock_db)

    # Insert raw daily records for October 2026
    raw_collection = mock_db["aqi_records"]
    raw_collection.docs = [
        {"date": "01-10-2026", "data": {"Mumbai": {"Predicted_AQI": 100}}},
        {"date": "02-10-2026", "data": {"Mumbai": {"Predicted_AQI": 120}}},
        {"date": "03-10-2026", "data": {"Mumbai": {"Predicted_AQI": 140}}}
    ]

    # Expected average for Mumbai in 2026-10: (100 + 120 + 140) / 3 = 120.0
    # Run 1
    calculate_and_store_monthly_mean_aqi(client=mock_client)
    target = mock_db["monthly_aqi"]
    month_doc_run1 = target.find_one({"month": "2026-10"})
    assert month_doc_run1 is not None
    assert month_doc_run1["Mumbai"] == 120.0

    # Run 2 (Must remain 120.0, NOT (120 + 120)/2 or modified)
    calculate_and_store_monthly_mean_aqi(client=mock_client)
    month_doc_run2 = target.find_one({"month": "2026-10"})
    assert month_doc_run2["Mumbai"] == 120.0

    # Run 3
    calculate_and_store_monthly_mean_aqi(client=mock_client)
    month_doc_run3 = target.find_one({"month": "2026-10"})
    assert month_doc_run3["Mumbai"] == 120.0
