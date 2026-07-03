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

def test_query_ads_success():
    """Test query_ads tool when valid SELECT is provided."""
    import src.server
    
    mock_client = MagicMock()
    mock_query_job = MagicMock()
    # Mocking rows returned
    mock_row = MagicMock()
    mock_row.items.return_value = [("ad_id", "CR123"), ("advertiser_name", "MOCK ADVERTISER")]
    mock_query_job.__iter__.return_value = [mock_row]
    mock_client.query.return_value = mock_query_job
    
    original_client = src.server.bq_client
    src.server.bq_client = mock_client
    
    try:
        result = src.server.query_ads("SELECT ad_id, advertiser_name FROM `creative_stats` LIMIT 10")
        data = json.loads(result)
        assert data["status"] == "success"
        assert len(data["rows"]) == 1
        assert data["rows"][0]["ad_id"] == "CR123"
        mock_client.query.assert_called_once()
        # Verify query had LIMIT 10 preserved
        called_sql = mock_client.query.call_args[0][0]
        assert "LIMIT 10" in called_sql
    finally:
        src.server.bq_client = original_client

def test_query_ads_non_select():
    """Test query_ads tool blocks non-SELECT queries."""
    import src.server
    
    result = src.server.query_ads("DELETE FROM `creative_stats` WHERE 1=1")
    data = json.loads(result)
    assert data["status"] == "error"
    assert "Only read-only SELECT" in data["message"]

def test_query_ads_injects_limit():
    """Test query_ads tool injects LIMIT if missing."""
    import src.server
    
    mock_client = MagicMock()
    mock_query_job = MagicMock()
    mock_query_job.__iter__.return_value = []
    mock_client.query.return_value = mock_query_job
    
    original_client = src.server.bq_client
    src.server.bq_client = mock_client
    
    try:
        src.server.query_ads("SELECT * FROM `creative_stats`")
        called_sql = mock_client.query.call_args[0][0]
        assert "LIMIT 100" in called_sql
    finally:
        src.server.bq_client = original_client

def test_get_top_advertisers_success():
    """Test get_top_advertisers tool executes correct query and parses output."""
    import src.server
    
    mock_client = MagicMock()
    mock_query_job = MagicMock()
    
    # Mocking rows returned with aggregated data
    mock_row = MagicMock()
    mock_row.items.return_value = [
        ("advertiser_name", "BIG SPENDER INC"),
        ("total_max_spend_usd", 1500000),
        ("total_min_spend_usd", 1000000),
        ("total_days_active", 450),
        ("ad_count", 250)
    ]
    mock_query_job.__iter__.return_value = [mock_row]
    mock_client.query.return_value = mock_query_job
    
    original_client = src.server.bq_client
    src.server.bq_client = mock_client
    
    try:
        result = src.server.get_top_advertisers(region="US", limit=5)
        data = json.loads(result)
        
        assert data["status"] == "success"
        assert len(data["advertisers"]) == 1
        assert data["advertisers"][0]["advertiser_name"] == "BIG SPENDER INC"
        # Verify range-based metric formatted as JSON object
        assert data["advertisers"][0]["spend_range_usd"]["min"] == 1000000
        assert data["advertisers"][0]["spend_range_usd"]["max"] == 1500000
        
        called_sql = mock_client.query.call_args[0][0]
        assert "SUM(spend_range_max_usd)" in called_sql
        assert "regions = 'US'" in called_sql
        assert "LIMIT 5" in called_sql
    finally:
        src.server.bq_client = original_client

def test_search_advertiser_ads_success():
    """Test search_advertiser_ads query building, filtering, and parsing."""
    import src.server
    
    mock_client = MagicMock()
    mock_query_job = MagicMock()
    
    mock_row = MagicMock()
    mock_row.items.return_value = [
        ("ad_id", "CR999"),
        ("ad_type", "VIDEO"),
        ("regions", "US"),
        ("advertiser_name", "HARRIS FOR PRESIDENT"),
        ("impressions", "10000-50000"),
        ("spend_range_min_usd", 1000),
        ("spend_range_max_usd", 5000),
        ("date_range_start", "2024-01-01"),
        ("date_range_end", "2024-01-10")
    ]
    mock_query_job.__iter__.return_value = [mock_row]
    mock_client.query.return_value = mock_query_job
    
    original_client = src.server.bq_client
    src.server.bq_client = mock_client
    
    try:
        result = src.server.search_advertiser_ads(
            advertiser_name="HARRIS FOR PRESIDENT",
            limit=5,
            region="US",
            start_date="2024-01-01",
            end_date="2024-01-15",
            ad_type="VIDEO"
        )
        data = json.loads(result)
        
        assert data["status"] == "success"
        assert len(data["ads"]) == 1
        assert data["ads"][0]["ad_id"] == "CR999"
        
        # Verify spend & impression range formatting
        assert data["ads"][0]["spend_range_usd"]["min"] == 1000
        assert data["ads"][0]["spend_range_usd"]["max"] == 5000
        assert data["ads"][0]["impressions_range"]["min"] == 10000
        assert data["ads"][0]["impressions_range"]["max"] == 50000
        
        called_sql = mock_client.query.call_args[0][0]
        assert "advertiser_name LIKE '%HARRIS FOR PRESIDENT%'" in called_sql
        assert "regions = 'US'" in called_sql
        assert "date_range_start >= '2024-01-01'" in called_sql
        assert "date_range_end <= '2024-01-15'" in called_sql
        assert "ad_type = 'VIDEO'" in called_sql
    finally:
        src.server.bq_client = original_client

