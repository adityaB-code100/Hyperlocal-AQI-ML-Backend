from pathlib import Path
from app.config import Config

GEOJSON_PATH = Config.GEOJSON_PATH

def get_geojson_path() -> Path:
    """Return the resolved Path to india_district.geojson."""
    return GEOJSON_PATH
