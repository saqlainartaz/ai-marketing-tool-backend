# Brief: Client Content Engine — ingestion core

## What this is

A **document-processing engine** that turns a client's raw pile — call and meeting
transcripts, sales calls, footage, brand assets — into structured, provenance-tracked,
queryable brand knowledge, including a versioned **voice profile** for that client.

It is **backend infrastructure**. Every downstream tool — LinkedIn posts, landing pages,
reel scripts, email sequences, PR angles, and whatever comes later — is a *consumer* of
this engine, not a part of it. Nothing in this repo generates marketing copy.

## Why this shape

From the prior-art research in `docs/RESEARCH.md` (142 GitHub repos surveyed, 17 analyzed
in depth, 2026-07-29):

- **Generation is saturated.** One free project ships 19 platform playbooks; another ships
  122 marketing skills. Building generation is redundant work.
- **Publishing is finished.** Postiz (33.9k★) and BrightBean own self-hosted scheduling.
- **Document parsing is solved as libraries.** Docling (63.9k★) and Unstructured (15.2k★)
  convert anything to structured data — and neither knows anything about marketing.
- **Nobody has assembled ingestion into a product.** No project surveyed builds a
  multi-tenant, marketing-semantic, provenance-tracked brand-knowledge layer. The single
  closest competitor states the same premise and then delegates 100% of ingestion to
  someone else's connectors — it has no parser, no store, no pipeline.

The gap is exactly where this engine sits.

## What being shared infrastructure means

These are the constraints that follow from "everything else depends on this." They are more
important than any individual feature.

1. **The API contract is the product.** Downstream tools bind to it. Design and version the
   contract before optimising internals. A breaking change here breaks every tool at once.
2. **Multi-tenancy from day one.** Client isolation must be a primitive, not a later
   migration. Every surveyed marketing tool is single-brand-per-project and would need a
   rewrite to serve an agency; retrofitting tenancy into shared infrastructure is the single
   most expensive mistake available here.
3. **Provenance is structural, not a feature.** Every atom carries source, location within
   source, and timestamp. Downstream tools must be able to answer "where did this claim come
   from" — *"the sales call on 14 March at 14:22"*, not *"the model wrote it."* This is also
   what substantiates the "in the client's voice" promise instead of merely asserting it.
4. **Format extensibility behind a stable interface.** Text and transcripts now; image, then
   video later. Adding a modality must not change the contract. Ingestion adapters pluggable.
5. **Idempotent and reprocessable.** The same file ingested twice yields the same atoms. The
   corpus grows weekly as new calls land, so the voice profile must recompute over a changed
   corpus without duplicating anything. Profile versions should be diffable — *"the voice
   profile changed after these 6 calls, here's what moved."*
6. **Sales calls are a privileged input type, not just another document.** They record the
   objections, phrasings and proof points that actually work on real buyers. Extract those as
   first-class structures. No surveyed project does this, and it is the sharpest
   differentiator available.

## Scope boundary

**In scope:** ingestion adapters, parsing, transcription, atomisation, the knowledge store,
tenancy and access control, voice-profile extraction and versioning, the query/retrieval API.

**Out of scope for this repo:** copy generation, platform-specific formatting, scheduling,
publishing, analytics, any UI beyond what's needed to review a voice profile.

## Reuse and licence rules (hard constraints)

Verified during the 2026-07-29 research. Treat as binding.

**Safe to reuse:**
- **Docling** (MIT) — document parsing. Do not write your own PDF/docx/pptx parser.
- **Unstructured** (Apache-2.0) — alternative/complement for ETL.
- **claude-repurpose** (MIT) — its *atomisation* model and per-platform reference files.
- **brand-loom** (Apache-2.0) — provider abstraction, parity eval, and the `fake` provider
  pattern that lets the whole system run in CI with zero API keys. Copy this early.
- **TribeAI Brand Voice** (MIT) — voice-profile schema: the "We Are / We Are Not" framework,
  confidence scoring, and the **Open Questions** pattern (when sources conflict, surface a
  "confirm or override" decision with a recommendation rather than guessing silently).

**Never copy code from** — no licence at all, which means all rights reserved regardless of
how instructive the architecture is: `inbeomheo/insight-engine`, `inbharatai/SocialFlow`,
`lukasbach/pensieve`. Reading them for design ideas is fine; copying is not.

**AGPL — API or side-car only:** Postiz, BrightBean. Self-host beside the product or call
over HTTP. Linking their code into a hosted service triggers network copyleft across the
entire service.

**NOASSERTION — read the licence file first:** WEBOS, payload-ai.

## Stack

Undecided — settle it in the first session. The one hard constraint: the reuse list above is
Python-first (Docling, Unstructured, Whisper, most vector stores). Anything else means either
a service boundary to a Python ingestion worker or reimplementing solved work. Choose
deliberately, and record the choice and its reasoning.

## Guiding principle

**Orchestrate, don't reimplement** — the clearest lesson from the healthiest competitor
surveyed. Chain Docling, Whisper, `yt-dlp`, `ffmpeg`. The value is the knowledge layer
between them, not any individual step.

## Open decisions for the first session

- Stack and service topology (single service vs. ingestion worker + API).
- Storage: vector store choice, and whether atoms live in the same store as their embeddings.
- The tenancy model — row-level isolation, schema-per-client, or separate stores.
- The atom schema, and how a voice profile is represented and versioned.
- Whether the first consumer is built in-repo as a reference client or kept fully external.

## A note on the research

`docs/RESEARCH.md` is a snapshot dated **2026-07-29**. It proves what existed on that date —
it cannot prove what doesn't exist, and several competitors were weeks old and moving fast.
Re-check the licence and activity of anything before depending on it. The strongest
commercial competition (Jasper, Copy.ai, Writer.com, Castmagic, Descript) is closed-source
and was invisible to that research entirely.
