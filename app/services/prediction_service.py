import logging
from pathlib import Path
from typing import Optional, Union
import pandas as pd
from app.config import Config
from models.prediction_model import predict_aqi_from_csv
from app.utils.date_utils import parse_date

logger = logging.getLogger(__name__)

def get_file_train(village: str) -> Path:
    """Resolve training CSV file path for given city/village."""
    file_path = Config.TRAINING_DATA_DIR / f"{village}_train.csv"
    if not file_path.exists():
        # Fallback case-insensitive search
        for f in Config.TRAINING_DATA_DIR.glob("*.csv"):
            if f.stem.lower() == f"{village.lower()}_train":
                return f
        raise FileNotFoundError(f"Training data not found for {village} at {file_path}")
    return file_path

def get_file_input(village: str) -> Path:
    """Resolve input CSV file path for given city/village."""
    file_path = Config.INPUT_DATA_DIR / f"{village}.csv"
    if not file_path.exists():
        for f in Config.INPUT_DATA_DIR.glob("*.csv"):
            if f.stem.lower() == village.lower():
                return f
        raise FileNotFoundError(f"Input data not found for {village} at {file_path}")
    return file_path

def get_data_by_date(village: str, input_date: str) -> pd.DataFrame:
    """
    Filters rows from CSV that match the input date and returns DataFrame
    with Predicted_AQI column.
    """
    try:
        input_file = get_file_input(village)
        train_file = get_file_train(village)
    except FileNotFoundError as e:
        logger.error(str(e))
        return pd.DataFrame()

    try:
        df = pd.read_csv(input_file, encoding="utf-8")
    except Exception as e:
        logger.error("Failed to read input CSV for %s: %s", village, e)
        return pd.DataFrame()

    if 'Timestamp' not in df.columns:
        logger.warning("'Timestamp' column missing in %s", input_file)
        return pd.DataFrame()

    # Clean timestamp column
    df['Timestamp'] = df['Timestamp'].astype(str).str.strip()
    df['Timestamp_parsed'] = pd.to_datetime(df['Timestamp'], format='%d-%m-%Y %H:%M', errors='coerce')

    try:
        search_date = parse_date(input_date)
    except ValueError as e:
        logger.error("Invalid date format provided to prediction: %s", e)
        return pd.DataFrame()

    # Filter rows matching the specified calendar date
    filtered_df = df[df['Timestamp_parsed'].dt.date == search_date.date()].copy()
    if filtered_df.empty:
        logger.info("No rows found for %s on date %s", village, input_date)
        return pd.DataFrame()

    filtered_df = filtered_df.sort_values(by='Timestamp_parsed')
    filtered_df.drop(columns=['Timestamp_parsed'], inplace=True)

    try:
        return predict_aqi_from_csv(train_file, filtered_df)
    except Exception as e:
        logger.error("Prediction failed for %s on %s: %s", village, input_date, e)
        return pd.DataFrame()
