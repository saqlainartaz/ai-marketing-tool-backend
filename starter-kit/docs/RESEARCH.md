# Precedent Research: Client Content Engine — 2026-07-29

**The idea researched:** a tool that ingests a client's raw pile — call and meeting transcripts, sales calls, footage, brand assets — turns it into structured brand knowledge, and generates LinkedIn posts, landing pages, reel scripts, email sequences and PR angles *in that client's voice*. Stated core: **the ingestion pipeline**. Output is text and scripts for now; image and real video rendering are later roadmap. Users span agency/studio, in-house marketing team, and solo founder.

---

## 1. The number that matters

**142 repos surfaced across 20 search angles. 17 analyzed in depth. 10 overlap meaningfully with the idea. Zero cover it end-to-end.**

**Verdict: the space is Crowded where you are not building, and Open where you are.**

That split is the whole finding, so it's worth stating precisely:

- **Output generation is saturated.** Turning one input into twenty platform-native posts is a solved, commoditised problem with a dozen free implementations. `claude-repurpose` alone ships 19 platform playbooks. `adclaw` ships 122 marketing skills, `marketing-cli` 72. Building this yourself is redundant work.
- **Publishing is saturated and mature.** Postiz (33.9k stars, 74 contributors, released 4 days ago) and BrightBean Studio (2.1k stars) already own self-hosted multi-channel scheduling.
- **Document ingestion is solved as infrastructure.** Docling (63.9k stars, 270 contributors, released today) and Unstructured (15.2k, 147 contributors) convert anything to structured data. Neither knows anything about marketing.
- **Ingestion-as-a-brand-knowledge-product is genuinely unoccupied.** Nobody takes a client's raw first-party corpus — calls, footage, assets — and builds a durable, multi-tenant, versioned brand-knowledge store that grounds generation. The one repo that comes closest to the *concept* has no ingestion code at all.

The most similar single project, **TribeAI's Brand Voice plugin**, describes your premise almost word for word — "the brand knowledge that makes a company recognizable rarely lives anywhere useful… scattered across Notion, Confluence, Google Drive, Gong, Slack, and years of sales calls and meeting transcripts." It then solves it by delegating every ingestion step to Claude Cowork's MCP connectors. Its 27 files are agent prompts and skill definitions. There is no parser, no store, no pipeline. **Your stated core is precisely the part it doesn't build.**

---

## 2. Landscape

| Repo | What it is | Stars | Last push | Licence |
|---|---|---|---|---|
| docling-project/docling | Document parsing for gen-AI; the ingestion standard | 63,940 | 2026-07-29 | MIT |
| gitroomhq/postiz-app | Agentic social-media scheduling platform | 33,906 | 2026-07-29 | AGPL-3.0 |
| Unstructured-IO/unstructured | Open-source ETL: complex documents to clean structured formats | 15,221 | 2026-07-26 | Apache-2.0 |
| brightbeanxyz/brightbean-studio | Self-hosted multi-workspace social management (Buffer alternative) | 2,080 | 2026-07-12 | AGPL-3.0 |
| ashbuilds/payload-ai | AI generation inside Payload CMS (text, image, voice) | 533 | 2026-07-24 | NOASSERTION |
| Laurent00TT/PharosRAG | Local-first agentic RAG: multi-format ingest, hybrid retrieval, ACL, citations | 292 | 2026-07-22 | MIT |
| AgriciDaniel/claude-repurpose | One input to 10+ platform-optimised outputs, 19 platforms | 128 | 2026-04-10 | MIT |
| lukasbach/pensieve | Desktop meeting recorder + local Whisper + local LLM summaries | 113 | 2026-05-30 | NONE |
| eight-acres-lab/openmelon | Content-creation agent runtime: projects, material pool, provenance | 83 | 2026-05-11 | Apache-2.0 |
| dageno-agents/seo-geo-content-engine | SEO/GEO content workflows for brands and agencies | 56 | 2026-07-06 | MIT |
| shyftai/WEBOS | "Content Operating System" — markdown sources of truth + 30 commands | 38 | 2026-03-27 | NOASSERTION |
| TribeAI/claude-cowork-brand-voice-plugin | Scattered brand materials to enforceable AI voice guardrails | 34 | 2026-06-01 | MIT |
| citedy/adclaw | Multi-agent marketing team, 122 skills, shared memory, Docker | 28 | 2026-06-07 | Apache-2.0 |
| MoizIbnYousaf/marketing-cli | Agent-native marketing CLI: 72 skills + compounding brand memory | 27 | 2026-07-28 | MIT |
| inbharatai/SocialFlow | Self-hosted autonomous social CMO, 6 agents, brand kit | 24 | 2026-05-09 | NONE |
| hogan-tech/brand-loom | Model-agnostic marketing skills; open core of hosted Neoxra | 22 | 2026-07-22 | Apache-2.0 |
| inbeomheo/insight-engine | YouTube/docs to 14 content styles; RAG, workspaces, auto-publish | 21 | 2026-07-17 | NONE |

