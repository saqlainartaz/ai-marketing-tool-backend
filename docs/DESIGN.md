# Client Content Engine — Design & M1 Implementation Plan

## Context

InsideSuccess.TV needs the backend for its end-of-funnel SaaS: a **document-processing
engine** that turns a client's raw pile (sales-call transcripts, onboarding forms, brand
docs) into structured, provenance-tracked, queryable brand knowledge, plus (later) a
versioned voice profile per client. A Next.js frontend already exists in a separate repo
and will consume this engine over REST. Nothing in this repo generates marketing copy.

Initially the InsideSuccess team onboards clients and pre-loads their context; clients get
login credentials to the frontend. Self-signup + paid feature gating come later.

Source docs: `starter-kit/docs/BRIEF.md` (scope, constraints, licence rules) and
`starter-kit/docs/RESEARCH.md` (prior-art survey, 2026-07-29). The repo root for the new
code: `c:\Users\saqla\Desktop\InsideSuccess\marketing tool` (greenfield, not yet git).

## Decisions locked in brainstorming (2026-07-29)

| Decision | Choice | Why |
|---|---|---|
| Operator model | Hosted SaaS backend; team-operated onboarding first, self-signup later | User's funnel model |
| V1 inputs | Text & documents only (PDF, docx, txt, md, transcripts-as-text) | Transcription (Whisper) added later behind same adapter interface |
| Stack | **Python FastAPI monolith**; Next.js frontend stays in its own repo | Reuse list (Docling etc.) is Python-first; OpenAPI → typed TS client for frontend |
| Storage | **Postgres + pgvector** — one DB for relational data, embeddings, profiles, jobs | One backup story, FKs for provenance, fine to millions of atoms |
| Tenancy | **Row-level: `client_id` on every table + Postgres RLS** | DB-enforced isolation; standard SaaS pattern; cheap migrations |
| Interfaces | REST `/v1` now; **MCP server as immediate follow-up milestone** (M3) | Claude-native consumers with zero extra tooling |
| Cleaning | **Type-aware normalize/clean stage inside the pipeline** — no separate ETL infra | Raw file immutable; cleaned text derived; cleaner version recorded; re-runnable |
| M1 scope | Ingestion + query first; voice profile is M2 | Voice quality depends on atoms being right |

## Architecture

```
Next.js frontend (exists, separate repo)
        │  REST /v1, service-token auth
        ▼
FastAPI service (this repo)
  ├─ API layer — clients, documents, atoms, search, context
  ├─ Pipeline — parse (Docling) → clean (type-aware) → atomise (LLM) → embed
  ├─ LLM providers — anthropic | fake   (keyless CI — brand-loom pattern)
  └─ Embedding providers — voyage | fake
        │
        ▼
Postgres + pgvector (RLS per client_id) · Object storage for raw files (S3-compatible; local disk in dev)
```

Background jobs: DB-backed `jobs` table + in-process async worker loop. No Redis/Celery in v1.

## Data model

- **clients** — tenant root. All tables carry `client_id`; RLS enforces isolation.
- **documents** — `source_type` (`sales_call_transcript` | `meeting_transcript` |
  `onboarding_form` | `brand_doc` | `other`), `source_authority` tier (AUTHORITATIVE 1.0 /
  OPERATIONAL 0.8 / CONVERSATIONAL 0.6 / CONTEXTUAL 0.3 / STALE 0.1 — TribeAI weights,
  used for conflict resolution and ranking), `sha256` per client (content-addressed,
  idempotent re-upload), status machine (`uploaded → parsed → cleaned → atomised |
  failed`), raw-file pointer, metadata JSONB (call date, participants), `pipeline_version`.
