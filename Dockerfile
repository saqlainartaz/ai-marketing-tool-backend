# Client Content Engine — production image (Render-ready)
# Large image (~3-4GB): Docling pulls PyTorch for PDF/docx parsing. Expected.

FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependency layer first — cached unless pyproject/lock change.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .
RUN uv sync --frozen --no-dev

# Render injects PORT; default for local docker runs.
CMD ["sh", "-c", "uv run --no-dev uvicorn content_engine.main:create_app --factory --host 0.0.0.0 --port ${PORT:-10000}"]
