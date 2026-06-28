# Architecture Overview: political-ads-mcp

This project provides an intelligent interface between Large Language Models (LLMs) and Google's public Political Ads transparency dataset (`bigquery-public-data.google_political_ads.creative_stats`) via the Model Context Protocol (MCP).

## Core Components

1. **FastMCP Server (`src/server.py`)**
   - We utilize the `FastMCP` framework from the official Python `mcp` library.
   - It acts as the bridge, listening on `stdio` (or potentially HTTP/SSE) for incoming tool invocation requests from an MCP-compliant client (like an AI assistant).

2. **Google Cloud BigQuery Client**
   - The application maintains a globally instantiated `google.cloud.bigquery.Client`.
   - It relies on Application Default Credentials (ADC), ensuring that the server inherently assumes the identity and permissions of the environment it runs in (e.g., local developer credentials or a service account in production).
   - This single client is injected into or accessed by the various MCP tool functions to execute SQL queries.

3. **Data Source (`creative_stats`)**
   - The primary data source is the massive public dataset hosted by Google.
   - Because of its size, direct LLM-driven SQL execution is discouraged due to context limits and latency.
   - Instead, the MCP server abstracts the SQL complexity into specific, parameterized tools (e.g., `get_top_advertisers(region)`).

4. **Testing (`tests/`)**
   - The project uses `pytest` and `pytest-mock`.
   - The BigQuery client is heavily mocked during testing to ensure the server logic and tool schemas can be validated rapidly without incurring cloud costs or requiring active network connections in CI environments.

## Future Expansion: Looker Studio Pipeline

While the MCP server enables AI agents to query the data programmatically, a secondary goal of this repository is to facilitate human-readable dashboards.

In future iterations, Python scripts may be added to execute scheduled, heavy aggregation queries against the public dataset and materialize the results into a smaller, cheaper table within a personal GCP project. Looker Studio will then connect to this aggregated table, providing a fast, visual dashboard of political ad spending.