def test_search_advertiser_ads_validation_errors():
    """Test search_advertiser_ads blocks SQL injection and bad formats."""
    import src.server
    
    # We don't need a real client because validation runs first
    # 1. SQL injection in name
    result = src.server.search_advertiser_ads(advertiser_name="Name' OR 1=1")
    assert "Invalid character" in json.loads(result)["message"]
    
    # 2. SQL injection in region
    result = src.server.search_advertiser_ads(advertiser_name="Valid", region="US'")
    assert "Invalid character" in json.loads(result)["message"]
    
    # 3. Invalid start_date format
    result = src.server.search_advertiser_ads(advertiser_name="Valid", start_date="01-01-2024")
    assert "YYYY-MM-DD format" in json.loads(result)["message"]
    
    # 4. Invalid end_date format
    result = src.server.search_advertiser_ads(advertiser_name="Valid", end_date="2024/01/01")
    assert "YYYY-MM-DD format" in json.loads(result)["message"]
    
    # 5. SQL injection in ad_type
    result = src.server.search_advertiser_ads(advertiser_name="Valid", ad_type="VIDEO'")
    assert "Invalid character" in json.loads(result)["message"]

def test_parse_impressions_range():
    """Test _parse_impressions_range helper parses all formatted inputs correctly."""
    from src.server import _parse_impressions_range
    
    # Empty cases
    assert _parse_impressions_range(None) == {"min": None, "max": None}
    assert _parse_impressions_range("") == {"min": None, "max": None}
    
    # Less than / Less than or equal
    assert _parse_impressions_range("≤ 10,000") == {"min": 0, "max": 10000}
    assert _parse_impressions_range("<= 5,000") == {"min": 0, "max": 5000}
    
    # Greater than / plus
    assert _parse_impressions_range("≥ 1,000,000") == {"min": 1000000, "max": None}
    assert _parse_impressions_range(">= 5000") == {"min": 5000, "max": None}
    assert _parse_impressions_range("250000+") == {"min": 250000, "max": None}
    
    # Ranges
    assert _parse_impressions_range("10000-50000") == {"min": 10000, "max": 50000}
    assert _parse_impressions_range("abc-def") == {"min": None, "max": None}
    
    # Single numbers / fallbacks
    assert _parse_impressions_range("10000") == {"min": 10000, "max": 10000}
    assert _parse_impressions_range("no digits here") == {"min": None, "max": None}

@patch("requests.post")
def test_create_grafana_dashboard_success(mock_post):
    """Test create_grafana_dashboard tool on successful POST to Grafana API."""
    import src.server
    
    # Mock requests.post response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "success",
        "url": "/d/test-uid/test-slug",
        "uid": "test-uid"
    }
    mock_post.return_value = mock_response
    
    # Mock BigQuery client to bypass pre-flight
    mock_client = MagicMock()
    mock_query_job = MagicMock()
    mock_query_job.__iter__.return_value = [{"col": 1}]
    mock_client.query.return_value = mock_query_job
    
    original_client = src.server.bq_client
    src.server.bq_client = mock_client
    
    try:
        # Call the tool (SQL, chart_type, title)
        result = src.server.create_grafana_dashboard(
            sql="SELECT * FROM `creative_stats` LIMIT 10",
            chart_type="barchart",
            title="My Test Dashboard"
        )
        
        data = json.loads(result)
        assert data["status"] == "success"
        assert "http://localhost:3000/d/test-uid/test-slug" in data["dashboard_url"]
        
        # Verify post is called with expected payload
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "/api/dashboards/db" in args[0]
        assert "dashboard" in kwargs["json"]
        assert kwargs["json"]["dashboard"]["title"] == "My Test Dashboard"
        assert kwargs["json"]["dashboard"]["panels"][0]["type"] == "barchart"
        
    finally:
        src.server.bq_client = original_client

