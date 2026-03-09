import os
import json
import sqlite3
import pandas as pd
import numpy as np
from database import execute_query
from dataset_loader import DB_PATH


def auto_analyze_csv(table_name: str, df: pd.DataFrame) -> dict:
    """
    Fully autonomous dataset analyzer.
    Takes a DataFrame loaded from CSV and produces a complete analysis result
    including schema detection, feature classification, relationship detection,
    summary statistics, and pre-generated chart specifications.
    """

    # ═══════════════════════════════════════════
    # STEP 1: Schema Detection
    # ═══════════════════════════════════════════
    total_rows = len(df)
    total_cols = len(df.columns)

    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
    bool_columns = df.select_dtypes(include=['bool']).columns.tolist()

    # Detect date columns (try parsing object columns as dates)
    date_columns = []
    for col in df.select_dtypes(include=['datetime64']).columns.tolist():
        date_columns.append(col)

    for col in categorical_columns[:]:
        sample = df[col].dropna().head(20)
        try:
            parsed = pd.to_datetime(sample, infer_datetime_format=True, errors='coerce')
            if parsed.notna().sum() > len(sample) * 0.7:
                date_columns.append(col)
                categorical_columns.remove(col)
                # Convert the column
                df[col] = pd.to_datetime(df[col], errors='coerce')
        except:
            pass

    # Filter out ID-like columns from categoricals (high cardinality)
    id_columns = []
    true_categoricals = []
    for col in categorical_columns:
        nunique = df[col].nunique()
        if nunique > total_rows * 0.8 or nunique > 200:
            id_columns.append(col)
        else:
            true_categoricals.append(col)

    # ═══════════════════════════════════════════
    # STEP 2: Feature Classification
    # ═══════════════════════════════════════════
    metrics = []  # Numeric columns good for aggregation
    dimensions = []  # Categorical columns good for grouping

    for col in numeric_columns:
        col_data = df[col].dropna()
        if len(col_data) == 0:
            continue
        # Skip columns that look like IDs (sequential integers with high cardinality)
        if col_data.nunique() > total_rows * 0.8 and col_data.dtype in ['int64', 'int32']:
            id_columns.append(col)
            continue
        metrics.append({
            "name": col,
            "min": round(float(col_data.min()), 2),
            "max": round(float(col_data.max()), 2),
            "mean": round(float(col_data.mean()), 2),
            "median": round(float(col_data.median()), 2),
            "std": round(float(col_data.std()), 2) if len(col_data) > 1 else 0,
            "sum": round(float(col_data.sum()), 2),
            "null_count": int(df[col].isna().sum())
        })

    for col in true_categoricals:
        col_data = df[col].dropna()
        if len(col_data) == 0:
            continue
        top_values = col_data.value_counts().head(10)
        dimensions.append({
            "name": col,
            "unique_count": int(col_data.nunique()),
            "top_values": {str(k): int(v) for k, v in top_values.items()},
            "null_count": int(df[col].isna().sum())
        })

    # ═══════════════════════════════════════════
    # STEP 3: Relationship Detection
    # ═══════════════════════════════════════════
    correlations = []
    metric_names = [m["name"] for m in metrics]
    if len(metric_names) >= 2:
        corr_matrix = df[metric_names].corr()
        for i in range(len(metric_names)):
            for j in range(i + 1, len(metric_names)):
                corr_val = corr_matrix.iloc[i, j]
                if not np.isnan(corr_val) and abs(corr_val) > 0.3:
                    correlations.append({
                        "col1": metric_names[i],
                        "col2": metric_names[j],
                        "correlation": round(float(corr_val), 3),
                        "strength": "strong" if abs(corr_val) > 0.7 else "moderate"
                    })

    # Top/bottom detection per metric per dimension
    top_performers = []
    for dim in dimensions[:3]:  # Limit to first 3 dimensions
        for met in metrics[:3]:  # Limit to first 3 metrics
            try:
                grouped = df.groupby(dim["name"])[met["name"]].sum().sort_values(ascending=False)
                if len(grouped) >= 2:
                    top_performers.append({
                        "dimension": dim["name"],
                        "metric": met["name"],
                        "top": str(grouped.index[0]),
                        "top_value": round(float(grouped.iloc[0]), 2),
                        "bottom": str(grouped.index[-1]),
                        "bottom_value": round(float(grouped.iloc[-1]), 2)
                    })
            except:
                pass

    # Anomaly detection (simple z-score based)
    anomalies = []
    for met in metrics[:5]:
        col_data = df[met["name"]].dropna()
        if len(col_data) < 10:
            continue
        mean_val = col_data.mean()
        std_val = col_data.std()
        if std_val > 0:
            z_scores = ((col_data - mean_val) / std_val).abs()
            outlier_count = int((z_scores > 2).sum())
            if outlier_count > 0:
                anomalies.append({
                    "column": met["name"],
                    "outlier_count": outlier_count,
                    "pct_outliers": round(100 * outlier_count / len(col_data), 1),
                    "description": f"{outlier_count} values in '{met['name']}' are more than 2 standard deviations from the mean ({round(mean_val, 2)})"
                })

    # ═══════════════════════════════════════════
    # STEP 4: Auto-Generate Chart Specifications
    # ═══════════════════════════════════════════
    charts = []
    chart_id = 1

    # Chart 1: Overall summary bar chart (top dimension by top metric)
    if dimensions and metrics:
        dim = dimensions[0]
        met = metrics[0]
        try:
            agg_data = df.groupby(dim["name"])[met["name"]].sum().sort_values(ascending=False).head(15).reset_index()
            agg_data.columns = [dim["name"], met["name"]]
            charts.append({
                "id": f"chart_{chart_id}",
                "chartType": "bar",
                "title": f"{met['name'].replace('_', ' ').title()} by {dim['name'].replace('_', ' ').title()}",
                "subtitle": f"Top categories ranked by total {met['name'].replace('_', ' ')}",
                "xKey": dim["name"],
                "yKeys": [met["name"]],
                "yLabels": [met["name"].replace('_', ' ').title()],
                "data": agg_data.to_dict(orient="records"),
                "layout": "full",
                "colorScheme": "blue",
                "showLegend": False,
                "showGrid": True,
                "stacked": False,
                "sortBy": "value_desc"
            })
            chart_id += 1
        except:
            pass

    # Chart 2: Time trend (if date column exists)
    if date_columns and metrics:
        date_col = date_columns[0]
        met = metrics[0]
        try:
            df_copy = df.copy()
            df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
            df_copy = df_copy.dropna(subset=[date_col])
            df_copy['_month'] = df_copy[date_col].dt.strftime('%Y-%m')
            trend_data = df_copy.groupby('_month')[met["name"]].sum().reset_index()
            trend_data.columns = ['month', met["name"]]
            trend_data = trend_data.sort_values('month')
            if len(trend_data) >= 2:
                charts.append({
                    "id": f"chart_{chart_id}",
                    "chartType": "line",
                    "title": f"{met['name'].replace('_', ' ').title()} Trend Over Time",
                    "subtitle": f"Monthly trend of {met['name'].replace('_', ' ')}",
                    "xKey": "month",
                    "yKeys": [met["name"]],
                    "yLabels": [met["name"].replace('_', ' ').title()],
                    "data": trend_data.to_dict(orient="records"),
                    "layout": "half",
                    "colorScheme": "green",
                    "showLegend": False,
                    "showGrid": True,
                    "stacked": False,
                    "sortBy": "natural"
                })
                chart_id += 1
        except:
            pass

    # Chart 3: Pie/Donut chart (composition of top dimension)
    if dimensions and metrics:
        dim = dimensions[0]
        met = metrics[0]
        try:
            pie_data = df.groupby(dim["name"])[met["name"]].sum().sort_values(ascending=False).head(6).reset_index()
            pie_data.columns = [dim["name"], met["name"]]
            charts.append({
                "id": f"chart_{chart_id}",
                "chartType": "donut",
                "title": f"{met['name'].replace('_', ' ').title()} Share by {dim['name'].replace('_', ' ').title()}",
                "subtitle": f"Proportional breakdown (top 6)",
                "xKey": dim["name"],
                "yKeys": [met["name"]],
                "yLabels": [met["name"].replace('_', ' ').title()],
                "data": pie_data.to_dict(orient="records"),
                "layout": "half",
                "colorScheme": "multi",
                "showLegend": True,
                "showGrid": False,
                "stacked": False,
                "sortBy": "value_desc"
            })
            chart_id += 1
        except:
            pass

    # Chart 4: Second dimension comparison (if exists)
    if len(dimensions) >= 2 and metrics:
        dim2 = dimensions[1]
        met = metrics[0]
        try:
            agg_data2 = df.groupby(dim2["name"])[met["name"]].sum().sort_values(ascending=False).head(10).reset_index()
            agg_data2.columns = [dim2["name"], met["name"]]
            charts.append({
                "id": f"chart_{chart_id}",
                "chartType": "bar",
                "title": f"{met['name'].replace('_', ' ').title()} by {dim2['name'].replace('_', ' ').title()}",
                "subtitle": f"Comparison across {dim2['name'].replace('_', ' ')} categories",
                "xKey": dim2["name"],
                "yKeys": [met["name"]],
                "yLabels": [met["name"].replace('_', ' ').title()],
                "data": agg_data2.to_dict(orient="records"),
                "layout": "half",
                "colorScheme": "amber",
                "showLegend": False,
                "showGrid": True,
                "stacked": False,
                "sortBy": "value_desc"
            })
            chart_id += 1
        except:
            pass

    # Chart 5: Multi-metric comparison (if multiple metrics exist)
    if len(metrics) >= 2 and dimensions:
        dim = dimensions[0]
        met1 = metrics[0]
        met2 = metrics[1]
        try:
            multi_data = df.groupby(dim["name"])[[met1["name"], met2["name"]]].sum().sort_values(met1["name"], ascending=False).head(10).reset_index()
            charts.append({
                "id": f"chart_{chart_id}",
                "chartType": "bar",
                "title": f"{met1['name'].replace('_', ' ').title()} vs {met2['name'].replace('_', ' ').title()}",
                "subtitle": f"Two key metrics compared across {dim['name'].replace('_', ' ')}",
                "xKey": dim["name"],
                "yKeys": [met1["name"], met2["name"]],
                "yLabels": [met1["name"].replace('_', ' ').title(), met2["name"].replace('_', ' ').title()],
                "data": multi_data.to_dict(orient="records"),
                "layout": "full",
                "colorScheme": "multi",
                "showLegend": True,
                "showGrid": True,
                "stacked": False,
                "sortBy": "value_desc"
            })
            chart_id += 1
        except:
            pass

    # Chart 6: Data table (first 25 rows)
    if total_rows > 0:
        table_data = df.head(25).fillna("N/A")
        # Convert all values to string-safe
        for col in table_data.columns:
            table_data[col] = table_data[col].astype(str)
        charts.append({
            "id": f"chart_{chart_id}",
            "chartType": "table",
            "title": "Raw Data Preview",
            "subtitle": f"Showing first 25 of {total_rows} rows",
            "xKey": table_data.columns[0],
            "yKeys": [table_data.columns[0]],
            "yLabels": [table_data.columns[0]],
            "data": table_data.to_dict(orient="records"),
            "layout": "full",
            "colorScheme": "blue",
            "showLegend": False,
            "showGrid": True,
            "stacked": False,
            "sortBy": "natural"
        })
        chart_id += 1

    # ═══════════════════════════════════════════
    # STEP 5: Generate KPI Summary Stats
    # ═══════════════════════════════════════════
    summary_stats = []
    stat_icons = ["revenue", "users", "growth", "time", "quality", "inventory"]

    summary_stats.append({
        "id": "kpi_rows",
        "label": "Total Records",
        "value": f"{total_rows:,}",
        "rawValue": total_rows,
        "delta": None,
        "trend": "neutral",
        "icon": "users"
    })

    summary_stats.append({
        "id": "kpi_cols",
        "label": "Total Features",
        "value": str(total_cols),
        "rawValue": total_cols,
        "delta": f"{len(numeric_columns)} numeric, {len(true_categoricals)} categorical",
        "trend": "neutral",
        "icon": "inventory"
    })

    for i, met in enumerate(metrics[:4]):
        icon = stat_icons[min(i, len(stat_icons) - 1)]
        summary_stats.append({
            "id": f"kpi_{met['name']}",
            "label": f"Total {met['name'].replace('_', ' ').title()}",
            "value": _format_number(met["sum"]),
            "rawValue": met["sum"],
            "delta": f"Avg: {_format_number(met['mean'])}",
            "trend": "up" if met["mean"] > met["median"] else "neutral",
            "icon": icon
        })

    # ═══════════════════════════════════════════
    # STEP 6: Generate Insights
    # ═══════════════════════════════════════════
    insights = []

    # Top performers
    for tp in top_performers[:3]:
        insights.append(f"'{tp['top']}' leads in {tp['metric'].replace('_', ' ')} with a total of {_format_number(tp['top_value'])}, while '{tp['bottom']}' has the lowest at {_format_number(tp['bottom_value'])}.")

    # Correlations
    for corr in correlations[:2]:
        direction = "positive" if corr["correlation"] > 0 else "negative"
        insights.append(f"There is a {corr['strength']} {direction} correlation ({corr['correlation']}) between {corr['col1'].replace('_', ' ')} and {corr['col2'].replace('_', ' ')}.")

    # Anomalies
    for anom in anomalies[:2]:
        insights.append(f"Anomaly detected: {anom['description']}.")

    # Distribution info
    for met in metrics[:2]:
        if met["std"] > 0:
            cv = met["std"] / met["mean"] if met["mean"] != 0 else 0
            if cv > 1:
                insights.append(f"The '{met['name'].replace('_', ' ')}' column has high variability (CV = {round(cv, 2)}), indicating diverse values across records.")

    if not insights:
        insights.append(f"Dataset contains {total_rows} records across {total_cols} columns.")
        if metrics:
            insights.append(f"Primary metric '{metrics[0]['name']}' ranges from {_format_number(metrics[0]['min'])} to {_format_number(metrics[0]['max'])}.")

    # ═══════════════════════════════════════════
    # STEP 7: Suggested Follow-up Queries
    # ═══════════════════════════════════════════
    follow_ups = []
    if dimensions and metrics:
        follow_ups.append({"id": "f1", "label": f"Top {dimensions[0]['name']}", "query": f"Show top 10 {dimensions[0]['name']} by {metrics[0]['name']}", "category": "drill_down"})
    if date_columns and metrics:
        follow_ups.append({"id": "f2", "label": "Monthly Trend", "query": f"Show monthly trend of {metrics[0]['name']}", "category": "drill_down"})
    if len(metrics) >= 2:
        follow_ups.append({"id": "f3", "label": "Correlation View", "query": f"Show correlation between {metrics[0]['name']} and {metrics[1]['name']}", "category": "compare"})
    if len(dimensions) >= 2:
        follow_ups.append({"id": "f4", "label": f"Group by {dimensions[1]['name']}", "query": f"Show {metrics[0]['name'] if metrics else 'count'} by {dimensions[1]['name']}", "category": "drill_down"})

    # ═══════════════════════════════════════════
    # FINAL: Assemble complete dashboard
    # ═══════════════════════════════════════════
    return {
        "type": "dashboard",
        "dashboardTitle": f"AI Analysis: {table_name.replace('_', ' ').title()}",
        "domain": "custom",
        "routed_domain": "custom",
        "routed_domain_name": "Auto-Analyzed Dataset",
        "queryIntent": "distribution",

        "datasetSummary": {
            "total_rows": total_rows,
            "total_columns": total_cols,
            "numeric_features": [m["name"] for m in metrics],
            "categorical_features": [d["name"] for d in dimensions],
            "date_features": date_columns,
            "id_features": id_columns
        },

        "summaryStats": summary_stats,
        "charts": charts,

        "businessInsight": " | ".join(insights[:3]) if insights else "Dataset loaded successfully with no significant patterns detected.",
        "aiInsights": insights,
        "anomalies": [a["description"] for a in anomalies],
        "recommendations": [
            f"Focus analysis on '{metrics[0]['name']}' as it's the primary numeric metric." if metrics else "Add numeric columns for deeper analysis.",
            f"Group data by '{dimensions[0]['name']}' for the most meaningful categorical breakdown." if dimensions else "Add categorical columns for grouping analysis.",
        ],
        "correlations": correlations,
        "topPerformers": top_performers,

        "followUpSuggestions": follow_ups[:4],
        "sqlExecuted": f"SELECT * FROM {table_name} LIMIT 50",
        "rowsReturned": total_rows,
        "alerts": [{"message": a["description"], "severity": "warning"} for a in anomalies[:3]]
    }


def _format_number(val):
    """Format a number for display in KPIs."""
    if val is None:
        return "N/A"
    val = float(val)
    if abs(val) >= 1_000_000_000:
        return f"{val / 1_000_000_000:.1f}B"
    elif abs(val) >= 1_000_000:
        return f"{val / 1_000_000:.1f}M"
    elif abs(val) >= 1_000:
        return f"{val / 1_000:.1f}K"
    elif abs(val) < 1 and val != 0:
        return f"{val:.3f}"
    else:
        return f"{val:,.0f}"