- **atoms** — typed knowledge unit: `atom_type` (positive: `quote`, `stat`, `story`,
  `insight`, `value_prop`, `howto`, `casestudy`, `positioning`, `terminology`,
  `language_quote`, `concrete_differentiator`; sales-call privileged: `objection`,
  `proof_point`, `phrasing`, `pain_point`; **negative/constraint types**:
  `anti_positioning`, `voice_constraint`, `claims_blacklist` w/ `say_instead`,
  `anti_learning`). **M1 taxonomy is narrowed to 9 types** (reviewer decision): `tldr`,
  `insight`, `pain_point`, `objection`, `proof_point`, `quote`, `terminology`,
  `claims_blacklist`, `voice_constraint` — full taxonomy lands M1B/M2 (enum+prompt
  change only). Fields: text, structured payload JSONB, **provenance** (document_id +
  source sha256, location-in-source, speaker, timestamp), confidence, impact 1-5,
  `evidence_kind` (`measured|quoted|inferred|unverified`), **lifecycle**
  `status` (`provisional|confirmed|deprecated` — extraction yields provisional; operator/
  client confirmation promotes, recorded in a decisions log with reason), `stale_after`
  per atom type (freshness windows), embedding (pgvector), tsvector,
  `content_hash` + `pipeline_version` for idempotency. Reprocessing a doc replaces its
  atoms atomically (confirmed status survives via content-hash matching).
- **voice_profiles** (M2) — versioned JSONB: "We Are / We Are Not" (TribeAI schema, MIT),
  confidence scores, **Open Questions** (source conflicts surfaced as confirm/override
  decisions), corpus snapshot (doc ids) → diffable versions.
- **decisions** — append-only log of confirm/override/deprecate actions on atoms:
  `{atom_id, decision, reason, actor, created_at}` (openmelon pattern).
- **lineage** — append-only per-transformation records: `{document_id, source_sha, stage,
  cleaner_or_model, prompt_hash, params, ts}` — full reproducibility of every atom.
- **jobs** — pipeline job queue/state.

## API contract v1

```
POST /v1/clients                                create client
GET  /v1/clients
POST /v1/clients/{id}/documents                 multipart upload + source_type
GET  /v1/clients/{id}/documents                 list + statuses
GET  /v1/clients/{id}/documents/{doc}           status, provenance detail
POST /v1/clients/{id}/documents/{doc}/reprocess
GET  /v1/clients/{id}/atoms?type=&limit=        list/filter
POST /v1/clients/{id}/search                    hybrid semantic+keyword → atoms w/ provenance
POST /v1/clients/{id}/context                   ★ context-injection: task/topic → bundle
                                                  ordered by authority (confirmed canon →
                                                  constraints/blacklists → personas →
                                                  supporting atoms), each atom w/ provenance
                                                  + staleness flag + usage hints; voice
                                                  snapshot section (tone, audience,
                                                  do_phrases, avoid_phrases — brand-loom
                                                  contract, every field optional)
GET  /health
```

Auth v1: static service API key (frontend server → engine). Per-user auth remains in the
frontend; hardens at self-signup time.

## Licence ledger (binding — from BRIEF.md)

- Reuse freely: Docling (MIT), Unstructured (Apache-2.0), claude-repurpose (MIT),
  brand-loom (Apache-2.0), TribeAI Brand Voice (MIT).
- Ideas only, never code: insight-engine, SocialFlow, pensieve (no licence), WEBOS,
  payload-ai (NOASSERTION).
- AGPL side-car only: Postiz, BrightBean.
- Every new dependency: check licence, record it in the summary.

## Milestones

Reviewer feedback (2026-07-29, approved direction): keep architecture, split M1 into
three thin, independently testable phases. One issue at a time; no future features
outside issue scope.

- **M1 — "Provenance-safe Intake Spine"** (this plan), split:
  - **M1A — Reliable intake spine (keyless end-to-end):** FastAPI skeleton; docker-compose
    Postgres+pgvector; SQLAlchemy+Alembic; clients/documents/atoms/jobs/lineage/decisions
    schema; RLS policies + fail-closed startup; local raw storage; upload + sha256 dedupe;
    text/md parser; transcript cleaner; **deterministic fake atomizer + fake embedder**;
    `/atoms` endpoint; keyless pytest; RLS zero-recall test. No real LLM call anywhere.
  - **M1B — Real retrieval quality:** anthropic LLM + voyage embedding adapters (lazy
    imports, env-gated); structured extraction prompts (narrowed taxonomy); Docling for
    PDF/docx; atom replacement idempotency; hybrid pgvector+tsvector search (both legs
    under RLS); `/search`; `/context`; parity eval; 3-fixture demo.
  - **M1C — Operator review controls:** confirm/override/deprecate endpoints; decisions
    log workflow; confirmed atoms survive reprocessing; review/audit tests.
