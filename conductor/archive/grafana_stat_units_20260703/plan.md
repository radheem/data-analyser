# Implementation Plan

## Phase 1: Intelligent Unit Normalization [checkpoint: 986ccf7]
- [x] Task: Implement Unit Normalization Helper (986ccf7)
    - [x] Write failing unit tests in `tests/test_grafana_generators.py` for `normalize_grafana_unit` covering currencies (USD, eur, GBP), standard strings (percent), and empty fallbacks.
    - [x] Implement `normalize_grafana_unit` in `src/grafana_generators.py` to handle 3-letter currency formatting and passthroughs.
- [x] Task: Conductor - User Manual Verification 'Phase 1: Intelligent Unit Normalization' (Protocol in workflow.md)

## Phase 2: Core Panel Generators Update [checkpoint: fbba3d9]
- [x] Task: Inject Units into Existing Panels (fbba3d9)
    - [x] Update tests for Bar, Line, and Pie generators to pass a custom `unit` and assert it appears in `fieldConfig.defaults.unit`.
    - [x] Modify `generate_bar_chart_panel`, `generate_line_chart_panel`, and `generate_pie_chart_panel` to accept the `unit` parameter, normalize it, and inject it into the JSON schema.
- [x] Task: Implement Stat Panel Generator (fbba3d9)
    - [x] Write failing test for `generate_stat_panel` verifying correct `type`, `unit` injection, and sparkline configuration (`graphMode`).
    - [x] Implement `generate_stat_panel` in `src/grafana_generators.py`.
- [x] Task: Conductor - User Manual Verification 'Phase 2: Core Panel Generators Update' (Protocol in workflow.md)

## Phase 3: MCP Tool Integration [checkpoint: 6fb5d44]
- [x] Task: Update Tool Signatures and Parsers (6fb5d44)
    - [x] Write failing integration tests in `tests/test_advanced_dashboard_crud.py` verifying `unit` parsing in `create_multi_chart_dashboard` and chart type resolution for `stat` panels.
    - [x] Update `_resolve_panel_generator_and_type` in `src/server.py` to route `"stat"` charts to `generate_stat_panel`.
    - [x] Update `create_multi_chart_dashboard` and `add_chart_to_dashboard` tools to extract the `unit` string from the user payload and pass it downstream.
- [x] Task: Conductor - User Manual Verification 'Phase 3: MCP Tool Integration' (Protocol in workflow.md)