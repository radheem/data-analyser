import os
import re
import json
import logging
import hashlib
import requests
import time
import threading
from mcp.server.fastmcp import FastMCP
from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError

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

def ensure_grafana_service_account():
    """Ensure that a Grafana Service Account exists and generate a token, saving it persistently."""
    config_dir = "/app/mcp-config"
    token_path = os.path.join(config_dir, "token")
    
    # Check if we are running in docker or local
    if not os.path.exists(config_dir):
        # Fallback to a local folder for development/testing outside of Docker
        config_dir = "deploy/grafana/mcp-config"
        token_path = os.path.join(config_dir, "token")
        
    os.makedirs(config_dir, exist_ok=True)
    
    if os.path.exists(token_path):
        log.info(f"Persistent Grafana Service Account Token already exists at {token_path}")
        return
        
    # Get internal/external Grafana API URL
    grafana_api_url = os.environ.get("GRAFANA_API_URL", "http://grafana:3000")
    
    log.info(f"Waiting for Grafana to be healthy at {grafana_api_url}...")
    
    # Poll Grafana API health endpoint
    health_url = f"{grafana_api_url.rstrip('/')}/api/health"
    max_retries = 30
    for i in range(max_retries):
        try:
            res = requests.get(health_url, timeout=3)
            if res.status_code == 200:
                log.info("Grafana is healthy and ready.")
                break
        except Exception:
            pass
        log.info(f"Grafana not ready yet, retrying... ({i+1}/{max_retries})")
        time.sleep(2)
    else:
        log.warning("Grafana did not become healthy in time. Skipping service account provisioning.")
        return

    # Create Service Account
    # Since anonymous access with Admin role is enabled locally, we don't need authentication header
    sa_url = f"{grafana_api_url.rstrip('/')}/api/serviceaccounts"
    sa_payload = {
        "name": "mcp-sa",
        "role": "Admin",
        "isDisabled": False
    }
    
    try:
        log.info("Creating Grafana Service Account 'mcp-sa'...")
        res = requests.post(sa_url, json=sa_payload, timeout=10)
        
        sa_id = None
        if res.status_code == 201:
            sa_data = res.json()
            sa_id = sa_data.get("id")
            log.info(f"Created Service Account with ID: {sa_id}")
        elif res.status_code == 409 or "already exists" in res.text:
            log.info("Service account 'mcp-sa' already exists, searching for ID...")
            search_res = requests.get(sa_url, timeout=10)
            if search_res.status_code == 200:
                accounts = search_res.json()
                for acct in accounts:
                    if acct.get("name") == "mcp-sa":
                        sa_id = acct.get("id")
                        log.info(f"Found existing Service Account with ID: {sa_id}")
                        break
        else:
            log.warning(f"Failed to create/find service account: {res.status_code} - {res.text}")
            return
            
        if not sa_id:
            log.warning("Could not resolve Service Account ID.")
            return
            
        # Generate token for the Service Account
        token_url = f"{sa_url}/{sa_id}/tokens"
        token_payload = {
            "name": "mcp-sa-token"
        }
        
        log.info(f"Generating token for Service Account ID {sa_id}...")
        token_res = requests.post(token_url, json=token_payload, timeout=10)
        if token_res.status_code == 200:
            token_data = token_res.json()
            token = token_data.get("key")
            if token:
                with open(token_path, "w") as ft:
                    ft.write(token)
                log.info(f"Successfully saved persistent Service Account Token to {token_path}")
            else:
                log.warning("No token key returned from token endpoint.")
        else:
            log.warning(f"Failed to generate Service Account Token: {token_res.status_code} - {token_res.text}")
            
    except Exception as e:
        log.warning(f"Failed to auto-configure Grafana Service Account: {e}")

# Run provisioning steps
setup_grafana_datasource()
threading.Thread(target=ensure_grafana_service_account, daemon=True).start()

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
        
    if "LIMIT" not in clean_sql.upper():
        clean_sql += " LIMIT 100"
        
    try:
        query_job = bq_client.query(clean_sql)
        results = []
        for row in query_job:
            row_dict = {}
            for key, val in row.items():
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
            row_dict = {}
            for key, val in row.items():
                row_dict[key] = val
                
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
        
    cleaned = impressions_str.replace(",", "").strip()
    
    if "≤" in cleaned or "<=" in cleaned:
        nums = re.findall(r"\d+", cleaned)
        if nums:
            return {"min": 0, "max": int(nums[0])}
            
    if "≥" in cleaned or ">=" in cleaned or "+" in cleaned:
        nums = re.findall(r"\d+", cleaned)
        if nums:
            return {"min": int(nums[0]), "max": None}
            
    parts = cleaned.split("-")
    if len(parts) == 2:
        try:
            return {"min": int(parts[0]), "max": int(parts[1])}
        except ValueError:
            pass
            
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

if __name__ == "__main__":
    import os
    transport = os.environ.get("MCP_TRANSPORT", "stdio")
    mcp.run(transport=transport)
