# Implementation Plan: Bootstrap Python FastMCP Server and BigQuery Client

## Phase 1: Project Initialization and Dependencies
- [x] Task: Initialize Python project with `uv` (09bc4fb)
    - [ ] Create `pyproject.toml`
    - [ ] Configure Python version constraint (>=3.12)
- [x] Task: Add Dependencies (b231bff)
    - [ ] Add `mcp` package
    - [ ] Add `google-cloud-bigquery` package
- [x] Task: Conductor - User Manual Verification 'Phase 1: Project Initialization and Dependencies' (Protocol in workflow.md) (e399acc)

## Phase 2: Core Server Implementation
- [x] Task: Implement `server.py` scaffold (f9a2529)
    - [ ] Write Tests: Create `tests/test_server.py` with a basic test asserting the FastMCP instance can be created.
    - [ ] Implement: Instantiate `FastMCP("political-ads-mcp")` in `server.py`
    - [ ] Implement: Add standard `if __name__ == "__main__":` block to run the server.
- [ ] Task: Implement BigQuery Client
    - [ ] Write Tests: Mock the BigQuery client and test the initialization logic.
    - [ ] Implement: Add global/reusable BigQuery client instantiation in `server.py`.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Core Server Implementation' (Protocol in workflow.md)

## Phase 3: Health Check Tool Implementation
- [ ] Task: Implement `ping_bigquery` tool
    - [ ] Write Tests: Add a test verifying the tool returns the expected success structure when the mock client succeeds.
    - [ ] Implement: Create the `@mcp.tool()` function `ping_bigquery`.
    - [ ] Implement: Execute a `SELECT 1` query using the BigQuery client within the tool.
    - [ ] Implement: Add error handling for `DefaultCredentialsError`.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Health Check Tool Implementation' (Protocol in workflow.md)