@patch("requests.post")
def test_create_grafana_dashboard_preflight_failure(mock_post):
    """Test create_grafana_dashboard tool aborts and returns error if pre-flight query fails."""
    import src.server
    
    # Mock BigQuery client to raise exception on query execution
    mock_client = MagicMock()
    mock_client.query.side_effect = Exception("BigQuery SQL syntax error.")
    
    original_client = src.server.bq_client
    src.server.bq_client = mock_client
    
    try:
        result = src.server.create_grafana_dashboard(
            sql="SELECT INVALID_COLUMN FROM `creative_stats`",
            chart_type="barchart",
            title="My Bad Dashboard"
        )
        
        data = json.loads(result)
        assert data["status"] == "error"
        assert "BigQuery SQL syntax error" in data["message"]
        
        # Verify requests.post was NEVER called (aborted early!)
        mock_post.assert_not_called()
        
    finally:
        src.server.bq_client = original_client

@patch("requests.post")
@patch("src.grafana_generators.generate_bar_chart_panel")
def test_create_grafana_dashboard_fallback_to_table(mock_gen_bar, mock_post):
    """Test create_grafana_dashboard tool falls back to a table panel if chart generation fails."""
    import src.server
    
    # Mock the bar chart panel generator to raise an error
    mock_gen_bar.side_effect = Exception("Mocked generation failure.")
    
    # Mock requests.post response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "success",
        "url": "/d/test-uid/test-slug",
        "uid": "test-uid"
    }
    mock_post.return_value = mock_response
    
    # Mock BigQuery client to bypass pre-flight
    mock_client = MagicMock()
    mock_query_job = MagicMock()
    mock_query_job.__iter__.return_value = [{"col": 1}]
    mock_client.query.return_value = mock_query_job
    
    original_client = src.server.bq_client
    src.server.bq_client = mock_client
    
    try:
        result = src.server.create_grafana_dashboard(
            sql="SELECT * FROM `creative_stats` LIMIT 10",
            chart_type="barchart",
            title="My Fallback Dashboard"
        )
        
        data = json.loads(result)
        assert data["status"] == "success"
        assert data["resolved_chart_type"] == "table"
        
        # Verify post is called with table type
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["dashboard"]["panels"][0]["type"] == "table"
        
    finally:
        src.server.bq_client = original_client

@patch("os.path.exists")
def test_setup_grafana_datasource(mock_exists):
    """Test setup_grafana_datasource parses credentials and writes provisioning YAML."""
    from unittest.mock import mock_open
    import src.server
    
    # Mock both gcp-creds.json and provisioning directory to exist
    mock_exists.side_effect = lambda path: True
    
    m_open = mock_open(read_data='{"client_email": "test@gcp.com", "project_id": "test-project", "private_key": "-----BEGIN PRIVATE KEY-----"}')
    with patch("builtins.open", m_open):
        src.server.setup_grafana_datasource()
        
    # Verify open was called to write the yaml file and the pem file
    m_open.assert_any_call("deploy/grafana/provisioning/datasources/bigquery.yaml", "w")
    m_open.assert_any_call("deploy/grafana/google-key.pem", "w")
    write_args = [call[0][0] for call in m_open().write.call_args_list]
    joined_writes = "".join(write_args)
    assert "clientEmail: test@gcp.com" in joined_writes
    assert "defaultProject: test-project" in joined_writes
    assert "-----BEGIN PRIVATE KEY-----" in joined_writes

@patch("requests.post")
def test_create_grafana_dashboard_sql_rewriter(mock_post):
    """Test create_grafana_dashboard tool automatically rewrites DATE as time to TIMESTAMP."""
    import src.server
    
    # Mock requests.post response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "success",
        "url": "/d/test-uid/test-slug",
        "uid": "test-uid"
    }
    mock_post.return_value = mock_response
    
    # Mock BigQuery client to bypass pre-flight
    mock_client = MagicMock()
    mock_query_job = MagicMock()
    mock_query_job.__iter__.return_value = [{"col": 1}]
    mock_client.query.return_value = mock_query_job
    
    original_client = src.server.bq_client
    src.server.bq_client = mock_client
    
    try:
        src.server.create_grafana_dashboard(
            sql="SELECT date_range_start as time FROM `creative_stats`",
            chart_type="timeseries",
            title="Rewrite Test"
        )
        
        # Verify post is called with rewritten SQL
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        raw_sql = kwargs["json"]["dashboard"]["panels"][0]["targets"][0]["rawSql"]
        assert "TIMESTAMP(date_range_start) as time" in raw_sql
        
    finally:
        src.server.bq_client = original_client


