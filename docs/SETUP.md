# Setup Guide

## Prerequisites
1. **Python 3.12+** installed on your system.
2. **[uv](https://github.com/astral-sh/uv)** installed.
3. A Google Cloud Project with the **BigQuery API** enabled.
4. The `gcloud` CLI installed and authenticated.

## Installation

1. Clone or navigate to the repository directory.
2. Install the project dependencies using `uv`:
   ```bash
   uv sync
   ```
   This will automatically create a `.venv` directory and install the required packages (`mcp`, `google-cloud-bigquery`, `pytest`, etc.) according to `uv.lock`.

## Authentication (Google Cloud)

The `political-ads-mcp` server uses Google's Application Default Credentials (ADC) to authenticate with BigQuery.

1. Ensure you are logged in to your Google Cloud account via the CLI:
   ```bash
   gcloud auth application-default login
   ```
2. Make sure the authenticated account has the necessary permissions (e.g., `BigQuery Data Viewer` and `BigQuery User`) to run queries in your chosen GCP project.
3. Ensure your default project is set or explicitly set the `GOOGLE_CLOUD_PROJECT` environment variable before running the server:
   ```bash
   export GOOGLE_CLOUD_PROJECT="your-project-id"
   ```

## Running the Server

You can run the MCP server directly using `uv`:

```bash
uv run src/server.py
```

By default, FastMCP will start and listen on standard input/output (stdio) for MCP clients (like Claude Desktop or Cursor). 

## Running Tests

To run the unit tests and check code coverage:

```bash
uv run pytest --cov=src --cov-report=term-missing
```

## Dynamic Grafana Dashboard Setup

The project includes an auto-provisioned local Grafana setup running inside Docker, enabling the AI agent to dynamically convert your natural language queries into instant, interactive visual dashboards.

### Prerequisites (for Visualization)
- **Docker** and **Docker Compose** installed on your machine.
- Your GCP Service Account JSON key saved as `gcp-creds.json` in the root of the project directory.

### Running the Visualization Environment
1. Put your `gcp-creds.json` Service Account key in the project root.
2. Start the containerized services:
   ```bash
   docker compose -f deploy/docker-compose.yml up -d --build
   ```
   On startup, the MCP server automatically reads your `gcp-creds.json`, extracts the credentials, auto-generates the Grafana `bigquery.yaml` provisioning file, and extracts the raw PEM key to `deploy/grafana/google-key.pem` (safely git-ignored).
3. Access the Grafana UI by opening your browser to:
   ```
   http://localhost:3000
   ```
   *Note: Anonymous Admin access is enabled by default for local development, so you can inspect, view, and modify dashboards without any login requirements!*

### Dynamic Visualization via Grafana MCP
Once the environment is running, the official Grafana MCP server is exposed at `http://localhost:8000/sse` with standard capabilities. Any compatible MCP client (like Claude Desktop or Cursor) can use standard dashboard tools to query BigQuery and create charts:
- **`create_or_update_dashboard`**: Generate full JSON layouts dynamically.
- **`patch_dashboard`**: Perform lightweight updates.
- **`query_datasource`**: Query BigQuery or any other database configured in Grafana natively.