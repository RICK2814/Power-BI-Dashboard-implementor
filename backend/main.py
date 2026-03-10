from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import pandas as pd
import sqlite3
import json
import uuid
import os
import traceback

from schema_registry import DOMAINS, DATASETS
from database import execute_query, get_table_schema
from gemini import (
    route_query, generate_sql, generate_chart_config,
    handle_followup, explain_error, extract_schema_from_csv,
    generate_insights, gemini_analyze_csv
)
from dataset_loader import DB_PATH
from auto_analyzer import auto_analyze_csv

def _read_csv_robust(file_path):
    """Try multiple encodings to read a CSV file with extreme robustness."""
    encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252', 'iso-8859-1', 'utf-16']
    for enc in encodings:
        try:
            print(f"Attempting read with {enc}...")
            # Use low_memory=False to prevent mixed type warnings
            return pd.read_csv(file_path, encoding=enc, low_memory=False)
        except Exception as e:
            print(f"Failed with {enc}: {str(e)[:50]}")
            continue
    
    # Absolute fallback: Read with latin1 AND replace errors
    print("Final fallback: latin1 with errors='replace'")
    try:
        return pd.read_csv(file_path, encoding='latin1', errors='replace', low_memory=False)
    except:
        # One truly final fallback: try separator detection if it's not a comma
        return pd.read_csv(file_path, sep=None, engine='python', encoding='latin1', errors='replace')



