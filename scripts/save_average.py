import statistics
import logging
from datetime import datetime
from typing import Optional
from pymongo import MongoClient
from app.database.mongodb import get_db, get_mongo_client
from app.config import Config

logger = logging.getLogger(__name__)

def calculate_and_store_monthly_mean_aqi(client: Optional[MongoClient] = None, db_name: str = None):
    """
    Calculates monthly mean AQI per city directly from source observations in aqi_records,
    then upserts to monthly_aqi.
    
    IDEMPOTENT: Derives the monthly average exclusively from raw source records.
    Repeated execution with identical source records yields the exact same results.
    """
    db = get_db(db_name, client=client)
    source = db["aqi_records"]
    target = db["monthly_aqi"]

    # Dictionary: {month_key ("YYYY-MM"): {city: [aqi_values]}}
    monthly_citywise_aqi = {}

    for doc in source.find():
        date_str = doc.get("date")
        if not date_str:
            continue

        date_obj = None
        for fmt in ("%d-%m-%Y", "%Y-%m-%d"):
            try:
                date_obj = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue

        if not date_obj:
            continue

        month_key = date_obj.strftime("%Y-%m")

        city_data = doc.get("data", {})
        if isinstance(city_data, dict):
            for city, values in city_data.items():
                if isinstance(values, dict):
                    aqi = values.get("Predicted_AQI")
                    if aqi is not None:
                        try:
                            aqi_num = float(aqi)
                            monthly_citywise_aqi.setdefault(month_key, {}).setdefault(city, []).append(aqi_num)
                        except (ValueError, TypeError):
                            continue

    # Calculate idempotent average from raw source values
    for month, cities in monthly_citywise_aqi.items():
        month_doc = {"month": month}
        for city, aqis in cities.items():
            if aqis:
                # Direct average of all source records for this month
                month_doc[city] = round(statistics.mean(aqis), 2)

        target.update_one(
            {"month": month},
            {"$set": month_doc},
            upsert=True
        )

    logger.info("Monthly mean AQI stored/updated idempotently.")
    return monthly_citywise_aqi

if __name__ == "__main__":
    calculate_and_store_monthly_mean_aqi()
