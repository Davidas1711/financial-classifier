#!/usr/bin/env python3
"""
Generate test data to demonstrate yearly subscription handling
"""

import pandas as pd
import random
from datetime import datetime, timedelta

def generate_yearly_subscription_test():
    """
    Generate transactions with monthly and yearly subscription amounts
    """
    
    transactions = []
    
    # Valid monthly subscriptions
    monthly_valid = [
        {"description": "Amazon Prime", "amount": -14.99, "expected_result": "valid_monthly"},
        {"description": "Netflix", "amount": -15.99, "expected_result": "valid_monthly"},
        {"description": "Spotify", "amount": -9.99, "expected_result": "valid_monthly"},
        {"description": "Disney+", "amount": -13.99, "expected_result": "valid_monthly"},
        {"description": "Apple Music", "amount": -10.99, "expected_result": "valid_monthly"},
    ]
    
    # Valid yearly subscriptions (should NOT be flagged as anomalies)
    yearly_valid = [
        {"description": "Amazon Prime", "amount": -139.00, "expected_result": "valid_yearly"},
        {"description": "Netflix", "amount": -194.99, "expected_result": "valid_yearly"},
        {"description": "Spotify", "amount": -99.00, "expected_result": "valid_yearly"},
        {"description": "Disney+", "amount": -79.99, "expected_result": "valid_yearly"},
        {"description": "Apple Music", "amount": -109.00, "expected_result": "valid_yearly"},
    ]
    
    # Anomalous amounts (should be flagged)
    anomalous = [
        {"description": "Amazon Prime", "amount": -500.00, "expected_result": "anomaly_yearly"},
        {"description": "Netflix", "amount": -1000.00, "expected_result": "anomaly_yearly"},
        {"description": "Spotify", "amount": -600.00, "expected_result": "anomaly_yearly"},
        {"description": "Amazon Prime", "amount": -100.00, "expected_result": "anomaly_monthly"},
        {"description": "Netflix", "amount": -200.00, "expected_result": "anomaly_monthly"},
    ]
    
    # Combine all transactions
    all_transactions = monthly_valid + yearly_valid + anomalous
    
    for i, trans in enumerate(all_transactions):
        # Random date within last 3 months
        date = datetime.now() - timedelta(days=random.randint(0, 90))
        
        transactions.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Description': trans['description'],
            'Amount': trans['amount'],
            'Expected_Result': trans['expected_result']
        })
    
    return pd.DataFrame(transactions)

if __name__ == "__main__":
    # Generate test data
    yearly_data = generate_yearly_subscription_test()
    
    # Save to input directory
    output_file = "data/input/test_yearly_subscriptions.csv"
    yearly_data.to_csv(output_file, index=False)
    
    print(f"Generated {len(yearly_data)} test transactions for yearly subscription handling")
    print(f"Saved to: {output_file}")
    print("\nExpected results:")
    print(yearly_data['Expected_Result'].value_counts())
    print("\nValid yearly subscriptions (should NOT be flagged):")
    valid_yearly = yearly_data[yearly_data['Expected_Result'] == 'valid_yearly']
    for _, row in valid_yearly.iterrows():
        print(f"  {row['Description']}: ${row['Amount']:.2f}")
    print("\nAnomalous amounts (should be flagged):")
    anomalous = yearly_data[yearly_data['Expected_Result'].str.contains('anomaly')]
    for _, row in anomalous.iterrows():
        print(f"  {row['Description']}: ${row['Amount']:.2f} ({row['Expected_Result']})")
