import logging
from typing import Optional
from pymongo import MongoClient
from app.database.repositories import save_processed_data

logger = logging.getLogger(__name__)

def save_or_update_data(date: str, village: str, extra_data: dict, client: Optional[MongoClient] = None):
    """
    Saves or updates data in the processed_data collection.
    If the date exists, updates the specific village data.
    If not, inserts a new document.
    """
    save_processed_data(date, village, extra_data, client=client)

if __name__ == "__main__":
    pass
