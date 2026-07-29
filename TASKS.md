# TASKS — issue queue (GitHub issues live here until a remote exists)

Workflow: one issue at a time, TDD, branch `feat/N-slug`, conventional commits,
breadcrumb on completion. Full rules: `docs/AI_CODING_RULES.md`.

---

## Issue 1 — Project skeleton  `feat/1-project-skeleton`  [done 2026-07-29]

**Goal:** Bootable FastAPI service + tooling + operating files; pytest green keyless.

**Scope:** git repo, uv project, pyproject deps, FastAPI app factory + `/health`,
docker-compose (pgvector Postgres), pytest wiring, operating files, .gitignore.

**Non-goals:** database schema, RLS, uploads, providers, pipeline.

**Done when:**
- [x] `python -m uv run pytest` passes with zero API keys (1 passed, pristine output)
- [x] `/health` returns 200 `{"status": "ok"}` via TestClient
- [x] `docker compose config` validates
- [x] Operating files exist; CLAUDE.md points at AI_CODING_RULES.md

---

## Issue 2 — Schema + RLS  `feat/2-schema-rls`  [done 2026-07-29]

**Goal:** Full M1 schema with DB-enforced tenant isolation.

**Scope:** clients/documents/atoms/jobs/lineage/decisions tables (SQLAlchemy + Alembic);
RLS policies keyed on `current_setting('app.client_id')`; per-request session-variable
middleware; fail-closed startup (refuse to boot on missing/invalid tenant-auth config);
service-token auth dependency.

**Non-goals:** upload handling, pipeline stages, real providers.

**Done when:**
- [x] Alembic migration creates all tables + RLS policies against dockerized Postgres
- [x] Cross-tenant zero-recall regression test passes **with the app-layer guard
      disabled** (DB policy alone blocks leakage — reads, writes, and no-context cases)
- [x] Service boots only with valid service-token config; fails closed otherwise
- [x] Full pytest green, keyless (11 passed, pristine)

---

## Issue 3 — Upload + sha256 dedupe  `feat/3-upload-dedupe`  [done 2026-07-29]

**Goal:** Immutable, content-addressed raw-file intake.

**Scope:** `POST /v1/clients/{id}/documents` multipart + `source_type` +
`source_authority`; sha256 content addressing; per-client dedupe (re-upload → same
document, 200 not duplicate); local-disk storage adapter behind an S3-compatible
interface; document status machine start (`uploaded`).

**Non-goals:** parsing, cleaning, atoms.

**Done when:**
- [x] Duplicate upload creates no duplicate rows/files (200 + same id on re-upload)
- [x] Raw file is written once, never mutated; path derived from sha256 (atomic publish)
- [x] Document row carries source_type, source_authority, sha256, status
- [x] Full pytest green, keyless (17 passed)

Breadcrumb: clients + documents routers live under service-token auth; storage is an
S3-shaped `RawStorage` Protocol with `LocalDiskStorage`; invalid source_type → 422.
Next: Issue 4 parse+clean. No blockers.

---

## Issue 4 — Parse + clean (text/md)  `feat/4-parse-clean`  [done 2026-07-29]

**Goal:** Text/markdown parse + type-aware transcript cleaner, provenance-preserving.

**Scope:** text/md parser producing structured sections with location map + eager
heading tree (`breadcrumb`, `section_anchor`, `level_reliable`; strip TOCs); transcript
cleaner (speaker-label normalization, filler stripping, timestamp collapsing, PII
redaction); cleaner version recorded in lineage; golden-file tests on fixture
transcripts; document status transitions `uploaded → parsed → cleaned`.

**Non-goals:** PDF/docx (Docling lands in M1B), atomisation, embeddings.

**Done when:**
- [x] Golden-file tests: fixture transcript → expected cleaned output, stable
- [x] Raw file unchanged; cleaned text stored as derived artifact (`cleaned_path`,
      migration 0002; `put_derived` kept apart from immutable raw tree)
- [x] Lineage records `{source_sha, stage, cleaner_version, ts}` per transformation
- [x] Full pytest green, keyless (30 passed)

Breadcrumb: `pipeline/` package — parse.py (eager heading tree, TOC strip, anchors),
clean.py (timestamps, speaker normalization, fillers, small-talk, PII email/phone,
versioned), runner.py `run_parse_and_clean` (idempotent, statuses uploaded→parsed→
cleaned). Next: Issue 5 fake providers + atomizer + /atoms. No blockers.

---

## Issue 5 — Fake providers + fake atomizer  `feat/5-fake-providers`  [done 2026-07-29]

**Goal:** Deterministic keyless pipeline end-to-end: cleaned text → provisional atoms
with provenance + embeddings.

