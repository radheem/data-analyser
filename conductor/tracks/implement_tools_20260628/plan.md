# Implementation Plan: Implement tools for mcp

## Phase 1: Ontology and Generic Query Tools
- [x] Task: Implement `political_ads_ontology` tool (0db4911)
    - [ ] Write Tests: Create tests to verify the tool returns the expected schema dictionary/string.
    - [ ] Implement: Create the `@mcp.tool()` function returning the schema details.
- [x] Task: Implement `query_ads` tool (5e8232c)
    - [ ] Write Tests: Mock the BigQuery client to verify it executes custom SQL and cleanly traps errors.
    - [ ] Implement: Create the `@mcp.tool()` function, ensure read-only safety, and enforce row limits.
- [~] Task: Conductor - User Manual Verification 'Phase 1: Ontology and Generic Query Tools' (Protocol in workflow.md)

## Phase 2: Top Advertisers Tool
- [ ] Task: Implement `get_top_advertisers` tool
    - [ ] Write Tests: Mock the BigQuery client to verify SQL construction, specifically sorting by `spend_range_max_usd`.
    - [ ] Implement: Create the `@mcp.tool()` function.
    - [ ] Implement: Add logic to format spend and impression ranges as JSON objects.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Top Advertisers Tool' (Protocol in workflow.md)

## Phase 3: Ad Search Tool
- [ ] Task: Implement `search_advertiser_ads` tool
    - [ ] Write Tests: Mock the BigQuery client to verify SQL `WHERE` clause construction for region, dates, and ad types.
    - [ ] Implement: Create the `@mcp.tool()` function taking the optional filters.
    - [ ] Implement: Apply the JSON object range formatting to the result payload.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Ad Search Tool' (Protocol in workflow.md)

## Phase 4: Containerized End-to-End Testing
- [ ] Task: Configure Docker Compose for Interactive Stdio
    - [ ] Implement: Update `deploy/docker-compose.yml` to include `stdin_open: true` and `tty: true`.
- [ ] Task: Verify Container Execution
    - [ ] Implement: Build and run the service via Docker Compose and check logs for "Successfully initialized BigQuery client."
- [ ] Task: Run Host-Side Tests Against Container
    - [ ] Implement: Run `PYTHONPATH=. uv run pytest tests/` on the host to verify all mock and integration tests execute successfully.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Containerized End-to-End Testing' (Protocol in workflow.md)