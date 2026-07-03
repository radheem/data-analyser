import os
import re
import json
import logging
import hashlib
import requests
from mcp.server.fastmcp import FastMCP
from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError
from src import grafana_generators

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("political-ads-mcp")

def setup_grafana_datasource():
    """Dynamically configure the Grafana BigQuery datasource by parsing gcp-creds.json."""
    creds_path = "gcp-creds.json"
    yaml_path = "deploy/grafana/provisioning/datasources/bigquery.yaml"
    pem_path = "deploy/grafana/google-key.pem"
    
    if os.path.exists(creds_path) and os.path.exists(os.path.dirname(yaml_path)):
        try:
            with open(creds_path, "r") as f:
                creds = json.load(f)
                
            client_email = creds.get("client_email")
            project_id = creds.get("project_id")
            private_key = creds.get("private_key")
            
            # Write the private key string to a raw PEM file for Grafana to read
            if private_key:
                with open(pem_path, "w") as fp:
                    fp.write(private_key)
                log.info("Successfully extracted PEM private key to local file.")
                
            if client_email and project_id:
                yaml_content = f"""apiVersion: 1

datasources:
  - name: BigQuery
    type: grafana-bigquery-datasource
    access: proxy
    isDefault: true
    jsonData:
      authenticationType: jwt
      clientEmail: {client_email}
      defaultProject: {project_id}
      tokenUri: https://oauth2.googleapis.com/token
      privateKeyPath: /etc/grafana/google-key.pem
    editable: true
"""
                with open(yaml_path, "w") as fy:
                    fy.write(yaml_content)
                log.info(f"Successfully auto-configured Grafana datasource for project '{project_id}' and client '{client_email}'.")
        except Exception as e:
            log.warning(f"Failed to auto-configure Grafana datasource: {e}")

setup_grafana_datasource()

# Instantiate the FastMCP server based on transport env
transport = os.environ.get("MCP_TRANSPORT", "stdio")
if transport == "sse":
    mcp = FastMCP("political-ads-mcp", host="0.0.0.0", port=5000)
else:
    mcp = FastMCP("political-ads-mcp")

# Initialize BigQuery client globally
try:
    bq_client = bigquery.Client()
    log.info("Successfully initialized BigQuery client.")
except DefaultCredentialsError:
    log.warning("Could not find default credentials. BigQuery client initialization failed. "
                "Ensure GOOGLE_APPLICATION_CREDENTIALS is set.")
    bq_client = None

@mcp.tool()
def ping_bigquery() -> str:
    """A simple health check tool to verify BigQuery connectivity.
    Executes a basic 'SELECT 1' query and returns the result."""
    if bq_client is None:
        return json.dumps({
            "status": "error",
            "message": "BigQuery client is not initialized. Check credentials."
        })
        
    try:
        query_job = bq_client.query("SELECT 1")
        # Fetch the first row and its first column value
        for row in query_job:
            val = row[0]
            return json.dumps({
                "status": "success",
                "result": val
            })
        return json.dumps({"status": "error", "message": "No rows returned."})
    except Exception as e:
        log.exception("Error executing ping_bigquery")
        return json.dumps({"status": "error", "message": str(e)})

