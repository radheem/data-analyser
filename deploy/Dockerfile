FROM python:3.12-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set working directory
WORKDIR /app
ENV PYTHONPATH=/app

# Copy dependency definition
COPY pyproject.toml uv.lock ./

# Install dependencies into system/container python
RUN uv sync --frozen --no-install-project

# Copy source code
COPY src/ ./src/

# Run the FastMCP server
CMD ["uv", "run", "src/server.py"]
