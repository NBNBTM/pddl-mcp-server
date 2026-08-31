FROM python:3.14-slim AS planner-builder

ARG FAST_DOWNWARD_REF=824499f8f7b1d3f8c0260b2b8b0740ee815dcdca

RUN apt-get update \
    && apt-get install --yes --no-install-recommends build-essential ca-certificates cmake git \
    && rm -rf /var/lib/apt/lists/*

RUN git init /opt/fast-downward \
    && git -C /opt/fast-downward remote add origin https://github.com/aibasel/downward.git \
    && git -C /opt/fast-downward fetch --depth 1 origin "${FAST_DOWNWARD_REF}" \
    && git -C /opt/fast-downward checkout --detach FETCH_HEAD

WORKDIR /opt/fast-downward
RUN python build.py


FROM python:3.14-slim AS runtime

ENV FAST_DOWNWARD_PATH=/opt/fast-downward/fast-downward.py \
    OUTPUT_DIR=/app/output \
    PDDL_MCP_DISABLE_DOTENV=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md server.py .mcp.json ./
COPY src ./src
RUN python -m pip install --no-cache-dir .

COPY --from=planner-builder /opt/fast-downward /opt/fast-downward

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "from pddl_mcp.server import app; assert app" || exit 1

CMD ["python", "server.py"]
