import os
from dotenv import load_dotenv

load_dotenv()

def get_mongo_uri():
    """Read MongoDB URI from .env"""
    uri = os.getenv("MONGO_URI")

    if not uri:
        raise ValueError("MONGO_URI not found in .env file")

    return uri