app = FastAPI(title="Universal ConvoBI — Agentic BI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory sessions
sessions = {}


# ════════════════════════════════════════════
# Pydantic Models
# ════════════════════════════════════════════
class QueryRequest(BaseModel):
    prompt: str
    session_id: str
    domain: Optional[str] = None  # Optional — if not set, auto-route

class FollowupRequest(BaseModel):
    prompt: str
    session_id: str
    current_dashboard: dict
    current_sql: str
    domain: Optional[str] = None


# ════════════════════════════════════════════
# Helper: Build full schema context
# ════════════════════════════════════════════
def get_all_schemas_string():
    """Build a combined schema string for all domains."""
    parts = []
    for k, v in DOMAINS.items():
        parts.append(f"[{k}] {v['name']}: {v['schema_string']}")
    return "\n".join(parts)

def get_domain_keys():
    return list(DOMAINS.keys())


# ════════════════════════════════════════════
# ENDPOINT: Health Check
# ════════════════════════════════════════════
@app.get("/")
def read_root():
    return {"message": "Universal ConvoBI Agentic API is running.", "status": "healthy"}


# ════════════════════════════════════════════
# ENDPOINT: Get Domains
# ════════════════════════════════════════════
@app.get("/api/domains")
def get_domains():
    domain_list = []
    for k, v in DOMAINS.items():
        domain_list.append({
            "id": k,
            "name": v["name"],
            "table": v["table"],
            "metrics": v["key_metrics"].split(', '),
            "queries": v["demo_queries"]
        })
    return domain_list


# ════════════════════════════════════════════
# ENDPOINT: AGENTIC QUERY (Main Pipeline)
# Ask anything → auto-route → SQL → execute → charts → insights
# ════════════════════════════════════════════
@app.post("/api/query")
def process_query(req: QueryRequest):
    try:
        # ── STEP 0: Route the query ──
        domain_id = req.domain
        routing_info = None

        if not domain_id or domain_id == "auto":
            all_schemas = get_all_schemas_string()
            routing_info = route_query(req.prompt, all_schemas, get_domain_keys())

            if routing_info.get("route") == "general":
                # It's a general question — return AI answer directly
                return {
                    "type": "general_answer",
                    "dashboardTitle": "AI Assistant",
                    "businessInsight": routing_info.get("answer", "I'm not sure how to answer that."),
                    "charts": [],
                    "summaryStats": [],
                    "followUpSuggestions": [
                        {"id": "f1", "label": "Show retail data", "query": "Show monthly revenue trend", "category": "drill_down"},
                        {"id": "f2", "label": "HR overview", "query": "What is the average salary by department?", "category": "drill_down"},
                        {"id": "f3", "label": "Finance summary", "query": "Show transaction volume by month", "category": "drill_down"}
                    ],
                    "sqlExecuted": None,
                    "rowsReturned": 0
                }

            domain_id = routing_info.get("domain_id")

        # Validate domain
        if domain_id not in DOMAINS and domain_id != "custom":
            return explain_error(req.prompt, f"Could not identify the right dataset for your question.", get_all_schemas_string())

        # Get domain metadata
        session = sessions.get(req.session_id, {})

        if domain_id == "custom":
            schema_string = session.get("schema_string", "No custom schema available.")
            custom_table_name = session.get("table_name") or session.get("schema", {}).get("tableName", "uploaded_data")
            domain_meta = {
                "name": "Custom Data",
                "key_metrics": ", ".join(session.get("schema", {}).get("keyMetrics", [])),
                "date_columns": "",
                "dimension_columns": ", ".join(session.get("schema", {}).get("keyDimensions", [])),
                "table": custom_table_name
            }
        else:
            domain_meta = DOMAINS[domain_id]
            schema_string = domain_meta["schema_string"]

        # Use rewritten query if available from router
        effective_query = req.prompt
        if routing_info and routing_info.get("rewritten_query"):
            effective_query = routing_info["rewritten_query"]

        # ── STEP 1: Generate SQL ──
        raw_sql = generate_sql(
            domain_name=domain_meta["name"],
            schema_string=schema_string,
            query=effective_query,
            key_metrics=domain_meta["key_metrics"],
            date_columns=domain_meta.get("date_columns", ""),
            dimension_columns=domain_meta.get("dimension_columns", ""),
            available_tables=domain_meta["table"]
        )

        if raw_sql.startswith("ERROR:"):
            return explain_error(req.prompt, raw_sql, schema_string)

        # ── STEP 2: Execute SQL ──
        data_rows = execute_query(raw_sql)

        if isinstance(data_rows, dict) and "error" in data_rows:
            return explain_error(req.prompt, data_rows["error"], schema_string)

        if not data_rows:
            return explain_error(req.prompt, "Query ran successfully but returned 0 rows.", schema_string)

        # ── STEP 3: Generate Chart Config + Dashboard ──
        chart_config = generate_chart_config(
            domain=domain_id,
            user_query=req.prompt,
            sql_executed=raw_sql,
            data_rows=data_rows
        )

        if isinstance(chart_config, dict) and "error" in chart_config and "dashboardTitle" not in chart_config:
            print("Chart config error:", chart_config["error"])
            # Return a basic fallback dashboard
            col_keys = list(data_rows[0].keys()) if data_rows else []
            chart_config = {
                "dashboardTitle": f"Results for: {req.prompt[:50]}",
                "domain": domain_id,
                "queryIntent": "comparison",
                "summaryStats": [{"id": "kpi_1", "label": "Total Records", "value": str(len(data_rows)), "trend": "neutral", "icon": "revenue"}],
                "charts": [{"id": "chart_1", "chartType": "table", "title": "Query Results", "subtitle": "Raw data", "xKey": col_keys[0] if col_keys else "col", "yKeys": col_keys[1:2] if len(col_keys) > 1 else col_keys[:1], "yLabels": col_keys[1:2] if len(col_keys) > 1 else col_keys[:1], "data": [], "layout": "full", "colorScheme": "blue", "showLegend": False, "showGrid": True, "stacked": False}],
                "businessInsight": "Data retrieved successfully. Chart generation encountered an issue, showing raw results.",
                "followUpSuggestions": [],
                "alerts": []
            }

        # Inject actual data
        chart_config["sqlExecuted"] = raw_sql
        chart_config["rowsReturned"] = len(data_rows)
        chart_config["type"] = "dashboard"
        chart_config["routed_domain"] = domain_id
        chart_config["routed_domain_name"] = domain_meta["name"]

        for chart in chart_config.get("charts", []):
            chart["data"] = data_rows

        # ── STEP 4: Generate Insights ──
        try:
            insights_data = generate_insights(domain_id, data_rows, raw_sql)
            chart_config["aiInsights"] = insights_data.get("insights", [])
            chart_config["anomalies"] = insights_data.get("anomalies", [])
            chart_config["recommendations"] = insights_data.get("recommendations", [])
        except:
            chart_config["aiInsights"] = []
            chart_config["anomalies"] = []
            chart_config["recommendations"] = []

        # ── Update Session ──
        if req.session_id not in sessions:
            sessions[req.session_id] = {"history": [], "domain": domain_id}

        sessions[req.session_id]["history"].append({
            "query": req.prompt,
            "sql": raw_sql,
            "domain": domain_id,
            "dashboard_title": chart_config.get("dashboardTitle", "Dashboard")
        })
        sessions[req.session_id]["domain"] = domain_id

        return chart_config

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "type": "error",
            "userMessage": f"An unexpected error occurred: {str(e)}",
            "suggestions": ["Try a simpler question", "Show all retail data", "What departments exist?"],
            "didYouMean": None
        }


