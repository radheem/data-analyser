# Track Specification: Bootstrap Python FastMCP Server and BigQuery Client

## Overview
This track focuses on initializing the Python project foundation using `uv` and standing up a basic `FastMCP` server capable of communicating with the Google Cloud BigQuery API. This serves as the necessary plumbing before we implement the complex, data-specific MCP tools.

## Functional Requirements
- **Environment Setup:** Initialize a new Python project using `uv` with Python 3.12+.
- **Dependencies:** Install `mcp` (for FastMCP) and `google-cloud-bigquery`.
- **Server Implementation:** Create a `server.py` file that instantiates a FastMCP server named `political-ads-mcp`.
- **BigQuery Client:** Establish a global or reusable `google.cloud.bigquery.Client` instance within the server context.
- **Health Check Tool:** Implement a basic `@mcp.tool()` named `ping_bigquery` that runs a trivial query (e.g., `SELECT 1`) to verify API connectivity and authentication.

## Non-Functional Requirements
- **Authentication:** The server must rely on Application Default Credentials (ADC) for Google Cloud authentication.
- **Error Handling:** The BigQuery client connection process should fail gracefully if credentials are not found.

## Acceptance Criteria
- [ ] A `pyproject.toml` exists and manages dependencies via `uv`.
- [ ] Running the server script starts a valid FastMCP server via `stdio` or `sse`.
- [ ] The `ping_bigquery` tool successfully returns a response confirming the BigQuery connection is active.