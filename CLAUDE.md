# CLAUDE.md — Client Content Engine

Backend document-processing engine: turns a client's raw pile (sales-call transcripts,
onboarding forms, brand docs) into multi-tenant, provenance-tracked, queryable brand
knowledge. Python FastAPI + Postgres/pgvector. A Next.js frontend (separate repo)
consumes the REST API. **Nothing in this repo generates marketing copy.**

## Rules — read and follow `docs/AI_CODING_RULES.md`

The full rules live in [docs/AI_CODING_RULES.md](docs/AI_CODING_RULES.md) and are
binding. The ones violated most easily:

- **Never bypass Postgres RLS; never drop provenance.** Every atom carries source,
  location, timestamp.
- **Keyless tests.** pytest must pass with zero API keys (fake providers are the default).
- **No new dependency without a licence check recorded** (pyproject licence ledger +
  `docs/DECISIONS.md`).
- **Hard M1 non-goals:** no frontend, no copy generation, no billing, no self-signup,
  no Redis/Celery.
- **One issue at a time** from `TASKS.md`; TDD; conventional commits; breadcrumb at
  session end.

## Key docs

- `docs/DESIGN.md` — approved architecture & data model (2026-07-29)
- `docs/M1_SCOPE.md` — current milestone scope + acceptance criteria
- `docs/API_CONTRACT.md` — the public API contract (the product)
- `docs/DECISIONS.md` — decision log (append-only)
- `TASKS.md` — issue queue + breadcrumbs
- `starter-kit/docs/BRIEF.md` + `RESEARCH.md` — original brief and prior-art survey

## Commands

- `python -m uv sync` — install deps (uv scripts dir not on bash PATH; use `python -m uv`)
- `python -m uv run pytest` — run tests (must pass keyless)
- `docker compose up -d` — Postgres + pgvector for local dev
