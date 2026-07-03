# Implementation Plan

## Phase 1: Infrastructure & Grafana Provisioning [checkpoint: 17609ad]
- [x] Task: Set up Grafana Provisioning Directories
    - [x] Create `deploy/grafana/provisioning/datasources` directory.
    - [x] Create `deploy/grafana/provisioning/dashboards` directory.
- [x] Task: Configure BigQuery Datasource
    - [x] Create `deploy/grafana/provisioning/datasources/bigquery.yaml` configured for the BigQuery plugin.
- [x] Task: Configure Dashboard Provisioning
    - [x] Create `deploy/grafana/provisioning/dashboards/provider.yaml` to point to local dashboard mounts.
- [x] Task: Update Docker Compose
    - [x] Update `deploy/docker-compose.yml` to include a `grafana` service.
    - [x] Map the provisioning directories as volumes in the Grafana container.
    - [x] Set environment variables to install the `doitintl-bigquery-datasource` plugin automatically.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Infrastructure & Grafana Provisioning' (Protocol in workflow.md)

## Phase 2: Grafana Dashboard JSON Generators
- [ ] Task: Setup JSON Generator Module
    - [ ] Create a new module `src/grafana_generators.py` to isolate JSON creation logic.
    - [ ] Write failing test for base dashboard JSON structure generation in a new test file `tests/test_grafana_generators.py`.
    - [ ] Implement base dashboard JSON structure generation to pass test.
- [ ] Task: Implement Chart Type Generators
    - [ ] Write failing tests for Bar Chart, Line Chart, Pie Chart, and Table panel JSON generation.
    - [ ] Implement generator logic for Bar Chart, Line Chart, Pie Chart, and Table to pass tests.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Grafana Dashboard JSON Generators' (Protocol in workflow.md)

## Phase 3: Resilient MCP Tool Integration
- [ ] Task: Implement `create_grafana_dashboard` Tool - Core Logic
    - [ ] Write failing test in `tests/test_server.py` for the new `create_grafana_dashboard` tool.
    - [ ] Implement basic tool logic in `src/server.py` to push generated dashboards to Grafana's HTTP API.
- [ ] Task: Implement Pre-flight SQL Check
    - [ ] Write failing test for pre-flight SQL check (aborting on invalid query/no data).
    - [ ] Update tool logic to execute the query via BigQuery client before generating the dashboard.
- [ ] Task: Implement Fallback and Validation
    - [ ] Write failing test for falling back to a Table view when chart generation or validation fails.
    - [ ] Update tool logic to catch generation errors, validate the JSON structure, and trigger the Table fallback.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Resilient MCP Tool Integration' (Protocol in workflow.md)