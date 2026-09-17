# Una sola imagen para todo: API, panel, Slack, migraciones, seed e ingesta.
# Cambia el comando, no la imagen.

FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS base
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:$PATH"
WORKDIR /app

# Dependencias primero: se cachean mientras no cambie uv.lock
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

COPY README.md alembic.ini ./
COPY src ./src
COPY corpus ./corpus
COPY data ./data
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# --- Desarrollo: suma pytest y ruff; el código y sus tests se montan como volumen ---
FROM base AS dev
COPY eval ./eval
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked
CMD ["uvicorn", "onboarding.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "src"]

# --- Producción (Render). Tiene que ser la última etapa ---
FROM base AS prod
RUN useradd --create-home app && chown -R app /app
USER app
EXPOSE 8000
CMD ["sh", "-c", "uvicorn onboarding.api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
