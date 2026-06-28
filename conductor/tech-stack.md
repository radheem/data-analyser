# Technology Stack

## Core Language & Package Management
- **Python 3.12+:** The primary programming language for the backend server and data processing.
- **uv:** The preferred, extremely fast package manager and virtual environment tool for Python.

## Backend & MCP Server
- **mcp (FastMCP):** The official Python SDK for the Model Context Protocol, providing the `FastMCP` framework to easily expose functions as tools to LLMs.
- **google-cloud-bigquery:** The official Google Cloud client library used to securely query the public datasets and optionally write aggregated data to your personal project.

## Dashboard & Visualization
- **Looker Studio (formerly Data Studio):** Used to build the visual dashboard, connecting natively to BigQuery to visualize the political ad metrics.