- **M2:** voice profile extraction (TribeAI schema: We Are/We Are Not w/ evidence,
  tone matrix on 3 dials, terminology tiers, Open Questions w/ mandatory recommendation,
  weighted confidence rollup + WEBOS-style numeric voice spectrums and marketing-cli
  example lines), versioning + diffs, review/approve endpoints, per-client
  knowledge-completeness score (L0-L4).
- **M3:** MCP server over the same query layer.
- **Later:** audio/video transcription, user auth + billing, connectors (Zoom/Fathom/
  Granola/GHL auto-pull).

## Working agreements (from reviewer feedback)

- **Operating files at repo start:** `IDEA.md`, `TASKS.md`, `RETRO.md`, `docs/DESIGN.md`,
  `docs/M1_SCOPE.md`, `docs/API_CONTRACT.md`, `docs/DECISIONS.md`,
  `docs/AI_CODING_RULES.md` (product boundary, hard non-goals, M1 priorities, required
  tests — content per reviewer spec), `docs/DEPLOY_CHECKLIST.md` (stub) and `.github/`
  templates (stubs — no GitHub remote yet; issues live in `TASKS.md` until one exists).
  **A repo `CLAUDE.md` embeds/points to AI_CODING_RULES.md** so the rules actually load
  into every Claude session.
- **Issue-based workflow:** work is broken into issue-style tasks in `TASKS.md`, each
  with Goal / Scope / Non-goals / Done-when / Tasks (failing test → minimal code →
  targeted test → full pytest → docs). One issue at a time.
- **Branches & commits:** one branch per issue (`feat/1-project-skeleton`,
  `feat/2-schema-rls`, `feat/3-upload-dedupe`, `feat/4-parse-clean`,
  `feat/5-fake-providers`, `feat/6-search-context`, `feat/7-e2e-demo`); conventional
  commits (`feat(db): add documents table with RLS`).
- **Breadcrumbs:** end of each issue/session, write Completed / Next / Blocker to the
  issue or `TASKS.md`.
- **Prompt-injection hygiene (M1 requirement):** uploaded docs are untrusted input —
  document text is delimited as data in extraction prompts (never interpretable as
  instructions), retrieved text labeled `trust: untrusted` in API responses, PII
  minimized in atoms (TribeAI redaction guardrails), raw files immutable and private.
- **Hard non-goals for M1:** no frontend, no copy generation, no billing, no self-signup,
  no Redis/Celery, no real API keys in tests, never bypass RLS, never drop provenance,
  no new dependency without licence check recorded.

## M1 implementation steps

1. **Repo skeleton & tooling** — `git init`; `uv` project; FastAPI, SQLAlchemy 2 + Alembic,
   pydantic-settings; `docker-compose.yml` with `pgvector/pgvector` Postgres image;
   pytest + keyless-CI wiring; operating files above; save the approved design doc under
   `docs/DESIGN.md`.
2. **Schema + RLS migration** — tables above (incl. decisions + lineage); RLS policies
   keyed on `current_setting('app.client_id')`; per-request session-variable middleware;
   **fail-closed startup** (refuse to boot on missing/invalid tenant-auth config);
   **cross-tenant zero-recall regression test** (keyless, fake embeddings — PharosRAG
   `acl_regression` pattern).
3. **Providers** — `LLMProvider` Protocol (anthropic | fake) and `EmbeddingProvider`
   (voyage | fake): registry + env-var resolution + lazy vendor imports (brand-loom
   pattern, Apache-2.0); FakeProvider deterministic (echo + shape-valid JSON);
   FakeEmbedder = hash-based deterministic vectors; parity-eval script (fake always,
   real providers auto-gated on env keys, exit 1 on failure).
4. **Upload + raw storage** — multipart endpoint, sha256 content addressing + dedupe,
   local-disk storage adapter behind an S3-compatible interface.
5. **Parse stage** — Docling adapter → structured text with location map + **eager
   heading tree** (`breadcrumb`, `section_anchor`, `level_reliable`; strip TOCs).
6. **Clean stage** — type-aware cleaners (transcript normalizer first: speaker labels,
   filler stripping, timestamp collapsing; PII redaction per TribeAI guardrails);
   cleaner version recorded in lineage; golden-file tests on fixture transcripts.
