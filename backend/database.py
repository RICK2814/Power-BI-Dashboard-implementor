import sqlite3
import pandas as pd
from dataset_loader import DB_PATH

def execute_query(sql_query):
    # Security Validation
    upper_query = sql_query.upper()
    forbidden = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "EXEC", "--", "XP_"]
    for f in forbidden:
        if f in upper_query:
            return {"error": f"Security violation: Query contains forbidden keyword '{f}'"}

    try:
        conn = sqlite3.connect(DB_PATH)
        # We return both columns and rows separately or as JSON depending on the need.
        # Returning as list of dicts:
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df.to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}

def get_table_schema(table_name):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    conn.close()
    
    # columns format: (cid, name, type, notnull, dflt_value, pk)
    # We construct a simple schema string
    col_strings = []
    for col in columns:
        col_strings.append(f"{col[1]} {col[2]}")
    return f"{table_name}({', '.join(col_strings)})"
