# Client Content Engine

Backend document-processing engine for InsideSuccess.TV: turns a client's raw pile
(sales-call transcripts, onboarding forms, brand docs) into multi-tenant,
provenance-tracked, queryable brand knowledge. Consumed by a Next.js frontend
(separate repo) over a versioned REST API. **This repo never generates marketing copy.**

## Quick start

```bash
docker compose up -d          # Postgres 17 + pgvector
python -m uv sync             # install dependencies
python -m uv run pytest       # tests — pass with ZERO API keys (fake providers)
python -m uv run uvicorn content_engine.main:create_app --factory --reload
```

## Where things are

| What | Where |
|---|---|
| Architecture & data model | `docs/DESIGN.md` |
| Current milestone scope + acceptance criteria | `docs/M1_SCOPE.md` |
| API contract (the product) | `docs/API_CONTRACT.md` |
| Decision log | `docs/DECISIONS.md` |
| AI coding rules (binding) | `docs/AI_CODING_RULES.md` |
| Issue queue + breadcrumbs | `TASKS.md` |
| Original brief + prior-art research | `starter-kit/docs/` |
