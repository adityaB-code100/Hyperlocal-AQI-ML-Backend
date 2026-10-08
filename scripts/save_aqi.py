import logging
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from app.database.mongodb import get_mongo_client, get_db
from app.database.repositories import save_aqi_records, parse_date_to_dmy
from app.config import Config

logger = logging.getLogger(__name__)

def save_aqi_to_mongo(records: List[Dict[str, Any]], city: str,
                      mongo_uri: Optional[str] = None,
                      db_name: str = None,
                      collection_name: str = "aqi_records",
                      client: Optional[MongoClient] = None):
    """
    Save AQI records into MongoDB in nested {city: pollutants} format grouped by date.
    
    Args:
        records (list of dict): Each dict must contain 'date' and pollutant fields.
        city (str): City/village name for the document.
    """
    try:
        active_client = client or (MongoClient(mongo_uri) if mongo_uri else get_mongo_client())
        save_aqi_records(records, city, client=active_client, db_name=db_name, collection_name=collection_name)
    except Exception as e:
        logger.error("Failed to save AQI records for %s: %s", city, e)
        raise

if __name__ == "__main__":
    pass