# ════════════════════════════════════════════
# ENDPOINT: Follow-up Query
# ════════════════════════════════════════════
@app.post("/api/followup")
def process_followup(req: FollowupRequest):
    try:
        session = sessions.get(req.session_id, {})
        domain_id = req.domain or session.get("domain", "retail")
        
        # 1. Get Domain Metadata & Schema
        if domain_id == "custom":
            schema_string = session.get("schema_string", "No custom schema available.")
            domain_name = "Custom Upload"
        else:
            domain_meta = DOMAINS.get(domain_id, {})
            schema_string = domain_meta.get("schema_string", "")
            domain_name = domain_meta.get("name", domain_id)

        # 2. Check if this follow-up is actually a "New Subject"
        # If the user asks something completely unrelated, we should ROUTE it freshly.
        routing_info = route_query(req.prompt, get_all_schemas_string(), get_domain_keys())
        if routing_info.get("route") == "general":
             return {
                "type": "general_answer",
                "dashboardTitle": "AI Assistant",
                "businessInsight": routing_info.get("answer", "I'm not sure how to answer that."),
                "charts": [],
                "summaryStats": [],
                "followUpSuggestions": [
                    {"id": "f1", "label": "Back to current data", "query": "Show dashboard again", "category": "drill_down"}
                ],
                "sqlExecuted": None,
                "rowsReturned": 0
            }
        
        # If it re-routed to a DIFFERENT domain, handle it as a fresh query
        new_domain = routing_info.get("domain_id")
        if new_domain and new_domain != domain_id:
            req.domain = new_domain
            return process_query(req)

        # 3. Handle actual Follow-up (modifying current state)
        follow_up_result = handle_followup(
            current_dashboard=req.current_dashboard,
            current_sql=req.current_sql,
            original_query=session.get("history", [{}])[-1].get("query", "") if session.get("history") else "",
            followup_instruction=req.prompt,
            schema_string=schema_string
        )

        if "error" in follow_up_result:
            return explain_error(req.prompt, follow_up_result["error"], schema_string)

        # If there's modified SQL, run it
        modified_sql = follow_up_result.get("modifiedSQL")
        if modified_sql and modified_sql != req.current_sql:
            data_rows = execute_query(modified_sql)
            if isinstance(data_rows, dict) and "error" in data_rows:
                return explain_error(req.prompt, "Follow-up SQL error: " + data_rows["error"], schema_string)

            dashboard = follow_up_result.get("dashboard", req.current_dashboard)
            # Inject new data into all charts
            for chart in dashboard.get("charts", []):
                chart["data"] = data_rows
            
            dashboard["sqlExecuted"] = modified_sql
            dashboard["rowsReturned"] = len(data_rows)
            dashboard["type"] = "dashboard"
            dashboard["routed_domain"] = domain_id
            dashboard["routed_domain_name"] = domain_name

            # Update session history
            if req.session_id in sessions:
                sessions[req.session_id]["history"].append({
                    "query": req.prompt,
                    "sql": modified_sql,
                    "domain": domain_id,
                    "dashboard_title": dashboard.get("dashboardTitle", "Follow-up")
                })

            return dashboard

        result = follow_up_result.get("dashboard", req.current_dashboard)
        result["type"] = "dashboard"
        return result

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"type": "error", "userMessage": str(e), "suggestions": []}


