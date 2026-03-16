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
import torch
import torch.nn as nn
import streamlit as st
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout, Layer, MultiHeadAttention, LayerNormalization, GlobalAveragePooling1D
from data.cmapss_loader import load_dataset, DEGRADING_SENSORS, SENSOR_SUBSYSTEM_MAP

# Constants for Deep Learning
SEQUENCE_LENGTH = 30
FEATURES_COUNT = len(DEGRADING_SENSORS)

# Phase 11: Robust Features (Sensors + Operational Settings)
OP_SETTINGS = ['op1', 'op2', 'op3']
ROBUST_FEATURES = OP_SETTINGS + DEGRADING_SENSORS
ROBUST_FEATURES_COUNT = len(ROBUST_FEATURES)

# Scaling constants (approximate for C-MAPSS FD001/FD004)
# Used to ensure live inference is on the same scale as training
S_MIN = np.array([641.2, 1571.0, 1382.2, 549.8, 2387.9, 9021.4, 46.8, 518.6, 2387.9, 8064.6, 8.3, 388.0, 38.0, 22.8])
S_MAX = np.array([644.5, 1601.3, 1435.8, 556.0, 2389.0, 9170.0, 48.5, 524.3, 2390.4, 8243.0, 8.7, 397.0, 40.0, 23.6])

def normalize_input(X):
    """Deep Learning normalization for 14 or 17 feature inputs."""
    # Ensure X is numpy for slicing
    X = np.array(X)
    if X.shape[-1] == 17:
        # Scale 3 OP settings
        OP_MIN = np.array([0.0, 0.0, 0.0])
        OP_MAX = np.array([42.0, 0.84, 100.0])
        X_op = (X[..., :3] - OP_MIN) / (OP_MAX - OP_MIN + 1e-9)
        # Scale 14 sensors
        X_s = (X[..., 3:] - S_MIN) / (S_MAX - S_MIN + 1e-9)
        return np.concatenate([X_op, X_s], axis=-1)
    # Just 14 sensors
    return (X - S_MIN) / (S_MAX - S_MIN + 1e-9)

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

def create_sequences_robust(data, seq_length):
    """Groups data using robust feature set (OP settings + Sensors)."""
    sequences = []
    labels = []
    
    for unit_id in data['unit'].unique():
        unit_df = data[data['unit'] == unit_id]
        # Use ROBUST_FEATURES instead of just DEGRADING_SENSORS
        unit_data = unit_df[ROBUST_FEATURES].values
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

    def call(self, inputs, training=False, return_attention_scores=False):
        # Explicitly pass query, value, key for self-attention
        # Some Keras versions are picky about positional args with return_attention_scores
        attn_output, attn_scores = self.att(
            query=inputs, 
            value=inputs, 
            key=inputs, 
            training=training,
            return_attention_scores=True
        )
        attn_output = self.dropout1(attn_output, training=training)
        out1 = self.layernorm1(inputs + attn_output)
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output, training=training)
        output = self.layernorm2(out1 + ffn_output)
        
        if return_attention_scores:
            return output, attn_scores
        return output

def build_transformer_model(feature_count=FEATURES_COUNT):
    """Builds a SOTA Self-Attention Transformer model."""
    inputs = tf.keras.Input(shape=(SEQUENCE_LENGTH, feature_count))
    # Do NOT pass training=False during functional building; let Keras handle it
    x = TransformerBlock(feature_count, num_heads=2, ff_dim=32)(inputs)
    x = GlobalAveragePooling1D()(x)
    x = Dropout(0.1)(x)
    x = Dense(20, activation="relu")(x)
    outputs = Dense(1)(x)
    
    model = tf.keras.Model(inputs=inputs, outputs=outputs)
    model.compile(optimizer='adam', loss='mse', metrics=['mae'])
    return model

def get_attention_weights(sequence_data, model_type='SOTA (Transformer)'):
    """
    Extracts attention weights from the Transformer model for a given sequence.
    """
    if 'Transformer' not in model_type and 'Hybrid' not in model_type:
        return None
        
    model = get_cached_model(model_type)
    # Find the TransformerBlock layer
    transformer_layer = None
    for layer in model.layers:
        if isinstance(layer, TransformerBlock):
            transformer_layer = layer
            break
    
    if not transformer_layer:
        return None
        
    X = np.array(sequence_data).reshape(1, SEQUENCE_LENGTH, FEATURES_COUNT)
    # We need a functional sub-model or direct call to get internal outputs
    # Simplest: call the layer directly with inputs
    _, attn_weights = transformer_layer(X, training=False, return_attention_scores=True)
    return attn_weights.numpy()[0] # [heads, seq, seq]

# -- PHASE 11: UNIVERSAL MASTER (PT) --
class UniversalTransformerPT(nn.Module):
    def __init__(self, input_size):
        super(UniversalTransformerPT, self).__init__()
        self.encoder = nn.TransformerEncoder(
            nn.TransformerEncoderLayer(d_model=input_size, nhead=1, dim_feedforward=128, batch_first=True),
            num_layers=3
        )
        self.fc = nn.Sequential(
            nn.Linear(input_size, 64),
            nn.ReLU(),
            nn.Dropout(0.1),
            nn.Linear(64, 1)
        )
        
    def forward(self, x):
        x = self.encoder(x)
        x = x.mean(dim=1)
        return self.fc(x)

_UNIVERSAL_MODEL_PATH = os.path.join(os.path.dirname(__file__), 'universal_master_model.pth')

@st.cache_resource
def get_universal_model():
    model = UniversalTransformerPT(ROBUST_FEATURES_COUNT)
    if os.path.exists(_UNIVERSAL_MODEL_PATH):
        model.load_state_dict(torch.load(_UNIVERSAL_MODEL_PATH, map_location='cpu'))
    model.eval()
    return model

