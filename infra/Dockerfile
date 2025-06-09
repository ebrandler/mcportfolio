# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    build-essential \
    g++ \
    git \
    cmake \
    && rm -rf /var/lib/apt/lists/*

ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh

ENV PATH="/root/.local/bin/:$PATH"

COPY pyproject.toml uv.lock ./
RUN uv pip install --system

# Final stage
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    build-essential \
    g++ \
    git \
    cmake \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code
COPY mcportfolio/ ./mcportfolio/
COPY examples/ ./examples/
COPY pyproject.toml ./

# Expose the default HTTP port
EXPOSE 8001

# Add healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8001/health || exit 1

# Run the server with HTTP transport
CMD ["uvicorn", "mcportfolio.server.main:create_asgi_app", "--factory", "--host", "0.0.0.0", "--port", "8001"]