# ════════════════════════════════════════════
# HELPER: Run Gemini analysis pipeline on a table
# ════════════════════════════════════════════
def _run_gemini_analysis(table_name: str, df: pd.DataFrame, domain_label: str = "Custom Upload"):
    """Shared Gemini analysis pipeline for both uploads and pre-loaded domains."""
    import numpy as np

    def clean_str(s):
        """Final last-resort string cleaning for JSON serializability."""
        if not isinstance(s, str): return str(s)
        try:
            return s.encode('utf-8', 'ignore').decode('utf-8')
        except:
            return "".join(i for i in s if ord(i) < 128)

    # 1. Get schema string
    try:
        schema_string = get_table_schema(table_name)
    except:
        schema_string = f"Table: {table_name}"

    # 2. Build data preview (first 30 rows) - cleaned
    try:
        preview_rows = df.head(30).to_dict(orient="records")
        # Deep clean any potentially broken strings
        cleaned_preview = []
        for row in preview_rows:
            cleaned_row = {clean_str(k): (clean_str(v) if isinstance(v, str) else (None if pd.isna(v) else v)) for k, v in row.items()}
            cleaned_preview.append(cleaned_row)
        data_preview = json.dumps(cleaned_preview, default=str)
    except:
        data_preview = "[]"

    # 3. Build stats summary
    try:
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        cat_cols = df.select_dtypes(include=['object', 'category', 'string']).columns.tolist()
        
        stats_parts = [f"Total rows: {len(df)}", f"Total columns: {len(df.columns)}"]
        stats_parts.append(f"Numeric columns: {', '.join(numeric_cols[:10])}")
        stats_parts.append(f"Categorical columns: {', '.join(cat_cols[:10])}")

        for col in numeric_cols[:8]:
            try:
                col_data = df[col].dropna()
                if len(col_data) > 0:
                    stats_parts.append(f"{col}: min={float(col_data.min()):.2f}, max={float(col_data.max()):.2f}, mean={float(col_data.mean()):.2f}")
            except: pass

        for col in cat_cols[:6]:
            try:
                top = df[col].value_counts().head(5)
                stats_parts.append(f"{clean_str(col)}: {df[col].nunique()} unique. Top: {dict(top)}")
            except: pass
        
        stats_summary = clean_str("\n".join(stats_parts))
    except Exception as e:
        stats_summary = f"Dataset with {len(df)} rows and {len(df.columns)} columns."

    # 4. Call Gemini for full analysis
    try:
        gemini_result = gemini_analyze_csv(table_name, schema_string, data_preview, stats_summary)
    except Exception as e:
        gemini_result = {"error": str(e)}

    if "error" in gemini_result and "dashboardTitle" not in gemini_result:
        # Fallback to local auto analyzer
        try:
            return auto_analyze_csv(table_name, df)
        except:
            return {"type": "error", "userMessage": "Data analysis failed."}

    # 5. Execute each chart's SQL and populate with REAL data
    for chart in gemini_result.get("charts", []):
        try:
            sql = chart.get("sql_query")
            if sql:
                chart_data = execute_query(sql)
                if isinstance(chart_data, dict) and "error" in chart_data:
                    chart["data"] = []
                elif chart_data:
                    # Clean all query results for safety
                    final_data = []
                    for row in chart_data:
                        final_data.append({clean_str(k): (clean_str(v) if isinstance(v, str) else (None if pd.isna(v) else v)) for k, v in row.items()})
                    chart["data"] = final_data
                else:
                    chart["data"] = []
        except:
            chart["data"] = []

    # 6. Assemble complete dashboard (cleaned)
    res = {
        "type": "dashboard",
        "dashboardTitle": clean_str(gemini_result.get("dashboardTitle", "Data Dashboard")),
        "routed_domain": "custom",
        "routed_domain_name": clean_str(domain_label),
        "summaryStats": gemini_result.get("summaryStats", []),
        "charts": gemini_result.get("charts", []),
        "businessInsight": clean_str(gemini_result.get("businessInsight", "")),
        "aiInsights": [clean_str(i) for i in gemini_result.get("aiInsights", [])],
        "anomalies": [clean_str(a) for a in gemini_result.get("anomalies", [])],
        "recommendations": [clean_str(r) for r in gemini_result.get("recommendations", [])],
        "followUpSuggestions": gemini_result.get("followUpSuggestions", []),
        "sqlExecuted": gemini_result.get("sqlExecuted", f"SELECT * FROM {table_name} LIMIT 50")
    }
    return res



