import pandas as pd
import xgboost as xgb

def predict_aqi_from_csv(train_csv, input_df):
# save_model_path='xgb_aqi_model.joblib'):
    """
    Train AQI model from train_csv and predict AQI for input_df.
    Returns DataFrame with new column 'Predicted_AQI'.
    """
    # Load and clean training data
    train_df = pd.read_csv(train_csv,).drop_duplicates().ffill().bfill()
    input_df = input_df.ffill().bfill()

    # Process Timestamp → numeric feature
    if 'Timestamp' in train_df.columns:
        train_df['Timestamp'] = pd.to_datetime(train_df['Timestamp'], format='%d-%m-%Y %H:%M', errors='coerce')
        start_time = train_df['Timestamp'].min()
        train_df['time_seconds'] = (train_df['Timestamp'] - start_time).dt.total_seconds()
        train_df.drop(columns=['Timestamp'], inplace=True)

    if 'Timestamp' in input_df.columns:
        input_df['Timestamp'] = pd.to_datetime(input_df['Timestamp'], format='%d-%m-%Y %H:%M', errors='coerce')
        input_df['time_seconds'] = (input_df['Timestamp'] - start_time).dt.total_seconds()
        input_df.drop(columns=['Timestamp'], inplace=True)

    # Split features & target
    feature_cols = [col for col in train_df.columns if col != 'AQI']
    X_train = train_df[feature_cols]
    y_train = train_df['AQI']

    # Train XGBoost model
    model = xgb.XGBRegressor(
        objective='reg:squarederror',
        eval_metric='rmse',
        n_estimators=200,
        learning_rate=0.1,
        max_depth=6,
        random_state=42
    )
    model.fit(X_train, y_train)

    # Predict
    input_df['Predicted_AQI'] = model.predict(input_df[feature_cols])
    #print("Predictions:\n", input_df['Predicted_AQI'])

    return input_df
    #mango_data(input_df)
