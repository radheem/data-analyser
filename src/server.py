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

if __name__ == "__main__":
    mcp.run()
