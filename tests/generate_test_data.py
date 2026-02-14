#!/usr/bin/env python3
"""
Generate simplified test data for financial classifier
"""

import pandas as pd
import random
from datetime import datetime, timedelta
import os


class SimpleTestDataGenerator:
    def __init__(self):
        # Use merchants from your existing configuration
        self.merchants = {
            'Food & Dining': [
                'Starbucks', 'McDonalds', 'Chipotle', 'Subway', 'Taco Bell',
                'Dunkin', 'Chick-Fil-A', 'Wendys', 'Panera', 'Uber Eats'
            ],
            'Shopping': [
                'Amazon', 'Walmart', 'Target', 'Best Buy', 'Home Depot',
                'Costco', 'Walgreens', 'CVS', 'Etsy', 'eBay'
            ],
            'Transportation': [
                'Uber', 'Lyft', 'Shell', 'Exxon', 'Chevron', 'Parking', 'Tolls'
            ],
            'Bills & Utilities': [
                'Verizon', 'AT&T', 'Comcast', 'Netflix', 'Spotify', 'Electric', 'Insurance'
            ],
            'Healthcare': [
                'Pharmacy', 'Doctor', 'Hospital', 'Dentist', 'Urgent Care'
            ],
            'Entertainment': [
                'Gaming Platform', 'Gym Membership', 'Sports Event', 'Bowling Alley'
            ],
            'Banking & Fees': [
                'Wire Transfer', 'Property Tax', 'ATM Fee', 'Service Charge'
            ],
            'Income': [
                'Paycheck', 'Salary', 'Direct Deposit', 'Dividend', 'Refund', 'Rebate'
            ]
        }
        
        # Typical amount ranges by category
        self.amount_ranges = {
            'Food & Dining': (5, 100),
            'Shopping': (10, 500),
            'Transportation': (5, 200),
            'Bills & Utilities': (20, 500),
            'Healthcare': (20, 300),
            'Entertainment': (10, 150),
            'Banking & Fees': (5, 100),
            'Income': (500, 10000)
        }
    
    def generate_normal_transactions(self, count=500):
        """Generate normal, everyday transactions"""
        transactions = []
        
        for i in range(count):
            category = random.choice(list(self.merchants.keys()))
            merchant = random.choice(self.merchants[category])
            
            # Generate realistic amount
            min_amount, max_amount = self.amount_ranges[category]
            if category == 'Income':
                amount = round(random.uniform(min_amount, max_amount), 2)
            else:
                amount = -round(random.uniform(min_amount, max_amount), 2)
            
            # Generate random date within last year
            days_ago = random.randint(0, 365)
            date = datetime.now() - timedelta(days=days_ago)
            
            # Create realistic description
            if category == 'Income':
                descriptions = [
                    f"POS {merchant} #{random.randint(1000, 9999)}",
                    f"Direct Deposit {merchant}",
                    f"ACH {merchant}",
                    f"{merchant} Payment"
                ]
            else:
                descriptions = [
                    f"POS {merchant} #{random.randint(1000, 9999)}",
                    f"ACH {merchant} #{random.randint(1000, 9999)}",
                    f"{merchant} Purchase",
                    f"DC {merchant} *{random.randint(1000, 9999)}"
                ]
            
            description = random.choice(descriptions)
            
            transactions.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Description': description,
                'Amount': amount,
                'Merchant': merchant,
                'Category': category
            })
        
        return pd.DataFrame(transactions)
    
    def generate_sample_transactions(self, count=50):
        """Generate a small sample of transactions for quick testing"""
        transactions = []
        
        # Include a few examples from each major category
        sample_merchants = [
            ('Starbucks', 'Food & Dining', -12.50),
            ('Amazon', 'Shopping', -89.99),
            ('Uber', 'Transportation', -23.75),
            ('Netflix', 'Bills & Utilities', -15.99),
            ('Pharmacy', 'Healthcare', -45.20),
            ('Paycheck', 'Income', 2500.00),
            ('Walmart', 'Shopping', -156.32),
            ('Shell', 'Transportation', -45.00),
            ('Verizon', 'Bills & Utilities', -75.00),
            ('Target', 'Shopping', -67.89)
        ]
        
        for i, (merchant, category, amount) in enumerate(sample_merchants):
            days_ago = i * 10  # Spread them out
            date = datetime.now() - timedelta(days=days_ago)
            
            transactions.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Description': f"POS {merchant} #{random.randint(1000, 9999)}",
                'Amount': amount,
                'Merchant': merchant,
                'Category': category
            })
        
        return pd.DataFrame(transactions)


def main():
    """Generate simplified test data"""
    generator = SimpleTestDataGenerator()
    
    # Ensure data/input directory exists
    os.makedirs('data/input', exist_ok=True)
    
    print("Generating simplified test data...")
    
    # Generate normal transactions
    normal_df = generator.generate_normal_transactions(500)
    normal_csv_path = 'data/input/test_transactions.csv'
    normal_df.to_csv(normal_csv_path, index=False)
    normal_df.to_excel('data/input/test_transactions.xlsx', index=False)
    print(f"Saved {len(normal_df)} normal transactions to {normal_csv_path}")
    
    # Generate small sample for quick testing
    sample_df = generator.generate_sample_transactions()
    sample_csv_path = 'data/input/sample_transactions.csv'
    sample_df.to_csv(sample_csv_path, index=False)
    print(f"Saved {len(sample_df)} sample transactions to {sample_csv_path}")
    
    print("\nSimplified test data generation complete!")
    print("Files created:")
    print(f"  - {normal_csv_path} (500 normal transactions)")
    print(f"  - {sample_csv_path} (10 sample transactions)")
    print(f"  - data/input/merchant_reference.csv (merchant list from config)")


if __name__ == "__main__":
    main()
