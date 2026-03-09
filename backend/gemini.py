import os
import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv(override=True)

# Initialize the Gemini client
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key) if api_key else None


import time

def call_gemini(system_instruction: str, user_content: str, response_format: str = "text", temperature: float = 0.1) -> str:
    if not client:
        return '{"error": "GEMINI_API_KEY not set"}' if response_format == "json" else "ERROR: GEMINI_API_KEY not set"

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        temperature=temperature,
        response_mime_type="application/json" if response_format == "json" else "text/plain",
    )

    max_retries = 3
    retry_delay = 2  # base delay in seconds

    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model="models/gemini-2.0-flash",
                contents=user_content,
                config=config,
            )
            return response.text
        except Exception as e:
            err_msg = str(e)
            if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)
                    print(f"⚠️ Gemini Rate Limit (429). Retrying in {wait_time}s... (Attempt {attempt + 1}/{max_retries})")
                    time.sleep(wait_time)
                    continue
            
            if response_format == "json":
                return '{"error": "Gemini API failed: ' + err_msg.replace('"', "'") + '"}'
            return f"ERROR: Gemini API failed - {e}"
    
    return '{"error": "Max retries exceeded for Gemini API"}' if response_format == "json" else "ERROR: Max retries exceeded"


# ═══════════════════════════════════════════════════════
# STEP 0: AGENTIC ROUTER — Detects intent + domain automatically
# ═══════════════════════════════════════════════════════
def route_query(user_query: str, all_schemas: str, domain_keys: list):
    """Routes user query to the right domain or answers general questions."""
    system = f"""You are an AI Business Intelligence Agent Router.

Your job: Given a user's question, determine:
1. Is it a DATA question (about business data we have)? → route to the correct domain
2. Is it a GENERAL question (greeting, general knowledge, coding help)? → answer directly

AVAILABLE DATASETS AND THEIR SCHEMAS:
{all_schemas}

AVAILABLE DOMAIN KEYS: {json.dumps(domain_keys)}

Return ONLY valid JSON:
{{
  "route": "data|general",
  "domain_id": "one of the domain keys above if route=data, else null",
  "confidence": 0.0 to 1.0,
  "detected_intent": "trend|comparison|ranking|distribution|composition|correlation|cohort|general_question",
  "detected_metrics": ["list of metrics the user is asking about"],
  "detected_dimensions": ["list of dimensions/groupings"],
  "answer": "If route=general, provide a helpful complete answer here. Else null.",
  "rewritten_query": "If route=data, rewrite the user query to be more precise for SQL generation. Else null."
}}

RULES:
- If the question mentions sales, revenue, orders, products, categories → likely retail
- If it mentions employees, salary, attrition, department, HR → likely hr
- If it mentions transactions, fraud, banking, payments → likely finance
- If it mentions patients, diagnosis, hospital, billing → likely healthcare
- If it mentions supply chain, shipping, defect, supplier → likely supply_chain
- If it mentions restaurant, food, menu, waiter, dining → likely restaurant
- If it mentions property, house, real estate, bedrooms, price per sqft → likely real_estate
- If it mentions churn, MRR, subscription, acquisition, SaaS → likely marketing
- If the question is about general knowledge, greetings, or non-data topics → route=general
- ALWAYS try to detect metrics and dimensions from the question
- If ambiguous between domains, pick the MOST LIKELY one with lower confidence"""

    user = f"User Question: {user_query}"
    try:
        res = call_gemini(system, user, "json", 0.1)
        clean = res.strip().strip("`")
        if clean.startswith("json\n"):
            clean = clean[5:]
        return json.loads(clean)
    except Exception as e:
        err_msg = str(e)
        if "429" in err_msg or "RESOURCE_EXHAUSTED" in err_msg:
             return {
                "route": "general", 
                "answer": "The Agentic AI is currently experiencing high demand (Rate Limit 429). Analysis of this data is temporarily paused. Please try again in 30 seconds.", 
                "confidence": 1.0
            }
        return {"route": "general", "answer": f"I couldn't process that right now. (AI Error: {err_msg[:100]})", "confidence": 0}


