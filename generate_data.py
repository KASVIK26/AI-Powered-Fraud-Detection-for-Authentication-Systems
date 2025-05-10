import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os
import hashlib

def generate_biometrics(is_fraud, username):
    """Generate realistic biometric patterns with distinct fraud patterns"""
    # Use username hash as seed for consistency per user
    user_seed = int(hashlib.sha256(username.encode()).hexdigest(), 16) % (2**32)
    np.random.seed(user_seed)
    
    if is_fraud:
        # Fraudster patterns - more erratic
        return {
            'mouse_velocity': np.random.uniform(500, 1500),  # Much faster movements
            'mouse_distance': np.random.uniform(4000, 8000),  # Longer distances
            'keystroke_dwell': np.random.uniform(30, 80),     # Very short key presses
            'keystroke_flight': np.random.uniform(80, 200)    # Long pauses between keys
        }
    else:
        # Genuine user patterns - more consistent
        base_velocity = np.random.uniform(200, 400)
        base_distance = np.random.uniform(1000, 2500)
        return {
            'mouse_velocity': base_velocity * np.random.uniform(0.9, 1.1),
            'mouse_distance': base_distance * np.random.uniform(0.9, 1.1),
            'keystroke_dwell': np.random.uniform(80, 150),   # Natural typing rhythm
            'keystroke_flight': np.random.uniform(20, 60)     # Normal pauses
        }

def generate_auth_dataset(num_records=10000, fraud_ratio=0.03):
    """Generate comprehensive authentication dataset with biometric patterns"""
    np.random.seed(42)
    
    # User configurations
    users = [f"user_{i}" for i in range(1, 101)]
    devices = ["Mobile", "Desktop"]
    browsers = ["Chrome", "Firefox", "Safari"]
    locations = ["US", "IN", "UK", "DE", "SG"]
    
    # Generate base data
    df = pd.DataFrame({
        "timestamp": [datetime.now() - timedelta(minutes=random.randint(0, 10080)) 
                     for _ in range(num_records)],
        "username": np.random.choice(users, num_records),
        "ip_address": [f"192.168.1.{random.randint(1,50)}" for _ in range(num_records)],
        "user_agent": [f"{random.choice(browsers)}-{random.choice(devices)}" 
                      for _ in range(num_records)],
        "location": np.random.choice(locations, num_records),
        "login_success": np.random.choice([0, 1], num_records, p=[0.1, 0.9]),
        "is_fraud": np.zeros(num_records)
    })
    
    # Mark fraud cases with different patterns
    fraud_indices = np.random.choice(num_records, int(num_records*fraud_ratio), replace=False)
    df.loc[fraud_indices, "is_fraud"] = 1
    
    # Sort for feature calculation
    df = df.sort_values(['username', 'timestamp'])
    
    # Feature Engineering
    # 1. Login attempts in last hour
    df['login_attempts_1h'] = df.groupby('username')['timestamp'].transform(
        lambda x: x.diff().dt.total_seconds().lt(3600).cumsum()
    )
    
    # 2. IP changes
    df['ip_changes_24h'] = df.groupby('username')['ip_address'].transform(
        lambda x: x.ne(x.shift()).cumsum()
    )
    
    # 3. Device anomalies
    df['user_agent_mismatch'] = (df['user_agent'] != 
                                df.groupby('username')['user_agent'].transform('first')).astype(int)
    
    # 4. Time since last login
    df['last_success'] = df[df['login_success']==1].groupby('username')['timestamp'].transform('last')
    df['time_since_last_login'] = (df['timestamp'] - df['last_success']).dt.total_seconds()/60
    df['time_since_last_login'] = df['time_since_last_login'].fillna(0)
    
    # 5. Location anomalies
    df['location_change'] = (df.groupby('username')['location'].shift() != df['location']).astype(int)
    
    # 6. Generate biometric features
    biometrics = df.apply(lambda row: generate_biometrics(row['is_fraud'], row['username']), axis=1)
    for f in ['mouse_velocity', 'mouse_distance', 'keystroke_dwell', 'keystroke_flight']:
        df[f] = biometrics.apply(lambda x: x[f])
    
    # Clean up
    df.drop(columns=['last_success'], inplace=True)
    
    # Save
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/auth_logs.csv", index=False)
    print(f"Generated dataset with {len(df)} records ({len(fraud_indices)} fraud cases)")
    return df

if __name__ == "__main__":
    generate_auth_dataset()