Links to every repo above appear in the deep dives in section 4.

---

## 3. Feature-overlap matrix

Rows are your idea's defining features. ✓ = does it · ~ = partial · ✗ = doesn't.

| Feature | Brand Voice | claude-repurpose | marketing-cli | adclaw | WEBOS | SocialFlow | insight-engine | PharosRAG | Postiz |
|---|---|---|---|---|---|---|---|---|---|
| Multi-source ingestion (transcripts, A/V, brand assets) | ~ delegated | ~ | ~ | ✓ | ✗ | ✗ | ~ | ✓ | ✗ |
| Voice profile extracted from client material | ✓ | ✗ | ~ | ~ | ~ | ~ | ✗ | ✗ | ✗ |
| Multi-tenant / per-client separation | ✗ | ✗ | ✗ | ~ | ~ | ✗ | ~ | ✓ | ✓ |
| Output breadth (LI, landing, reel, email seq, PR) | ~ | ✓ | ✓ | ✓ | ~ | ~ | ~ | ✗ | ✗ |
| Persistent searchable knowledge store / grounding | ~ | ✗ | ~ | ~ | ~ | ✗ | ✓ | ✓ | ✗ |
| Review to approve to publish loop | ~ | ✗ | ~ | ~ | ✓ | ✓ | ✓ | ✗ | ✓ |
| Self-hostable + reuse-friendly licence | ✗ | ✓ | ✓ | ✓ | ~ | ✗ | ✗ | ✓ | ~ |

**Read the matrix by column, not by row.** Every column has holes, and the holes are consistent: the marketing tools have breadth and no memory; the infrastructure tools have memory and no marketing semantics. **No column scores ✓ on ingestion + voice extraction + grounded store together.** That intersection is your idea.

---

## 4. Deep dives

### 4.1 TribeAI / claude-cowork-brand-voice-plugin — the closest concept, the emptiest engine

