# Initial Concept
I want to build a Python MCP server and a Data Studio (Looker Studio) dashboard pipeline using the BigQuery `bigquery-public-data.google_political_ads.creative_stats` dataset.

# Product Vision

This project creates a unified intelligence and visualization pipeline for Google's Political Ads transparency data. It serves a dual purpose: enabling autonomous AI agents to explore ad spending and targeting via an MCP server, while simultaneously providing a human-readable visual dashboard via Looker Studio.

## Target Audience
- **AI Agents / LLMs:** Requiring programmatic, structured access to query top advertisers, specific campaigns, and targeting criteria.
- **Data Analysts & Researchers:** Requiring a high-level visual dashboard to monitor political ad spending trends across regions.

## Key Goals
- Establish a read-only, safe, and rate-limited FastMCP server for querying BigQuery.
- Provide targeted MCP tools (e.g., `get_top_advertisers`, `search_advertiser_ads`) instead of just raw SQL access to lower token consumption and improve agent reliability.
- Set up a robust data pipeline that can support Looker Studio (either via direct connection or pre-aggregated tables in a personal GCP project).

## Core Features
1. **Political Ads MCP Server:** A Python-based `FastMCP` application with tools to fetch data from the `creative_stats` table.
2. **Dynamic Grafana Visualization:** A resilient, agent-triggered dashboard creation system supporting full dashboard and individual chart CRUD operations, auto-grid layout formatting (half vs full-width stacking), metadata updates, and portable JSON template exports.
3. **Dashboard Data Pipeline:** (Optional) Scheduled Python/SQL scripts to materialize aggregated summary tables to optimize Looker Studio performance.