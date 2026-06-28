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

if __name__ == "__main__":
    mcp.run()
