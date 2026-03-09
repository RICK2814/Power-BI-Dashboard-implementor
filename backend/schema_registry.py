DOMAINS = {
    "retail": {
        "name": "RETAIL / E-COMMERCE",
        "table": "retail_orders",
        "key_metrics": "revenue, profit, quantity, discount",
        "date_columns": "order_date, ship_date",
        "dimension_columns": "category, sub_category, region, segment",
        "schema_string": "retail_orders(order_id, order_date DATE, ship_date DATE, customer_id, customer_name, segment, region, state, city, category, sub_category, product_name, sales REAL, quantity INTEGER, discount REAL, profit REAL, ship_mode)",
        "demo_queries": [
            {"label": "Revenue Trend", "query": "Show monthly revenue trend for 2023 vs 2024"},
            {"label": "Most Profitable", "query": "Which product category has the highest profit margin?"},
            {"label": "Top Customers", "query": "Top 10 customers by lifetime value this year"},
            {"label": "Regional MTD", "query": "Regional performance comparison — which region is growing fastest?"}
        ]
    },
    "hr": {
        "name": "HR / PEOPLE ANALYTICS",
        "table": "hr_employees",
        "key_metrics": "salary, attrition rate, years_at_company",
        "date_columns": "None directly, but years_at_company and age act as continuous time",
        "dimension_columns": "department, job_role, gender, performance_rating",
        "schema_string": "hr_employees(employee_id, name, department, job_role, gender, age INTEGER, education, marital_status, salary REAL, years_at_company INTEGER, years_in_role INTEGER, performance_rating INTEGER, overtime, attrition, business_travel, distance_from_home INTEGER)",
        "demo_queries": [
            {"label": "Attrition Rate", "query": "Which department has the highest attrition rate?"},
            {"label": "Salary Dist", "query": "Show salary distribution by department and gender"},
            {"label": "Overtime Attrition", "query": "What percentage of employees who work overtime leave the company?"},
            {"label": "Average Tenure", "query": "Average tenure by job role — who stays longest?"}
        ]
    },
    "finance": {
        "name": "FINANCE / BANKING",
        "table": "finance_transactions",
        "key_metrics": "amount, fraud_count",
        "date_columns": "transaction_date",
        "dimension_columns": "transaction_type, merchant_category, city, is_fraud",
        "schema_string": "finance_transactions(transaction_id, transaction_date DATE, customer_id, account_type, transaction_type, amount REAL, merchant_category, city, country, is_fraud INTEGER, payment_method, balance_after REAL)",
        "demo_queries": [
            {"label": "Transaction Vol", "query": "Show total transaction volume by month and payment method"},
            {"label": "Fraud Incidents", "query": "Which merchant category has the most fraud incidents?"},
            {"label": "Credit vs Debit", "query": "Compare debit vs credit transaction amounts by quarter"},
            {"label": "Top Cities", "query": "Top 5 cities by total spending volume"}
        ]
    },
    "healthcare": {
        "name": "HEALTHCARE",
        "table": "healthcare_patients",
        "key_metrics": "billing_amount, length_of_stay",
        "date_columns": "admission_date, discharge_date",
        "dimension_columns": "diagnosis, hospital, admission_type",
        "schema_string": "healthcare_patients(patient_id, admission_date DATE, discharge_date DATE, age INTEGER, gender, blood_type, diagnosis, doctor, hospital, insurance_provider, billing_amount REAL, room_type, admission_type, test_results)",
        "demo_queries": [
            {"label": "Avg Billing", "query": "What is the average billing amount by diagnosis?"},
            {"label": "Monthly Admissions", "query": "Show monthly admissions trend by admission type"},
            {"label": "Longest Stay", "query": "Which age group has the longest average stay?"},
            {"label": "Top Diagnoses", "query": "Top diagnoses by frequency and average cost"}
        ]
    },
    "supply_chain": {
        "name": "SUPPLY CHAIN",
        "table": "supply_chain",
        "key_metrics": "revenue, defect_rates, stock_levels",
        "date_columns": "None directly, but lead_times implies duration",
        "dimension_columns": "product_type, supplier_name, location",
        "schema_string": "supply_chain(product_id, product_name, product_type, sku, price REAL, availability INTEGER, units_sold INTEGER, revenue REAL, stock_levels INTEGER, lead_times INTEGER, order_quantities INTEGER, supplier_name, location, defect_rates REAL, shipping_times INTEGER, shipping_costs REAL, transportation_mode, routes, customer_demographics)",
        "demo_queries": [
            {"label": "Defect Rates", "query": "Which supplier has the highest defect rate?"},
            {"label": "Turnover", "query": "Show inventory turnover by product type"},
            {"label": "Avg Shipping", "query": "Average shipping time by transportation mode and route"},
            {"label": "Understocked", "query": "Revenue vs stock levels — which products are understocked?"}
        ]
    },
    "restaurant": {
        "name": "RESTAURANT / F&B",
        "table": "restaurant_orders",
        "key_metrics": "total_price, quantity, rating",
        "date_columns": "order_date, order_time",
        "dimension_columns": "category, payment_method, order_type",
        "schema_string": "restaurant_orders(order_id, order_date DATE, order_time, day_of_week, customer_id, item_name, category, quantity INTEGER, unit_price REAL, total_price REAL, payment_method, order_type, table_number INTEGER, waiter_id, rating INTEGER)",
        "demo_queries": [
            {"label": "Top Revenue", "query": "Which menu items generate the most revenue?"},
            {"label": "Peak Hours", "query": "Show peak hours by day of week using order volume"},
            {"label": "Avg Order Val", "query": "Average order value by payment method and order type"},
            {"label": "Best Reviews", "query": "Customer rating trends — which category gets best reviews?"}
        ]
    },
    "real_estate": {
        "name": "REAL ESTATE",
        "table": "real_estate",
        "key_metrics": "price, sqft_living",
        "date_columns": "sale_date, yr_built",
        "dimension_columns": "zipcode, city, condition",
        "schema_string": "real_estate(property_id, sale_date DATE, price REAL, bedrooms INTEGER, bathrooms INTEGER, sqft_living INTEGER, sqft_lot INTEGER, floors INTEGER, waterfront INTEGER, view_rating INTEGER, condition INTEGER, grade INTEGER, city, zipcode, lat REAL, long REAL, yr_built INTEGER, yr_renovated INTEGER)",
        "demo_queries": [
            {"label": "Price per Sqft", "query": "Show average price per sqft by city"},
            {"label": "Bedrooms vs Price", "query": "How does number of bedrooms affect sale price?"},
            {"label": "Price Trend", "query": "Monthly transaction volume and average price trend"},
            {"label": "High Apprec", "query": "Which zipcodes have highest price appreciation?"}
        ]
    },
    "marketing": {
        "name": "MARKETING / SaaS",
        "table": "marketing_customers",
        "key_metrics": "mrr, churn_rate, ltv",
        "date_columns": "signup_date, churn_date",
        "dimension_columns": "plan_type, acquisition_channel, country",
        "schema_string": "marketing_customers(customer_id, signup_date DATE, plan_type, mrr REAL, tenure_months INTEGER, churn INTEGER, churn_date DATE, acquisition_channel, country, age INTEGER, gender, num_logins INTEGER, support_tickets INTEGER, contract_type, payment_method)",
        "demo_queries": [
            {"label": "Churn by Plan", "query": "What is monthly churn rate by plan type?"},
            {"label": "LTV:CAC", "query": "Which acquisition channel has best LTV:CAC ratio?"},
            {"label": "MRR Growth", "query": "Show MRR growth and expansion revenue month over month"},
            {"label": "Cohort Retention", "query": "Cohort retention analysis — which signup month retains best?"}
        ]
    }
}

