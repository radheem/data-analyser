import pytest
import json
from unittest.mock import patch, MagicMock
from src.server import mcp

def test_mcp_instance():
    """Test that the FastMCP instance is correctly initialized with the expected name."""
    assert mcp.name == "political-ads-mcp"

def test_bq_client_initialization():
    """Test that the BigQuery client is instantiated globally."""
    import src.server
    assert hasattr(src.server, "bq_client")

@patch("src.server.bigquery.Client")
def test_bq_client_auth_failure(mock_client, caplog):
    """Test fallback when DefaultCredentialsError is raised."""
    from google.auth.exceptions import DefaultCredentialsError
    import importlib
    import src.server
    
    mock_client.side_effect = DefaultCredentialsError("Mocked auth failure")
    
    # Reload the module to trigger the try/except block again
    importlib.reload(src.server)
    
    assert src.server.bq_client is None
    assert "Could not find default credentials" in caplog.text

def test_ping_bigquery_success():
    """Test ping_bigquery tool when client is available and query succeeds."""
    import src.server
    
    # Mock the bq_client and its query execution
    mock_client = MagicMock()
    mock_query_job = MagicMock()
    # Mocking row iteration to simulate `SELECT 1` returning a single row containing `1`
    mock_row = MagicMock()
    mock_row.__getitem__.return_value = 1
    mock_query_job.__iter__.return_value = [mock_row]
    mock_client.query.return_value = mock_query_job
    
    # Temporarily set the mock client
    original_client = src.server.bq_client
    src.server.bq_client = mock_client
    
    try:
        result = src.server.ping_bigquery()
        data = json.loads(result)
        assert data["status"] == "success"
        assert data["result"] == 1
        mock_client.query.assert_called_once_with("SELECT 1")
    finally:
        # Restore the original client
        src.server.bq_client = original_client

def test_ping_bigquery_uninitialized():
    """Test ping_bigquery tool when client failed to initialize."""
    import src.server
    
    original_client = src.server.bq_client
    src.server.bq_client = None
    
    try:
        result = src.server.ping_bigquery()
        data = json.loads(result)
        assert data["status"] == "error"
        assert "not initialized" in data["message"]
    finally:
        src.server.bq_client = original_client

def test_political_ads_ontology():
    """Test political_ads_ontology tool returning the expected schema details."""
    import src.server
    result = src.server.political_ads_ontology()
    data = json.loads(result)
    assert "table" in data
    assert "columns" in data["table"]
    assert "ad_id" in data["table"]["columns"]
