# CLAUDE.md

Guidance for Claude Code working in this repository.

## What this project is

A **document-processing engine** that turns a client's raw pile — call and meeting
transcripts, sales calls, footage, brand assets — into structured, provenance-tracked,
queryable brand knowledge, including a versioned voice profile per client.

This is **backend infrastructure**. Downstream tools (LinkedIn posts, landing pages, reel
scripts, email sequences, PR angles, and future features) consume this engine. **Nothing in
this repo generates marketing copy.** If a task drifts toward generation, that belongs in a
consumer, not here.

Read `docs/BRIEF.md` before starting substantive work. It carries the scope boundary, the
design constraints, and the licence rules. `docs/RESEARCH.md` is the prior-art survey the
brief is built on — consult it before proposing to build something from scratch.

## Non-negotiables

These follow from being shared infrastructure. Don't trade them away for speed.

- **Multi-tenancy is a primitive.** Client isolation is designed in, never retrofitted.
- **Provenance is structural.** Every atom carries source, location within source, and
  timestamp. No exceptions, no "we'll add it later."
- **The public API is a contract.** Downstream tools bind to it. Version it; treat breaking
  changes as significant events, not refactors.
- **Idempotent ingestion.** The same input twice yields the same atoms.
- **Orchestrate, don't reimplement.** Chain Docling, Whisper, `yt-dlp`, `ffmpeg`. Never write
  a document parser.

## Licence rules

Binding — see `docs/BRIEF.md` for the full list and reasoning.

- **Reuse freely:** Docling (MIT), Unstructured (Apache-2.0), claude-repurpose (MIT),
  brand-loom (Apache-2.0), TribeAI Brand Voice (MIT).
- **Never copy code from** `insight-engine`, `SocialFlow`, `pensieve` — no licence means all
  rights reserved. Reading for design ideas is fine.
- **AGPL (Postiz, BrightBean):** call over an API or run as a side-car. Never link into this
  codebase.
- Before adding any new dependency or lifting any code, **check the licence and say what it
  is** in your summary.

## How to work here

- Before building anything, check whether a maintained library already does it. The research
  doc exists so this repo doesn't rebuild solved work.
- Prefer a `fake` / no-key provider path so the whole system runs in CI without API keys.
  (Pattern borrowed from brand-loom — worth setting up early rather than bolting on.)
- When sources conflict or something is genuinely ambiguous, surface it as a decision with a
  recommendation rather than guessing silently. This applies to your own work and to the
  product's behaviour when a client's materials disagree with each other.
- Record architectural decisions and their reasoning as you make them. The stack, storage,
  tenancy model and atom schema are all still open — whoever picks them should write down why.

## Current state

Greenfield. Stack undecided. The one constraint: the reuse list is Python-first, so anything
else needs a service boundary to a Python ingestion worker or means reimplementing solved
work. See "Open decisions for the first session" in `docs/BRIEF.md`.
