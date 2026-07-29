# AI Coding Rules

## Product boundary

This repo is a backend document-processing engine for client brand/customer context.

It ingests raw material and returns structured, provenance-tracked, queryable knowledge.

## Hard non-goals for M1

- Do not build frontend UI.
- Do not generate marketing copy.
- Do not add billing.
- Do not add self-signup.
- Do not add Redis, Celery, or external queue infrastructure.
- Do not require real Anthropic/Voyage keys for tests.
- Do not bypass Postgres RLS.
- Do not silently drop provenance.
- Do not add dependencies without checking and recording license compatibility.

## M1 priorities

1. Reliable ingestion
2. Immutable raw files
3. Parse/clean pipeline
4. Deterministic fake providers
5. Provenance on every atom
6. Tenant isolation through RLS
7. Search/context endpoints
8. Keyless E2E demo

## Required tests

- pytest passes with zero API keys
- duplicate upload creates no duplicates
- reprocess is idempotent
- search/context return provenance
- cross-tenant zero-recall passes at DB level
- fake providers are deterministic

## Prompt-injection hygiene (M1 requirement)

Uploaded documents are untrusted input:

- Document text is delimited as data in extraction prompts — never interpretable as
  instructions.
- Retrieved source text is labeled `trust: untrusted` in API responses.
- Atoms carry no unnecessary PII (redaction guardrails in the clean stage).
- Raw files are immutable and private.

## Workflow

- Issue-based: every task lives in `TASKS.md` with Goal / Scope / Non-goals / Done-when.
  One issue at a time. Do not add future features unless explicitly in issue scope.
- One branch per issue (`feat/N-slug`); conventional commits
  (`feat(db): add documents table with RLS`).
- TDD per issue: failing test → minimal code → targeted test → full pytest → docs.
- End every issue/session with a Breadcrumb (Completed / Next / Blocker) in `TASKS.md`.
