def generate_base_dashboard(uid: str, title: str, panels: list = None) -> dict:
    """Generate the base Grafana dashboard JSON structure."""
    if panels is None:
        panels = []
        
    return {
        "id": None,
        "uid": uid,
        "title": title,
        "tags": ["political-ads", "mcp-generated"],
        "timezone": "browser",
        "schemaVersion": 39,
        "version": 1,
        "refresh": "1m",
        "panels": panels
    }

def _get_datasource_ref(datasource_name: str = "BigQuery") -> dict:
    """Helper to return the standard BigQuery datasource object for Grafana panels."""
    return {
        "type": "grafana-bigquery-datasource",
        "uid": datasource_name
    }

def generate_bar_chart_panel(id_num: int, title: str, sql: str, datasource_name: str = "BigQuery") -> dict:
    """Generate a Grafana Bar Chart panel JSON."""
    return {
        "id": id_num,
        "type": "barchart",
        "title": title,
        "datasource": _get_datasource_ref(datasource_name),
        "targets": [
            {
                "format": "table",
                "rawSql": sql,
                "refId": "A"
            }
        ],
        "gridPos": {
            "h": 12,
            "w": 24,
            "x": 0,
            "y": 0
        },
        "options": {
            "orientation": "auto",
            "barRadius": 0,
            "barWidth": 0.97,
            "groupWidth": 0.7,
            "showValue": "auto",
            "stacking": "none",
            "xTickLabelRotation": -45,
            "xTickLabelMaxLength": 25,
            "tooltip": { "mode": "single", "sort": "none" },
            "legend": { "displayMode": "list", "placement": "bottom", "calcs": [] }
        }
    }

def generate_line_chart_panel(id_num: int, title: str, sql: str, datasource_name: str = "BigQuery") -> dict:
    """Generate a Grafana Line Chart (timeseries) panel JSON."""
    return {
        "id": id_num,
        "type": "timeseries",
        "title": title,
        "datasource": _get_datasource_ref(datasource_name),
        "targets": [
            {
                "format": "table",
                "rawSql": sql,
                "refId": "A"
            }
        ],
        "gridPos": {
            "h": 12,
            "w": 24,
            "x": 0,
            "y": 0
        },
        "fieldConfig": {
            "defaults": {
                "custom": {
                    "drawStyle": "line",
                    "lineInterpolation": "linear",
                    "barAlignment": 0,
                    "lineWidth": 2,
                    "fillOpacity": 10,
                    "gradientMode": "none"
                },
                "color": { "mode": "palette-classic" },
                "unit": "short"
            }
        },
        "options": {
            "tooltip": { "mode": "single", "sort": "none" },
            "legend": { "displayMode": "list", "placement": "bottom", "calcs": [] }
        }
    }

def generate_pie_chart_panel(id_num: int, title: str, sql: str, datasource_name: str = "BigQuery") -> dict:
    """Generate a Grafana Pie Chart panel JSON."""
    return {
        "id": id_num,
        "type": "piechart",
        "title": title,
        "datasource": _get_datasource_ref(datasource_name),
        "targets": [
            {
                "format": "table",
                "rawSql": sql,
                "refId": "A"
            }
        ],
        "gridPos": {
            "h": 12,
            "w": 24,
            "x": 0,
            "y": 0
        },
        "options": {
            "reduceOptions": {
                "values": False,
                "calcs": ["lastNotNull"],
                "fields": ""
            },
            "pieType": "pie",
            "tooltip": { "mode": "single", "sort": "none" },
            "legend": { "displayMode": "list", "placement": "bottom", "calcs": [] }
        }
    }

def generate_table_panel(id_num: int, title: str, sql: str, datasource_name: str = "BigQuery") -> dict:
    """Generate a Grafana Table panel JSON."""
    return {
        "id": id_num,
        "type": "table",
        "title": title,
        "datasource": _get_datasource_ref(datasource_name),
        "targets": [
            {
                "format": "table",
                "rawSql": sql,
                "refId": "A"
            }
        ],
        "gridPos": {
            "h": 12,
            "w": 24,
            "x": 0,
            "y": 0
        },
        "options": {
            "showHeader": True,
            "footer": {
                "show": False,
                "reducer": ["sum"],
                "fields": []
            }
        }
    }