[github.com/TribeAI/claude-cowork-brand-voice-plugin](https://github.com/TribeAI/claude-cowork-brand-voice-plugin) — *34★ · 5 forks · MIT · 5 contributors · no release · last push 2026-06-01*

**Why it's similar:** it is the only project that frames the problem the way you do — brand knowledge is scattered across sales calls, meeting transcripts, decks and Slack, and the job is to consolidate it into something an LLM can write from. Its three commands map onto your pipeline: `/discover-brand` (ingest), `/generate-guidelines` (voice profile), `/enforce-voice` (generate). Its `conversation-analysis` agent is explicitly for sales-call transcripts.

**Architecture:** 27 files, zero application code. `.mcp.json` wires 7 connectors — Notion, Atlassian, Box, Microsoft 365, Figma, **Gong** and **Granola** — and five markdown agents plus three skills do the reasoning. Ingestion is entirely "ask Claude to search the connectors."

**Execution health:** weak as a product, strong as a specification. Five contributors, no releases, static for ~2 months, built as a Cowork launch-partner marketing artifact by a consultancy. Nobody is going to out-execute you here.

**Worth borrowing:** the *"We Are / We Are Not"* framework as the voice-profile schema; **confidence scoring** on extracted guidelines; and the **Open Questions** pattern — when sources conflict or stated-vs-practiced brand diverges, surface it as a "confirm or override" decision with a recommendation instead of silently guessing. For an agency onboarding a client, that pattern is worth more than any generator. Voice constant / tone flexing by context (cold email vs. proposal vs. LinkedIn) is the right model for your multi-format output. MIT — reuse freely.

### 4.2 AgriciDaniel / claude-repurpose — the output layer, already built

[github.com/AgriciDaniel/claude-repurpose](https://github.com/AgriciDaniel/claude-repurpose) — *128★ · 26 forks · MIT · **1 contributor** · no release · last push 2026-04-10*

**Why it's similar:** it is your generation half in isolation, and it is thorough. 19 platforms with per-platform playbooks including newsletter + **3-email drip sequence**, Instagram reel script, TikTok script, LinkedIn carousel. Its pipeline — extract, then **atomise into 5–15 reusable atoms** (stats, quotes, insights, contrarian takes), then 6 parallel agents, then 30+ organised files — is the sanest generation architecture found in this research.

**Architecture:** 66 files. Real ingestion scripts exist but are thin: `extract_transcript.py`, `transcribe_audio.py`, `extract_article.py`, `fetch_images.py`. Everything else is `skills/*/SKILL.md` prompt packs plus reference files on hook formulas and engagement benchmarks.

**Execution health:** popular but fragile — **one contributor**, no releases, untouched for 3½ months. Treat as a source, not a dependency.

**Worth borrowing:** the atomisation step (your knowledge store should hold atoms, not raw documents); the per-platform reference files; the "why not just cross-post" argument, which is genuinely good positioning material. MIT — you can lift the platform playbooks directly.

### 4.3 MoizIbnYousaf / marketing-cli — the most actively maintained direct competitor

[github.com/MoizIbnYousaf/marketing-cli](https://github.com/MoizIbnYousaf/marketing-cli) — *27★ · MIT · 3 contributors · v0.6.0 · last push 2026-07-28 (yesterday)*

**Why it's similar:** it is the only project explicitly selling **"brand memory that compounds across sessions"** — a `brand/` directory with `voice-profile.md`, `audience.md`, `positioning.md`, `competitors.md`, `learnings.md` and a `SCHEMA.md`, so session 10 starts where session 9 ended. Its dogfood folder shows exactly your output set: `landing-hero.md`, `email-welcome.md`, `lead-magnet-checklist.md`, `seo-outline.md`.

**Architecture:** 1,310 files, TypeScript strict, 2,624 tests, npm-installable, plus a local Next.js "Studio" dashboard. Notably it **chains external CLIs rather than reimplementing** — `whisper-cli`, `yt-dlp`, `ffmpeg`, `firecrawl-cli`, `playwright`, `remotion` — and ships "best-practices skills" documenting how to drive each one.

**Execution health:** the healthiest small competitor. Regular releases, pushed yesterday, real test suite.

**The gap it leaves you:** brand memory is *hand-maintained markdown augmented by research agents*, not *extracted from the client's own corpus*. It researches your brand from the outside (competitors, audience, backlinks). It does not sit on 40 hours of your client's sales calls. And it is single-project by design — no multi-client model. Its chain-don't-reimplement philosophy is the single best strategic lesson in this landscape.

### 4.4 hogan-tech / brand-loom — proof the valuable part is being held back

[github.com/hogan-tech/brand-loom](https://github.com/hogan-tech/brand-loom) — *22★ · Apache-2.0 · 3 contributors · v0.1.0 (2026-07-14) · last push 2026-07-22*

**Why it matters more than its size suggests:** brand-loom is the open core of a commercial product (Neoxra), and the README is unusually explicit about what stays closed. Ten commodity skills ship free — hook, caption, hashtags, repurpose, SEO outline, LinkedIn post. **"Auto voice extraction"**, multi-platform orchestration and the Brand Kit are the hosted paid tier. Every skill takes an optional `brand_context` dict that ships empty.

**Read this as market validation.** A team that studied this space concluded generation is a giveaway and *voice extraction from client material is the thing worth charging for*. That is your core.

**Worth borrowing:** the provider abstraction (OpenAI / Anthropic / Gemini / Ollama / fake) with a **parity eval** proving every skill works on every model, and the `fake` provider that lets the whole system run in CI with zero keys. Both are cheap to copy and disproportionately useful. Apache-2.0.

### 4.5 Laurent00TT / PharosRAG — the ingestion engine you'd otherwise build

[github.com/Laurent00TT/PharosRAG](https://github.com/Laurent00TT/PharosRAG) — *292★ · MIT · **1 contributor** · no release · last push 2026-07-22 · Chinese docs*

**Why it's similar:** it is your core layer, minus marketing. PDFs, scans, docx, pptx, xlsx into chunking, hybrid retrieval, and answers **with citations traceable to the page**, plus enterprise ACL and multi-identity auth (the multi-tenant primitive nobody else here has), exposed over both HTTP and MCP.

**Architecture:** 164 files, Python, Qdrant, a resident daemon that owns the model and vector store so agent sessions become thin clients. Running on 77 documents / 7,652 chunks. Extensive design docs on chunking evaluation and lazy heading trees — though the 12-part learning series is in Chinese.

**Execution health:** solo maintainer, no releases, 292 stars but **0 forks** — read, not adopted. Don't depend on it; do read `docs/methodology/CHUNKING_EVALUATION.md` and the ACL design before designing your own store. MIT.

### 4.6 citedy / adclaw — the only one that claims real content ingestion

[github.com/citedy/adclaw](https://github.com/citedy/adclaw) — *28★ · Apache-2.0 · 5 contributors · v1.0.32 · last push 2026-06-07 · 14 open issues*

**Why it's similar:** the feature table lists **"Content Ingestion — Ingest YouTube, PDFs, web pages, audio"** alongside 122 marketing skills, multi-agent personas with shared memory, and one-click Railway/DigitalOcean deploys. Closest thing to a complete self-hosted marketing system in this set.

**Architecture:** 1,232 files, Python backend + React console, 25 bundled MCP servers, 24 LLM providers with automatic fallback, Telegram/Discord/Feishu channels. Commercially backed by Citedy.

**Health and caution:** genuinely maintained, but the surface area is enormous relative to five contributors, and the personas/shared-memory model is agent collaboration — *not* per-client brand isolation. Interesting detail: every skill gets a security score from a 208-pattern static scan plus LLM audit, which is a real answer to "can I trust community skills." Apache-2.0.

### 4.7 The rest, briefly

- [**shyftai/WEBOS**](https://github.com/shyftai/WEBOS) (38★, 1 contributor, static since March, **NOASSERTION licence**) — a markdown "content OS": `BRAND.md`, `TOV.md`, `AUDIENCE.md`, `LEARNINGS.md` as living sources of truth read before every action, 8 quality gates before any content is approved, and an explicit **Agency multi-brand role**. The quality-gate list (brief, brand, audience, SEO, readability, **source check: claims cited, nothing fabricated**, page type, internal links) is the best review rubric found here. Copy the rubric, not the code — the licence is unclear.
- [**inbeomheo/insight-engine**](https://github.com/inbeomheo/insight-engine) (21★, **no licence**, Korean docs, 1,104 files) — the most complete *ingest, RAG, generate, approve, publish* loop found: 4-stage transcript fallback ending in local Whisper, ChromaDB store, team workspaces with Owner/Editor/Viewer and an approval flow, MCP auto-publish. Also the sharpest warning: **no licence means no code reuse**, whatever the architecture is worth.
- [**eight-acres-lab/openmelon**](https://github.com/eight-acres-lab/openmelon) (83★, Apache-2.0, Go) — matters for your *footage and assets* half and your image/video roadmap: a hash-addressed **material pool**, project-scoped character and reference libraries, creative-continuity "spaces", and **artifact provenance** written to `provenance.jsonl`. The only project treating generated assets as things with traceable lineage.
- [**inbharatai/SocialFlow**](https://github.com/inbharatai/SocialFlow) (24★, **no licence**, 1 contributor) — a Scout, Planner, Creator, Reviewer, Publisher, Analyst agent chain, with a Brand Kit covering colours, logo, fonts, tone, forbidden styles and CTAs. The Brand Kit *schema* is a useful reference for structuring brand assets; the code is unlicensed and single-maintainer.
- [**lukasbach/pensieve**](https://github.com/lukasbach/pensieve) (113★, **no licence**) — local meeting recording with bundled Whisper and local-LLM summaries. Proves the desktop-capture path is viable; can't be reused.
- [**gitroomhq/postiz-app**](https://github.com/gitroomhq/postiz-app) (33.9k★, AGPL-3.0, 74 contributors, released 4 days ago) and [**brightbeanxyz/brightbean-studio**](https://github.com/brightbeanxyz/brightbean-studio) (2.1k★, AGPL-3.0, multi-workspace for agencies) — the publishing layer is finished. Both **AGPL**: fine to self-host beside your product or call over its API; linking their code into a hosted SaaS triggers network copyleft over your whole service.
- [**docling-project/docling**](https://github.com/docling-project/docling) (63.9k★, MIT, 270 contributors, released today) and [**Unstructured-IO/unstructured**](https://github.com/Unstructured-IO/unstructured) (15.2k★, Apache-2.0, 147 contributors) — use one of these for document parsing. Docling is MIT and the more active of the two. Writing your own PDF/pptx/docx parser would be the single clearest waste of effort available to you.

---

## 5. Gap analysis

Your bet was that existing tools generate well but ingest badly. **The research supports the bet, with one correction: they don't ingest badly so much as they don't ingest at all.** Ingestion is either delegated to someone else's connectors (Brand Voice), reduced to four helper scripts (claude-repurpose), chained out to external CLIs (marketing-cli), or solved beautifully in a completely different context (Docling, PharosRAG).

Five specific gaps, ordered by how defensible they look:

1. **Per-client brand knowledge as a first-class, multi-tenant object.** Every marketing tool here is single-brand-per-project — a `brand/` folder or a set of markdown files. An agency running twelve clients gets twelve checkouts. The only multi-tenancy in this landscape lives in publishing tools (Postiz, BrightBean workspaces) and in one RAG project's ACL layer (Pharos). Nobody has *multi-client brand memory with governed ingestion*. This is the clearest hole.
2. **Voice derived from first-party evidence, and versioned.** Brand Voice extracts a profile but stores it as a static guidelines document. marketing-cli maintains one by hand. brand-loom sells extraction as a paid feature. Nobody treats the voice profile as a **versioned artifact recomputed as the corpus grows** — which is exactly what happens in real client work as new calls land every week. "Your voice profile changed after these 6 calls; here's the diff" is a feature nobody offers.
3. **Grounding and traceability in generated marketing content.** PharosRAG cites back to the page; WEBOS has a "claims cited, nothing fabricated" gate. In every generation tool examined, outputs are ungrounded prose. For agency work this is the trust problem: when a client asks "where did this claim come from," the answer should be "your sales call on 14 March at 14:22," not "the model wrote it." This also directly substantiates the "in the client's voice" promise instead of merely asserting it.
4. **Sales calls as a distinct, privileged input.** Brand Voice reaches Gong and Granola via MCP but only mines them for tone. Nobody treats sales calls as what they actually are — a record of the objections, phrasings and proof points that *work on real buyers*. A landing page built from the five objections that recur across 40 calls is a materially different product from a landing page built from a topic prompt. No repo in this set does that.
5. **Footage and brand assets as governed inputs.** Only openmelon treats materials as hash-addressed, provenance-tracked project assets, and it's aimed at character-consistent image generation. Even at text-and-scripts stage, "which brand assets exist, which are current, which are approved" is unowned — and it's the foundation your image/video roadmap will need anyway.

**Where you should not differentiate:** platform-specific output formatting, PDF parsing, scheduling and publishing, hook/caption/hashtag prompt libraries. All four are commodity, free, and better than what a first version would produce.

---

## 6. Recommendation

### REUSE + BUILD — confidence: high on the landscape read, medium on the commercial conclusion

**Build** — and this is the whole product:

- The multi-tenant brand-knowledge store: client, corpus, atoms, **versioned voice profile**, with isolation between clients.
- The marketing-semantic layer over ingestion: not "chunk this PDF" but "this is a sales call; extract objections, proof points, phrasings, the way this person actually opens a pitch."
- Grounding: every generated artifact traces to source atoms with timestamps.
- The agency onboarding path — point it at a new client's pile, get a reviewable voice profile with confidence scores and open questions.

**Reuse** (all permissively licensed, verified in this research):

- **Docling** (MIT) for document parsing. Do not write your own.
- **claude-repurpose** (MIT) platform playbooks and the atomisation model — lift the reference files, skip the runtime.
- **brand-loom** (Apache-2.0) provider abstraction, parity eval, and the `fake` provider for keyless CI.
- **TribeAI Brand Voice** (MIT) voice-profile schema — "We Are / We Are Not", confidence scoring, Open Questions.
- **WEBOS** 8-gate quality rubric — as a rubric, since the licence is NOASSERTION.

**Use, don't absorb:** Postiz or BrightBean for publishing, self-hosted alongside and driven over their API. Both are AGPL-3.0; linking their code into a hosted product would put your entire service under network copyleft.

**Do not reuse code from:** insight-engine, SocialFlow, pensieve (**no licence at all** — the default is all-rights-reserved, regardless of how instructive the architecture is). WEBOS and payload-ai are NOASSERTION — read their licence files before touching either.

**Strategic lesson, from marketing-cli:** orchestrate, don't reimplement. Chain `whisper-cli`, `yt-dlp`, `ffmpeg`, Docling. Your value is the knowledge layer between them, not any individual step.

### What this research could NOT determine

- **The real competition is commercial and invisible to GitHub.** Jasper's Brand Voice, Copy.ai, Writer.com, Typeface, Castmagic, Descript, Opus Clip, Repurpose.io and similar do not publish source. This report maps the open-source landscape only — a clear GitHub gap is not a clear market gap, and on this idea the closed-source field is likely where the actual contest is.
- **Output quality.** Nothing here was run. Whether any of these tools actually reproduce a voice convincingly is unknown from READMEs.
- **Whether stars mean users.** Several competitors are weeks old with promotional READMEs; 292 stars and 0 forks (PharosRAG) suggests reading, not adoption.
- **Non-English projects were assessed partially** — insight-engine documents in Korean, PharosRAG's design series in Chinese. Both may contain relevant detail this report missed.

---

## 7. Methodology appendix

**Run date:** 2026-07-29 · **Tooling:** Precedent (`tools/github_search.py`, `tools/github_repo_details.py`) against the GitHub search API · **Candidates:** 142 unique repos (80 + 63, 1 overlap) · **Deep-analysed:** 17, all fetched successfully with READMEs, no errors.

**Round 1** — 12 queries, `--limit 30 --min-stars 20`:

| Query | Results | Query | Results |
|---|---|---|---|
| multimodal ingestion pipeline | 0 | content repurposing | 3 |
| brand knowledge base | 1 | marketing copy generator | 1 |
| sales call transcript analysis | 0 | linkedin post generator | 5 |
| transcript to content | 5 | topic:content-generation | 28 |
| brand voice AI | 5 | topic:copywriting | 28 |
| writing style clone | 2 | AI ghostwriter | 3 |

**Round 2 (refinement)** — 8 queries, `--limit 30 --min-stars 10`, vocabulary learned from round-1 triage:

| Query | Results | Query | Results |
|---|---|---|---|
| content atomization | 0 | self-hosted social media scheduler | 6 |
| brand memory | 6 | document ingestion library | 2 |
| personal brand agent | 5 | AI content agency | 7 |
| meeting transcript summarizer | 8 | content operating system | 30 |

**Caveats on the numbers.** Three queries returned zero results — GitHub ANDs every search term, so multi-word phrases that read naturally to a human ("content atomization", "sales call transcript analysis") match nothing, even though `claude-repurpose` uses the exact phrase "Content Atomization" in its README body. Counts of 28 and 30 are at or near the 30-per-query cap, so those angles were truncated, not exhausted. Three repos (Postiz, Unstructured, Docling) were added by hand during triage because no query surfaced them — a reminder that keyword recall alone would have missed the two most important reuse candidates in the report.

**The honesty caveat.** This research proves what **exists**. It cannot prove what doesn't. A repo with a vague description, an unusual name, or a non-English README can sit in plain sight and never match a query. Treat "nobody does X" throughout this report as "20 search angles and 17 deep reads did not find anyone doing X."
