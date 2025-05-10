import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import joblib
import os
from datetime import datetime

class FraudDetector:
    def __init__(self):
        self.model = IsolationForest(
            n_estimators=200,
            contamination=0.03,
            random_state=42,
            verbose=1
        )
        self.scaler = StandardScaler()
        self.model_path = "models/fraud_detection_model.pkl"
        self.scaler_path = "models/scaler.pkl"
        self.standard_features = [
            'login_attempts_1h',
            'ip_changes_24h',
            'user_agent_mismatch',
            'time_since_last_login',
            'location_change'
        ]
        self.biometric_features = [
            'mouse_velocity',
            'mouse_distance',
            'keystroke_dwell',
            'keystroke_flight'
        ]
        
        os.makedirs("models", exist_ok=True)
        if os.path.exists(self.model_path) and os.path.exists(self.scaler_path):
            print("Loading existing model...")
            self.model = joblib.load(self.model_path)
            self.scaler = joblib.load(self.scaler_path)
        else:
            print("Training new model...")
            self.train_model()

    def train_model(self):
        """Train model using generated dataset and biometric patterns"""
        # Load dataset
        df = pd.read_csv("data/auth_logs.csv")
        
        # Verify all features exist
        missing_std = [f for f in self.standard_features if f not in df.columns]
        missing_bio = [f for f in self.biometric_features if f not in df.columns]
        
        if missing_std:
            raise ValueError(f"Missing standard features: {missing_std}")
        if missing_bio:
            print(f"Warning: Missing biometric features: {missing_bio}")
            for f in missing_bio:
                df[f] = 0
        
        # Train model
        X = df[self.standard_features + self.biometric_features]
        y = df['is_fraud']
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled[y == 0])
        
        # Save models
        joblib.dump(self.model, self.model_path)
        joblib.dump(self.scaler, self.scaler_path)
        print("Model trained successfully with features:", 
              self.standard_features + self.biometric_features)

    def predict(self, features, biometrics=None):
        """Predict fraud using both standard and biometric features"""
        try:
            # Convert to DataFrame if needed
            if isinstance(features, dict):
                X = pd.DataFrame([features])
            else:
                X = features.copy()
            
            # Ensure all standard features exist
            for f in self.standard_features:
                if f not in X.columns:
                    X[f] = 0
                    
            # Add biometric features if available
            if biometrics:
                bio_data = {
                    'mouse_velocity': biometrics.get('mouse', {}).get('avgVelocity', 0),
                    'mouse_distance': biometrics.get('mouse', {}).get('totalDistance', 0),
                    'keystroke_dwell': biometrics.get('keyboard', {}).get('avgDwellTime', 0),
                    'keystroke_flight': biometrics.get('keyboard', {}).get('avgFlightTime', 0)
                }
                for f in self.biometric_features:
                    X[f] = bio_data.get(f, 0)
            
            # Ensure all features are present
            all_features = self.standard_features + self.biometric_features
            for f in all_features:
                if f not in X.columns:
                    X[f] = 0
                    
            # Scale and predict
            X_scaled = self.scaler.transform(X[all_features])
            return self.model.predict(X_scaled)[0] == -1
            
        except Exception as e:
            print(f"Prediction error: {str(e)}")
            return True  # Fail-safe: assume fraud on error

    def get_feature_names(self):
        """Return all feature names used by the model"""
        return self.standard_features + self.biometric_features

if __name__ == "__main__":
    fd = FraudDetector()