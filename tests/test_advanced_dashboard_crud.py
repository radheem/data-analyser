import pytest
import json
from unittest.mock import patch, MagicMock, mock_open
import src.server

def test_list_grafana_dashboards_success():
    """Test list_grafana_dashboards successfully returns dashboards with mcp-generated tag."""
    # This test will initially fail because list_grafana_dashboards does not exist yet.
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [
        {
            "uid": "abc123xyz789",
            "title": "Test Multi-Chart Dashboard",
            "url": "/d/abc123xyz789/test-multi-chart-dashboard",
            "type": "dash-db",
            "tags": ["political-ads", "mcp-generated"]
        }
    ]
    
    with patch("requests.get", return_value=mock_response) as mock_get:
        result = src.server.list_grafana_dashboards()
        data = json.loads(result)
        
        assert data["status"] == "success"
        assert len(data["dashboards"]) == 1
        assert data["dashboards"][0]["uid"] == "abc123xyz789"
        assert "test-multi-chart-dashboard" in data["dashboards"][0]["url"]
        mock_get.assert_called_once()

def test_get_grafana_dashboard_success():
    """Test get_grafana_dashboard successfully retrieves raw JSON of a dashboard."""
    # This test will initially fail because get_grafana_dashboard does not exist yet.
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "dashboard": {
            "uid": "abc123xyz789",
            "title": "Test Dashboard Model",
            "panels": []
        },
        "meta": {}
    }
    
    with patch("requests.get", return_value=mock_response) as mock_get:
        result = src.server.get_grafana_dashboard("abc123xyz789")
        data = json.loads(result)
        
        assert data["status"] == "success"
        assert data["dashboard"]["uid"] == "abc123xyz789"
        assert data["dashboard"]["title"] == "Test Dashboard Model"
        mock_get.assert_called_once()

def test_update_dashboard_success():
    """Test update_dashboard successfully updates title and refresh interval."""
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = {
        "dashboard": {
            "uid": "abc123xyz789",
            "title": "Old Title",
            "refresh": "1m",
            "tags": ["mcp-generated"],
            "panels": []
        }
    }
    
    mock_post_response = MagicMock()
    mock_post_response.status_code = 200
    mock_post_response.json.return_value = {
        "uid": "abc123xyz789",
        "url": "/d/abc123xyz789/new-title",
        "status": "success"
    }
    
    with patch("requests.get", return_value=mock_get_response) as mock_get, \
         patch("requests.post", return_value=mock_post_response) as mock_post:
         
        result = src.server.update_dashboard(uid="abc123xyz789", title="New Title", refresh="5s")
        data = json.loads(result)
        
        assert data["status"] == "success"
        assert "New Title" in data["message"]
        
        # Verify get was called to fetch the original
        mock_get.assert_called_once()
        # Verify post was called to update
        mock_post.assert_called_once()
        post_payload = mock_post.call_args[1]["json"]
        assert post_payload["dashboard"]["title"] == "New Title"
        assert post_payload["dashboard"]["refresh"] == "5s"

def test_delete_grafana_dashboard_success():
    """Test delete_grafana_dashboard successfully deletes dashboard with 'mcp-generated' tag."""
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = {
        "dashboard": {
            "uid": "abc123xyz789",
            "title": "Delete Me",
            "tags": ["political-ads", "mcp-generated"]
        }
    }
    
    mock_delete_response = MagicMock()
    mock_delete_response.status_code = 200
    mock_delete_response.json.return_value = {
        "message": "Dashboard Delete Me deleted"
    }
    
    with patch("requests.get", return_value=mock_get_response) as mock_get, \
         patch("requests.delete", return_value=mock_delete_response) as mock_delete:
         
        result = src.server.delete_grafana_dashboard("abc123xyz789")
        data = json.loads(result)
        
        assert data["status"] == "success"
        assert "deleted successfully" in data["message"]
        mock_get.assert_called_once()
        mock_delete.assert_called_once()

def test_delete_grafana_dashboard_fails_without_tag():
    """Test delete_grafana_dashboard raises safety error if 'mcp-generated' tag is missing."""
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = {
        "dashboard": {
            "uid": "abc123xyz789",
            "title": "User Dashboard",
            "tags": ["important", "not-mcp-generated"]
        }
    }
    
    with patch("requests.get", return_value=mock_get_response) as mock_get, \
         patch("requests.delete") as mock_delete:
         
        result = src.server.delete_grafana_dashboard("abc123xyz789")
        data = json.loads(result)
        
        assert data["status"] == "error"
        assert "Safety Protection" in data["message"]
        mock_get.assert_called_once()
        mock_delete.assert_not_called()

def test_create_multi_chart_dashboard_success():
    """Test create_multi_chart_dashboard successfully validates and deploys a multi-panel dashboard."""
    mock_post_response = MagicMock()
    mock_post_response.status_code = 200
    mock_post_response.json.return_value = {
        "uid": "multi123xyz7",
        "url": "/d/multi123xyz7/multi-test",
        "status": "success"
    }
    
    charts = [
        {"title": "Chart One", "sql": "SELECT 1", "chart_type": "barchart", "width": "half"},
        {"title": "Chart Two", "sql": "SELECT 2", "chart_type": "timeseries", "width": "full"}
    ]
    
    with patch("requests.post", return_value=mock_post_response) as mock_post, \
         patch("src.server.bq_client") as mock_bq:
         
        # Simulate successful BigQuery pre-flight query run
        mock_bq.query.return_value = MagicMock()
        
        result = src.server.create_multi_chart_dashboard("Multi Test", charts)
        data = json.loads(result)
        
        assert data["status"] == "success"
        assert data["uid"] == "19e22e0a7e1f"
        assert "Multi Test" in data["message"]
        
        mock_post.assert_called_once()
        post_payload = mock_post.call_args[1]["json"]
        panels = post_payload["dashboard"]["panels"]
        
        assert len(panels) == 2
        # Verify coordinates applied correctly
        assert panels[0]["title"] == "Chart One"
        assert panels[0]["gridPos"] == {"x": 0, "y": 0, "w": 12, "h": 8}
        
        assert panels[1]["title"] == "Chart Two"
        assert panels[1]["gridPos"] == {"x": 0, "y": 8, "w": 24, "h": 8}

