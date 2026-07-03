# Implementation Plan: Migrate to Official Grafana MCP

## Phase 1: Strip Custom Grafana Logic
- [ ] Task: Remove Custom Dashboard Generators
    - [ ] Remove `src/grafana_generators.py`
    - [ ] Remove `tests/test_grafana_generators.py`
    - [ ] Remove `tests/test_advanced_dashboard_crud.py`
- [ ] Task: Refactor MCP Server
    - [ ] Write Tests (Red Phase): Update `tests/test_server.py` to remove tests for deleted dashboard CRUD tools.
    - [ ] Implement (Green Phase): Remove dashboard CRUD tools from `src/server.py`. Keep core BigQuery tools.
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Strip Custom Grafana Logic' (Protocol in workflow.md)

## Phase 2: Token Auto-Provisioning
- [ ] Task: Implement Boot Hook
    - [ ] Write Tests (Red Phase): Add unit tests for `ensure_grafana_service_account` boot hook in `tests/test_server.py`.
    - [ ] Implement (Green Phase): Create `ensure_grafana_service_account()` in `src/server.py` to poll Grafana, create service account, generate token, and save to volume.
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Token Auto-Provisioning' (Protocol in workflow.md)

## Phase 3: Docker Compose Updates
- [ ] Task: Configure Docker Environment
    - [ ] Write Tests (Red Phase): Verify configuration visually or via simple script if applicable (mostly configuration change).
    - [ ] Implement (Green Phase): Update `deploy/docker-compose.yml` to add shared volume `mcp-config` to `mcp-server`.
    - [ ] Implement (Green Phase): Add `grafana-mcp` service using `grafana/mcp-grafana` image, configured with custom entrypoint to load token.
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Docker Compose Updates' (Protocol in workflow.md)