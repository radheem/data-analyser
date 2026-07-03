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
    panel = generate_bar_chart_panel(1, "Test Bar Chart", "SELECT * FROM test")
    assert panel["id"] == 1
    assert panel["type"] == "barchart"
    assert panel["title"] == "Test Bar Chart"
    assert panel["targets"][0]["rawSql"] == "SELECT * FROM test"
    assert panel["targets"][0]["format"] == "table"
    assert panel["options"]["xTickLabelRotation"] == -45
    assert panel["options"]["xTickLabelMaxLength"] == 25

def test_generate_line_chart_panel():
    panel = generate_line_chart_panel(2, "Test Line Chart", "SELECT * FROM test")
    assert panel["id"] == 2
    assert panel["type"] == "timeseries"
    assert panel["title"] == "Test Line Chart"
    assert panel["targets"][0]["rawSql"] == "SELECT * FROM test"
    assert panel["targets"][0]["format"] == "table"
    assert panel["transformations"][0]["id"] == "convertFieldType"
    assert panel["transformations"][0]["options"]["fields"]["time"]["destinationType"] == "time"

def test_generate_pie_chart_panel():
    panel = generate_pie_chart_panel(3, "Test Pie Chart", "SELECT * FROM test")
    assert panel["id"] == 3
    assert panel["type"] == "piechart"
    assert panel["title"] == "Test Pie Chart"
    assert panel["targets"][0]["rawSql"] == "SELECT * FROM test"
    assert panel["targets"][0]["format"] == "table"

def test_generate_table_panel():
    panel = generate_table_panel(4, "Test Table", "SELECT * FROM test")
    assert panel["id"] == 4
    assert panel["type"] == "table"
    assert panel["title"] == "Test Table"
    assert panel["targets"][0]["rawSql"] == "SELECT * FROM test"
    assert panel["targets"][0]["format"] == "table"
