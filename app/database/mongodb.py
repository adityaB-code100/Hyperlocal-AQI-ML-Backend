import os
import logging
from pymongo import MongoClient
from app.config import Config

logger = logging.getLogger(__name__)

_client = None

def get_mongo_uri() -> str:
    """Read MongoDB URI from environment or config safely."""
    uri = Config.MONGO_URI or os.getenv("MONGO_URI")
    if not uri:
        raise ValueError("MONGO_URI environment variable is not configured.")
    return uri

def get_mongo_client(uri: str = None, timeout_ms: int = 5000) -> MongoClient:
    """
    Get a PyMongo client instance with timeout settings.
    Credentials are never exposed in error logs.
    """
    global _client
    target_uri = uri or get_mongo_uri()
    try:
        if _client is None or uri is not None:
            client = MongoClient(
                target_uri,
                serverSelectionTimeoutMS=timeout_ms,
                connectTimeoutMS=timeout_ms
            )
            if uri is None:
                _client = client
            return client
        return _client
    except Exception as e:
        logger.error("Failed to initialize MongoDB client: %s", type(e).__name__)
        raise

def get_db(db_name: str = None, client: MongoClient = None):
    """Retrieve database instance."""
    client_instance = client or get_mongo_client()
    target_db_name = db_name or Config.DATABASE_NAME
    return client_instance[target_db_name]

def close_client():
    """Close active client connection."""
    global _client
    if _client:
        _client.close()
        _client = None