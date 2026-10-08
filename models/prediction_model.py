import os
import logging
from pathlib import Path
from typing import Union
import pandas as pd
import xgboost as xgb

logger = logging.getLogger(__name__)

def predict_aqi_from_csv(train_csv: Union[str, Path], input_df: pd.DataFrame) -> pd.DataFrame:
    """
    Train an XGBoost AQI model from train_csv and predict AQI for input_df.
    Returns input_df with an added 'Predicted_AQI' column.
    
    Robust against missing files, empty frames, and missing values.
    """
    train_path = Path(train_csv)
    if not train_path.exists():
        raise FileNotFoundError(f"Training dataset not found at: {train_path}")

    if input_df is None or input_df.empty:
        logger.warning("Input DataFrame for prediction is empty")
        result_df = pd.DataFrame() if input_df is None else input_df.copy()
        result_df['Predicted_AQI'] = []
        return result_df

    # Copy input dataframe to avoid mutating caller's data
    df_input = input_df.copy()

    # Load and clean training data
    train_df = pd.read_csv(train_path).drop_duplicates().ffill().bfill()
    df_input = df_input.ffill().bfill()

    if 'AQI' not in train_df.columns:
        raise ValueError(f"Training file {train_path.name} must contain target column 'AQI'")

    # Process Timestamp -> numeric feature if present
    start_time = None
    if 'Timestamp' in train_df.columns:
        train_df['Timestamp'] = pd.to_datetime(train_df['Timestamp'], format='%d-%m-%Y %H:%M', errors='coerce')
        start_time = train_df['Timestamp'].min()
        train_df['time_seconds'] = (train_df['Timestamp'] - start_time).dt.total_seconds()
        train_df.drop(columns=['Timestamp'], inplace=True)

    if 'Timestamp' in df_input.columns:
        df_input['Timestamp'] = pd.to_datetime(df_input['Timestamp'], format='%d-%m-%Y %H:%M', errors='coerce')
        if start_time is None:
            start_time = df_input['Timestamp'].min()
        df_input['time_seconds'] = (df_input['Timestamp'] - start_time).dt.total_seconds()
        df_input.drop(columns=['Timestamp'], inplace=True)

    # Align feature columns
    feature_cols = [col for col in train_df.columns if col != 'AQI']
    
    # Ensure all required features are present in input
    for col in feature_cols:
        if col not in df_input.columns:
            logger.warning("Feature column '%s' missing in input, defaulting to 0", col)
            df_input[col] = 0

    X_train = train_df[feature_cols]
    y_train = train_df['AQI']

    # Train XGBoost model
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        eval_metric='rmse',
        n_estimators=100,
        learning_rate=0.1,
        max_depth=6,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Predict
    predictions = model.predict(df_input[feature_cols])
    # Ensure non-negative AQI predictions
    df_input['Predicted_AQI'] = [max(0, round(float(p))) for p in predictions]

    return df_input
