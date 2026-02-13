#!/usr/bin/env python3
"""
Generate test data with anomalous amounts to test AI sanity checks
"""

import pandas as pd
import random
from datetime import datetime, timedelta

def generate_anomaly_test_data():
    """
    Generate transactions with normal and anomalous amounts
    """
    
    transactions = []
    
    # Normal transactions (should pass validation)
    normal_transactions = [
        {"description": "Spotify", "amount": -9.99, "expected_result": "valid"},
        {"description": "Netflix", "amount": -15.99, "expected_result": "valid"},
        {"description": "Starbucks", "amount": -12.50, "expected_result": "valid"},
        {"description": "Uber", "amount": -25.00, "expected_result": "valid"},
        {"description": "Amazon", "amount": -45.99, "expected_result": "valid"},
        {"description": "Verizon", "amount": -85.00, "expected_result": "valid"},
        {"description": "Disney+", "amount": -7.99, "expected_result": "valid"},
        {"description": "Amazon Prime", "amount": -14.99, "expected_result": "valid"},
    ]
    
    # Anomalous transactions (should trigger AI sanity check)
    anomalous_transactions = [
        {"description": "Spotify", "amount": -150.00, "expected_result": "ai_anomaly"},  # 15x normal price
        {"description": "Netflix", "amount": -6000.00, "expected_result": "ai_anomaly"}, # Extreme anomaly
        {"description": "Starbucks", "amount": -500.00, "expected_result": "ai_anomaly"}, # 10x normal
        {"description": "Uber", "amount": -800.00, "expected_result": "ai_anomaly"},   # 4x normal max
        {"description": "Amazon", "amount": -15000.00, "expected_result": "ai_anomaly"}, # Extreme
        {"description": "Verizon", "amount": -2000.00, "expected_result": "ai_anomaly"}, # 6x normal
        {"description": "Disney+", "amount": -200.00, "expected_result": "ai_anomaly"},  # 8x normal
        {"description": "Amazon Prime", "amount": -100.00, "expected_result": "ai_anomaly"}, # 5x normal
    ]
    
    # Combine all transactions
    all_transactions = normal_transactions + anomalous_transactions
    
    for i, trans in enumerate(all_transactions):
        # Random date within last month
        date = datetime.now() - timedelta(days=random.randint(0, 30))
        
        transactions.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Description': trans['description'],
            'Amount': trans['amount'],
            'Expected_Result': trans['expected_result']
        })
    
    return pd.DataFrame(transactions)

if __name__ == "__main__":
    # Generate test data
    anomaly_data = generate_anomaly_test_data()
    
    # Save to input directory
    output_file = "data/input/test_anomaly_detection.csv"
    anomaly_data.to_csv(output_file, index=False)
    
    print(f"Generated {len(anomaly_data)} test transactions for anomaly detection")
    print(f"Saved to: {output_file}")
    print("\nExpected results:")
    print(anomaly_data['Expected_Result'].value_counts())
    print("\nAnomalous transactions:")
    anomalous = anomaly_data[anomaly_data['Expected_Result'] == 'ai_anomaly']
    for _, row in anomalous.iterrows():
        print(f"  {row['Description']}: ${row['Amount']:.2f}")