# ═══════════════════════════════════════════════════════
# STEP 1 (P1): SQL GENERATOR
# ═══════════════════════════════════════════════════════
def generate_sql(domain_name, schema_string, query, key_metrics, date_columns, dimension_columns, available_tables):
    system = f"""You are a world-class SQL analyst embedded in a universal BI platform.

ACTIVE DOMAIN: {domain_name}
ACTIVE TABLES AND SCHEMAS:
{schema_string}

RULES:
1. Return ONLY raw SQLite SQL. Zero explanation. Zero markdown.
2. Use ONLY columns from the schema above. Never hallucinate columns.
3. Always alias aggregates: SUM(sales) AS total_sales
4. Time-series: use strftime('%Y-%m', date_col) AS month
5. Cross-table queries: use proper JOINs when needed
6. Top N: always ORDER BY metric DESC LIMIT N
7. Percentages: ROUND(100.0 * val / SUM(val) OVER(), 2) AS pct
8. Growth rate: use LAG() window function for period-over-period
9. Cohort analysis: use DATE() and GROUP BY signup month
10. If unanswerable from schema, return EXACTLY:
    ERROR: Cannot answer this query with available data in {available_tables}

BUSINESS CONTEXT FOR THIS DOMAIN:
- Key metrics for {domain_name}: {key_metrics}
- Common time dimensions: {date_columns}
- Primary grouping dimensions: {dimension_columns}"""

    user = f"User Query: {query}"
    result = call_gemini(system, user, "text", 0.1).strip()
    # Clean any markdown formatting
    result = result.strip("`").strip()
    if result.startswith("sql\n") or result.startswith("sql\r"):
        result = result[4:].strip()
    if result.startswith("SQL\n") or result.startswith("SQL\r"):
        result = result[4:].strip()
    return result


# ═══════════════════════════════════════════════════════
# STEP 2 (P2): CHART CONFIG + DASHBOARD GENERATOR
# ═══════════════════════════════════════════════════════
def generate_chart_config(domain, user_query, sql_executed, data_rows):
    preview = data_rows[:100]

    system = """You are an elite data visualization architect for a BI platform.
You must return ONLY a single valid JSON object. No markdown. No backticks.

REQUIRED JSON STRUCTURE:
{
  "dashboardTitle": "string — executive-friendly, max 60 chars",
  "domain": "string",
  "queryIntent": "trend|comparison|ranking|distribution|composition|correlation|cohort",

  "summaryStats": [
    {
      "id": "kpi_1",
      "label": "string",
      "value": "formatted string (e.g. $2.4M, 94.2%, 1,204)",
      "rawValue": 0,
      "delta": "string|null (e.g. +12.4% vs last period)",
      "trend": "up|down|neutral|null",
      "icon": "revenue|users|growth|time|quality|risk|inventory|conversion"
    }
  ],

  "charts": [
    {
      "id": "chart_1",
      "chartType": "bar|line|area|pie|donut|scatter|table|heatmap|funnel",
      "title": "string",
      "subtitle": "string — one business insight from this chart",
      "xKey": "string — column name for X axis",
      "yKeys": ["string — column names for Y axis values"],
      "yLabels": ["string — human labels for Y keys"],
      "groupKey": null,
      "data": [],
      "layout": "full|half|third",
      "colorScheme": "blue|green|amber|rose|violet|teal|multi",
      "showLegend": true,
      "showGrid": true,
      "stacked": false,
      "sortBy": "value_desc|value_asc|label_asc|natural|null",
      "annotations": [],
      "tableColumns": null
    }
  ],

  "sqlExecuted": "string",
  "rowsReturned": 0,
  "dataConfidence": "high|medium|low",
  "dataConfidenceReason": "string",

  "businessInsight": "string — 2-3 sentence executive summary of what this data means. Be specific with numbers.",

  "followUpSuggestions": [
    { "id": "f1", "label": "max 5 words", "query": "full NL query", "category": "drill_down|filter|compare|forecast" },
    { "id": "f2", "label": "string", "query": "string", "category": "string" },
    { "id": "f3", "label": "string", "query": "string", "category": "string" }
  ],

  "alerts": []
}

CHART SELECTION RULES (NON-NEGOTIABLE):
- line/area   → date/time column present (trends over time)
- bar         → categorical comparisons, <= 20 categories
- stacked bar → multi-dimension breakdown over categories
- pie/donut   → composition/share, <= 6 slices ONLY
- scatter     → two numeric columns (correlation)
- table       → > 25 rows OR user said 'list/table/all/details'
- ALWAYS use multiple charts when data supports it (2-3 charts ideal)
- ALWAYS lead with KPI summaryStats (min 2, max 6)
- ALWAYS add businessInsight paragraph with real numbers from the data
- ALWAYS generate 3 followUpSuggestions relevant to result
- xKey and yKeys MUST match actual column names in the data
- ADD alerts if any metric is anomalous"""

    user = f"Domain: {domain}\nQuery: {user_query}\nSQL Executed: {sql_executed}\nRows returned: {len(data_rows)}\nData sample:\n{json.dumps(preview)}"
    try:
        response_text = call_gemini(system, user, "json", 0.2)
        clean = response_text.strip().strip("`")
        if clean.startswith("json\n"):
            clean = clean[5:]
        return json.loads(clean)
    except Exception as e:
        return {"error": f"Failed to parse chart config: {str(e)}"}


