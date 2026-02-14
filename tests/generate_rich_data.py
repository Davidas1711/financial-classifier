import pandas as pd
import random
from datetime import datetime, timedelta

# 1. Define High Net Worth Merchants & Categories
merchants = {
    "Travel & Transport": ["NetJets", "Lufthansa First Class", "VistaJet", "Yacht Charter Service", "Aman Resorts", "Four Seasons Paris", "St. Regis Maldives"],
    "Luxury Retail": ["Graff Diamonds", "Patek Philippe Boutique", "Hermès", "Louis Vuitton", "Savile Row Bespoke", "Christie's Auction", "Sotheby's"],
    "Dining & Social": ["Noma", "The Fat Duck", "Private Members Club (Annabel's)", "Caviar House", "Vintage Wine Merchants"],
    "Estate & Staff": ["Elite Estate Staffing", "Property Tax - Aspen", "Property Tax - Hamptons", "Lawn & Garden - Estate", "Interior Design - Kelly Wearstler"],
    "Financial & Legal": ["Goldman Sachs PWM", "Family Office Fee", "Capital Call - Sequoia", "Wire Transfer - Investment", "Top-Tier Legal retainer"],
    "Philanthropy": ["Global Education Fund", "Arts Museum Donation", "Medical Research Foundation"]
}

# 2. Generate 3,000 Rows of Data
data = []
start_date = datetime(2025, 1, 1)

for i in range(3000):
    category = random.choice(list(merchants.keys()))
    merchant = random.choice(merchants[category])
    
    # Determine amount based on category "luxury" level
    if category == "Financial & Legal" or category == "Philanthropy":
        amount = round(random.uniform(50000, 500000), 2)  # High-end transfers
    elif "Jet" in merchant or "Yacht" in merchant or "Real Estate" in merchant:
        amount = round(random.uniform(25000, 150000), 2)  # Heavy hitters
    else:
        amount = round(random.uniform(500, 15000), 2)    # "Daily" high-end spending

    # Add random transaction noise (Store IDs, cities)
    description = f"{merchant} - {''.join(random.choices('0123456789ABC', k=6))}"
    
    date = start_date + timedelta(days=random.randint(0, 364))
    data.append([date.strftime("%Y-%m-%d"), description, amount])

# 3. Save to CSV
df = pd.DataFrame(data, columns=["Date", "Description", "Amount"])
df.to_csv("rich_person_expenditure_3000.csv", index=False)

print("File 'rich_person_expenditure_3000.csv' created with 3,000 high-net-worth rows.")
