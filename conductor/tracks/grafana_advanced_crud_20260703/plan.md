# Implementation Plan

## Phase 1: Core Dashboard Retrieval & Lifecycle [checkpoint: 6a86dc4]
- [x] Task: Implement Dashboard Listing and Retrieval (6a86dc4)
    - [x] Write failing tests for `list_grafana_dashboards` and `get_grafana_dashboard` tools.
    - [x] Implement `list_grafana_dashboards` using Grafana's `/api/search` endpoint filtering by `tags=mcp-generated`.
    - [x] Implement `get_grafana_dashboard` using Grafana's `/api/dashboards/uid/{uid}` endpoint.
- [x] Task: Implement Dashboard Metadata Updates and Safety Deletions (6a86dc4)
    - [x] Write failing tests for `update_dashboard` and `delete_grafana_dashboard` (including safety tag check).
    - [x] Implement `update_dashboard` to modify metadata and push via `/api/dashboards/db`.
    - [x] Implement `delete_grafana_dashboard` to fetch, verify the `mcp-generated` tag, and call the DELETE API.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Core Dashboard Retrieval & Lifecycle' (Protocol in workflow.md)

## Phase 2: Dynamic Auto-Grid Layout System
- [ ] Task: Upgrade JSON Generators for Width Formatting
    - [ ] Modify all panel generators in `src/grafana_generators.py` to accept and apply `width` ("half" -> 12, "full" -> 24) and `x`, `y` coordinates.
    - [ ] Write failing tests for the new `calculate_next_grid_position(panels, new_width)` helper algorithm.
    - [ ] Implement the `calculate_next_grid_position` algorithm to handle side-by-side half-width pairing and full-width row stacking.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Dynamic Auto-Grid Layout System' (Protocol in workflow.md)

## Phase 3: Multi-Chart CRUD Operations
- [ ] Task: Implement Multi-Chart Creation
    - [ ] Write failing test for `create_multi_chart_dashboard`, ensuring it aborts atomically on pre-flight failure.
    - [ ] Implement `create_multi_chart_dashboard` utilizing the grid calculator and batch SQL validation.
- [ ] Task: Implement Appending & Deleting Individual Charts
    - [ ] Write failing tests for `add_chart_to_dashboard` and `delete_chart_from_dashboard`.
    - [ ] Implement `add_chart_to_dashboard` to calculate the next position and append the panel array.
    - [ ] Implement `delete_chart_from_dashboard` to filter the panels array by ID and save.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Multi-Chart CRUD Operations' (Protocol in workflow.md)

## Phase 4: Local Dashboard JSON Exports
- [ ] Task: Implement JSON Exporter Tool
    - [ ] Write failing test for `export_dashboard_json` verifying internal IDs are stripped and file is written.
    - [ ] Ensure the local export directory `deploy/grafana/dashboards/exported_dashboards` exists.
    - [ ] Implement `export_dashboard_json` to fetch, clean, and write the JSON file to disk.
- [ ] Task: Conductor - User Manual Verification 'Phase 4: Local Dashboard JSON Exports' (Protocol in workflow.md)