@mcp.tool()
def political_ads_ontology() -> str:
    """Returns the schema description and ontology for the public Google political ads table.
    Use this to understand available fields, their types, and descriptions before querying."""
    ontology = {
        "table": {
            "name": "bigquery-public-data.google_political_ads.creative_stats",
            "description": "Google Ads transparency data tracking political/public interest ads.",
            "columns": {
                "ad_id": "STRING - Unique identifier for each ad.",
                "ad_url": "STRING - URL link to the ad on the Google Ads Transparency Center.",
                "ad_type": "STRING - Format of the ad (VIDEO, TEXT, IMAGE).",
                "regions": "STRING - General regions/countries where the ad served (e.g., US).",
                "advertiser_id": "STRING - Unique identifier for the paying advertiser.",
                "advertiser_name": "STRING - Public name of the advertiser (e.g., HARRIS FOR PRESIDENT).",
                "ad_campaigns_list": "STRING - Associated ad campaigns.",
                "date_range_start": "DATE - Calendar date when the ad first began serving.",
                "date_range_end": "DATE - Calendar date when the ad stopped serving.",
                "num_of_days": "INT64 - Total number of days active.",
                "first_served_timestamp": "TIMESTAMP - Precise Unix epoch timestamp when first displayed.",
                "last_served_timestamp": "TIMESTAMP - Precise Unix epoch timestamp when last displayed.",
                "impressions": "STRING - Approximate views, represented as a range (e.g., 100000-125000).",
                "spend_usd": "STRING - Exact spending on the ad in USD, if explicitly reported.",
                "age_targeting": "STRING - Target age demographics (e.g., 18-24, or a broader grouping).",
                "gender_targeting": "STRING - Target gender demographics (e.g., Male, Female, Unknown).",
                "geo_targeting_included": "STRING - Specific geographic areas where targeted to appear.",
                "geo_targeting_excluded": "STRING - Geographic areas explicitly excluded.",
                "is_funded_by_google_ad_grants": "BOOL - Whether ad campaign was funded using Google Ad Grants.",
                "spend_range_min_usd": "INT64 - Estimated lower bound of spend in USD.",
                "spend_range_max_usd": "INT64 - Estimated upper bound of spend in USD."
            }
        }
    }
    return json.dumps(ontology)

