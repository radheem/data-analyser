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

## Phase 2: Grafana Dashboard JSON Generators [checkpoint: 653e3f0]
- [x] Task: Setup JSON Generator Module
    - [x] Create a new module `src/grafana_generators.py` to isolate JSON creation logic.
    - [x] Write failing test for base dashboard JSON structure generation in a new test file `tests/test_grafana_generators.py`.
    - [x] Implement base dashboard JSON structure generation to pass test.
- [x] Task: Implement Chart Type Generators
    - [x] Write failing tests for Bar Chart, Line Chart, Pie Chart, and Table panel JSON generation.
    - [x] Implement generator logic for Bar Chart, Line Chart, Pie Chart, and Table to pass tests.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Grafana Dashboard JSON Generators' (Protocol in workflow.md)

## Phase 3: Resilient MCP Tool Integration [checkpoint: d7d287e]
- [x] Task: Implement `create_grafana_dashboard` Tool - Core Logic
    - [x] Write failing test in `tests/test_server.py` for the new `create_grafana_dashboard` tool.
    - [x] Implement basic tool logic in `src/server.py` to push generated dashboards to Grafana's HTTP API.
- [x] Task: Implement Pre-flight SQL Check
    - [x] Write failing test for pre-flight SQL check (aborting on invalid query/no data).
    - [x] Update tool logic to execute the query via BigQuery client before generating the dashboard.
- [x] Task: Implement Fallback and Validation
    - [x] Write failing test for falling back to a Table view when chart generation or validation fails.
    - [x] Update tool logic to catch generation errors, validate the JSON structure, and trigger the Table fallback.
- [x] Task: Conductor - User Manual Verification 'Phase 3: Resilient MCP Tool Integration' (Protocol in workflow.md)