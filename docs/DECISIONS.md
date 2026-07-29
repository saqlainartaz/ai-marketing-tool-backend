# Decisions — append-only log

Format: date · decision · reasoning · alternatives rejected.

---

## 2026-07-29 — Stack: Python FastAPI monolith

The reuse list (Docling, Unstructured, future Whisper) is Python-first; a TS backend
would need a Python worker anyway. Next.js frontend (separate repo) consumes the
OpenAPI-typed REST API. Rejected: TS API + Python worker (two codebases day one),
separate worker process (premature — DB-backed jobs in-process until volume demands).

## 2026-07-29 — Storage: Postgres + pgvector, single database

Atoms, embeddings, profiles, jobs in one DB: one backup story, real FKs for provenance,
adequate to millions of atoms. Rejected: Qdrant sidecar (justified only past ~10M
vectors), SQLite (weak for hosted SaaS concurrency).

## 2026-07-29 — Tenancy: row-level client_id + Postgres RLS

RLS keyed on `current_setting('app.client_id')`; fail-closed startup; zero-recall
regression test with app-layer guard disabled. Rejected: schema-per-client (migration
N-times, DDL at onboarding), database-per-client (ops burden).

## 2026-07-29 — v1 auth trust model

Static service key authenticates the frontend server; engine trusts frontend's
client_id scoping (see docs/API_CONTRACT.md). Changes at self-signup time.

## 2026-07-29 — Cleaning is a pipeline stage, not an ETL system

Raw files immutable + sha256-addressed; cleaned text derived; cleaner version recorded
in lineage; type-aware cleaners. No Airflow/Spark.

## 2026-07-29 — M1 split A/B/C (reviewer feedback)

M1A proves the spine keyless with deterministic fake providers; M1B adds real
providers + retrieval; M1C adds operator review. Atom taxonomy narrowed to 9 types for
M1. One issue at a time.

## 2026-07-29 — Licence ledger process

Every dependency's licence checked before adding and recorded in pyproject comments +
here. Binding source: starter-kit/docs/BRIEF.md. Notable: psycopg is LGPL-3.0 — used
via dynamic linking, unmodified, which is fine for a hosted service; revisit only if
vendoring/modifying it.

## 2026-07-29 — Embedding dimension pinned at 1024

`atoms.embedding` is `vector(1024)`. The fake embedder must emit 1024-dim vectors so
the M1A→M1B provider switch needs no column migration.

Update (verified 2026-07-30 against Voyage docs): M1B should use `voyage-4`
($0.06/M tokens, 1024-dim default — same pin, no migration; 200M-token free tier
covers ~400 client corpora). Voyage is the embeddings provider Anthropic's docs
recommend; Anthropic ships no embedding model. `voyage-4-lite` ($0.02/M) is the
step-down if cost ever matters; embedding cost is a rounding error vs LLM extraction.

## 2026-07-29 — Sync SQLAlchemy sessions (not async)

Endpoints use sync sessions in FastAPI's threadpool. Less complexity in tests and the
pipeline; revisit only if concurrency profiling demands async.

## 2026-07-29 — App role is a non-superuser created in migration 0001

Superusers/BYPASSRLS roles bypass RLS entirely, so serving requests as the compose
admin user would silently disable isolation. `engine_app` (NOSUPERUSER NOBYPASSRLS,
dev password in the migration; production rotates via ALTER ROLE outside migrations).
RLS policies use `NULLIF(current_setting('app.client_id', true), '')::uuid` — the
NULLIF guards the empty string a pooled connection reports after SET LOCAL on an
otherwise-undefined GUC. Verified by the zero-recall regression test.

## 2026-07-29 — Tooling: uv (Apache-2.0/MIT)

Installed via pip; invoked as `python -m uv` (scripts dir not on bash PATH on this
machine).
