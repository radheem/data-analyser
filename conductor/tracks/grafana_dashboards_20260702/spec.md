# Specification: Resilient Grafana Dashboard Integration

## Overview
Implement a resilient MCP tool for creating Grafana dashboards dynamically from natural language queries. The tool will use the Direct API Client approach (Approach A), supporting a restricted set of reliable chart types (Bar, Line, Pie, and Table). It will integrate with a locally run Grafana instance managed via an updated `deploy/docker-compose.yml`, utilizing local directory mounting for provisioning to avoid image rebuilds.

## Functional Requirements
1. **MCP Tools:** Create an MCP tool (e.g., `create_grafana_dashboard`) that takes a SQL query, a chart type (Explicitly provided by the LLM), and title as arguments.
2. **Supported Charts:** Implement JSON payload generation for Bar Charts, Line Charts, Pie Charts, and Data Tables.
3. **Grafana API Integration:** The tool must construct the Grafana Dashboard JSON and push it to the Grafana HTTP API (`/api/dashboards/db`).
4. **Resilient Creation Logic:**
   - **Pre-flight SQL Check:** Execute the SQL query to ensure it is valid and returns data before attempting to build the dashboard.
   - **JSON Validation:** Validate the generated Grafana JSON payload structure before sending it to the API.
   - **Fallback to Table:** If the generation of a specific chart type fails (or the data shape doesn't match the chart requirements), the system must gracefully fallback to generating a Table panel.
5. **Docker Compose Setup:** Update `deploy/docker-compose.yml` to include a Grafana service.
6. **File Provisioning:** Configure Grafana to use file-based provisioning for the BigQuery datasource and any default dashboards, mounting local directories (`deploy/grafana/...`) into the container.

## Non-Functional Requirements
- **Reliability:** Dashboard generation must not crash the MCP server and must return meaningful errors or a fallback table view to the LLM.
- **Performance:** Avoid excessive payload sizes by utilizing targeted Grafana panel definitions rather than massive generic templates.
- **Maintainability:** The mapping logic from chart type to Grafana JSON should be modular and easy to extend later.

## Acceptance Criteria
- A new `create_grafana_dashboard` MCP tool is available and functioning.
- The `deploy/docker-compose.yml` successfully spins up Grafana with the BigQuery datasource pre-configured via local files.
- The agent can successfully request a Bar Chart, Line Chart, Pie Chart, or Table, and receive a working Grafana dashboard URL in return.
- If an invalid chart configuration is requested or JSON generation fails, the system automatically creates a Table dashboard instead.
- Pre-flight SQL failures correctly abort dashboard creation and notify the agent.

## Out of Scope
- Building a completely new UI from scratch outside of Grafana.
- Supporting complex, multi-panel dashboards (initially, it will be one panel per generated dashboard).
- Implementing alerting or alerting rules in Grafana.
- Managing user authentication within Grafana (use simple admin/admin for local dev).