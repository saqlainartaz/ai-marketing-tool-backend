# IDEA

**Client Content Engine** — the end-of-funnel backend for InsideSuccess.TV clients.

Turn each client's raw pile (sales-call transcripts, onboarding forms, brand docs —
later audio/video) into structured, provenance-tracked, queryable brand knowledge with
a versioned voice profile. Downstream tools (LinkedIn posts, landing pages, reel
scripts, email sequences) consume this engine over REST/MCP; the engine itself never
writes marketing copy.

**Why this exists:** research (starter-kit/docs/RESEARCH.md, 2026-07-29) showed
generation and publishing are saturated open-source spaces; document parsing is solved
as libraries; but nobody has built multi-tenant, marketing-semantic, provenance-tracked
ingestion as a product. Sales calls as privileged input (objections, proof points, real
phrasings that work on buyers) is the sharpest differentiator.

**Business model:** InsideSuccess team onboards funnel clients and pre-loads context;
clients get frontend logins. Later: self-signup with paywalled features.

**North-star answer the engine must always give:** "Where did this claim come from?" →
"Your sales call on 14 March at 14:22" — never "the model wrote it."
