import os
from pathlib import Path
from dotenv import load_dotenv

# Project Root Directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment configuration
load_dotenv(BASE_DIR / ".env")

class Config:
    BASE_DIR = BASE_DIR
    DATA_DIR = BASE_DIR / "Data_set"
    TRAINING_DATA_DIR = DATA_DIR / "Training_data"
    INPUT_DATA_DIR = DATA_DIR / "input_data"
    GEOJSON_PATH = BASE_DIR / "data" / "india_district.geojson"
    GENERATED_MAPS_DIR = BASE_DIR / "generated" / "maps"
    
    # MongoDB Settings
    MONGO_URI = os.getenv("MONGO_URI", "")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "AQI_Project")
    
    # Target locations for AQI pipeline
    SUPPORTED_CITIES = ["Mumbai", "Nagpur", "Nanded", "Nashik", "Pune"]
