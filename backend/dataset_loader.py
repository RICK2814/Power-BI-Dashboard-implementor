import os
import sqlite3
import pandas as pd
from schema_registry import DATASETS, DOMAINS

DB_PATH = "universal-bi.db"
DATA_DIR = "data"

def load_datasets():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        
    conn = sqlite3.connect(DB_PATH)
    
    kaggle_available = False
    if os.getenv("KAGGLE_USERNAME") and os.getenv("KAGGLE_KEY"):
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
            api = KaggleApi()
            api.authenticate()
            kaggle_available = True
            print("Kaggle credentials found. Downloading datasets...")
        except Exception as e:
            print(f"Kaggle authentication failed ({e}). Falling back to synthetic datasets.")
            
    if not kaggle_available:
        print("No Kaggle credentials found. Falling back to synthetic datasets.")
        import faker
        fake = faker.Faker()
        import random
        from datetime import datetime, timedelta

    for ds in DATASETS:
        table_name = ds["table"]
        # Check if table already exists
        cursor = conn.cursor()
        cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        if cursor.fetchone():
            print(f"Table '{table_name}' already exists. Skipping load.")
            continue
            
        file_path = os.path.join(DATA_DIR, ds["file"])
        
        if kaggle_available:
            if not os.path.exists(file_path):
                print(f"Downloading {ds['kaggle_id']}...")
                try:
                    api.dataset_download_files(ds['kaggle_id'], path=DATA_DIR, unzip=True)
                except Exception as dl_e:
                    print(f"Failed to download {ds['kaggle_id']}: {dl_e}")
                    kaggle_available = False # fallback to synthetic for this or remaining
                    
        if not os.path.exists(file_path) and not kaggle_available:
            print(f"Generating synthetic data for {table_name}...")
            # Generating synthetic data based on domain
            rows = []
            for i in range(1, 101): # 100 rows
                if ds["domain"] == "retail":
                    rows.append({
                        "order_id": f"ORD-{i}", "order_date": (datetime.now() - timedelta(days=random.randint(1,365))).strftime("%Y-%m-%d"),
                        "ship_date": (datetime.now() - timedelta(days=random.randint(1,360))).strftime("%Y-%m-%d"),
                        "customer_id": f"CUST-{random.randint(1,50)}", "customer_name": fake.name(),
                        "segment": random.choice(["Consumer", "Corporate", "Home Office"]),
                        "region": random.choice(["East", "West", "North", "South"]),
                        "state": fake.state(), "city": fake.city(),
                        "category": random.choice(["Furniture", "Office Supplies", "Technology"]),
                        "sub_category": random.choice(["Chairs", "Tables", "Phones", "Storage"]),
                        "product_name": fake.catch_phrase(),
                        "sales": round(random.uniform(10.0, 1500.0), 2),
                        "quantity": random.randint(1, 10),
                        "discount": round(random.uniform(0.0, 0.5), 2),
                        "profit": round(random.uniform(-50.0, 500.0), 2),
                        "ship_mode": random.choice(["Standard", "Express", "Same Day"])
                    })
                elif ds["domain"] == "hr":
                    rows.append({
                        "employee_id": f"EMP-{i}", "name": fake.name(),
                        "department": random.choice(["Sales", "R&D", "HR", "Marketing"]),
                        "job_role": random.choice(["Manager", "Developer", "Analyst", "Director"]),
                        "gender": random.choice(["Male", "Female"]),
                        "age": random.randint(22, 60),
                        "education": random.choice(["Bachelors", "Masters", "PhD"]),
                        "marital_status": random.choice(["Single", "Married", "Divorced"]),
                        "salary": round(random.uniform(40000, 150000), 2),
                        "years_at_company": random.randint(0, 20),
                        "years_in_role": random.randint(0, 10),
                        "performance_rating": random.randint(1, 5),
                        "overtime": random.choice(["Yes", "No"]),
                        "attrition": random.choice(["Yes", "No", "No", "No"]),
                        "business_travel": random.choice(["Rarely", "Frequently", "Non-Travel"]),
                        "distance_from_home": random.randint(1, 40)
                    })
                elif ds["domain"] == "finance":
                    rows.append({
                        "transaction_id": f"TXN-{i}", "transaction_date": (datetime.now() - timedelta(days=random.randint(1,365))).strftime("%Y-%m-%d"),
                        "customer_id": f"CUST-{random.randint(1,50)}", "account_type": random.choice(["Checking", "Savings"]),
                        "transaction_type": random.choice(["Credit", "Debit"]),
                        "amount": round(random.uniform(5.0, 5000.0), 2),
                        "merchant_category": random.choice(["Retail", "Dining", "Travel", "Online"]),
                        "city": fake.city(), "country": "USA",
                        "is_fraud": random.choices([0, 1], weights=[0.95, 0.05])[0],
                        "payment_method": random.choice(["Card", "App", "Transfer"]),
                        "balance_after": round(random.uniform(100.0, 50000.0), 2)
                    })
                elif ds["domain"] == "healthcare":
                    rows.append({
                        "patient_id": f"PAT-{i}", "admission_date": (datetime.now() - timedelta(days=random.randint(10,365))).strftime("%Y-%m-%d"),
                        "discharge_date": (datetime.now() - timedelta(days=random.randint(1,9))).strftime("%Y-%m-%d"),
                        "age": random.randint(1, 90), "gender": random.choice(["Male", "Female"]),
                        "blood_type": random.choice(["A+", "O-", "B+", "AB+"]),
                        "diagnosis": random.choice(["Flu", "Fracture", "COVID-19", "Heart Attack", "Routine checkup"]),
                        "doctor": fake.name(), "hospital": f"{fake.city()} General",
                        "insurance_provider": random.choice(["BlueCross", "Aetna", "Medicare", "Cigna"]),
                        "billing_amount": round(random.uniform(500.0, 50000.0), 2),
                        "room_type": random.choice(["General", "Private", "ICU"]),
                        "admission_type": random.choice(["Emergency", "Elective"]),
                        "test_results": random.choice(["Normal", "Abnormal"])
                    })
                elif ds["domain"] == "supply_chain":
                    rows.append({
                        "product_id": f"PRD-{i}", "product_name": fake.word(),
                        "product_type": random.choice(["Raw Material", "Component", "Finished Good"]),
                        "sku": fake.ean13(), "price": round(random.uniform(5.0, 500.0), 2),
                        "availability": random.randint(0, 1000),
                        "units_sold": random.randint(0, 5000),
                        "revenue": round(random.uniform(100.0, 50000.0), 2),
                        "stock_levels": random.randint(0, 5000),
                        "lead_times": random.randint(1, 30),
                        "order_quantities": random.randint(10, 1000),
                        "supplier_name": fake.company(), "location": fake.city(),
                        "defect_rates": round(random.uniform(0.01, 10.0), 2),
                        "shipping_times": random.randint(1, 20),
                        "shipping_costs": round(random.uniform(5.0, 500.0), 2),
                        "transportation_mode": random.choice(["Air", "Sea", "Road", "Rail"]),
                        "routes": fake.word(), "customer_demographics": "N/A"
                    })
                elif ds["domain"] == "restaurant":
                    rows.append({
                        "order_id": f"RORD-{i}", "order_date": (datetime.now() - timedelta(days=random.randint(1,30))).strftime("%Y-%m-%d"),
                        "order_time": f"{random.randint(10,23):02d}:{random.randint(0,59):02d}",
                        "day_of_week": random.choice(["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]),
                        "customer_id": f"CUST-{random.randint(1,100)}",
                        "item_name": random.choice(["Burger", "Pizza", "Pasta", "Salad", "Soda"]),
                        "category": random.choice(["Main", "Sides", "Drinks", "Dessert"]),
                        "quantity": random.randint(1, 5),
                        "unit_price": round(random.uniform(5.0, 25.0), 2),
                        "total_price": round(random.uniform(5.0, 125.0), 2),
                        "payment_method": random.choice(["Cash", "Card", "App"]),
                        "order_type": random.choice(["Dine-in", "Takeaway", "Delivery"]),
                        "table_number": random.randint(1, 20),
                        "waiter_id": f"W-{random.randint(1,10)}",
                        "rating": random.randint(1, 5)
                    })
                elif ds["domain"] == "real_estate":
                    rows.append({
                        "property_id": f"PROP-{i}", "sale_date": (datetime.now() - timedelta(days=random.randint(1,365))).strftime("%Y-%m-%d"),
                        "price": round(random.uniform(100000, 2000000), 2),
                        "bedrooms": random.randint(1, 6), "bathrooms": random.randint(1, 5),
                        "sqft_living": random.randint(500, 5000), "sqft_lot": random.randint(1000, 20000),
                        "floors": random.randint(1, 3), "waterfront": random.choice([0, 1]),
                        "view_rating": random.randint(0, 4), "condition": random.randint(1, 5),
                        "grade": random.randint(1, 13), "city": fake.city(),
                        "zipcode": fake.zipcode(), "lat": fake.latitude(), "long": fake.longitude(),
                        "yr_built": random.randint(1900, 2024), "yr_renovated": random.choice([0, random.randint(1980, 2024)])
                    })
                elif ds["domain"] == "marketing":
                    rows.append({
                        "customer_id": f"CUST-{i}", "signup_date": (datetime.now() - timedelta(days=random.randint(30,730))).strftime("%Y-%m-%d"),
                        "plan_type": random.choice(["Basic", "Pro", "Enterprise"]),
                        "mrr": round(random.uniform(9.99, 999.99), 2),
                        "tenure_months": random.randint(1, 24),
                        "churn": str(random.choices([0, 1], weights=[0.8, 0.2])[0]),
                        "churn_date": (datetime.now() - timedelta(days=random.randint(1,30))).strftime("%Y-%m-%d") if random.choice([0, 1]) == 1 else None,
                        "acquisition_channel": random.choice(["Organic", "Paid", "Referral", "Social"]),
                        "country": fake.country(), "age": random.randint(18, 65),
                        "gender": random.choice(["Male", "Female"]),
                        "num_logins": random.randint(1, 100),
                        "support_tickets": random.randint(0, 5),
                        "contract_type": random.choice(["Monthly", "Annual"]),
                        "payment_method": random.choice(["Credit Card", "PayPal", "Bank Transfer"])
                    })
            df = pd.DataFrame(rows)
            df.to_csv(file_path, index=False)
            
        print(f"Loading {table_name} into SQLite...")
        try:
            # Robust reading with encoding fallbacks
            df = None
            for enc in ['utf-8', 'latin1', 'cp1252']:
                try:
                    df = pd.read_csv(file_path, encoding=enc)
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                df = pd.read_csv(file_path, encoding='utf-8', errors='replace')

            # Standardize column names
            df.columns = [c.strip().replace(' ', '_').replace('-', '_').lower() for c in df.columns]
            df.to_sql(table_name, conn, if_exists="replace", index=False)
        except Exception as e:
            print(f"Error loading {file_path} to DB: {e}")
            
    conn.close()
    print("Dataset loading complete.")

if __name__ == "__main__":
    load_datasets()
