import pytest
import json
from unittest.mock import patch, MagicMock
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

