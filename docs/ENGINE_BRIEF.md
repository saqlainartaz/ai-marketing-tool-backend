# Client Content Engine — Brief

*One-page overview of the backend. Written 2026-07-31. Deep detail lives in
`docs/DESIGN.md` (architecture), `docs/API_CONTRACT.md` (endpoints), and
`TASKS.md` (build history).*

## What it is

A multi-tenant document-processing engine for InsideSuccess.TV. The team drops
a client's raw materials in — sales-call transcripts, onboarding forms, brand
docs — and the engine turns them into **structured, provenance-tracked,
queryable brand knowledge**: typed knowledge atoms, hybrid search, a
context-injection endpoint, and a versioned voice profile per client. A
Next.js frontend (separate repo) consumes it over REST and does the actual
copy generation; **this engine never writes marketing copy itself**.

Live at `https://content-engine-nr4a.onrender.com` (Render: Docker web service
+ managed Postgres 17 with pgvector + persistent disk for raw files).

## Why it exists (vs. plain RAG)

Generic RAG retrieves text chunks. This engine ships four guarantees chunks
can't:

1. **Provenance** — every fact traces to a source document, line numbers, and
   speaker; every transformation is logged (append-only lineage).
2. **Human-governed trust** — atoms have a lifecycle
   (`provisional → confirmed / deprecated`). Extraction output is machine
   opinion until a human confirms it; removed atoms never reach generation;
   decisions are audit-logged and survive reprocessing.
3. **Negative knowledge** — the taxonomy includes `claims_blacklist` and
   `voice_constraint`: things a client must *never* say, always injected into
   generation context.
4. **DB-enforced isolation** — Postgres Row-Level Security (ENABLE + FORCE)
   on every tenant table; the app connects as a non-superuser role, so no app
   bug can leak one client's data to another. Proven by zero-recall
   regression tests with the app-layer guard disabled.

## How it works

```
upload (sha256-addressed, immutable, deduped)
  → parse   (text/md natively; PDF/docx/pptx via Docling)
  → clean   (type-aware: speaker labels, fillers, timestamps, PII redaction)
  → atomise (Claude extracts ≤60 typed atoms/doc; line-numbered data block
             so documents can't prompt-inject)
  → embed   (Voyage voyage-4, 1024-dim)
```

Jobs run on a DB-backed queue with an in-process async worker — no
Redis/Celery. Statuses: `uploaded → parsed → cleaned → atomised | failed`.

**Atom taxonomy (9 types):** tldr, insight, pain_point, objection,
proof_point, quote, terminology, claims_blacklist, voice_constraint. Each
atom carries text, payload, provenance, confidence, impact 1–5, evidence kind
(`measured/quoted/inferred/unverified`), and status.

**Retrieval:** hybrid search — pgvector cosine + Postgres full-text, fused
with Reciprocal Rank Fusion, both legs under RLS. Degrades gracefully to
keyword-only if the embedding provider is down or rate-limited.

**`/context` (the product):** one call returns everything a generator needs —
voice snapshot, constraints (blacklists always included), confirmed-first
retrieved atoms with provenance and staleness flags, and the full cleaned
corpus when it fits (≤100k chars), so generation sees the whole picture.

**Voice profiles (M2):** built async by the worker from the atom corpus.
TribeAI schema — We Are / We Are Not pairs with evidence and confidence, tone
matrix, terminology tiers, and Open Questions (each with a mandatory
recommendation). Versioned, diffed, draft → approved lifecycle.

## API surface (service-key auth, `/v1`)

Clients CRUD · document upload/list/status/reprocess · atoms list ·
atom decisions (confirm/override/deprecate) · decisions log · search ·
context · voice-profile build/get/versions/approve · health.

## Engineering discipline

- **Keyless CI:** 85 tests pass with zero API keys — deterministic fake
  LLM/embedding providers are the default; real providers (Claude Opus,
  Voyage) activate via env vars only.
- **TDD, one issue at a time**, conventional commits, breadcrumbs in
  `TASKS.md`; licence checked and recorded for every dependency.
- **Fail-closed config:** the service refuses to boot without valid
  service-token and tenant settings.

## Status & roadmap

**Done:** M1 (intake spine, real extraction, hybrid search, context, review
workflow) · M2 (voice profiles) · Docling ingestion · Render deployment ·
embedding-outage fallback.

**Parked (explicit decision required to unpark):** MCP server · Google Drive
auto-ingest · Whisper transcription · self-signup + billing · S3/R2 storage.
