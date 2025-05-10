import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    classification_report, 
    confusion_matrix,
    roc_curve, 
    auc,
    precision_recall_curve,
    average_precision_score
)
import json
import os
from datetime import datetime
from fraud_detector import FraudDetector

def load_data():
    """Load and validate dataset with strict feature checking"""
    try:
        # Load CSV data
        df = pd.read_csv("data/auth_logs.csv")
        print(f"Loaded raw dataset with {len(df)} records and {len(df.columns)} columns")
        
        # Initialize detector (loads the trained model)
        fd = FraudDetector()
        required_features = fd.get_feature_names()
        
        # Verify all required features exist
        missing_features = [f for f in required_features if f not in df.columns]
        if missing_features:
            raise ValueError(f"Critical error: Missing features in CSV: {missing_features}")
        
        # Verify target exists
        if 'is_fraud' not in df.columns:
            raise ValueError("Missing target column 'is_fraud'")
        
        # Ensure exact feature order match
        X = df[required_features]
        y = df['is_fraud']
        
        print("Feature validation successful. Using features in this exact order:")
        print(required_features)
        
        return X, y, fd
        
    except Exception as e:
        print(f"Data loading failed: {str(e)}")
        print("\nDebugging info:")
        if 'df' in locals():
            print("Columns in CSV:", df.columns.tolist())
        if 'fd' in locals():
            print("Features expected by model:", fd.get_feature_names())
        raise

def evaluate_model(X, y, fd):
    """Run comprehensive evaluation with strict feature validation"""
    try:
        # Create results directory
        os.makedirs("results", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Final feature validation
        expected_features = fd.get_feature_names()
        if list(X.columns) != expected_features:
            raise ValueError(
                f"CRITICAL: Feature order mismatch!\n"
                f"Expected: {expected_features}\n"
                f"Actual:   {list(X.columns)}\n"
                "This will cause prediction errors!"
            )
        
        # Scale features
        X_scaled = fd.scaler.transform(X)
        
        # Make predictions
        y_pred = (fd.model.predict(X_scaled) == -1).astype(int)
        
        # Generate evaluation metrics
        report = classification_report(y, y_pred, output_dict=True)
        conf_matrix = confusion_matrix(y, y_pred)
        
        # Save visualizations
        plt.figure(figsize=(8, 6))
        sns.heatmap(conf_matrix, annot=True, fmt='d', cmap='Blues',
                   xticklabels=['Legit', 'Fraud'],
                   yticklabels=['Legit', 'Fraud'])
        plt.title('Confusion Matrix')
        plt.savefig(f"results/confusion_matrix_{timestamp}.png")
        plt.close()
        
        # Save full report
        report_path = f"results/evaluation_report_{timestamp}.json"
        with open(report_path, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "model_features": expected_features,
                "data_features": list(X.columns),
                "feature_match": list(X.columns) == expected_features,
                "classification_report": report,
                "dataset_stats": {
                    "total_records": len(X),
                    "fraud_count": int(y.sum()),
                    "fraud_percentage": float(y.mean()) * 100
                }
            }, f, indent=2)
        
        print("\nEvaluation successfully completed!")
        print(f"Results saved to:\n- {report_path}")
        print(f"- results/confusion_matrix_{timestamp}.png")
        
    except Exception as e:
        print(f"\nEvaluation failed during modeling: {str(e)}")
        raise

def main():
    """Main execution function"""
    print("Starting evaluation process...")
    try:
        X, y, fd = load_data()
        evaluate_model(X, y, fd)
    except Exception as e:
        print(f"\nFATAL ERROR: Evaluation failed completely: {str(e)}")
        print("\nRecommended fixes:")
        print("1. Delete models/ directory and retrain")
        print("2. Verify generate_data.py includes all features")
        print("3. Check fraud_detector.py feature lists")

if __name__ == "__main__":
    main()