# ═══════════════════════════════════════════════════════
# STEP 3 (P3): CSV SCHEMA EXTRACTOR
# ═══════════════════════════════════════════════════════
def extract_schema_from_csv(table_name, csv_preview_json):
    system = """You are a business data analyst. Infer schema AND business domain from CSV.

Return ONLY valid JSON:
{
  "tableName": "snake_case_singular",
  "businessDomain": "retail|hr|finance|healthcare|supply_chain|restaurant|real_estate|marketing|other",
  "description": "one sentence: what this dataset tracks",
  "columns": [
    {
      "originalName": "exact CSV header",
      "sqlName": "snake_case SQL-safe name",
      "sqlType": "TEXT|REAL|INTEGER|DATE|BOOLEAN",
      "description": "business meaning",
      "sampleValues": [],
      "isMetric": true,
      "isDimension": true,
      "isDate": false,
      "isId": false,
      "dateFormat": null
    }
  ],
  "detectedGranularity": "transactional|daily|weekly|monthly|yearly|snapshot",
  "suggestedQueries": [
    { "label": "max 5 words", "query": "full NL query", "complexity": "simple|medium|advanced" }
  ],
  "keyMetrics": ["column names that are primary KPIs"],
  "keyDimensions": ["column names best for grouping/filtering"]
}"""
    user = f"Table Name: {table_name}\nData Preview:\n{csv_preview_json}"
    try:
        res = call_gemini(system, user, "json", 0.1)
        clean = res.strip().strip("`")
        if clean.startswith("json\n"):
            clean = clean[5:]
        return json.loads(clean)
    except:
        return {"error": "Failed to extract schema"}