7. **Atomise stage** — sectioned extraction windows (~800 tokens, min 200, max 1500,
   merge-up via breadcrumb); type-specific prompts (sales-call privileged taxonomy incl.
   negative types; composition guardrails: 5-15 atoms/doc, ≥1 tldr + ≥1 insight; ≤125-char
   quotes); structured-output parsing; atoms land `provisional`; prompt_hash recorded in
   lineage; atom replacement idempotency (confirmed status survives via content_hash).
8. **Embed + search** — pgvector + tsvector hybrid (RRF), **both legs under RLS**;
   `/search` endpoint; client_id assertion at response layer.
9. **Context endpoint** — authority-ordered bundle (see API contract) with staleness
   flags and voice snapshot; response shape = brand-loom `brand_context` superset.
10. **Jobs + status** — DB job table, async worker loop, document status transitions,
    `/reprocess`; atom confirm/override endpoint writing to decisions log.
11. **E2E demo test** — fake client, 3 fixture docs (synthetic sales-call transcript,
    onboarding form, brand PDF), assert objections retrievable with provenance pointing
    at the fixture transcript, zero keys required.

Phase mapping: **M1A** = steps 1, 2, 3 (fake providers only), 4, 5 (text/md only),
6, 7 (fake atomizer), 10 (jobs/status; not confirm endpoints), `/atoms` endpoint.
**M1B** = 3 (real adapters + parity eval), 5 (Docling PDF/docx), 7 (real extraction
prompts), 8, 9, 11. **M1C** = confirm/override/deprecate endpoints + decisions workflow
+ confirmed-atom survival tests.

## Verification — M1 demo acceptance criteria (reviewer-approved; M1 done only when all pass)

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

## Research refinements (from repo-mining agents)

### From TribeAI Brand Voice (MIT — adopt wholesale for M2 voice profiles)

- **Voice-profile JSON schema**: We Are / We Are Not pairs (4-7 rows), each attribute
  with `what_it_means`, `how_it_shows_up`, `what_to_avoid`, `evidence[]` (cited quotes),
  `confidence`; personality archetype; message pillars (with frequency % + effectiveness);
  terminology tiers (must-use / preferred / avoid / never-use); language-that-works +
  anti-patterns; generation metadata (version, replaces, sources, doc/conversation counts,
  overall confidence). Rule: omit empty sections; every example carries source attribution.
- **Tone model**: voice constant, tone flexes on exactly 3 dimensions — Formality, Energy,
  Technical Depth — in a context matrix (cold outreach / discovery / demo / proposal /
  follow-up / social / customer success). Compact and queryable per channel.
- **Confidence scoring**: High/Medium/Low per section with explicit criteria
  (corroborating-source count, explicitness, consistency, unresolved conflicts); numeric
  rollup with section weights (voice 30%, messaging 25%, tone 20%, terminology 15%,
  language 10%; H=1.0 M=0.6 L=0.3).
- **Open Questions object**: `{title, what_was_found, recommendation, decision_needed,
  priority}` — every question MUST include a recommendation. Conflict policy: recent wins
  unless older source is marked official.
- **Source authority tiers** → new `source_authority` field on documents:
  AUTHORITATIVE 1.0 / OPERATIONAL 0.8 / CONVERSATIONAL 0.6 / CONTEXTUAL 0.3 / STALE 0.1.
- **Sales-call extraction spec** (conversation-analysis agent): voice attributes,
  messaging patterns w/ frequency+effectiveness, tone by conversation phase, success
  phrases ("questions that engage", objection-handling patterns), anti-patterns.
  Guardrails: min 3 conversations before asserting a pattern, PII redaction, ≤125-char
  quotes, anonymized attribution.

### From claude-repurpose (MIT — extends atom model)

- Atom taxonomy to merge with ours: `tldr`, `stat`, `quote`, `insight`, `question`,
  `contrarian`, `howto`, `analogy`, `casestudy`, `prediction` (+ our privileged types
  `objection`, `proof_point`, `phrasing`, and `pain_point`, `terminology`, `positioning`,
  `story`, `value_prop`).
