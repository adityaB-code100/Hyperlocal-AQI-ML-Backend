import logging
from datetime import datetime
from typing import Optional, Dict, Any, List
from app.database.mongodb import get_mongo_client, get_db
from app.config import Config

logger = logging.getLogger(__name__)

def parse_date_to_dmy(date_str: str) -> Optional[str]:
    """Parse a date string in YYYY-MM-DD or DD-MM-YYYY format to DD-MM-YYYY."""
    if not date_str:
        return None
    for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str.strip(), fmt).strftime("%d-%m-%Y")
        except ValueError:
            continue
    logger.warning("Unrecognized date format: %s", date_str)
    return None

def get_aqi_data(date: str, village: Optional[str] = None, client=None,
                 db_name: str = None, collection_name: str = "aqi_records") -> Optional[Dict[str, Any]]:
    """
    Fetch raw AQI records for a given date and optionally a specific village.
    Schema in aqi_records: { "date": "DD-MM-YYYY", "data": { "<Village>": { ... } } }
    """
    db_date = parse_date_to_dmy(date)
    if not db_date:
        return None

    try:
        db = get_db(db_name, client=client)
        collection = db[collection_name]

        if village:
            doc = collection.find_one(
                {"date": db_date},
                {f"data.{village}": 1, "_id": 0}
            )
            if doc and "data" in doc and village in doc["data"]:
                return doc["data"][village]
            return None
        else:
            doc = collection.find_one({"date": db_date}, {"data": 1, "_id": 0})
            if doc and "data" in doc:
                return doc["data"]
            return None
    except Exception as e:
        logger.error("Error querying AQI data for %s: %s", date, type(e).__name__)
        return None

def get_aqi_by_village(date: str, client=None, db_name: str = None,
                       collection_name: str = "aqi_records") -> Optional[Dict[str, Any]]:
    """
    Fetch Predicted_AQI for all villages on a given date.
    Returns: { "VillageA": 56, "VillageB": 267 } or None if date not found.
    """
    db_date = parse_date_to_dmy(date)
    if not db_date:
        return None

    try:
        db = get_db(db_name, client=client)
        collection = db[collection_name]

        # Support querying either DD-MM-YYYY or YYYY-MM-DD for legacy records
        result = collection.find_one({"date": db_date})
        if not result:
            # Try parsing to YMD format
            dt_obj = datetime.strptime(db_date, "%d-%m-%Y")
            result = collection.find_one({"date": dt_obj.strftime("%Y-%m-%d")})

        if result and "data" in result:
            village_aqi = {}
            for v, pollutants in result["data"].items():
                if isinstance(pollutants, dict):
                    aqi = pollutants.get("Predicted_AQI")
                    if aqi is not None:
                        village_aqi[v] = aqi
            return village_aqi
        return None
    except Exception as e:
        logger.error("Error querying AQI by village for %s: %s", date, type(e).__name__)
        return None

def get_processed_data(date: str, village: Optional[str] = None, client=None,
                       db_name: str = None, collection_name: str = "processed_data") -> Optional[Dict[str, Any]]:
    """
    Fetch processed summary data for a given date and village.
    Consistent with the schema:
    { "date": "DD-MM-YYYY", "data": { "<Village>": { ...processed metrics... } } }
    """
    db_date = parse_date_to_dmy(date)
    if not db_date:
        return None

    try:
        db = get_db(db_name, client=client)
        collection = db[collection_name]

        if village:
            # First check nested data schema: data.<village>
            doc = collection.find_one(
                {"date": db_date},
                {f"data.{village}": 1, "_id": 0}
            )
            if doc and "data" in doc and village in doc["data"]:
                return doc["data"][village]

            # Fallback check for flat schema if legacy document exists
            legacy_doc = collection.find_one(
                {"date": db_date, "village": village},
                {"_id": 0}
            )
            if legacy_doc:
                return legacy_doc
            return None
        else:
            doc = collection.find_one({"date": db_date}, {"_id": 0})
            return doc
    except Exception as e:
        logger.error("Error querying processed data for %s, village %s: %s", date, village, type(e).__name__)
        return None

# Backwards compatibility for get_user.py
get_data = get_processed_data

def save_aqi_records(records: List[Dict[str, Any]], city: str, client=None,
                     db_name: str = None, collection_name: str = "aqi_records"):
    """
    Save AQI records into MongoDB in nested {city: pollutants} format grouped by date.
    """
    db = get_db(db_name, client=client)
    collection = db[collection_name]

    for rec in records:
        rec_copy = rec.copy()
        raw_date = rec_copy.pop("date", None)
        date = parse_date_to_dmy(raw_date) if raw_date else None
        if not date:
            continue

        collection.update_one(
            {"date": date},
            {"$set": {f"data.{city}": rec_copy}},
            upsert=True
        )
    logger.info("Inserted/Updated aqi records for %s", city)

def save_processed_data(date: str, village: str, extra_data: dict, client=None,
                        db_name: str = None, collection_name: str = "processed_data"):
    """
    Saves or updates processed summary data in processed_data collection.
    Uses consistent schema: { "date": date, "data": { village: extra_data } }
    """
    db_date = parse_date_to_dmy(date)
    if not db_date:
        return

    db = get_db(db_name, client=client)
    collection = db[collection_name]

    collection.update_one(
        {"date": db_date},
        {"$set": {f"data.{village}": extra_data}},
        upsert=True
    )
    logger.info("Saved processed data for %s, village %s", db_date, village)

def get_city_monthly_aqi(city: str, client=None, db_name: str = None,
                         collection_name: str = "monthly_aqi") -> Dict[str, float]:
    """Fetch all monthly AQI averages for a given city."""
    db = get_db(db_name, client=client)
    collection = db[collection_name]
    result = {}
    try:
        for doc in collection.find():
            month = doc.get("month")
            if month and city in doc:
                result[month] = doc[city]
    except Exception as e:
        logger.error("Error retrieving monthly AQI for city %s: %s", city, type(e).__name__)
    return result
