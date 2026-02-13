#!/usr/bin/env python3
"""
Generate synthetic financial transaction data for testing
"""

import pandas as pd
import random
from datetime import datetime, timedelta
import os


class TestDataGenerator:
    def __init__(self):
        self.merchants = {
            'Food & Dining': [
                'Starbucks', 'McDonalds', 'Chipotle', 'Subway', 'Pizza Hut',
                'Local Cafe', 'Restaurant Downtown', 'Food Truck', 'Burger King',
                'Taco Bell', 'KFC', 'Wendys', 'Panera Bread', 'Dunkin Donuts'
            ],
            'Shopping': [
                'Amazon', 'Walmart', 'Target', 'Costco', 'Home Depot',
                'Best Buy', 'Macy\'s', 'Nordstrom', 'Gap', 'Old Navy',
                'Apple Store', 'Microsoft Store', 'Lowe\'s', 'IKEA', 'Trader Joe\'s'
            ],
            'Transportation': [
                'Shell Gas Station', 'Chevron', 'Exxon', 'Uber', 'Lyft',
                'Public Transit', 'Parking Garage', 'Toll Bridge', 'Airport Parking',
                'Gas Station', 'BP Gas', 'Mobil Gas', 'Taxi Service', 'Rental Car'
            ],
            'Bills & Utilities': [
                'Electric Company', 'Gas Company', 'Water Department', 'Internet Provider',
                'Phone Company', 'Cable TV', 'Mortgage Payment', 'Rent Payment',
                'Insurance Premium', 'Property Tax', 'Trash Service', 'Sewer Service'
            ],
            'Healthcare': [
                'Hospital Medical Center', 'Doctor Office', 'Pharmacy', 'Dental Clinic',
                'Eye Doctor', 'Physical Therapy', 'Health Insurance', 'Urgent Care',
                'Medical Supply', 'Veterinary Clinic', 'Mental Health', 'Specialist'
            ],
            'Entertainment': [
                'Netflix', 'Spotify', 'Movie Theater', 'Concert Venue', 'Sports Event',
                'Gaming Platform', 'Streaming Service', 'Gym Membership', 'Golf Course',
                'Amusement Park', 'Museum', 'Bowling Alley', 'Arcade', 'Book Store'
            ],
            'Banking & Fees': [
                'Bank Fee', 'ATM Fee', 'Overdraft Fee', 'Wire Transfer', 'Credit Card Fee',
                'Late Payment Fee', 'Service Charge', 'Interest Charge', 'Foreign Transaction Fee',
                'Monthly Maintenance Fee', 'Paper Statement Fee', 'Stop Payment Fee'
            ],
            'Income': [
                'Salary Deposit', 'Payroll', 'Freelance Payment', 'Investment Return',
                'Tax Refund', 'Bonus Payment', 'Commission', 'Rental Income',
                'Dividend Payment', 'Interest Income', 'Cash Back', 'Rebate'
            ]
        }
        
        # Add some variations and misspellings for testing fuzzy matching
        self.merchant_variations = {
            'Starbucks': ['Starbucks Coffee', 'STARBUCKS', 'Starbcks', 'Star Bucks'],
            'McDonalds': ['MCDONALDS', 'Mc Donald\'s', 'Mcdonalds', 'McDonald\'s'],
            'Amazon': ['AMAZON', 'Amazon.com', 'AMZN', 'Amazon Prime'],
            'Walmart': ['WALMART', 'Wal-Mart', 'Walmart Supercenter'],
            'Target': ['TARGET', 'Target Stores', 'Target.com'],
            'Netflix': ['NETFLIX', 'Netflix.com', 'NFLX'],
            'Shell Gas Station': ['Shell', 'Shell Oil', 'Shell Gas'],
            'Uber': ['UBER', 'Uber.com', 'Uber Trip']
        }
    
    def generate_transactions(self, num_transactions=1000, start_date=None, end_date=None):
        """
        Generate synthetic transaction data
        """
        if start_date is None:
            start_date = datetime.now() - timedelta(days=365)
        if end_date is None:
            end_date = datetime.now()
        
        transactions = []
        
        for i in range(num_transactions):
            # Random date
            date = start_date + timedelta(
                days=random.randint(0, (end_date - start_date).days)
            )
            
            # Random category and merchant
            category = random.choice(list(self.merchants.keys()))
            base_merchant = random.choice(self.merchants[category])
            
            # Apply variations for testing
            if base_merchant in self.merchant_variations and random.random() < 0.3:
                merchant = random.choice(self.merchant_variations[base_merchant])
            else:
                merchant = base_merchant
            
            # Random amount based on category
            amount = self._generate_amount(category)
            
            # Random description variations
            description = self._generate_description(merchant, amount)
            
            transactions.append({
                'Date': date.strftime('%Y-%m-%d'),
                'Description': description,
                'Amount': amount,
                'Merchant': merchant,
                'Category': category
            })
        
        return pd.DataFrame(transactions)
    
    def _generate_amount(self, category):
        """
        Generate realistic amounts based on category
        """
        amount_ranges = {
            'Food & Dining': (5, 100),
            'Shopping': (10, 500),
            'Transportation': (3, 200),
            'Bills & Utilities': (50, 2000),
            'Healthcare': (20, 1000),
            'Entertainment': (5, 150),
            'Banking & Fees': (1, 100),
            'Income': (500, 10000)
        }
        
        min_amount, max_amount = amount_ranges.get(category, (1, 1000))
        
        # Generate amount with 2 decimal places
        amount = round(random.uniform(min_amount, max_amount), 2)
        
        # Make income amounts positive, others negative (expenses)
        if category == 'Income':
            return amount
        else:
            return -amount
    
    def _generate_description(self, merchant, amount):
        """
        Generate realistic transaction descriptions
        """
        prefixes = ['POS ', 'ACH ', 'DC ', 'CC ', '']
        suffixes = ['', ' #1234', ' *5678', f' ${abs(amount):.2f}']
        
        prefix = random.choice(prefixes)
        suffix = random.choice(suffixes)
        
        return f"{prefix}{merchant}{suffix}"
    
    def generate_problematic_data(self, num_transactions=100):
        """
        Generate data with validation issues for testing
        """
        transactions = []
        
        problems = [
            # Missing values
            {'Date': '', 'Description': 'Test Transaction', 'Amount': 50.00},
            {'Date': '2024-01-01', 'Description': '', 'Amount': 50.00},
            {'Date': '2024-01-01', 'Description': 'Test Transaction', 'Amount': ''},
            
            # Invalid amounts
            {'Date': '2024-01-01', 'Description': 'Zero Amount', 'Amount': 0.00},
            {'Date': '2024-01-01', 'Description': 'Excessive Amount', 'Amount': 15000.00},
            {'Date': '2024-01-01', 'Description': 'Negative Amount', 'Amount': -50000.00},
            {'Date': '2024-01-01', 'Description': 'Invalid Amount', 'Amount': 'not_a_number'},
            
            # Invalid dates
            {'Date': '2025-12-31', 'Description': 'Future Date', 'Amount': 50.00},
            {'Date': '2010-01-01', 'Description': 'Ancient Date', 'Amount': 50.00},
            {'Date': 'not_a_date', 'Description': 'Invalid Date', 'Amount': 50.00},
        ]
        
        # Repeat problems to reach desired count
        for i in range(num_transactions):
            problem = problems[i % len(problems)].copy()
            problem['Description'] = f"{problem['Description']} {i+1}"
            transactions.append(problem)
        
        return pd.DataFrame(transactions)
    
    def save_test_data(self, output_dir="data/input"):
        """
        Generate and save test data files
        """
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate normal test data
        print("Generating normal test data...")
        normal_data = self.generate_transactions(1000)
        normal_file = os.path.join(output_dir, 'test_transactions_normal.csv')
        normal_data.to_csv(normal_file, index=False)
        print(f"Saved {len(normal_data)} normal transactions to {normal_file}")
        
        # Generate Excel version
        excel_file = os.path.join(output_dir, 'test_transactions_normal.xlsx')
        normal_data.to_excel(excel_file, index=False)
        print(f"Saved Excel version to {excel_file}")
        
        # Generate problematic data
        print("Generating problematic test data...")
        problematic_data = self.generate_problematic_data(50)
        problematic_file = os.path.join(output_dir, 'test_transactions_problematic.csv')
        problematic_data.to_csv(problematic_file, index=False)
        print(f"Saved {len(problematic_data)} problematic transactions to {problematic_file}")
        
        # Generate data with different column names
        print("Generating data with different column names...")
        alt_data = self.generate_transactions(500)
        alt_data = alt_data.rename(columns={
            'Date': 'Transaction Date',
            'Description': 'Merchant Name',
            'Amount': 'Transaction Amount'
        })
        alt_file = os.path.join(output_dir, 'test_transactions_alt_columns.csv')
        alt_data.to_csv(alt_file, index=False)
        print(f"Saved {len(alt_data)} transactions with alternative column names to {alt_file}")
        
        return {
            'normal_csv': normal_file,
            'normal_excel': excel_file,
            'problematic': problematic_file,
            'alt_columns': alt_file
        }


if __name__ == "__main__":
    generator = TestDataGenerator()
    files = generator.save_test_data()
    print("\nTest data generation complete!")
    print("Files created:")
    for name, path in files.items():
        print(f"  {name}: {path}")