- Per-atom **impact rating 1-5** (standalone-viability) as a quality field.
- Composition guardrails for extraction prompts: 5-15 atoms per doc, always ≥1 `tldr` +
  ≥1 `insight`.
- `/context` bundle shape: typed+rated atoms, document-level framing (main argument,
  audience, topic), voice snapshot, options — one bundle.
- Their atoms carry **no provenance** — confirmed our provenance-on-every-atom design is
  the differentiator; keep TribeAI's evidence-citation discipline instead.
- Script conventions worth copying: JSON-to-stdout/diagnostics-to-stderr envelope with
  `error` field; SSRF guards on any future URL fetching.

### From WEBOS (ideas only — NOASSERTION), openmelon (Apache-2.0), marketing-cli (MIT)

- **Negative knowledge is first-class** (all three converge): atom types must include
  `anti_positioning`, `voice_constraint`, `claims_blacklist` (with `say_instead`),
  `anti_learning`, "words we don't use + why". Auto-extraction naturally produces
  positives; consumers demonstrably need the negatives.
- **Atom lifecycle** (openmelon's assumption→canon ladder): extracted atoms are
  `provisional`; operator/client confirmation promotes to `confirmed`, recorded in a
  **decisions log** `{atom_id, decision, reason, weight, created_at}`; feedback never
  silently overrides confirmed atoms.
- **Freshness windows** (marketing-cli): `stale_after` per atom type (e.g. market claims
  14d, voice/positioning 30d, keywords 90d, visual 180d); `/context` flags stale atoms.
- **Evidence discipline** (marketing-cli): `evidence_kind: measured|quoted|inferred|
  unverified`; "not measured, never fabricate" — no silent assertion.
- **Completeness ladder** (marketing-cli L0-L4): per-client knowledge-completeness score
  in the API — tells consumers how much to trust the context (M2).
- **Content addressing** (openmelon): raw files stored by sha256; append-only **lineage**
  records per transformation `{source_sha, stage, model, prompt_hash, generation_params,
  ts}` — makes "no fabricated claims" mechanically checkable downstream (WEBOS gate 6).
- **WEBOS 8-gate rubric** documented for downstream consumers (brief/brand/audience/SEO/
  readability/source-check/page-type/links) — our provenance makes gate 6 verifiable.
- **marketing-cli SCHEMA.md** = the consumer contract to satisfy: voice profile
  (personality, preferred/avoid vocabulary, verbatim example lines), positioning
  (anti-positioning, falsifiable differentiators), audience archetypes (`one_liner,
  demographic, top_pain, top_desire, watering_hole, language_quote`), claims blacklist.
  Our sales-call ingestion uniquely produces `language_quote` atoms.

### From brand-loom (Apache-2.0) + PharosRAG (MIT — design input, not dependency)

- **Provider pattern (copy near-verbatim)**: `LLMProvider` Protocol, registry + env-var
  resolution, lazy vendor imports with install-hint errors; `FakeProvider` fully
  deterministic (echo + shape-valid JSON when prompt requests JSON). Extend the pattern
  to a **fake embedding provider** (hash-based deterministic vectors). CI runs with zero
  secrets because fake is the default.
- **Parity eval**: fake always runs; real providers auto-included only when their env key
  exists; minimal well-formedness assertions; matrix report; exit 1 on failure.
- **Chunking numbers (measured, PharosRAG)**: target 800 tokens, min 200, max 1500;
  merge undersized sections upward via heading breadcrumb; strip TOCs at ingest. Lesson:
  don't over-invest in boundary algorithms — invest in provenance metadata + structure.
- **Eager heading tree** (~1ms/doc): per-chunk `breadcrumb`, `section_anchor`,
  `level_reliable` — copy onto atoms' provenance.
- **Tenancy discipline**: fail-closed at startup (refuse to boot on bad tenant config);
  RLS enforced inside every hybrid-search CTE (vector + FTS legs both under RLS, never
  filter after fusion); belt-and-braces client_id assertion at response layer; a
  **cross-tenant zero-recall regression test** that runs keyless with fake embeddings.
- **Citation contract**: `{page, span}` + `context_status: full_section|section_window`;
  tag retrieved text `trust: untrusted` (prompt-injection hygiene for MCP consumers).
