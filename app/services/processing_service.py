import math
import logging
from typing import Dict, Any, Optional, List, Tuple
from app.config import Config
from app.database.repositories import (
    get_aqi_data,
    get_aqi_by_village,
    save_processed_data
)
from app.services.map_service import mapgenerator
from app.services.aqi_service import create_aqi_forecast_chart, plot_monthly_aqi
from app.utils.date_utils import next_seven_days, next_days
from app.utils.pollutant_utils import filter_off, classify_pollutants

logger = logging.getLogger(__name__)

def compute_seven_day_metrics(paired_records: List[Tuple[str, float]]) -> Tuple[Optional[float], Optional[float], Optional[str], Optional[float], Optional[str]]:
    """
    Computes:
    - average AQI = sum(valid_values) / len(valid_values)
    - worst AQI (max) and its first occurring date
    - best AQI (min) and its first occurring date
    
    Handles duplicates deterministically by picking the first date of occurrence.
    Returns (avg_aqi, worst_aqi, worst_date, best_aqi, best_date).
    """
    if not paired_records:
        return None, None, None, None, None

    valid_pairs = []
    for d, val in paired_records:
        if val is not None and not (isinstance(val, float) and math.isnan(val)):
            try:
                valid_pairs.append((d, float(val)))
            except (ValueError, TypeError):
                continue

    if not valid_pairs:
        return None, None, None, None, None

    valid_values = [v for _, v in valid_pairs]
    avg_aqi = round(sum(valid_values) / len(valid_values), 2)

    # Deterministic highest and lowest: first occurrence
    worst_val = max(valid_values)
    best_val = min(valid_values)

    worst_date = next(d for d, v in valid_pairs if v == worst_val)
    best_date = next(d for d, v in valid_pairs if v == best_val)

    return avg_aqi, worst_val, worst_date, best_val, best_date

def processing_data(input_date: str, village: str, client=None) -> Dict[str, Any]:
    """
    Processes 7-day forecast metrics, pollutant classifications, and charts for a village.
    Maintains strict date-value pairing to prevent shifting on missing data.
    """
    date_list = next_seven_days(input_date)
    
    # 1. Fetch live AQI for input date
    live_aqi = None
    live_data = get_aqi_data(input_date, village=village, client=client)
    if live_data and "Predicted_AQI" in live_data:
        live_aqi = live_data["Predicted_AQI"]

    # 2. Gather 7-day data preserving exact date alignments
    aqi_date_pairs = []
    pm_date_pairs = []
    
    for date_k in date_list:
        data = get_aqi_data(date_k, village=village, client=client)
        aqi_val = None
        pm_val = None
        if data:
            aqi_val = data.get("Predicted_AQI")
            pm_val = data.get("PM2.5")
            
        aqi_date_pairs.append((date_k, aqi_val))
        pm_date_pairs.append((date_k, pm_val))

    # 3. Classify pollutants for current input date
    pollutants = None
    if live_data:
        pollutants = classify_pollutants(filter_off(live_data))

    # 4. Generate map for all villages on input_date
    village_aqi_data = get_aqi_by_village(input_date, client=client)
    if village_aqi_data:
        try:
            mapgenerator(input_date, village_aqi_data)
        except Exception as e:
            logger.error("Map generation error on %s: %s", input_date, e)

    # 5. Compute metrics
    avg_aqi_7_days, worst_aqi, worst_date, best_aqi, best_date = compute_seven_day_metrics(aqi_date_pairs)

    avg_3card_dict = {
        "worst_aqi": worst_date,
        "best_aqi": best_date,
        "worst_aqi_value": worst_aqi,
        "best_aqi_value": best_aqi
    }

    # Format output records with aligned date and values
    passing_data = [{"date": d, "value": v} for d, v in aqi_date_pairs]
    passing_pollutant = [{"date": d, "value": v} for d, v in pm_date_pairs]

    # Plotly forecast charts
    chart_dates = [d for d, _ in aqi_date_pairs]
    chart_values = [v for _, v in aqi_date_pairs]
    graph_html = create_aqi_forecast_chart(chart_dates, chart_values)
    avg_graph = plot_monthly_aqi(village)

    data_dict = {
        "date": input_date,
        "village": village,
        "passing_data": passing_data,
        "avg_3card_dict": avg_3card_dict,
        "avg_aqi_7_days": avg_aqi_7_days,
        "pollutants": pollutants,
        "passing_pollutant": passing_pollutant,
        "graph_html": graph_html,
        "avg_graph": avg_graph,
        "worst_aqi": worst_aqi,
        "best_aqi": best_aqi,
        "date_list": date_list,
        "village_aqi_data": village_aqi_data,
        "live_AQI": live_aqi
    }

    # Save to MongoDB processed_data collection
    try:
        save_processed_data(input_date, village, data_dict, client=client)
    except Exception as e:
        logger.error("Failed to save processed data for %s, %s: %s", input_date, village, e)

    return data_dict

def index2(start_date: str, days: int = 7, client=None):
    """Batch process forecast data for all supported cities over multiple days."""
    date_list = next_days(start_date, n_days=days)
    village_list = Config.SUPPORTED_CITIES

    for date_i in date_list:
        for village in village_list:
            logger.info("Processing data for date: %s, village: %s", date_i, village)
            processing_data(date_i, village, client=client)
