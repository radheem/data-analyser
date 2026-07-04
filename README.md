# Data Analyzer (Political Ads data visualization)

An intelligent Model Context Protocol (MCP) and visualization pipeline for Google's public Political Ads transparency dataset (`bigquery-public-data.google_political_ads.creative_stats`) utilizing Google BigQuery and the official Grafana MCP server.

---

## 🏛️ Architecture Overview

The system is split into two synchronized, high-performance services orchestrated via Docker Compose:

1. **Political Ads MCP Server (`src/server.py`)**:
   - A Python-based `FastMCP` application exposing optimized, specialized BigQuery tools.
   - Restricts LLM token usage by avoiding raw SQL spikes, utilizing targeted datasets (`get_top_advertisers`, `search_advertiser_ads`).
   - Automatically provisions a **BigQuery datasource** inside Grafana on boot.
   - Features a background boot-hook (`ensure_grafana_service_account`) that polls Grafana, auto-provisions an Admin Service Account (`mcp-sa`), generates a token, and writes it persistently to a shared volume.

2. **Official Grafana MCP Server (`grafana/mcp-grafana`)**:
   - Runs alongside Grafana to provide standard Model Context Protocol capabilities.
   - Automatically loads the persistently provisioned Service Account Token on boot via a resilient entrypoint loop.
   - Enables any MCP client (such as Claude Desktop, Cursor, or Zed) to query all configured datasources (like BigQuery), search, build, patch, and export visual Grafana dashboards dynamically.

---

## ⚙️ Prerequisites

- **Python 3.12+** (configured via `uv`).
- **Docker** and **Docker Compose** installed.
- **Google Cloud Platform (GCP)** Service Account JSON key with `BigQuery Data Viewer` and `BigQuery User` permissions.

---

## 🚀 Quick Start (Docker Deployment)

The fastest way to deploy the entire stack is using Docker Compose, which boots Grafana, the Python MCP server, and the official Grafana MCP server in total synchronization.

1. **Place your GCP Credentials**:
   Rename your Service Account JSON key to `gcp-creds.json` and save it in the root of this project.

2. **Start the containers**:
   ```bash
   docker compose -f deploy/docker-compose.yml up --build -d
   ```

3. **What happens under the hood**:
   - **Grafana** starts up, pre-installs the `grafana-bigquery-datasource` plugin, and enables anonymous Admin access on port `3000`.
   - The **Python MCP Server** boots, extracts credentials to generate `deploy/grafana/provisioning/datasources/bigquery.yaml`, polls Grafana API, creates the `mcp-sa` service account, and writes its token to `deploy/grafana/mcp-config/token`.
   - The **Grafana MCP Container** waits for the token file, loads it dynamically, and runs on port `8000` to expose Grafana dashboard and querying capabilities.

4. **Access Grafana**:
   Open your browser to: `http://localhost:3000` (Anonymous Admin access is enabled by default for local development).

---

## 🛠️ Python MCP Server Tools

The Python server (`src/server.py`) exposes several targeted dataset tools:

| Tool Name | Parameters | Description |
| :--- | :--- | :--- |
| `ping_bigquery` | None | Health check tool to verify BigQuery connectivity. |
| `political_ads_ontology` | None | Returns the full schema and metadata ontology of the public ads dataset. |
| `query_ads` | `sql` (string) | Execute a read-only custom SQL query (SELECT / WITH) capped at 100 rows. |
| `get_top_advertisers` | `region` (string), `limit` (int) | Get highest spending political advertisers, active days, and ad count. |
| `search_advertiser_ads` | `advertiser_name`, `limit`, `region`, `start_date`, `end_date`, `ad_type` | Advanced search for ads by advertiser name with optional filters. |

---

## 📊 Grafana MCP Capabilities

The official `grafana/mcp-grafana` server running on port `8000` allows your AI assistant (e.g., Claude Desktop, Cursor) to:
- **`create_or_update_dashboard`**: Generate rich visual dashboards containing charts, panels, and variables using standard JSON format.
- **`patch_dashboard`**: Perform lightweight updates (rename titles, update queries, modify panels).
- **`search_dashboards`**: Retrieve existing dashboard lists and UIDs.
- **`query_datasource`**: Query BigQuery or any other database configured in Grafana natively.

---

## 🧪 Running Local Tests

You can run unit tests and verify the code quality of the Python MCP server and its auto-provisioning pipelines locally:

1. **Install Python environment**:
   ```bash
   uv sync
   ```
2. **Execute tests with pytest**:
   ```bash
   uv run pytest
   ```

All 16 unit tests will run, heavily mocking BigQuery client and Grafana API endpoints to verify complete code correctness without cloud fees or network calls.
