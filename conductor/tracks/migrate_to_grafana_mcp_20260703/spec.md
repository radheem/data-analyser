# Specification: Migrate to Official Grafana MCP

## Overview
This track focuses on migrating the project's dashboard generation capabilities to the official `grafana/mcp-grafana` Docker container. It involves stripping out custom Grafana logic from the Python FastMCP server, reducing it to solely serve BigQuery dataset tools. An automated provisioner will be implemented to securely maintain a Grafana Service Account Token across deployments.

## Functional Requirements
- **Token Auto-Provisioning:** The Python server must contain a boot hook (`ensure_grafana_service_account()`) that automatically provisions and persistently saves a Grafana Service Account Token to a mounted volume if one does not already exist.
- **Docker Compose Updates:** 
  - Deploy a new `grafana-mcp` service using the official `grafana/mcp-grafana` image, configured for SSE transport on port 8000.
  - The `grafana-mcp` container must load the dynamically provisioned service account token at startup.
  - A shared volume must be configured between the `mcp-server` and `grafana-mcp` to facilitate token handoff.

## Non-Functional Requirements
- **Code Cleanliness:** All obsolete dashboard generation code (`src/grafana_generators.py`), tools, and associated tests must be completely removed from the repository.
- **Resilience:** The token auto-provisioner must gracefully poll Grafana until it is healthy before attempting creation, avoiding race conditions during Docker compose boot.

## Acceptance Criteria
- [ ] `src/grafana_generators.py` and its tests are removed.
- [ ] Dashboard CRUD tools are removed from `src/server.py`.
- [ ] `docker compose up` successfully spins up all containers.
- [ ] The token is successfully written to `/app/mcp-config/token`.
- [ ] The `grafana-mcp` container boots, reads the token, and successfully exposes its MCP tools via SSE.
- [ ] All remaining Python tests pass successfully.

## Out of Scope
- Modifying the core BigQuery data querying tools (`political_ads_ontology`, `query_ads`).
- Upgrading or changing the version of the local Grafana instance itself.