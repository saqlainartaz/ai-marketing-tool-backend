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

## Issue 7 — Real provider adapters + parity eval  `feat/7-real-providers`  [done 2026-07-30]

**Goal:** Anthropic LLM + Voyage embedding adapters behind the existing registry;
parity eval. Keyless tests stay green; real calls activate only via env keys.

**Done when:**
- [x] `ENGINE_LLM_PROVIDER=anthropic` / `ENGINE_EMBEDDING_PROVIDER=voyage` resolve
- [x] Missing keys fail closed at call time with helpful errors (never at import)
- [x] Fake + real embedders share the `input_type` signature (query vs document)
- [x] Parity eval: fake always, real env-gated, exit 1 on failure — ALL PASS keyless
- [x] Full pytest green keyless (51 passed, 2 live-key tests skipped)

Breadcrumb: anthropic (MIT) + voyageai (MIT) added; AnthropicLLM defaults to
claude-opus-5 (env ENGINE_ANTHROPIC_MODEL), sends no sampling params (400 on Opus 5),
enables server-side refusal fallbacks (`fallbacks: "default"`), raises on refusal;
VoyageEmbedder defaults voyage-4 @1024 (env ENGINE_VOYAGE_MODEL). Next: Issue 8 real
extraction prompts. Needs ANTHROPIC_API_KEY + VOYAGE_API_KEY + a real anonymized
transcript to validate quality. No blockers for code; keys block live validation.

## Issue 8 — Real LLM atomizer  `feat/8-real-atomizer`  [done 2026-07-30]

**Goal:** Replace the fake atomizer with Claude-driven extraction when a real provider
is configured; validate quality on real client fixtures.

**Done when:**
- [x] LLMAtomizer: line-numbered `<document>` data block (injection hygiene), 9-type
      taxonomy with marketing semantics, per-source-type framing, hard validation
      (unknown types dropped, values clamped, garbage raises → job fails visibly)
- [x] Runner routes by provider: fake → rule-based (keyless CI unchanged), real →
      LLM atomizer; lineage records actor + prompt_hash
- [x] Keyless tests via scripted stub LLM (parsing, clamping, determinism, fenced
      JSON, injection delimiting) — 61 passed
- [x] Live-tuned on real fixtures (Keira transcript, Barbara onboarding): all 9 types
      extracted; claims_blacklist correctly flags clinical/income/privacy-sensitive
      claims with say_instead alternatives; voice_constraints capture signature
      language; provenance line+speaker accurate

Breadcrumb: two tuning iterations were needed — the model fills its favorite types
(insight/proof_point) before quote/voice_constraint/claims_blacklist unless coverage
is an explicit numbered rule; cap raised to 60 atoms/doc for real corpora.
Extraction sample saved at data/real-client/_barbara_extraction.txt (gitignored).
Next: Issue 9 Docling (PDF/docx), then Issue 10 hybrid search + /search. No blockers.

## Issue 10 — Hybrid search + /search  `feat/10-hybrid-search`  [done 2026-07-30]

pgvector cosine + full-text legs (both under RLS) fused with RRF; POST /search with
type filter, 422 on blank query, ranked results with provenance + untrusted label.
(Built before Issue 9 — Docling is a heavy dependency, search had higher value.)

## Issue 11 — /context bundle  `feat/11-context-endpoint`  [done 2026-07-30]

Authority-ordered bundle: voice snapshot (brand-loom shape, derived from quote/
voice_constraint/claims_blacklist atoms) → constraints (always included) →
hybrid-searched atoms (confirmed-first) → full cleaned corpus fast path
(context_full_corpus_max_chars, default 100k chars). Staleness flags, completeness
counts, tenant-scoped, 70 keyless tests green.

## Issue 12 — Live real-provider E2E demo  `feat/12-live-demo`  [done 2026-07-30]

scripts/live_demo.py: Keira transcript + Barbara onboarding through upload → worker →
Claude Opus 5 extraction → Voyage embeddings → Postgres → /search + /context.
Result: 110 atoms; objection search surfaced real objections from both documents with
line+speaker provenance; /context voice snapshot captured faith language + "don't
sanitize her into corporate language"; avoid_phrases carried trauma-content and
income-promise warnings. M1 acceptance criteria 5-7 demonstrated on real data.
Note: Voyage free tier is 3 RPM until a payment method is added — retries absorb it
but ingestion at volume will be slow until then.

## Issue 13 — Operator review workflow (M1C)  `feat/13-review-workflow`  [done 2026-07-30]