def test_create_multi_chart_dashboard_sql_failure():
    """Test create_multi_chart_dashboard aborts immediately if any SQL pre-flight check fails."""
    charts = [
        {"title": "Good Chart", "sql": "SELECT 1", "chart_type": "barchart"},
        {"title": "Bad Chart", "sql": "SELECT * FROM invalid_table", "chart_type": "table"}
    ]
    
    with patch("requests.post") as mock_post, \
         patch("src.server.bq_client") as mock_bq:
         
        # Make the second query fail in pre-flight dry-run
        mock_bq.query.side_effect = [MagicMock(), Exception("Table not found")]
        
        result = src.server.create_multi_chart_dashboard("Atomic Abort Test", charts)
        data = json.loads(result)
        
        assert data["status"] == "error"
        assert "Pre-flight SQL Check Error" in data["message"]
        assert "Table not found" in data["message"]
        
        # Requests post should NEVER have been called due to abort
        mock_post.assert_not_called()

def test_add_chart_to_dashboard_success():
    """Test add_chart_to_dashboard retrieves, appends, and updates dashboard."""
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = {
        "dashboard": {
            "uid": "abc123xyz789",
            "title": "Existing Dash",
            "panels": [
                {
                    "id": 1,
                    "title": "Panel 1",
                    "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8}
                }
            ],
            "tags": ["mcp-generated"]
        }
    }
    
    mock_post_response = MagicMock()
    mock_post_response.status_code = 200
    mock_post_response.json.return_value = {
        "uid": "abc123xyz789",
        "url": "/d/abc123xyz789/existing-dash",
        "status": "success"
    }
    
    with patch("requests.get", return_value=mock_get_response) as mock_get, \
         patch("requests.post", return_value=mock_post_response) as mock_post, \
         patch("src.server.bq_client") as mock_bq:
         
        mock_bq.query.return_value = MagicMock()
        
        result = src.server.add_chart_to_dashboard(
            uid="abc123xyz789",
            chart_type="piechart",
            sql="SELECT 1",
            title="Panel 2",
            width="half"
        )
        data = json.loads(result)
        
        assert data["status"] == "success"
        mock_get.assert_called_once()
        mock_post.assert_called_once()
        
        post_payload = mock_post.call_args[1]["json"]
        panels = post_payload["dashboard"]["panels"]
        assert len(panels) == 2
        # Verify side-by-side positioning
        assert panels[1]["gridPos"] == {"x": 12, "y": 0, "w": 12, "h": 8}

def test_delete_chart_from_dashboard_success():
    """Test delete_chart_from_dashboard removes target panel and updates dashboard."""
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = {
        "dashboard": {
            "uid": "abc123xyz789",
            "title": "Delete Panel Dash",
            "panels": [
                {"id": 1, "title": "Good Panel"},
                {"id": 2, "title": "Dead Panel"}
            ],
            "tags": ["mcp-generated"]
        }
    }
    
    mock_post_response = MagicMock()
    mock_post_response.status_code = 200
    mock_post_response.json.return_value = {
        "uid": "abc123xyz789",
        "status": "success"
    }
    
    with patch("requests.get", return_value=mock_get_response) as mock_get, \
         patch("requests.post", return_value=mock_post_response) as mock_post:
         
        result = src.server.delete_chart_from_dashboard(uid="abc123xyz789", chart_id=2)
        data = json.loads(result)
        
        assert data["status"] == "success"
        mock_get.assert_called_once()
        mock_post.assert_called_once()
        
        post_payload = mock_post.call_args[1]["json"]
        panels = post_payload["dashboard"]["panels"]
        assert len(panels) == 1
        assert panels[0]["id"] == 1

def test_export_dashboard_json_success():
    """Test export_dashboard_json fetches the dashboard, strips internal IDs, and writes it to disk."""
    mock_get_response = MagicMock()
    mock_get_response.status_code = 200
    mock_get_response.json.return_value = {
        "dashboard": {
            "id": 42,
            "uid": "export123xyz",
            "title": "Export Dashboard",
            "version": 15,
            "panels": [
                {"id": 1, "title": "Chart 1"}
            ],
            "tags": ["mcp-generated"]
        }
    }
    
    with patch("requests.get", return_value=mock_get_response) as mock_get, \
         patch("builtins.open", mock_open()) as mock_file, \
         patch("os.makedirs") as mock_makedirs:
         
        result = src.server.export_dashboard_json("export123xyz")
        data = json.loads(result)
        
        assert data["status"] == "success"
        assert "export123xyz.json" in data["file_path"]
        
        mock_get.assert_called_once()
        mock_makedirs.assert_called_once()
        mock_file.assert_called_once()
        
        # Verify JSON written had top-level 'id' and 'version' stripped/normalized
        written_content = "".join([call.args[0] for call in mock_file().write.call_args_list])
        written_json = json.loads(written_content)
        
        assert written_json["id"] is None
        assert "version" not in written_json or written_json["version"] == 1



