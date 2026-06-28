# Product Guidelines

## 1. Data Integrity and Safety
- **Read-Only Access:** The MCP server must operate with strictly read-only permissions against the BigQuery datasets.
- **Resource Limits:** Implement strict limits (e.g., `LIMIT 100`) on all MCP queries to prevent massive data egress and ensure fast response times for AI agents.

## 2. API & MCP Tool Design
- **Targeted Tools First:** Prefer exposing specific, parameterized tools (e.g., `get_top_advertisers(region)`) rather than open-ended SQL execution tools to provide reliable, low-context interactions for LLMs.
- **Clear Ontologies:** Provide a descriptive tool (e.g., `political_ads_ontology`) that explains the dataset schema clearly to the LLM.
- **Error Handling:** All database errors must be caught and returned as clean JSON error messages, rather than crashing the FastMCP server.

## 3. Dashboard UX (Looker Studio)
- **Clarity over Clutter:** Focus on the primary metrics (Total Spend, Impressions, Top Advertisers) before drilling down into complex demographics.
- **Performance:** If dashboard load times exceed 5 seconds, implement pre-aggregated tables in BigQuery rather than querying the raw 3M+ row public dataset directly.