"""
Machine Learning Engine for Predictive Maintenance.

Trains a Random Forest Regressor to predict Remaining Useful Life (RUL)
dynamically based on real-time sensor readings from the NASA C-MAPSS dataset.
"""

import functools
import os
import joblib
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import root_mean_squared_error, mean_absolute_error
from data.cmapss_loader import load_dataset, DEGRADING_SENSORS

# Define path to save the model
_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'rul_rf_model.joblib'
)


def prepare_training_data(dataset='FD001'):
    """
    Prepare the C-MAPSS dataset for ML training by computing RUL labels.

    Returns
    -------
    X : np.ndarray
        Feature matrix (sensor readings).
    y : np.ndarray
        Target vector (Remaining Useful Life in cycles).
    """
    print(f"Loading {dataset} dataset for training...")
    train_df, _, _ = load_dataset(dataset)

    # Calculate RUL for each row in train_df
    print("Computing target RUL values...")
    # Get max cycle for each unit
    max_cycles = train_df.groupby('unit')['cycle'].max()
    
    # Merge max cycle back to the dataframe
    train_df = train_df.merge(max_cycles.rename('max_cycle'), on='unit')
    
    # RUL is max cycle minus current cycle
    train_df['RUL'] = train_df['max_cycle'] - train_df['cycle']
    
    # Define features (we only use sensors that show degradation)
    features = DEGRADING_SENSORS
    
    # Extract X (features) and y (target)
    X = train_df[features].values
    y = train_df['RUL'].values
    
    return X, y


def train_model(dataset='FD001'):
    """
    Train the RUL prediction model and save it to disk.
    
    Returns
    -------
    dict
        Dictionary containing evaluation metrics.
    """
    X, y = prepare_training_data(dataset)
    
    print(f"Training Random Forest Regressor on {X.shape[0]} samples...")
    # Initialize Random Forest Regressor
    # Using 50 trees for speed/size tradeoff, max_depth to prevent overfitting
    rf_model = RandomForestRegressor(
        n_estimators=50, 
        max_depth=15, 
        random_state=42, 
        n_jobs=-1
    )
    
    # Train the model
    rf_model.fit(X, y)
    
    # Evaluate on the training set (just to get a baseline)
    y_pred = rf_model.predict(X)
    rmse = root_mean_squared_error(y, y_pred)
    mae = mean_absolute_error(y, y_pred)
    
    print(f"Training Complete. RMSE: {rmse:.2f} cycles, MAE: {mae:.2f} cycles.")
    
    # Save the object to disk
    print(f"Saving model to {_MODEL_PATH}...")
    joblib.dump(rf_model, _MODEL_PATH)
    print("Model saved successfully.")
    
    return {
        'rmse': rmse,
        'mae': mae,
        'model_path': _MODEL_PATH
    }


@functools.lru_cache(maxsize=1)
def get_ml_model():
    """Load and cache the trained ML model in memory."""
    if not os.path.exists(_MODEL_PATH):
        raise FileNotFoundError(f"Model not found at {_MODEL_PATH}. Run train_model() first.")
    return joblib.load(_MODEL_PATH)


def predict_rul(sensor_readings, model=None):
    """
    Predict RUL for a given set of sensor readings.
    
    Parameters
    ----------
    sensor_readings : array-like
        Array of sensor values corresponding to DEGRADING_SENSORS.
        Shape should be (n_samples, len(DEGRADING_SENSORS)).
    model : RandomForestRegressor, optional
        Pre-loaded model. If None, it will be loaded from cache.
        
    Returns
    -------
    np.ndarray
        Predicted RUL values.
    """
    rf_model = model if model is not None else get_ml_model()
    
    # Ensure it's a 2D array
    readings = np.array(sensor_readings)
    if readings.ndim == 1:
        readings = readings.reshape(1, -1)
        
    return rf_model.predict(readings)


if __name__ == "__main__":
    train_model()