@mcp.tool()
def query_ads(sql: str) -> str:
    """Execute a read-only custom SQL query (SELECT / WITH) over the Google political ads dataset.
    Results are capped at a maximum of 100 rows.
    Example:
    - SELECT advertiser_name, SUM(spend_range_max_usd) FROM `bigquery-public-data.google_political_ads.creative_stats` GROUP BY advertiser_name LIMIT 10"""
    # Security/Safety check: strictly read-only
    clean_sql = sql.strip()
    if not clean_sql.upper().startswith("SELECT") and not clean_sql.upper().startswith("WITH"):
        return json.dumps({
            "status": "error",
            "message": "Security Error: Only read-only SELECT or WITH statements are allowed."
        })

    if bq_client is None:
        return json.dumps({
            "status": "error",
            "message": "BigQuery client is not initialized. Check credentials."
        })
        
    # Enforce LIMIT 100 to prevent cost/egress spikes
    if "LIMIT" not in clean_sql.upper():
        clean_sql += " LIMIT 100"
        
    try:
        query_job = bq_client.query(clean_sql)
        results = []
        for row in query_job:
            # Convert row mapping to dict
            row_dict = {}
            for key, val in row.items():
                # Handle dates and timestamps serialization
                if hasattr(val, "isoformat"):
                    row_dict[key] = val.isoformat()
                else:
                    row_dict[key] = val
            results.append(row_dict)
            
        return json.dumps({
            "status": "success",
            "rows": results
        })
    except Exception as e:
        log.exception(f"Error executing custom query: {clean_sql}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

@mcp.tool()
def get_top_advertisers(region: str = "US", limit: int = 10) -> str:
    """Get the highest spending political advertisers in a specific region.
    Returns the public names, total ad count, aggregated spend range in USD, and active days.
    Primary sorting is based on total maximum estimated USD spend."""
    if bq_client is None:
        return json.dumps({
            "status": "error",
            "message": "BigQuery client is not initialized. Check credentials."
        })
        
    sql = f"""
        SELECT 
            advertiser_name,
            SUM(spend_range_min_usd) as total_min_spend_usd,
            SUM(spend_range_max_usd) as total_max_spend_usd,
            SUM(num_of_days) as total_days_active,
            COUNT(*) as ad_count
        FROM `bigquery-public-data.google_political_ads.creative_stats`
        WHERE regions = '{region}'
        GROUP BY advertiser_name
        ORDER BY total_max_spend_usd DESC
        LIMIT {limit}
    """
    
    try:
        query_job = bq_client.query(sql)
        advertisers = []
        for row in query_job:
            # Construct row dict with custom formatting for ranges as JSON objects
            row_dict = {}
            for key, val in row.items():
                row_dict[key] = val
                
            # Create structured JSON objects for the min/max spend range
            spend_range = {
                "min": row_dict.get("total_min_spend_usd"),
                "max": row_dict.get("total_max_spend_usd")
            }
            
            advertisers.append({
                "advertiser_name": row_dict.get("advertiser_name"),
                "spend_range_usd": spend_range,
                "total_days_active": row_dict.get("total_days_active"),
                "ad_count": row_dict.get("ad_count")
            })
            
        return json.dumps({
            "status": "success",
            "region": region,
            "advertisers": advertisers
        })
    except Exception as e:
        log.exception(f"Error in get_top_advertisers: {str(e)}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

def _parse_impressions_range(impressions_str: str) -> dict:
    """Helper to parse raw impressions ranges like '10000-50000' or '≤ 10000' into min/max ints."""
    if not impressions_str:
        return {"min": None, "max": None}
        
    import re
    # Strip spaces and commas
    cleaned = impressions_str.replace(",", "").strip()
    
    # Handle '≤ 10000'
    if "≤" in cleaned or "<=" in cleaned:
        nums = re.findall(r"\d+", cleaned)
        if nums:
            return {"min": 0, "max": int(nums[0])}
            
    # Handle '≥ 1000000' or '1000000+'
    if "≥" in cleaned or ">=" in cleaned or "+" in cleaned:
        nums = re.findall(r"\d+", cleaned)
        if nums:
            return {"min": int(nums[0]), "max": None}
            
    # Handle standard range '10000-50000'
    parts = cleaned.split("-")
    if len(parts) == 2:
        try:
            return {"min": int(parts[0]), "max": int(parts[1])}
        except ValueError:
            pass
            
    # Fallback to general digit extraction
    nums = re.findall(r"\d+", cleaned)
    if len(nums) == 2:
        return {"min": int(nums[0]), "max": int(nums[1])}
    elif len(nums) == 1:
        return {"min": int(nums[0]), "max": int(nums[0])}
        
    return {"min": None, "max": None}

@mcp.tool()
def search_advertiser_ads(
    advertiser_name: str,
    limit: int = 10,
    region: str = None,
    start_date: str = None,
    end_date: str = None,
    ad_type: str = None
) -> str:
    """Search for political advertisements by advertiser name with optional filters.
    Supports filtering by region (e.g. US), date ranges, and ad format (VIDEO, TEXT, IMAGE).
    Spend and impression bounds are parsed and returned as structured JSON objects."""
    # Standard security check for sql injection on string parameters
    if "'" in advertiser_name:
        return json.dumps({"status": "error", "message": "Invalid character in advertiser_name."})
        
    if region:
        if "'" in region:
            return json.dumps({"status": "error", "message": "Invalid character in region."})
            
    if start_date:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", start_date):
            return json.dumps({"status": "error", "message": "start_date must be in YYYY-MM-DD format."})
            
    if end_date:
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", end_date):
            return json.dumps({"status": "error", "message": "end_date must be in YYYY-MM-DD format."})
            
    if ad_type:
        if "'" in ad_type:
            return json.dumps({"status": "error", "message": "Invalid character in ad_type."})

    if bq_client is None:
        return json.dumps({
            "status": "error",
            "message": "BigQuery client is not initialized. Check credentials."
        })
        
    conditions = [f"advertiser_name LIKE '%{advertiser_name}%'"]
    
    if region:
        conditions.append(f"regions = '{region}'")
        
    if start_date:
        conditions.append(f"date_range_start >= '{start_date}'")
        
    if end_date:
        conditions.append(f"date_range_end <= '{end_date}'")
        
    if ad_type:
        conditions.append(f"ad_type = '{ad_type}'")
        
    where_clause = " AND ".join(conditions)
    
    sql = f"""
        SELECT 
            ad_id,
            ad_url,
            ad_type,
            regions,
            advertiser_name,
            impressions,
            spend_range_min_usd,
            spend_range_max_usd,
            date_range_start,
            date_range_end,
            num_of_days
        FROM `bigquery-public-data.google_political_ads.creative_stats`
        WHERE {where_clause}
        ORDER BY date_range_start DESC
        LIMIT {limit}
    """
    
    try:
        query_job = bq_client.query(sql)
        ads = []
        for row in query_job:
            row_dict = {}
            for key, val in row.items():
                if hasattr(val, "isoformat"):
                    row_dict[key] = val.isoformat()
                else:
                    row_dict[key] = val
                    
            # Parse ranges as JSON objects
            spend_range = {
                "min": row_dict.get("spend_range_min_usd"),
                "max": row_dict.get("spend_range_max_usd")
            }
            impressions_range = _parse_impressions_range(row_dict.get("impressions"))
            
            ads.append({
                "ad_id": row_dict.get("ad_id"),
                "ad_url": row_dict.get("ad_url"),
                "ad_type": row_dict.get("ad_type"),
                "regions": row_dict.get("regions"),
                "advertiser_name": row_dict.get("advertiser_name"),
                "spend_range_usd": spend_range,
                "impressions_range": impressions_range,
                "date_range_start": row_dict.get("date_range_start"),
                "date_range_end": row_dict.get("date_range_end"),
                "num_of_days": row_dict.get("num_of_days")
            })
            
        return json.dumps({
            "status": "success",
            "count": len(ads),
            "ads": ads
        })
    except Exception as e:
        log.exception(f"Error searching advertiser ads: {sql}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

@mcp.tool()
def create_grafana_dashboard(sql: str, chart_type: str, title: str) -> str:
    """Create a resilient Grafana dashboard containing a single panel of the specified chart type.
    
    Supported chart types:
    - 'barchart': For comparing categorical data (e.g. spending by advertiser)
    - 'timeseries': For time-based trends (e.g. daily spending)
    - 'piechart': For proportional or distribution data
    - 'table': For raw data lists
    
    Returns a JSON string containing the status, dashboard UID, and a direct URL to the created dashboard."""
    # Ensure SQL is SELECT/WITH
    clean_sql = sql.strip()
    if not clean_sql.upper().startswith("SELECT") and not clean_sql.upper().startswith("WITH"):
        return json.dumps({
            "status": "error",
            "message": "Security Error: Only read-only SELECT or WITH statements are allowed."
        })
        
    # Pre-emptively rewrite raw DATE columns aliased as 'time' to TIMESTAMP(column)
    # so that BigQuery returns a true TIMESTAMP, which Grafana natively recognizes on its time axis.
    clean_sql = re.sub(r"\b(date_range_start|date_range_end)\s+as\s+time\b", r"TIMESTAMP(\1) as time", clean_sql, flags=re.IGNORECASE)
    
    # Pre-flight query execution check (using BigQuery dry_run to validate syntax/columns for $0 cost)
    if bq_client is not None:
        try:
            job_config = bigquery.QueryJobConfig(dry_run=True, use_query_cache=False)
            bq_client.query(clean_sql, job_config=job_config)
        except Exception as bq_err:
            log.exception(f"Pre-flight dry-run failed for query: {clean_sql}")
            return json.dumps({
                "status": "error",
                "message": f"Pre-flight SQL Check Error: {str(bq_err)}"
            })
        
    # Standardize/validate chart_type
    chart_type_lower = chart_type.lower().replace(" ", "").replace("_", "")
    
    # Map chart_type_lower to the correct generator
    if "bar" in chart_type_lower:
        panel_gen = grafana_generators.generate_bar_chart_panel
        resolved_type = "barchart"
    elif "line" in chart_type_lower or "time" in chart_type_lower or "trend" in chart_type_lower:
        panel_gen = grafana_generators.generate_line_chart_panel
        resolved_type = "timeseries"
    elif "pie" in chart_type_lower or "proportion" in chart_type_lower or "dist" in chart_type_lower:
        panel_gen = grafana_generators.generate_pie_chart_panel
        resolved_type = "piechart"
    else:
        panel_gen = grafana_generators.generate_table_panel
        resolved_type = "table"

    # Generate a deterministic UID from the title using sha256 to ensure consistent updating
    uid = hashlib.sha256(title.encode('utf-8')).hexdigest()[:12]
    
    # Create the panel JSON
    try:
        panel_json = panel_gen(id_num=1, title=title, sql=clean_sql)
    except Exception as e:
        log.exception(f"Failed to generate panel JSON for {resolved_type}. Falling back to table.")
        panel_json = grafana_generators.generate_table_panel(id_num=1, title=title, sql=clean_sql)
        resolved_type = "table"
        
    # Generate the base dashboard JSON wrapping the panel
    dashboard_json = grafana_generators.generate_base_dashboard(uid=uid, title=title, panels=[panel_json])
    
    # Load Grafana configuration from environment variables
    grafana_api_url = os.environ.get("GRAFANA_API_URL", "http://localhost:3000")
    grafana_external_url = os.environ.get("GRAFANA_EXTERNAL_URL", "http://localhost:3000")
    grafana_token = os.environ.get("GRAFANA_API_TOKEN", None)
    
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if grafana_token:
        headers["Authorization"] = f"Bearer {grafana_token}"
        
    payload = {
        "dashboard": dashboard_json,
        "overwrite": True
    }
    
    api_endpoint = f"{grafana_api_url.rstrip('/')}/api/dashboards/db"
    
    try:
        # Post to Grafana API
        res = requests.post(api_endpoint, json=payload, headers=headers, timeout=10)
        
        if res.status_code != 200:
            return json.dumps({
                "status": "error",
                "message": f"Grafana API returned status {res.status_code}: {res.text}"
            })
            
        data = res.json()
        dashboard_url = f"{grafana_external_url.rstrip('/')}{data.get('url')}"
        
        return json.dumps({
            "status": "success",
            "uid": uid,
            "resolved_chart_type": resolved_type,
            "dashboard_url": dashboard_url,
            "message": f"Resilient dashboard '{title}' created successfully!"
        })
        
    except Exception as e:
        log.exception("Error creating Grafana dashboard")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

@mcp.tool()
def list_grafana_dashboards() -> str:
    """List all dashboards in Grafana that are tagged with 'mcp-generated'.

    Returns a JSON string containing the status and a list of dashboard metadata (uid, title, and external URL)."""
    grafana_api_url = os.environ.get("GRAFANA_API_URL", "http://localhost:3000")
    grafana_external_url = os.environ.get("GRAFANA_EXTERNAL_URL", "http://localhost:3000")
    grafana_token = os.environ.get("GRAFANA_API_TOKEN", None)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if grafana_token:
        headers["Authorization"] = f"Bearer {grafana_token}"

    api_endpoint = f"{grafana_api_url.rstrip('/')}/api/search"
    params = {"tag": "mcp-generated"}

    try:
        res = requests.get(api_endpoint, params=params, headers=headers, timeout=10)
        if res.status_code != 200:
            return json.dumps({
                "status": "error",
                "message": f"Grafana API returned status {res.status_code}: {res.text}"
            })

        dashboards_data = res.json()
        dashboards = []
        for d in dashboards_data:
            url = f"{grafana_external_url.rstrip('/')}{d.get('url', '')}"
            dashboards.append({
                "uid": d.get("uid"),
                "title": d.get("title"),
                "url": url
            })

        return json.dumps({
            "status": "success",
            "dashboards": dashboards
        })

    except Exception as e:
        log.exception("Error listing Grafana dashboards")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

@mcp.tool()
def get_grafana_dashboard(uid: str) -> str:
    """Retrieve the full raw JSON model of an existing Grafana dashboard by its unique identifier (UID).

    Returns a JSON string containing the status and the complete dashboard JSON structure."""
    grafana_api_url = os.environ.get("GRAFANA_API_URL", "http://localhost:3000")
    grafana_token = os.environ.get("GRAFANA_API_TOKEN", None)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if grafana_token:
        headers["Authorization"] = f"Bearer {grafana_token}"

    api_endpoint = f"{grafana_api_url.rstrip('/')}/api/dashboards/uid/{uid}"

    try:
        res = requests.get(api_endpoint, headers=headers, timeout=10)
        if res.status_code != 200:
            return json.dumps({
                "status": "error",
                "message": f"Grafana API returned status {res.status_code}: {res.text}"
            })

        data = res.json()
        dashboard_json = data.get("dashboard")
        return json.dumps({
            "status": "success",
            "dashboard": dashboard_json
        })

    except Exception as e:
        log.exception(f"Error retrieving Grafana dashboard with UID {uid}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

@mcp.tool()
def update_dashboard(uid: str, title: str = None, refresh: str = None) -> str:
    """Update high-level metadata (such as title or refresh interval) of an existing dashboard.

    Returns a JSON string containing the status and a success message."""
    grafana_api_url = os.environ.get("GRAFANA_API_URL", "http://localhost:3000")
    grafana_token = os.environ.get("GRAFANA_API_TOKEN", None)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if grafana_token:
        headers["Authorization"] = f"Bearer {grafana_token}"

    # Step 1: Fetch the existing dashboard model
    get_endpoint = f"{grafana_api_url.rstrip('/')}/api/dashboards/uid/{uid}"
    try:
        get_res = requests.get(get_endpoint, headers=headers, timeout=10)
        if get_res.status_code != 200:
            return json.dumps({
                "status": "error",
                "message": f"Failed to retrieve existing dashboard for update: {get_res.text}"
            })
        
        dashboard_data = get_res.json()
        dashboard_json = dashboard_data.get("dashboard")
        
        # Step 2: Modify metadata fields if provided
        updated = False
        if title is not None:
            dashboard_json["title"] = title
            updated = True
        if refresh is not None:
            dashboard_json["refresh"] = refresh
            updated = True
            
        if not updated:
            return json.dumps({
                "status": "success",
                "message": "No updates requested."
            })
            
        # Step 3: Increment version and post back
        dashboard_json["version"] = dashboard_json.get("version", 1) + 1
        payload = {
            "dashboard": dashboard_json,
            "overwrite": True
        }
        
        post_endpoint = f"{grafana_api_url.rstrip('/')}/api/dashboards/db"
        res = requests.post(post_endpoint, json=payload, headers=headers, timeout=10)
        if res.status_code != 200:
            return json.dumps({
                "status": "error",
                "message": f"Grafana API update failed with status {res.status_code}: {res.text}"
            })
            
        return json.dumps({
            "status": "success",
            "message": f"Dashboard '{dashboard_json.get('title')}' updated successfully!"
        })

    except Exception as e:
        log.exception(f"Error updating Grafana dashboard with UID {uid}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

@mcp.tool()
def delete_grafana_dashboard(uid: str) -> str:
    """Delete an existing dashboard by UID. For safety, only dashboards with the 'mcp-generated' tag can be deleted.

    Returns a JSON string containing the status and a success message."""
    grafana_api_url = os.environ.get("GRAFANA_API_URL", "http://localhost:3000")
    grafana_token = os.environ.get("GRAFANA_API_TOKEN", None)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    if grafana_token:
        headers["Authorization"] = f"Bearer {grafana_token}"

    # Step 1: Fetch dashboard model to check tags for safety
    get_endpoint = f"{grafana_api_url.rstrip('/')}/api/dashboards/uid/{uid}"
    try:
        get_res = requests.get(get_endpoint, headers=headers, timeout=10)
        if get_res.status_code != 200:
            return json.dumps({
                "status": "error",
                "message": f"Failed to retrieve dashboard to verify tags: {get_res.text}"
            })
        
        dashboard_data = get_res.json()
        dashboard_json = dashboard_data.get("dashboard", {})
        tags = dashboard_json.get("tags", [])
        
        if "mcp-generated" not in tags:
            return json.dumps({
                "status": "error",
                "message": "Safety Protection Error: Only dashboards tagged with 'mcp-generated' can be deleted."
            })

        # Step 2: Proceed with DELETE
        delete_endpoint = f"{grafana_api_url.rstrip('/')}/api/dashboards/uid/{uid}"
        res = requests.delete(delete_endpoint, headers=headers, timeout=10)
        if res.status_code != 200:
            return json.dumps({
                "status": "error",
                "message": f"Grafana API deletion failed with status {res.status_code}: {res.text}"
            })
            
        return json.dumps({
            "status": "success",
            "message": f"Dashboard with UID '{uid}' was deleted successfully!"
        })

    except Exception as e:
        log.exception(f"Error deleting Grafana dashboard with UID {uid}")
        return json.dumps({
            "status": "error",
            "message": str(e)
        })

if __name__ == "__main__":
    import os
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)
