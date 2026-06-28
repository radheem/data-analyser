import pytest
from src.server import mcp

def test_mcp_instance():
    """Test that the FastMCP instance is correctly initialized with the expected name."""
    assert mcp.name == "political-ads-mcp"
