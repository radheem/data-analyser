# Specification: Advanced Grafana Dashboard CRUD & Layout Operations

## Overview
Extend the existing Grafana MCP integration to support comprehensive dashboard lifecycle management. This track introduces tools for listing, retrieving, updating, and exporting dashboards. It significantly expands dashboard creation to support multi-chart layouts with an intelligent auto-grid system that accommodates both "half-width" and "full-width" chart orientations without requiring manual coordinate calculations from the AI agent.

## Functional Requirements
1. **New MCP Tools:**
   - `list_grafana_dashboards()`: Lists all dashboards tagged with `mcp-generated`.
   - `get_grafana_dashboard(uid)`: Retrieves the raw JSON structure for a given dashboard UID.
   - `create_multi_chart_dashboard(title, charts)`: Accepts a list of chart configurations, auto-calculates their grid layout, and deploys a new dashboard.
   - `add_chart_to_dashboard(uid, chart_type, sql, title, width)`: Appends a single chart to an existing dashboard, maintaining grid flow.
   - `update_dashboard(uid, title, refresh)`: Modifies high-level dashboard metadata.
   - `delete_chart_from_dashboard(uid, chart_id)`: Removes a specific panel from a dashboard and repositions remaining charts (or leaves gaps).
   - `delete_grafana_dashboard(uid)`: Deletes a dashboard entirely.
   - `export_dashboard_json(uid)`: Saves the dashboard JSON to disk locally at `deploy/grafana/dashboards/exported_dashboards/{uid}.json`.
2. **Auto-Grid Layout System:**
   - Panels will support an optional `width` parameter (`"half"` for 12 columns, `"full"` for 24 columns).
   - The backend will dynamically calculate `x`, `y`, `w`, and `h` coordinates.
   - Half-width panels will efficiently pair up side-by-side on the same row where possible. Full-width panels will force a new row.
3. **Safety & Validation:**
   - **Pre-flight Checks:** If any chart in a batch request fails its BigQuery SQL dry-run, the entire dashboard creation/update process must abort immediately to ensure atomic integrity.
   - **Deletion Safety:** The `delete_grafana_dashboard` tool must verify the dashboard possesses the `mcp-generated` tag before executing the deletion to protect manually created dashboards.
   - **JSON Export:** The `export_dashboard_json` tool will strip internal Grafana identifiers (like `id` fields) to produce clean, easily importable dashboard templates.

## Non-Functional Requirements
- **Modularity:** Grid calculation logic should be cleanly abstracted into a helper function inside `grafana_generators.py` to keep the tool handlers clean.
- **Resilience:** Continue utilizing the defensive client-side transformations (`convertFieldType`) and fallback (Table) rendering logic established in the prior track.

## Acceptance Criteria
- All 8 new MCP tools are registered, documented, and callable.
- A multi-chart dashboard containing both full-width and half-width charts renders perfectly in Grafana without any panel collisions or overlaps.
- Attempting to delete a dashboard without the `mcp-generated` tag safely returns an error.
- A failed SQL syntax in any multi-chart batch aborts the entire operation and returns the precise BigQuery error string.
- Exported JSON files are cleanly written to the local Docker host filesystem volume.