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
import streamlit as st
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Layer, MultiHeadAttention, LayerNormalization, GlobalAveragePooling1D
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

from tensorflow.keras.layers import Layer, MultiHeadAttention, LayerNormalization, GlobalAveragePooling1D

class TransformerBlock(Layer):
    def __init__(self, embed_dim, num_heads, ff_dim, rate=0.1):
        super(TransformerBlock, self).__init__()
        self.att = MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)
        self.ffn = Sequential([
            Dense(ff_dim, activation="relu"), 
            Dense(embed_dim),
        ])
        self.layernorm1 = LayerNormalization(epsilon=1e-6)
        self.layernorm2 = LayerNormalization(epsilon=1e-6)
        self.dropout1 = Dropout(rate)
        self.dropout2 = Dropout(rate)

    def call(self, inputs, training=False):
        attn_output = self.att(inputs, inputs)
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        return self.layernorm2(out1 + ffn_output)

def build_transformer_model():
    """Builds a SOTA Self-Attention Transformer model."""
    inputs = tf.keras.Input(shape=(SEQUENCE_LENGTH, FEATURES_COUNT))
    x = TransformerBlock(FEATURES_COUNT, num_heads=2, ff_dim=32)(inputs, training=False)
    x = GlobalAveragePooling1D()(x)
    x = Dropout(0.1)(x)
    x = Dense(20, activation="relu")(x)
    outputs = Dense(1)(x)
    
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    return model

def build_lstm_model():
    """Defines the Elite LSTM architecture."""
    model = Sequential([
        LSTM(units=100, return_sequences=True, input_shape=(SEQUENCE_LENGTH, FEATURES_COUNT)),
        Dropout(0.2),
        LSTM(units=50, return_sequences=False),
        Dropout(0.2),
        Dense(units=25, activation='relu'),
        Dense(units=1)
    ])
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    return model

def train_model(model_type='LSTM', dataset='FD001', epochs=5):
    """Train either LSTM or Transformer."""
    train_df, _, _ = load_dataset(dataset)
    max_cycles = train_df.groupby('unit')['cycle'].max()
    train_df = train_df.merge(max_cycles.rename('max_cycle'), on='unit')
    train_df['RUL'] = train_df['max_cycle'] - train_df['cycle']
    
    X, y = create_sequences(train_df, SEQUENCE_LENGTH)
    
    if model_type == 'Transformer':
        model = build_transformer_model()
    else:
        model = build_lstm_model()
        
    model.fit(X, y, epochs=epochs, batch_size=32, verbose=0)
    
    path = _MODEL_PATH.replace('lstm', model_type.lower())
    model.save(path)
    return model

@st.cache_resource
def get_cached_model(model_type='LSTM'):
    path = _MODEL_PATH.replace('lstm', model_type.lower())
    if not os.path.exists(path):
        return train_model(model_type)
    return load_model(path, custom_objects={'TransformerBlock': TransformerBlock})

def predict_rul(sequence_data, model_type='LSTM'):
    """Multi-model prediction anchor."""
    # Standard mode fallback (random forest simulation)
    if model_type == 'Standard':
        # Simple health-based RUL proxy for 'Standard' baseline
        health = 1.0 - sequence_data[-1][0] # use first sensor as health proxy
        return np.array([health * 150.0])

    model = get_cached_model(model_type)
    X = np.array(sequence_data).reshape(1, SEQUENCE_LENGTH, FEATURES_COUNT)
    return model(X, training=False).numpy().flatten()

if __name__ == "__main__":
    train_model()