# ════════════════════════════════════════════
# ENDPOINT: Upload CSV → Gemini Analysis → Full Dashboard
# ════════════════════════════════════════════
@app.post("/api/upload")
async def upload_dataset(file: UploadFile = File(...), session_id: Optional[str] = Form(None)):
    """Upload any CSV → Gemini analyzes it → returns complete dashboard with charts, KPIs, insights."""
    try:
        content = await file.read()
        os.makedirs("data", exist_ok=True)
        temp_path = f"data/custom_{file.filename.replace(' ', '_')}"

        with open(temp_path, "wb") as f:
            f.write(content)

        # Robust read
        df = _read_csv_robust(temp_path)
        
        # Clean column names
        df.columns = [str(c).strip().replace(' ', '_').replace('-', '_').lower() for c in df.columns]

        table_name = "custom_" + file.filename.split('.')[0].replace('-', '_').replace(' ', '_').lower()

        # Load into SQLite
        conn = sqlite3.connect(DB_PATH)
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.close()

        # Run Gemini-powered analysis
        dashboard = _run_gemini_analysis(table_name, df, f"Upload: {file.filename}")

        # Persistence: Use existing session if provided, else create new
        if not session_id:
            session_id = str(uuid.uuid4())
            
        schema_string = get_table_schema(table_name)
        sessions[session_id] = {
            "schema_string": schema_string,
            "domain": "custom",
            "table_name": table_name,
            "history": [{"query": "Auto-Analysis", "sql": f"SELECT * FROM {table_name}", "domain": "custom", "dashboard_title": dashboard.get('dashboardTitle', 'Auto-Analysis')}]
        }

        dashboard["session_id"] = session_id
        dashboard["tableName"] = table_name
        return dashboard

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════
# ENDPOINT: Auto-Analyze Pre-loaded Domain
# ════════════════════════════════════════════
@app.post("/api/auto_analyze/{domain_id}")
def auto_analyze_domain(domain_id: str):
    """Auto-analyze a pre-loaded domain dataset using Gemini."""
    try:
        if domain_id not in DOMAINS:
            raise HTTPException(status_code=404, detail=f"Domain '{domain_id}' not found")

        domain = DOMAINS[domain_id]
        table_name = domain["table"]

        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
        conn.close()

        dashboard = _run_gemini_analysis(table_name, df, domain["name"])
        dashboard["routed_domain"] = domain_id
        dashboard["routed_domain_name"] = domain["name"]

        return dashboard
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════
# ENDPOINT: Get Available Tables
# ════════════════════════════════════════════
@app.get("/api/tables")
def get_tables():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        conn.close()
        return {"tables": tables}
    except:
        return {"tables": []}


# ════════════════════════════════════════════
# ENDPOINT: Session
# ════════════════════════════════════════════
@app.get("/api/session/{session_id}")
def get_session(session_id: str):
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    return sessions[session_id]


# ════════════════════════════════════════════
# Startup: Load datasets
# ════════════════════════════════════════════
@app.on_event("startup")
def startup_event():
    from dataset_loader import load_datasets
    load_datasets()
    
    # Debug print for API key
    key = os.getenv("GEMINI_API_KEY")
    if key:
        masked = key[:5] + "..." + key[-4:]
        print(f"📡 Gemini API key detected: {masked}")
    else:
        print("⚠️ WARNING: GEMINI_API_KEY is NOT set in .env")
        
    print("✅ ConvoBI Agentic Engine ready!")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
