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