POST /v1/clients/{id}/atoms/{atom_id}/decision (confirm | override | deprecate) with
mandatory reason + actor → append-only decisions log (GET /decisions). Override edits
text/payload, re-hashes, re-embeds, confirms. Deprecated atoms excluded from /search,
/context atoms, voice snapshot, and constraints. Reprocessing now replaces only
provisional atoms: reviewed rows survive verbatim (same id/status) and re-extracted
duplicates are skipped by content hash. 76 keyless tests green.

**M1 acceptance criteria: all 11 met** (criteria 5-7 demonstrated live on real client
data via scripts/live_demo.py, the rest by the keyless suite). M1 is COMPLETE.

## Issue 14 — Voice profiles (M2)  `feat/14-voice-profiles`  [done 2026-07-30]

Versioned, diffable, evidence-cited voice profiles (TribeAI schema): We Are/We Are Not
with cited atom evidence + confidence, personality archetype, tone matrix (voice
constant, tone flexes), terminology tiers, language that works/avoid, Open Questions
with mandatory recommendations. Migration 0004 (voice_profiles + RLS; jobs.document_id
nullable for client-level jobs). Builder routes fake/LLM like the atomizer; invented
evidence atom_ids scrubbed. Worker dispatches by job kind. Endpoints: POST build (202,
409 without atoms), GET latest/?version, GET /versions, POST /{v}/approve. Anthropic
provider now streams (SDK 10-min guard on large max_tokens). 80 keyless tests green.

Live build over 105 real atoms: profile caught that the demo corpus mixes TWO people
(Kara + Barbara), listed the exact atom ids to quarantine, flagged the revenue-figure
proof-vs-blacklist conflict, and demanded crisis-support boilerplate before any
ideation reference — the Open Questions pattern working as designed.
Saved: data/real-client/_voice_profile_v1.json (gitignored).

## Issue 9 — Docling PDF/docx ingestion  `feat/9-docling`  [done 2026-07-30]

docling (MIT) installed; pipeline routes .pdf/.docx/.pptx/.xlsx through a lazy
Docling→markdown adapter (module-singleton converter; text/md files never touch it),
then the existing parse→clean→atomise flow. Lineage records the docling version as
parse actor. Fast keyless tests stub the converter; real conversion verified via
RUN_DOCLING=1 (1 passed — model weights cached after first run).

Also fixed in this branch: **tests now run against a dedicated `content_engine_test`
database** (created on demand) — the suite can no longer wipe local dev data.

## DEPLOYED 2026-07-30: live on Render (content-engine-nr4a.onrender.com), full
## pipeline smoke-tested in production. Frontend wiring owned by Saqlain
## (docs/FRONTEND_INTEGRATION.md).
##
## Active queue: (1) merge frontend `feat/engine-wiring` + Vercel env vars [user],
## (2) Voyage payment method [user, pre-demo], (3) real-client onboarding run,
## (4) auth (Clerk/NextAuth -> client_id).
##
## PARKED (user decision, explicit unpark required): MCP server (M3) ·
## Google Drive auto-ingest · Whisper transcription · self-signup + billing ·
## S3/R2 raw storage.

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

## 2026-07-31 — Session: embed fallback + frontend milestone (console, LinkedIn, drill-downs)

Completed (this repo):
- Issue 16 (`feat/16-embed-fallback`): hybrid_search takes `query_embedding | None`;
  /search + /context wrap the embed call and degrade to keyword-only on provider
  failure (Voyage 3 RPM free-tier caused production 500s). 2 regression tests.

Completed (frontend repo, branch `feat/engine-wiring` @ 1089633 — NOT merged):
- /internal redesigned as a proper admin console (roster + detail, stat cards,
  unified single-action upload, paste intake, pipeline table w/ polling)
- Stat-card drill-downs: atoms browser exposing the M1C confirm/deprecate review
  workflow (first UI for it), full voice-profile view w/ Approve, objections filter
- LinkedIn generation: linkedin-post-writer skill (grounding rules override craft),
  context-mined idea cards, free-form chat flow; all 3 generation routes now append
  the full cleaned corpus from /context (fidelity fix)
- Client login links (HMAC, 30d), /profile client view, retry-fetch resilience,
  rotating thinking status; removed "set as active client" module
- `DEMO.local.md` runbook written (gitignored — contains live secrets)

Next:
- User: Voyage payment method, merge frontend branch, Vercel env vars, rotate
  Render DB password, pre-onboard a rich client before demo
- Code (on request): label unwired mock tools "Coming soon"; saved posts w/ atom
  citations; landing-page generator

Blocker:
- None. Voyage 3 RPM cap is the only production risk (mitigated by keyword fallback).
