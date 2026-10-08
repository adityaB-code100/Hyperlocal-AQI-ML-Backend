"""
AQI ML Pipeline Orchestrator

Executes the end-to-end data processing and machine learning workflow:
1. Load & validate input data for supported cities
2. Normalize pollutant names & features
3. Run XGBoost ML prediction
4. Save raw/predicted observations to MongoDB (aqi_records)
5. Calculate 7-day metrics, best/worst AQI dates, and chart components
6. Save processed summaries to MongoDB (processed_data)
7. Compute idempotent monthly averages in MongoDB (monthly_aqi)
8. Generate interactive Folium maps to generated/maps/
"""
import sys
import argparse
import logging
from typing import Optional
from pymongo import MongoClient

from app.config import Config
from app.utils.date_utils import get_current_date, next_days
from scripts.add_raw_data import index as run_raw_prediction_step
from app.services.processing_service import index2 as run_summary_processing_step
from scripts.save_average import calculate_and_store_monthly_mean_aqi

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("aqi_pipeline")

def run_pipeline(start_date: Optional[str] = None, days: int = 7,
                 client: Optional[MongoClient] = None,
                 generate_maps: bool = True) -> bool:
    """
    Executes the complete AQI ML pipeline sequentially.
    
    Args:
        start_date: Date to begin pipeline processing (DD-MM-YYYY or YYYY-MM-DD).
                    Defaults to current date if not provided.
        days: Number of consecutive forecast days to process (default 7).
        client: Optional PyMongo client instance (useful for mocking/testing).
        generate_maps: Flag to control geospatial map generation.
    """
    date = start_date or get_current_date()
    logger.info("==================================================")
    logger.info("Starting AQI ML Pipeline for date: %s (days=%d)", date, days)
    logger.info("Target Cities: %s", ", ".join(Config.SUPPORTED_CITIES))
    logger.info("==================================================")

    # ----------------------------------------------------
    # Step 1 - 4: ML Prediction & Raw Data Persistence
    # ----------------------------------------------------
    logger.info("[Step 1/3] Running ML predictions & saving to 'aqi_records'...")
    try:
        run_raw_prediction_step(date, days=days, client=client)
        logger.info("[Step 1/3] Raw prediction records successfully written to MongoDB.")
    except Exception as e:
        logger.error("[Step 1/3] Failed during raw prediction step: %s", e)
        raise

    # ----------------------------------------------------
    # Step 5 - 6 & 8: 7-Day Metrics, Visualizations & Map
    # ----------------------------------------------------
    logger.info("[Step 2/3] Processing 7-day metrics, charts & saving to 'processed_data'...")
    try:
        run_summary_processing_step(date, days=days, client=client)
        logger.info("[Step 2/3] Processed summaries & maps successfully created.")
    except Exception as e:
        logger.error("[Step 2/3] Failed during summary processing step: %s", e)
        raise

    # ----------------------------------------------------
    # Step 7: Idempotent Monthly Average Recomputation
    # ----------------------------------------------------
    logger.info("[Step 3/3] Calculating idempotent monthly averages in 'monthly_aqi'...")
    try:
        calculate_and_store_monthly_mean_aqi(client=client)
        logger.info("[Step 3/3] Monthly averages updated successfully.")
    except Exception as e:
        logger.error("[Step 3/3] Failed during monthly average calculation: %s", e)
        raise

    logger.info("==================================================")
    logger.info("AQI ML Pipeline finished successfully for %s!", date)
    logger.info("Output collections updated: aqi_records, processed_data, monthly_aqi")
    logger.info("==================================================")
    return True

def main():
    parser = argparse.ArgumentParser(description="AQI ML Pipeline Orchestrator")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Start date for pipeline in DD-MM-YYYY or YYYY-MM-DD format (default: today)"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of consecutive days to process (default: 7)"
    )
    parser.add_argument(
        "--no-maps",
        action="store_true",
        help="Disable Folium map generation"
    )
    args = parser.parse_args()

    run_pipeline(start_date=args.date, days=args.days, generate_maps=not args.no_maps)

if __name__ == "__main__":
    main()