# ═══════════════════════════════════════════════════════
# STEP 4 (P4): FOLLOW-UP / DASHBOARD MODIFIER
# ═══════════════════════════════════════════════════════
def handle_followup(current_dashboard, current_sql, original_query, followup_instruction, schema_string):
    system = f"""You are modifying an existing BI dashboard based on a follow-up instruction.

AVAILABLE SCHEMA:
{schema_string}

Current SQL: {current_sql}

Return ONLY valid JSON:
{{
  "action": "filter|drill_down|add_chart|replace_chart|change_period|sort|compare|forecast|clarify",
  "explanation": "plain English: what changed (max 2 sentences)",
  "modifiedSQL": "the new SQL query to run",
  "dashboard": {{ ...full dashboard structure same as P2... }},
  "clarificationQuestion": null
}}

ACTION RULES:
- filter       → narrows data ('only Q3', 'exclude returns', 'just New York')
- drill_down   → more detail ('by product', 'per customer', 'break down further')
- add_chart    → additional view ('also show as pie', 'add a table below')
- replace_chart → change type ('make it a line chart', 'show as bar instead')
- change_period → date range ('last 6 months', 'YTD', '2022 vs 2023')
- sort         → reordering ('sort by profit', 'ascending order')
- compare      → add comparison ('vs last year', 'compare East vs West')
- forecast     → extend trend line using linear projection
- clarify      → genuinely ambiguous only — always attempt best-guess first

IMPORTANT: modifiedSQL must be valid SQLite compatible SQL using ONLY columns from the schema."""

    user = f"Original Query: {original_query}\nFollow-up: {followup_instruction}\nCurrent Dashboard: {json.dumps(current_dashboard)}"
    try:
        res = call_gemini(system, user, "json", 0.2)
        clean = res.strip().strip("`")
        if clean.startswith("json\n"):
            clean = clean[5:]
        return json.loads(clean)
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════════════════════
# STEP 5 (P5): ERROR EXPLAINER
# ═══════════════════════════════════════════════════════
def explain_error(user_query, error_message, available_data):
    """Fallback error explanation when things go wrong."""
    import json
    
    # 1. Immediate exit for Rate Limits (prevent recursive fail)
    if "429" in str(error_message) or "RESOURCE_EXHAUSTED" in str(error_message):
        return {
            "type": "error",
            "userMessage": "Agentic AI is currently experiencing high demand (Rate Limit reached). Please wait a few seconds and try again.",
            "suggestions": ["Wait 10 seconds", "Try a different question"],
            "didYouMean": None
        }

    system = """You are a helpful BI Assistant. Explain the error in plain English.
Return ONLY valid JSON:
{
  "userMessage": "friendly non-technical explanation",
  "suggestions": ["suggested query 1", "suggested query 2"],
  "didYouMean": "suggested fix for the user query or null"
}"""
    user = f"Context: {available_data}\nQuery: {user_query}\nError: {error_message}"
    
    try:
        # 2. Try to get AI explanation
        res = call_gemini(system, user, "json", 0.3)
        clean = res.strip().strip("`")
        if clean.startswith("json\n"): clean = clean[5:]
        parsed = json.loads(clean)
        parsed["type"] = "error"
        return parsed
    except:
        # 3. Final fallback
        return {
            "type": "error",
            "userMessage": f"I encountered an error while processing your request: {error_message}",
            "suggestions": ["Check column names", "Try a simpler query", "Show all data"],
            "didYouMean": None
        }


# ═══════════════════════════════════════════════════════
# STEP 6: AUTO INSIGHT GENERATOR
# ═══════════════════════════════════════════════════════
def generate_insights(domain, data_rows, sql_executed):
    """Generate business insights from query results."""
    preview = data_rows[:50]
    system = """You are an AI Data Analyst. Generate business insights from the data.

Return ONLY valid JSON:
{
  "insights": [
    "insight 1 with specific numbers",
    "insight 2 with specific numbers",
    "insight 3 with specific numbers"
  ],
  "anomalies": ["any unusual patterns spotted"],
  "recommendations": ["actionable business recommendation"]
}"""
    user = f"Domain: {domain}\nSQL: {sql_executed}\nData:\n{json.dumps(preview)}"
    try:
        res = call_gemini(system, user, "json", 0.3)
        clean = res.strip().strip("`")
        if clean.startswith("json\n"):
            clean = clean[5:]
        return json.loads(clean)
    except:
        return {"insights": [], "anomalies": [], "recommendations": []}


