import pytest
from unittest.mock import patch
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
