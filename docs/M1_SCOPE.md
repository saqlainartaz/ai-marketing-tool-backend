# M1 — Provenance-safe Intake Spine

M1 proves, end-to-end and keyless, that the backend can take a client's documents and
return provenance-tracked, tenant-isolated, queryable atoms.

Phases (one issue at a time — see TASKS.md):

- **M1A — Reliable intake spine.** FastAPI skeleton; Postgres+pgvector via docker
  compose; SQLAlchemy+Alembic; clients/documents/atoms/jobs/lineage/decisions schema;
  RLS + fail-closed startup; local raw storage; upload + sha256 dedupe; text/md parser;
  transcript cleaner; deterministic fake atomizer + fake embedder; `/atoms`; keyless
  pytest; RLS zero-recall test. **No real LLM call anywhere.**
- **M1B — Real retrieval quality.** Anthropic + Voyage adapters (env-gated, lazy);
  structured extraction prompts (9-type taxonomy); Docling for PDF/docx; atom
  replacement idempotency; hybrid pgvector+tsvector search (both legs under RLS);
  `/search`; `/context`; parity eval; 3-fixture demo.
- **M1C — Operator review controls.** Confirm/override/deprecate endpoints; decisions
  log workflow; confirmed atoms survive reprocessing; review/audit tests.

## M1 atom taxonomy (narrowed — full taxonomy is M1B/M2)

`tldr` · `insight` · `pain_point` · `objection` · `proof_point` · `quote` ·
`terminology` · `claims_blacklist` · `voice_constraint`

## Out of scope for all of M1

Voice profile extraction (M2) · MCP (M3) · billing · self-signup · frontend ·
marketing copy generation · audio/video transcription · Redis/Celery.

## Acceptance criteria — M1 is done only when all pass

1. Create Client A and Client B.
2. Upload 3 fixture documents for Client A.
3. Upload overlapping content for Client B.
4. Pipeline creates provisional atoms.
5. Search "what objections do customers raise?"
6. Results include atom text, source document, location, confidence, evidence kind,
   authority tier, and client_id.
7. `/context` returns a usable bundle with provenance and staleness flags.
8. Client B cannot retrieve Client A's atoms (asserted with the response-layer guard
   disabled — DB-level RLS alone must block leakage).
9. Re-upload of the same file creates no duplicates.
10. Reprocess does not duplicate atoms.
11. `pytest` passes with zero API keys; fake providers are deterministic; parity eval
    passes on fake, real-provider columns appear when keys are set.