# ═══════════════════════════════════════════════════════
# STEP 7: GEMINI-POWERED CSV FULL ANALYSIS
# ═══════════════════════════════════════════════════════
def gemini_analyze_csv(table_name: str, schema_string: str, data_preview: str, stats_summary: str):
    """
    Uses Gemini to generate a complete dashboard from uploaded CSV data.
    Sends schema + data preview + basic stats → gets full dashboard JSON back.
    """
    system = """You are an AUTONOMOUS AI Business Intelligence Agent.
You receive a dataset's schema, sample data, and basic statistics.
Your job: generate a COMPLETE interactive dashboard specification.

RULES:
1. Detect the business domain from the data content
2. Identify the most important metrics and dimensions
3. Generate 3-5 meaningful chart specifications using ACTUAL column names
4. Generate 3-6 KPI summary cards with real calculated values from the stats
5. Write 3-5 specific business insights based on the actual data patterns
6. Detect anomalies and correlations
7. Suggest 3 follow-up queries the user would find valuable

CHART TYPE SELECTION RULES:
- Line chart: when a date/time column exists (show trends)
- Bar chart: for categorical comparisons (max 15 categories)
- Pie/Donut: for composition/share analysis (max 6 slices)
- Scatter: when two numeric columns may correlate
- Table: for detailed data view
- Area: for cumulative trends

Return ONLY valid JSON with this EXACT structure:
{
  "dashboardTitle": "AI Analysis: [descriptive title based on data]",
  "detectedDomain": "what business domain this data is about",
  "queryIntent": "distribution",

  "summaryStats": [
    {
      "id": "kpi_1",
      "label": "human readable label",
      "value": "formatted value (e.g. $2.4M, 94.2%, 1,204)",
      "rawValue": 0,
      "delta": "context info or null",
      "trend": "up|down|neutral",
      "icon": "revenue|users|growth|time|quality|risk|inventory|conversion"
    }
  ],

  "charts": [
    {
      "id": "chart_1",
      "chartType": "bar|line|area|pie|donut|scatter|table",
      "title": "Chart Title",
      "subtitle": "one-line insight from this chart",
      "xKey": "actual_column_name_from_schema",
      "yKeys": ["actual_column_name_from_schema"],
      "yLabels": ["Human Readable Label"],
      "groupKey": null,
      "data": [],
      "layout": "full|half",
      "colorScheme": "blue|green|amber|rose|violet|teal|multi",
      "showLegend": true,
      "showGrid": true,
      "stacked": false,
      "sortBy": "value_desc|value_asc|natural|null",
      "sql_query": "SQL query to populate this chart from the table"
    }
  ],

  "businessInsight": "2-3 sentence executive summary with specific numbers",

  "aiInsights": [
    "specific insight 1 with numbers",
    "specific insight 2 with numbers",
    "specific insight 3 with numbers"
  ],

  "anomalies": ["any unusual patterns"],
  "recommendations": ["actionable business recommendation"],

  "followUpSuggestions": [
    {"id": "f1", "label": "short label", "query": "full natural language query", "category": "drill_down|filter|compare"},
    {"id": "f2", "label": "short label", "query": "full query", "category": "drill_down"},
    {"id": "f3", "label": "short label", "query": "full query", "category": "compare"}
  ]
}

CRITICAL RULES:
- xKey and yKeys MUST use actual column names from the schema (snake_case)
- sql_query in each chart MUST be valid SQLite SQL using the actual table name
- KPI values should be calculated from the statistics provided
- Generate AT LEAST 3 charts and AT LEAST 3 KPIs
- Make insights SPECIFIC with real numbers from the data"""

    user = f"""TABLE NAME: {table_name}

SCHEMA:
{schema_string}

DATA PREVIEW (first 30 rows):
{data_preview}

BASIC STATISTICS:
{stats_summary}"""

    try:
        res = call_gemini(system, user, "json", 0.2)
        clean = res.strip().strip("`")
        if clean.startswith("json\n"):
            clean = clean[5:]
        return json.loads(clean)
    except Exception as e:
        return {"error": f"Gemini analysis failed: {str(e)}"}

