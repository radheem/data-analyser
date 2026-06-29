import json
import logging
from mcp.server.fastmcp import FastMCP
from google.cloud import bigquery
from google.auth.exceptions import DefaultCredentialsError

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("political-ads-mcp")

# Instantiate the FastMCP server
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

if __name__ == "__main__":
    mcp.run()