DATASETS = [
    {
        "kaggle_id": "vivek468/superstore-dataset-final",
        "file": "Sample - Superstore.csv",
        "table": "retail_orders",
        "domain": "retail"
    },
    {
        "kaggle_id": "pavansubhasht/ibm-hr-analytics-attrition-dataset",
        "file": "WA_Fn-UseC_-HR-Employee-Attrition.csv",
        "table": "hr_employees",
        "domain": "hr"
    },
    {
        "kaggle_id": "computingvictor/transactions-fraud-datasets",
        "file": "transactions_data.csv",
        "table": "finance_transactions",
        "domain": "finance"
    },
    {
        "kaggle_id": "prasad22/healthcare-dataset",
        "file": "healthcare_dataset.csv",
        "table": "healthcare_patients",
        "domain": "healthcare"
    },
    {
        "kaggle_id": "harshsingh2209/supply-chain-analysis",
        "file": "supply_chain_data.csv",
        "table": "supply_chain",
        "domain": "supply_chain"
    },
    {
        "kaggle_id": "blastchar/telco-customer-churn",
        "file": "WA_Fn-UseC_-Telco-Customer-Churn.csv",
        "table": "marketing_customers",
        "domain": "marketing"
    },
    {
        "kaggle_id": "harlfoxem/housesalesprediction",
        "file": "kc_house_data.csv",
        "table": "real_estate",
        "domain": "real_estate"
    },
    {
        "kaggle_id": "ahsan81/food-ordering-and-delivery-app-dataset",
        "file": "food_order.csv",
        "table": "restaurant_orders",
        "domain": "restaurant"
    }
]
