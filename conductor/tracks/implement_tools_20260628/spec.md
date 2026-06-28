# Track Specification: Implement tools for mcp

## Overview
This track implements the core data-fetching tools for the `political-ads-mcp` server. It expands the FastMCP instance with specialized functions that query the `bigquery-public-data.google_political_ads.creative_stats` dataset. The tools will provide an ontology, list top spenders, allow targeted ad searches, and provide a secure mechanism for read-only custom SQL queries.

## Functional Requirements
- **`political_ads_ontology()`:** Returns a detailed textual description of the `creative_stats` table schema, so the LLM understands what fields are queryable.
- **`get_top_advertisers(region, limit)`:** Returns the highest spending advertisers.
  - Must sort primarily by the maximum reported spend bounds (`spend_range_max_usd`).
- **`search_advertiser_ads(advertiser_name, limit, region, start_date, end_date, ad_type)`:** Returns ad campaign details for a specific entity.
  - Supports filtering by `region`, `start_date` / `end_date`, and `ad_type`.
- **`query_ads(sql)`:** A generic read-only SQL execution tool with a hard-coded limit.
- **Data Formatting:** All range-based metrics (like impressions or spend limits) returned by these tools must be parsed and returned as structured JSON objects (e.g., `{"min": 1000, "max": 5000}`) rather than raw strings to facilitate LLM parsing.

## Non-Functional Requirements
- **Performance:** Queries should utilize optimized BigQuery SQL patterns to return within the target 5-second window.
- **Safety:** The `query_ads` tool must catch and cleanly return BigQuery syntax and permission errors as JSON strings, preventing server crashes. It must forcefully append a `LIMIT` if none exists to avoid unbounded egress.

## Acceptance Criteria
- [ ] `political_ads_ontology` correctly describes the dataset and schema.
- [ ] `get_top_advertisers` accurately calculates and sorts advertisers by `spend_range_max_usd`.
- [ ] `search_advertiser_ads` correctly applies all optional filters (region, dates, ad type) and formats range outputs as JSON objects.
- [ ] `query_ads` successfully executes custom `SELECT` statements and handles errors gracefully.
- [ ] Unit tests for all tools verify BigQuery logic using `pytest-mock`.