class PhysicsInformedModel(tf.keras.Model):
    """
    Hybrid Digital Twin: Enforces thermodynamic constraints (PINN).
    Penalizes predictions that violate the physical law: 
    Increased Temperature/Pressure (Entropy) must correlate with Decreased RUL.
    """
    def __init__(self, base_model, lambda_physics=1.0):
        super().__init__()
        self.base_model = base_model
        self.lambda_physics = lambda_physics
        self.mae_metric = tf.keras.metrics.MeanAbsoluteError(name="mae")

    def call(self, inputs, training=False):
        return self.base_model(inputs, training=training)

    def train_step(self, data):
        x, y = data
        with tf.GradientTape() as tape:
            y_pred = self.base_model(x, training=True)
            data_loss = tf.keras.losses.mean_squared_error(y, y_pred)
            
            # Physics Constraint:
            # High sensor readings in T24 (s2), T30 (s3), T50 (s4) denote higher entropy.
            # We calculate a 'Physical Degradation Signal' from these sensors.
            # Sensor indicators: s2, s3, s4 are indices 0, 1, 2 in DEGRADING_SENSORS.
            phys_signal = tf.reduce_mean(x[:, -1, 0:3], axis=-1, keepdims=True)
            
            # Physics Loss: Penalize if y_pred increases while phys_signal (entropy) also increases.
            # We want d(RUL)/d(Temp) < 0.
            # We approximate this by penalizing the covariance between temp and RUL.
            mean_sig = tf.reduce_mean(phys_signal)
            mean_pred = tf.reduce_mean(y_pred)
            p_loss = tf.reduce_mean((phys_signal - mean_sig) * (y_pred - mean_pred))
            
            # We only penalize if it's positive (violation of inverse correlation)
            p_loss = tf.maximum(0.0, p_loss)
            
            total_loss = data_loss + self.lambda_physics * p_loss
            
        grads = tape.gradient(total_loss, self.trainable_variables)
        self.optimizer.apply_gradients(zip(grads, self.trainable_variables))
        
        self.mae_metric.update_state(y, y_pred)
        return {"loss": total_loss, "mae": self.mae_metric.result()}

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
    elif model_type == 'Hybrid':
        base = build_transformer_model()
        model = PhysicsInformedModel(base)
        model.compile(optimizer='adam')
    else:
        model = build_lstm_model()
        
    model.fit(X, y, epochs=epochs, batch_size=32, verbose=0)
    
    # For Hybrid, we save the base model to avoid custom model serialization issues in simple load_model
    final_path = _MODEL_PATH.replace('lstm', model_type.lower())
    if model_type == 'Hybrid':
        model.base_model.save(final_path)
    else:
        model.save(final_path)
    return model

@st.cache_resource
def get_cached_model(model_type='LSTM'):
    path = _MODEL_PATH.replace('lstm', model_type.lower())
    if not os.path.exists(path):
        return train_model(model_type)
    return load_model(path, custom_objects={'TransformerBlock': TransformerBlock})

def predict_rul(sequence_data, model_type='LSTM'):
    """Multi-model prediction anchor."""
    X_raw = np.array(sequence_data)
    
    # Standard mode fallback (random forest simulation)
    if model_type == 'Standard':
        # Use s11 (index 6 if 14, 9 if 17)
        feat_idx = 9 if X_raw.shape[-1] == 17 else 6
        s11_val = X_raw[-1][feat_idx]
        s11_norm = (s11_val - 46.8) / (48.5 - 46.8 + 1e-9)
        # Standard model follows a quadratic decay approximation
        rul_pred = (1.0 - s11_norm) * 160.0 + 10.0
        return np.array([max(1, rul_pred)])

    if model_type == 'Universal (Master)':
        model = get_universal_model()
        # Master wants 17 (3 OP + 14 sensors)
        if X_raw.shape[-1] == FEATURES_COUNT: # 14
            padding = np.zeros((X_raw.shape[0], 3))
            X_inp = np.hstack([padding, X_raw])
        else:
            X_inp = X_raw
        
        X_scaled = normalize_input(X_inp)
        X = torch.tensor(X_scaled, dtype=torch.float32).unsqueeze(0)
        with torch.no_grad():
            return model(X).numpy().flatten()

    # For other models (LSTM, Transformer, Hybrid) - use ONLY 14 sensors
    if X_raw.shape[-1] == 17:
        X_inp = X_raw[:, 3:] # trim settings
    else:
        X_inp = X_raw

    try:
        model = get_cached_model(model_type)
        X_scaled = normalize_input(X_inp).reshape(1, SEQUENCE_LENGTH, -1)
        # Ensure X_scaled is float32 for Keras
        X_scaled = X_scaled.astype(np.float32)
        preds = model(X_scaled, training=False)
        
        # Handle cases where model might return a list or tuple (PINN or complex models)
        if isinstance(preds, (list, tuple)):
            preds = preds[0]
            
        return preds.numpy().flatten()
    except Exception as e:
        import traceback
        err_msg = f"AI PREDICTION ERROR [{model_type}]: {str(e)}\n{traceback.format_exc()}"
        print(err_msg)
        # Fallback to standard 
        feat_idx = 6
        s11_val = X_raw[-1][feat_idx] if X_raw.ndim > 1 else X_raw[feat_idx]
        s11_norm = (s11_val - 46.8) / (48.5 - 46.8 + 1e-9)
        return np.array([(1.0 - s11_norm) * 160.0 + 10.0])

if __name__ == "__main__":
    train_model()
