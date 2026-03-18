FROM python:3.13-slim AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        openjdk-21-jre-headless \
        curl && \
    rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

WORKDIR /src
COPY . .

# Build wheel for distribution (standard Python package)
RUN uv build --wheel --out-dir /wheels

FROM python:3.13-slim

# Install runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends openjdk-21-jre-headless git && \
    rm -rf /var/lib/apt/lists/*

# Install wheel system-wide to /usr/local/bin
RUN --mount=type=bind,from=builder,source=/wheels,target=/wheels \
    pip install --no-cache-dir /wheels/*.whl

RUN useradd --system --no-create-home smart-tests
USER smart-tests

ENTRYPOINT ["smart-tests"]
