import pytest
from src.grafana_generators import (
    generate_base_dashboard,
    generate_bar_chart_panel,
    generate_line_chart_panel,
    generate_pie_chart_panel,
    generate_table_panel,
)

def test_generate_base_dashboard():
    uid = "test-dashboard"
    title = "Test Dashboard"
    dashboard = generate_base_dashboard(uid, title)
    
    assert dashboard["uid"] == uid
    assert dashboard["title"] == title
    assert dashboard["panels"] == []
    assert dashboard["schemaVersion"] >= 39

def test_generate_bar_chart_panel():
    panel = generate_bar_chart_panel(1, "Test Bar Chart", "SELECT * FROM test", unit="USD")
    assert panel["id"] == 1
    assert panel["type"] == "barchart"
    assert panel["title"] == "Test Bar Chart"
    assert panel["targets"][0]["rawSql"] == "SELECT * FROM test"
    assert panel["targets"][0]["format"] == "table"
    assert panel["options"]["xTickLabelRotation"] == -45
    assert panel["options"]["xTickLabelMaxLength"] == 25
    assert panel["fieldConfig"]["defaults"]["unit"] == "currencyUSD"

def test_generate_line_chart_panel():
    panel = generate_line_chart_panel(2, "Test Line Chart", "SELECT * FROM test", unit="EUR")
    assert panel["id"] == 2
    assert panel["type"] == "timeseries"
    assert panel["title"] == "Test Line Chart"
    assert panel["targets"][0]["rawSql"] == "SELECT * FROM test"
    assert panel["targets"][0]["format"] == "table"
    assert panel["transformations"][0]["id"] == "convertFieldType"
    assert panel["transformations"][0]["options"]["fields"]["time"]["destinationType"] == "time"
    assert panel["fieldConfig"]["defaults"]["unit"] == "currencyEUR"

def test_generate_pie_chart_panel():
    panel = generate_pie_chart_panel(3, "Test Pie Chart", "SELECT * FROM test", unit="percent")
    assert panel["id"] == 3
    assert panel["type"] == "piechart"
    assert panel["title"] == "Test Pie Chart"
    assert panel["targets"][0]["rawSql"] == "SELECT * FROM test"
    assert panel["targets"][0]["format"] == "table"
    assert panel["fieldConfig"]["defaults"]["unit"] == "percent"

def test_generate_table_panel():
    panel = generate_table_panel(4, "Test Table", "SELECT * FROM test")
    assert panel["id"] == 4
    assert panel["type"] == "table"
    assert panel["title"] == "Test Table"
    assert panel["targets"][0]["rawSql"] == "SELECT * FROM test"
    assert panel["targets"][0]["format"] == "table"

def test_generate_stat_panel():
    """Verify stat panel generator correctly packages single metric visualization with sparkline."""
    from src.grafana_generators import generate_stat_panel
    
    panel = generate_stat_panel(5, "Total Target Ads", "SELECT count(*) FROM stats", unit="GBP")
    assert panel["id"] == 5
    assert panel["type"] == "stat"
    assert panel["title"] == "Total Target Ads"
    assert panel["targets"][0]["rawSql"] == "SELECT count(*) FROM stats"
    assert panel["fieldConfig"]["defaults"]["unit"] == "currencyGBP"
    assert panel["options"]["graphMode"] == "area"  # Sparkline mode
    assert panel["options"]["textMode"] == "value"


def test_calculate_next_grid_position_empty():
    """Verify first panel placement for both half and full width."""
    from src.grafana_generators import calculate_next_grid_position
    
    # Empty panels list, adding "half"
    pos_half = calculate_next_grid_position([], "half")
    assert pos_half == {"x": 0, "y": 0, "w": 12, "h": 8}
    
    # Empty panels list, adding "full"
    pos_full = calculate_next_grid_position([], "full")
    assert pos_full == {"x": 0, "y": 0, "w": 24, "h": 8}

def test_calculate_next_grid_position_stacking():
    """Verify correct alignment and stacking with existing panels."""
    from src.grafana_generators import calculate_next_grid_position
    
    # 1. Existing half-width panel on the left (x:0, y:0, w:12, h:8)
    panels = [
        {"gridPos": {"x": 0, "y": 0, "w": 12, "h": 8}}
    ]
    # Adding another "half" should pair side-by-side on same row (x:12, y:0)
    pos = calculate_next_grid_position(panels, "half")
    assert pos == {"x": 12, "y": 0, "w": 12, "h": 8}
    
    # Adding a "full" should stack on a new row (x:0, y:8)
    pos = calculate_next_grid_position(panels, "full")
    assert pos == {"x": 0, "y": 8, "w": 24, "h": 8}
    
    # 2. Existing half-width panel on the right (x:12, y:0, w:12, h:8)
    panels = [
        {"gridPos": {"x": 0, "y": 0, "w": 12, "h": 8}},
        {"gridPos": {"x": 12, "y": 0, "w": 12, "h": 8}}
    ]
    # Adding "half" should start a new row (x:0, y:8)
    pos = calculate_next_grid_position(panels, "half")
    assert pos == {"x": 0, "y": 8, "w": 12, "h": 8}
    
    # 3. Existing full-width panel (x:0, y:0, w:24, h:8)
    panels = [
        {"gridPos": {"x": 0, "y": 0, "w": 24, "h": 8}}
    ]
    # Adding "half" should start a new row (x:0, y:8)
    pos = calculate_next_grid_position(panels, "half")
    assert pos == {"x": 0, "y": 8, "w": 12, "h": 8}

def test_normalize_grafana_unit():
    """Verify that normalize_grafana_unit correctly handles currencies and fallback strings."""
    from src.grafana_generators import normalize_grafana_unit
    
    # 1. Fallbacks & defaults
    assert normalize_grafana_unit(None) == "short"
    assert normalize_grafana_unit("") == "short"
    assert normalize_grafana_unit("  ") == "short"
    assert normalize_grafana_unit("short") == "short"
    
    # 2. ISO Currency 3-letter strings (case-insensitive)
    assert normalize_grafana_unit("USD") == "currencyUSD"
    assert normalize_grafana_unit("usd") == "currencyUSD"
    assert normalize_grafana_unit("EUR") == "currencyEUR"
    assert normalize_grafana_unit("eur") == "currencyEUR"
    assert normalize_grafana_unit("gbp") == "currencyGBP"
    assert normalize_grafana_unit("JPY") == "currencyJPY"
    
    # 3. Passthrough strings
    assert normalize_grafana_unit("percent") == "percent"
    assert normalize_grafana_unit("bytes") == "bytes"