**Scope:** `LLMProvider` Protocol + registry + env resolution (brand-loom pattern,
Apache-2.0); deterministic FakeProvider; FakeEmbedder (hash-based vectors, dimension
matching the real provider's — pin before implementing); deterministic fake atomizer
(rule-based extraction from fixture markers → typed atoms, M1 9-type taxonomy);
atoms land `provisional` with full provenance; jobs table + in-process async worker;
`GET /v1/clients/{id}/atoms`.

**Non-goals:** real Anthropic/Voyage calls, search, context.

**Done when:**
- [x] Same input twice → byte-identical atoms (determinism test)
- [x] Every atom has document_id, location, confidence, evidence_kind, status
- [x] `/atoms` returns same-client data only (+ `trust: untrusted` label)
- [x] Full pytest green, keyless (45 passed)

Breadcrumb: providers registry (fake default, env-resolved, lazy) + FakeLLM/FakeEmbedder
(hash-based 1024-dim); fake atomizer (rule-based, 9-type-compatible, guardrails);
run_atomise_and_embed (delete+reinsert idempotency, lineage atomise/embed); jobs worker
(engine_worker role w/ explicit jobs-only RLS policy, FOR UPDATE SKIP LOCKED, one
attempt then failed+recorded); upload enqueues; /atoms endpoint. Migration 0003.
Next: Issue 6 E2E + /reprocess. No blockers.

---

## Issue 6 — E2E intake spine demo  `feat/6-e2e-spine`  [done 2026-07-29 — M1A COMPLETE]

**Goal:** M1A acceptance: full keyless demo per docs/M1_SCOPE.md criteria 1-4, 8-11.

Breadcrumb: `/reprocess` endpoint (202, enqueues job, atoms converge by content hash);
test_e2e_spine covers two clients / three docs / worker pipeline / provenance-rich
objections / API-level isolation / dedupe / reprocess idempotency. 46 tests, zero keys.
Next: define M1B issues (real Anthropic+Voyage adapters, parity eval, Docling,
extraction prompts, hybrid search under RLS, /search, /context). No blockers.

---

## M1B issues (defined when M1A ships): real providers + parity eval, Docling,
## extraction prompts, hybrid search under RLS, /search, /context, 3-fixture demo.
## M1C issues: confirm/override/deprecate + decisions workflow + survival tests.

---

# Breadcrumbs

(append at end of each issue/session: Completed / Next / Blocker)

## 2026-07-29 — Issue 1 (feat/1-project-skeleton)

Completed:
- git repo on `main`; issue branch `feat/1-project-skeleton`
- uv project (invoke as `python -m uv` — scripts dir not on bash PATH)
- pyproject with licence-ledger comments; deps: fastapi, uvicorn, sqlalchemy, alembic,
  pydantic(-settings), psycopg, pgvector, python-multipart; dev: pytest(-asyncio),
  httpx/httpx2, ruff
- `create_app()` factory + `/health` (TDD: watched fail → minimal code → green, pristine)
- docker-compose: pgvector/pgvector:pg17 with healthcheck (validated)
- Operating files: IDEA/TASKS/RETRO, docs/{DESIGN,M1_SCOPE,API_CONTRACT,DECISIONS,
  AI_CODING_RULES,DEPLOY_CHECKLIST}.md, CLAUDE.md (embeds rules), .github stubs

Next:
- Issue 2 (`feat/2-schema-rls`): SQLAlchemy models + Alembic migration for
  clients/documents/atoms/jobs/lineage/decisions; RLS policies on
  `current_setting('app.client_id')`; per-request session-var middleware; fail-closed
  startup; zero-recall regression test (needs dockerized Postgres running)

Blocker:
- None. Note: Issue 2 tests need `docker compose up -d` first.

## 2026-07-29 — Issue 2 (feat/2-schema-rls)

Completed:
- Full M1 schema (clients/documents/atoms/jobs/lineage/decisions) in
  `models.py` + handwritten Alembic migration 0001
- RLS ENABLE+FORCE on all tenant tables; policy
  `client_id = NULLIF(current_setting('app.client_id', true), '')::uuid`
  (NULLIF guards pooled-connection '' after SET LOCAL — found by the test)
- Non-superuser `engine_app` role created in migration (superusers bypass RLS)
- `tenant_session()` context manager (set_config, transaction-local)
- Fail-closed Settings (SERVICE_API_KEY required, min 16 chars) wired into create_app
- `require_service_token` dependency (constant-time compare)
- Zero-recall tests: cross-tenant reads, writes (WITH CHECK), no-context (zero rows),
  app-role-not-superuser precondition

Next:
- Issue 3 (`feat/3-upload-dedupe`): clients + documents endpoints, multipart upload,
  sha256 content addressing + per-client dedupe, local-disk storage adapter behind
  S3-compatible interface, status machine start

Blocker:
- None.
