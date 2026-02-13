#!/usr/bin/env python3
"""
Generate challenging test data for AI classification
"""

import pandas as pd
import random
from datetime import datetime, timedelta

def generate_challenging_data():
    """
    Generate transactions with merchants that need AI classification
    """
    
    # Challenging merchants that aren't in the main mapping
    challenging_merchants = [
        # Food & Dining (challenging names)
        "Bistro 123", "Cafe Milano", "Taco Palace", "Burger Joint", "Pizza Express",
        "Sushi World", "Pasta House", "Grill Master", "Deli Corner", "Breakfast Spot",
        
        # Shopping (challenging names)
        "Tech Store", "Fashion Boutique", "Sports Shop", "Book Nook", "Gadget Galaxy",
        "Home Goods", "Clothing Emporium", "Electronics World", "Toy Store", "Jewelry Box",
        
        # Transportation (challenging names)
        "Ride Share", "Gas Station Plus", "Parking Garage", "Transit Pass", "Taxi Service",
        "Fuel Stop", "Metro Card", "Highway Toll", "Airport Shuttle", "Bike Rental",
        
        # Bills & Utilities (challenging names)
        "Phone Provider", "Internet Service", "Power Company", "Water Dept", "Insurance Co",
        "Cable TV", "Streaming Plus", "Cloud Storage", "Software Sub", "Web Hosting",
        
        # Healthcare (challenging names)
        "Medical Center", "Drug Store", "Health Clinic", "Eye Care", "Dental Office",
        "Physical Therapy", "Lab Services", "Urgent Care", "Specialist Group", "Pharmacy Plus",
        
        # Entertainment (challenging names)
        "Movie Theater", "Concert Hall", "Gaming Platform", "Music Service", "Video Streaming",
        "Sports Tickets", "Theme Park", "Golf Course", "Bowling Alley", "Arcade Fun",
        
        # Banking & Fees (challenging names)
        "Bank Charge", "ATM Fee", "Service Charge", "Interest Fee", "Overdraft Charge",
        "Wire Transfer", "Credit Card Fee", "Late Payment", "Annual Fee", "Transaction Fee",
        
        # Income (challenging names)
        "Salary Deposit", "Paycheck Direct", "Investment Return", "Dividend Payment", "Interest Income",
        "Freelance Pay", "Bonus Amount", "Tax Refund", "Cash Back", "Commission Earned"
    ]
    
    transactions = []
    
    for i, merchant in enumerate(challenging_merchants):
        # Random date within last year
        date = datetime.now() - timedelta(days=random.randint(0, 365))
        
        # Determine category based on merchant name (for testing)
        if any(keyword in merchant.lower() for keyword in ['bistro', 'cafe', 'taco', 'burger', 'pizza', 'sushi', 'pasta', 'grill', 'deli', 'breakfast']):
            category = "Food & Dining"
            amount = -round(random.uniform(10, 100), 2)
        elif any(keyword in merchant.lower() for keyword in ['tech', 'fashion', 'sports', 'book', 'gadget', 'home', 'clothing', 'electronics', 'toy', 'jewelry']):
            category = "Shopping"
            amount = -round(random.uniform(20, 500), 2)
        elif any(keyword in merchant.lower() for keyword in ['ride', 'gas', 'parking', 'transit', 'taxi', 'fuel', 'metro', 'toll', 'shuttle', 'bike']):
            category = "Transportation"
            amount = -round(random.uniform(5, 200), 2)
        elif any(keyword in merchant.lower() for keyword in ['phone', 'internet', 'power', 'water', 'insurance', 'cable', 'streaming', 'cloud', 'software', 'web']):
            category = "Bills & Utilities"
            amount = -round(random.uniform(50, 300), 2)
        elif any(keyword in merchant.lower() for keyword in ['medical', 'drug', 'health', 'eye', 'dental', 'physical', 'lab', 'urgent', 'specialist', 'pharmacy']):
            category = "Healthcare"
            amount = -round(random.uniform(20, 500), 2)
        elif any(keyword in merchant.lower() for keyword in ['movie', 'concert', 'gaming', 'music', 'video', 'sports', 'theme', 'golf', 'bowling', 'arcade']):
            category = "Entertainment"
            amount = -round(random.uniform(10, 150), 2)
        elif any(keyword in merchant.lower() for keyword in ['bank', 'atm', 'service', 'interest', 'overdraft', 'wire', 'credit', 'late', 'annual', 'transaction']):
            category = "Banking & Fees"
            amount = -round(random.uniform(1, 50), 2)
        else:  # Income
            category = "Income"
            amount = round(random.uniform(100, 5000), 2)
        
        transactions.append({
            'Date': date.strftime('%Y-%m-%d'),
            'Description': merchant,
            'Amount': amount,
            'Expected_Category': category
        })
    
    return pd.DataFrame(transactions)

if __name__ == "__main__":
    # Generate challenging test data
    challenging_data = generate_challenging_data()
    
    # Save to input directory
    output_file = "data/input/test_transactions_challenging.csv"
    challenging_data.to_csv(output_file, index=False)
    
    print(f"Generated {len(challenging_data)} challenging transactions")
    print(f"Saved to: {output_file}")
    print("\nCategory breakdown:")
    print(challenging_data['Expected_Category'].value_counts())
