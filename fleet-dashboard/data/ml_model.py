"""
Autonomous Deep Learning Engine - LSTM Prognostics

Replaces the traditional Random Forest regressor with a Deep LSTM 
(Long Short-Term Memory) neural network for time-series RUL prediction.
"""

import os
import joblib
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from data.cmapss_loader import load_dataset, DEGRADING_SENSORS

# Constants for Deep Learning
SEQUENCE_LENGTH = 30
FEATURES_COUNT = len(DEGRADING_SENSORS)

_MODEL_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    'rul_lstm_model.keras'
)

def create_sequences(data, seq_length):
    """
    Groups data into overlapping windows of seq_length for LSTM processing.
    """
    sequences = []
    labels = []
    
    for unit_id in data['unit'].unique():
        unit_df = data[data['unit'] == unit_id]
        unit_data = unit_df[DEGRADING_SENSORS].values
        unit_rul = unit_df['RUL'].values
        
        if len(unit_data) >= seq_length:
            for i in range(len(unit_data) - seq_length + 1):
                sequences.append(unit_data[i:i+seq_length])
                labels.append(unit_rul[i+seq_length-1])
                
    return np.array(sequences), np.array(labels)

def build_lstm_model():
    """
    Defines the God-Tier LSTM architecture.
    """
    model = Sequential([
        LSTM(units=100, return_sequences=True, input_shape=(SEQUENCE_LENGTH, FEATURES_COUNT)),
        Dropout(0.2),
        LSTM(units=50, return_sequences=False),
        Dropout(0.2),
        Dense(units=25, activation='relu'),
        Dense(units=1)  # Predicted RUL
    ])
    
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    return model

def train_model(dataset='FD001', epochs=10):
    """
    Prepare data, train LSTM, and save the model.
    """
    train_df, _, _ = load_dataset(dataset)
    
    # Calculate RUL
    max_cycles = train_df.groupby('unit')['cycle'].max()
    train_df = train_df.merge(max_cycles.rename('max_cycle'), on='unit')
    train_df['RUL'] = train_df['max_cycle'] - train_df['cycle']
    
    # Create windows
    X, y = create_sequences(train_df, SEQUENCE_LENGTH)
    
    print(f"Training LSTM on {X.shape[0]} sequences...")
    model = build_lstm_model()
    
    model.fit(X, y, epochs=epochs, batch_size=32, verbose=1)
    
    print(f"Saving LSTM model to {_MODEL_PATH}...")
    model.save(_MODEL_PATH)
    return model

@tf.function
def _fast_predict(model, X):
    return model(X, training=False)

def predict_rul(sequence_data, model=None):
    """
    Predict RUL using the Deep LSTM model.
    Expects a window of SEQUENCE_LENGTH cycles.
    """
    if model is None:
        try:
            model = load_model(_MODEL_PATH)
        except Exception:
            # Fallback if no model exists during initial dev
            return np.array([100.0])
            
    # Input should be (1, seq_length, features)
    X = np.array(sequence_data)
    if X.ndim == 2: # (seq_length, features)
        X = X.reshape(1, SEQUENCE_LENGTH, FEATURES_COUNT)
        
    prediction = _fast_predict(model, X)
    return prediction.numpy().flatten()

if __name__ == "__main__":
    train_model()
