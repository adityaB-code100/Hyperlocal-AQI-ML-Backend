import logging
import statistics
import pandas as pd
from typing import Optional, List
from pymongo import MongoClient
from app.config import Config
from app.services.prediction_service import get_data_by_date
from app.utils.date_utils import next_days
from scripts.save_aqi import save_aqi_to_mongo
from scripts.save_average import calculate_and_store_monthly_mean_aqi

logger = logging.getLogger(__name__)

def index(start_date: str, days: int = 7, client: Optional[MongoClient] = None):
    """
    Predicts AQI and pollutant metrics for supported cities across consecutive dates,
    saves the records to MongoDB, and recalculates monthly averages idempotently.
    """
    date_list = next_days(start_date, n_days=days)
    village_list = Config.SUPPORTED_CITIES

    for village in village_list:
        mean_list = []

        for date_i in date_list:
            df = get_data_by_date(village, date_i)

            if not df.empty and 'Predicted_AQI' in df.columns:
                mean_dict = {}
                for col in df.columns:
                    if pd.api.types.is_numeric_dtype(df[col]) and col.lower() != 'time':
                        col_mean = df[col].mean()
                        if pd.notna(col_mean):
                            # Clean column name annotations
                            clean_col = col.replace("(ug/m³)", "").replace("(°C)", "").replace("(%)", "").strip()
                            mean_dict[clean_col] = int(round(col_mean))

                mean_dict['date'] = date_i
                mean_list.append(mean_dict)
            else:
                logger.info("No predictions available for %s on %s", village, date_i)

        if mean_list:
            save_aqi_to_mongo(mean_list, city=village, client=client)
            logger.info("Processed and saved data for %s", village)

    # Recalculate monthly average idempotently after all city records have been updated
    calculate_and_store_monthly_mean_aqi(client=client)

if __name__ == "__main__":
    from app.utils.date_utils import get_current_date
    current_date = get_current_date()
    index(current_date)