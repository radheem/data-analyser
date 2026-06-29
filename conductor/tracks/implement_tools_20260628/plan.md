# Implementation Plan: Implement tools for mcp

## Phase 1: Ontology and Generic Query Tools [checkpoint: c9ec4f8]
- [x] Task: Implement `political_ads_ontology` tool (0db4911)
    - [ ] Write Tests: Create tests to verify the tool returns the expected schema dictionary/string.
    - [ ] Implement: Create the `@mcp.tool()` function returning the schema details.
- [x] Task: Implement `query_ads` tool (5e8232c)
    - [ ] Write Tests: Mock the BigQuery client to verify it executes custom SQL and cleanly traps errors.
    - [ ] Implement: Create the `@mcp.tool()` function, ensure read-only safety, and enforce row limits.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Ontology and Generic Query Tools' (Protocol in workflow.md) (c9ec4f8)

## Phase 2: Top Advertisers Tool [checkpoint: d24b5af]
- [x] Task: Implement `get_top_advertisers` tool (06712cf)
    - [ ] Write Tests: Mock the BigQuery client to verify SQL construction, specifically sorting by `spend_range_max_usd`.
    - [ ] Implement: Create the `@mcp.tool()` function.
    - [ ] Implement: Add logic to format spend and impression ranges as JSON objects.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Top Advertisers Tool' (Protocol in workflow.md) (d24b5af)

## Phase 3: Ad Search Tool [checkpoint: ac629cd]
- [x] Task: Implement `search_advertiser_ads` tool (232be48)
    - [ ] Write Tests: Mock the BigQuery client to verify SQL `WHERE` clause construction for region, dates, and ad types.
    - [ ] Implement: Create the `@mcp.tool()` function taking the optional filters.
    - [ ] Implement: Apply the JSON object range formatting to the result payload.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Ad Search Tool' (Protocol in workflow.md) (ac629cd)

## Phase 4: Containerized End-to-End Testing
- [x] Task: Configure Docker Compose for Interactive Stdio (0fafbd1)
    - [ ] Implement: Update `deploy/docker-compose.yml` to include `stdin_open: true` and `tty: true`.
- [ ] Task: Verify Container Execution
    - [ ] Implement: Build and run the service via Docker Compose and check logs for "Successfully initialized BigQuery client."
- [ ] Task: Run Host-Side Tests Against Container
    - [ ] Implement: Run `PYTHONPATH=. uv run pytest tests/` on the host to verify all mock and integration tests execute successfully.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Containerized End-to-End Testing' (Protocol in workflow.md)