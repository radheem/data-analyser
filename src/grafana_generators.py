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

def generate_bar_chart_panel(id_num: int, title: str, sql: str, datasource_name: str = "BigQuery", grid_pos: dict = None) -> dict:
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
        "gridPos": grid_pos or {
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

def generate_line_chart_panel(id_num: int, title: str, sql: str, datasource_name: str = "BigQuery", grid_pos: dict = None) -> dict:
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
        "gridPos": grid_pos or {
            "h": 12,
            "w": 24,
            "x": 0,
            "y": 0
        },
        "transformations": [
            {
                "id": "convertFieldType",
                "options": {
                    "fields": {
                        "time": {
                            "destinationType": "time"
                        }
                    }
                }
            }
        ],
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

def generate_pie_chart_panel(id_num: int, title: str, sql: str, datasource_name: str = "BigQuery", grid_pos: dict = None) -> dict:
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
        "gridPos": grid_pos or {
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

def generate_table_panel(id_num: int, title: str, sql: str, datasource_name: str = "BigQuery", grid_pos: dict = None) -> dict:
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
        "gridPos": grid_pos or {
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

def calculate_next_grid_position(panels: list, width: str) -> dict:
    """Calculate the next panel's grid position based on the width requested ('half' or 'full')
    and existing panels layout.

    - 'half': w=12, h=8
    - 'full': w=24, h=8
    """
    w = 12 if width == "half" else 24
    h = 8

    # 1. If empty, place at the top left
    if not panels:
        return {"x": 0, "y": 0, "w": w, "h": h}

    # 2. Inspect the last panel
    last_panel = panels[-1]
    last_grid = last_panel.get("gridPos", {})
    last_x = last_grid.get("x", 0)
    last_y = last_grid.get("y", 0)
    last_w = last_grid.get("w", 24)
    last_h = last_grid.get("h", 12)

    # If the new panel is full-width, always start a new row below the last panel
    if w == 24:
        return {"x": 0, "y": last_y + last_h, "w": w, "h": h}

    # If the new panel is half-width, check if there is space on the same row next to the last panel
    # The left half is x=0, right half is x=12.
    if last_x == 0 and last_w == 12:
        # Last panel was on the left half and was half-width. Place next to it on the right half.
        return {"x": 12, "y": last_y, "w": w, "h": h}
    else:
        # Last panel was full-width, or on the right half. Start a new row.
        return {"x": 0, "y": last_y + last_h, "w": w, "h": h}
