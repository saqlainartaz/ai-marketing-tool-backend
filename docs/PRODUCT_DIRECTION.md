# Product Direction — Who Uses This Tool, and What We Build For Them

**Status:** planning document. Adopted direction, no build commitment — every build
item here still goes through the normal issue workflow before any code changes.
**Date:** 2026-08-01
**Inputs:** the team persona research deck ("Five people. Five paths.", 2026-08-01,
built from our own 2,438 customers), a four-stream research pass (GitHub prior-art
via Precedent, competitor UX, agency approval workflows, cross-industry UX
patterns — sources in appendix), and a code-level feasibility audit of the current
app and engine.

---

## 1. Why this document exists

Friday's demo proved the technology works: engine ingests a client's raw material,
extracts provenance-tracked knowledge, builds a voice profile, and generates
grounded LinkedIn posts. What the demo also revealed: **the app was implicitly
designed for one kind of person** — someone who already knows what they want to
say and is comfortable in a chat/editor workspace. Nobody on the team could
sharply answer "who exactly is this for?"

The persona deck answered that with real customer data. This document turns the
deck plus independent research into an adopted product direction: who the users
are, what each needs, what we validated and pushed back on, what order to build
in, and which decisions remain open.

**The thinking order (from the deck, adopted as a standing rule):**
WHO is it for → what do they want to ACHIEVE → how do they BEHAVE → *then* design
the screen. The screen is the last decision, not the first.

---

## 2. The sorting model

Two questions split the entire customer base:

|  | **Knows HOW to do it** | **Doesn't know HOW** |
|---|---|---|
| **Knows WHAT to do** | Aspiring Authority (~20%) | Busy Operator (~30%) · Careful Professional (~25%) · Delegator (~15%) |
| **Doesn't know WHAT** | (rare in our base) | Overwhelmed Newcomer (hidden, big) |

Friday's app was built for the top-left cell. **~70% of the base lives in the
right column** — people who know the outcome they want but will not (or cannot)
operate a content workspace to get it.

---

## 3. The five personas

Percentages are of our 2,438-customer base, from the team deck.

### 3.1 The Busy Operator (~30%)
- **Who:** 50s. Runs a $1–5M trade or service business — roofer, contractor,
  restaurant owner. On job sites all day, phone in hand.
- **Wants to achieve:** more calls and booked jobs. Not "a LinkedIn post" — the
  post is a means.
- **Behavior:** phone-first, no patience. Will not learn, will not type, will not
  browse. Any task longer than ~30 seconds is abandoned.
- **Their ideal path:** gets a text "5 posts ready for August" → opens on phone in
  the truck → taps approve on 4, rejects 1 → posts go out with call-to-action →
  sees "12 calls came from your posts."
- **Stays if:** he can see the calls it brought. **Quits if:** the app asks him to
  think or type.

### 3.2 The Careful Professional (~25%)
- **Who:** 40s–60s. Doctor, lawyer, financial advisor. Reputation and compliance
  come first; one wrong AI sentence under their name is a disaster.
- **Wants to achieve:** more patients/clients, at zero reputational risk.
- **Behavior:** desktop, deliberate. Reads everything before it goes anywhere.
  Control beats speed. Will ask "where did this claim come from?"
- **Their ideal path:** weekly email "3 drafts await review" → reads each on
  desktop → checks the source of a claim → edits one line, approves two → archive
  shows what was published and when.
- **Stays if:** control, receipts, professional tone. **Quits if:** one
  hallucinated claim or one cringe post.

### 3.3 The Aspiring Authority (~20%)
- **Who:** 35–55, often female in our base. Coach, consultant, author selling
  $2–10k programs. The personal brand IS the business.
- **Wants to achieve:** audience and booked discovery calls — in *her* voice.
- **Behavior:** hands-on, already posts weekly; it just eats her week. The single
  test she applies to every output: "does it sound like ME?"
- **Their ideal path:** logs in Monday before a launch → picks objective ("book
  discovery calls") → generates 8 drafts, edits 3 → schedules the week → returns
  to see what performed.
- **Stays if:** voice fidelity and hours saved. **Quits if:** output sounds
  generic, or she outgrows us.

### 3.4 The Overwhelmed Newcomer (hidden, big — cuts across industries)
- **Who:** any industry. Just got filmed for their episode, proud and lost.
- **Wants to achieve:** someone to tell them the next step.
- **Behavior:** blank screens make them freeze; open-ended questions make them
  feel stupid. Needs to be led, one step at a time, with small visible wins.
- **Their ideal path:** first login after the episode airs → app says "3 things
  this week — start with this one" → taps the guided card, answers 2 simple
  questions → post is made FOR them, they approve → next week: "400 people saw
  it. Here's step 2."
- **Stays if:** being led, small wins landing weekly. **Quits if:** a blank chat
  box, or silence after day one.

### 3.5 The Delegator (~15%, our highest-paying VIPs)
- **Who:** owner of our biggest client businesses ($25k+). Understood the value
  instantly and will never log in personally. Has an assistant.
- **Wants to achieve:** results without their attention.
- **Behavior:** the assistant runs the tool; the owner judges the monthly report.
- **Their ideal path:** owner forwards login to assistant → assistant runs the
  monthly batch in one sitting, polishes, schedules → owner gets a monthly report
  (posted, views, calls) → renews, asks about done-for-you.
- **Stays if:** it runs without the owner's attention and the report proves
  value. **Quits if:** clumsy for the assistant, invisible to the boss.

---

## 4. Current-state audit — walking today's app as each persona

The deck's slide-12 exercise ("walk the app as one of them"), done against the
code as it exists on `feat/engine-wiring`:

| Persona | First 60 seconds today | Where they quit today |
|---|---|---|
| Operator | Lands on a dashboard with tool cards, chat, guided topics — all requiring reading and choices, on desktop-oriented layouts | Immediately. Nothing to tap-approve; nothing arrives by text; publishing doesn't exist, so "posts go out" never happens |
| Professional | Same dashboard; could open guided flow and generate; provenance EXISTS in the engine but is not shown next to a draft; no archive of what was published | The first time they ask "where did this claim come from?" and the UI can't answer (the engine can — atoms carry source + line numbers — but no draft view surfaces it) |
| Authority | Guided + chat + voice profile — genuinely served; ideas mined from her material; grounded generation | Mostly stays. Gaps: no scheduling/calendar, no performance view, no post library persistence |
| Newcomer | The same open-ended dashboard as everyone; `/onboarding` is a "coming soon" placeholder | The blank chat box. The exact thing the deck says makes them quit |
| Delegator's assistant | Could use the workspace like the Authority; no separation of assistant seat vs owner; no report exists | The owner never sees value (no report), so renewal risk even if the assistant copes |

Also worth naming: **the InsideSuccess team is a sixth user**. The `/internal`
console (client roster, packet intake, atom review with confirm/remove, voice
profile approval, login links) is the operator-side product and is what makes a
concierge interim model possible (§9).

**Honest conclusion:** today's app is a Full Workspace for persona 3, plus a
strong team console. The deck's diagnosis is correct.

---

## 5. What the research found

Four streams, run 2026-08-01. Full sources in the appendix.

### 5.1 Prior art on GitHub (via Precedent — 39 candidates screened, 8 deep-dived)

- **No open-source project routes different user types to different first
  screens.** Every tool in the space is single-surface, built for a hands-on
  creator: studio/editor + calendar (e.g. SamurAIGPT/social-post,
  AgriciDaniel/linkedin-content-creator, shnai0/linkedin-post-generator).
- **Approval queues exist only in ops tooling** — builderz-labs/marketing-dashboard
  (402★, MIT) treats content approval queues as a first-class surface with an
  "operator-led, approvals visible" philosophy that matches our provenance story;
  djangocms-moderation does approval mechanics for CMS content.
- **Client portals exist** — Vibra-Labs/Atrium (agency client portal): magic-link
  auth for clients, owner/admin vs member roles, white-label branding. Validates
  our HMAC login-link design and the role split we need for the Delegator.
- **Publishing is a solved problem we should not rebuild** (§7.2): Postiz
  (~25k★ open-source Buffer alternative, AGPL → side-car via API only, per our
  licence rules), Ayrshare (commercial unified API, 13+ networks), Typefully API
  (official agent-skills, actively maintained).
- **Precedent-style verdict:** the persona-routed front door is **BUILD (space:
  Open)**; the publishing layer is **REUSE**. Epistemic caveat: this proves what
  exists on GitHub, not what doesn't exist anywhere.

### 5.2 Commercial LinkedIn/social AI tools (Taplio, Supergrow, MagicPost, AuthoredUp, Typefully, Kleo, EasyGen, Jasper, Copy.ai)

- **Nobody verified routes personas at first-run.** Taplio asks industry/goals but
  only to tune the AI — everyone gets the same dashboard. Segmentation is
  expressed as *pricing tiers + workspace architecture*, never as different first
  screens. (Caveat: flows sit behind signup walls; this comes from reviews and
  vendor docs, not hands-on signup.)
- **The one place the category DOES give different users different screens:** the
  agency stack. Supergrow and MagicPost both ship per-client workspaces + a
  credential-free client connect link + a **no-login approval link** (MagicPost
  names it "Validation Mode"). The client is treated as an approver persona with
  a near-zero-UI surface (a link); the ghostwriter gets the full editor. This is
  structurally identical to our `/internal` + client-login-link split.
- **Voice creation converged on three stacked inputs:** LinkedIn history import
  (Taplio, MagicPost — low friction, criticized as "vanilla, never improves"),
  pasted writing samples, and structured questionnaires. Tools rated best at
  voice (Supergrow "Content DNA", Kleo) separate *how you write* from *what you
  know* — which our engine already does more rigorously (voice profile vs
  knowledge atoms, with provenance).
- **"Done-for-you" modes change the input medium; they don't remove the human.**
  Flagship: Supergrow **PostCast** — a 10–30 min adaptive AI voice interview that
  produces 3–7 drafts in the trained voice. Also: pick-from-viral-library
  (Taplio). No tool ships true zero-touch publishing as its main mode.
  **Strategic fit for us:** an interview IS a transcript, and transcripts are our
  engine's richest input — a Newcomer interview feeds the knowledge corpus and
  produces their first posts in one motion.
- **Pricing ladder mirrors the personas:** cheap tier = you write (no AI);
  mid ($39–69) = AI writes for you (solo creator); top = you write for others
  (seats, approvals, white-label). Useful later for our own packaging.

### 5.3 Agency approval workflows & done-for-you services

- **The industry converged on one flow for non-technical clients:**
  email/SMS/WhatsApp → **tokenized magic link, no login** → queue of post cards
  with network-accurate previews → Approve / Reject / Comment → **bulk approve**
  → **auto-reminders until action**. Shipped by Gain (single-use 24h links,
  auto-nagging), HeyOrca (pick-your-name, no auth — 100 Pound Social runs its
  whole done-for-you review on it), GoHighLevel (magic links "via email,
  WhatsApp, Slack, or anywhere" — built because local clients wouldn't log in),
  Cloud Campaign, Vista Social. **Any login wall causes approval stalls.**
  Our HMAC client links are already this pattern.
- **Native SMS approval exists nowhere.** GHL's magic-link-pasted-into-SMS is the
  de-facto standard; GHL's own ideas board shows demand outstripping supply.
  The deck's "roofer gets a text" is both achievable and a visible market gap.
- **Delegate seats have a standard shape — role inversion:** the VA gets a
  restricted "requires approval" creation seat; the owner holds only the approve
  bit (Buffer's pattern) or just the report email. Hootsuite adds deadline
  forcing-functions (expired-approvals queue).
- **Reports:** branded **PDF, auto-emailed monthly** is the production norm; most
  clients read the PDF and ignore dashboards. Contents led by **business
  outcomes (leads, calls, booked jobs), then traffic, with impressions/followers
  explicitly vanity/context**. Done-for-you services add a human "what we did /
  what's next" narrative.
- **The single biggest UX decision for busy owners:** publish-on-silence (content
  goes out unless rejected within N days) vs block-on-silence (nothing publishes
  without explicit approval). Agencies commonly practice publish-on-silence with
  a ~48h window; careful clients need block-on-silence.

### 5.4 Cross-industry patterns (outside the niche)

- **Goal-gated onboarding is standard consumer practice:** Notion, Duolingo,
  Headspace all ask ≤3 questions on first run — framed as **the outcome wanted
  ("what brings you here?"), not the job title** — and seed the whole experience
  from the answer. Personalized paths reportedly lift activation 22–48%
  (Appcues, single source, directional).
- **The interview model (TurboTax):** one question per screen, plain language,
  Back always available, live payoff indicator, uncommon branches skipped by
  default, raw complexity reachable only on request. The verified version of
  "never show a blank screen."
- **The structural warning — parallel modes rot:** Nielsen: shipping a lite
  edition plus a pro edition "splits your codebase, your documentation, and your
  budget"; Gmail's Basic HTML view was killed in 2024 rather than maintained.
  The durable pattern is **one surface with layered depth** (progressive
  disclosure, ~80% of tasks on level 1), with persona as *defaults + visibility
  flags*, never a fork.
- **Adaptable first, adaptive after:** let users self-declare at onboarding, let
  them re-declare anytime (persona is an editable setting, not an account type),
  and only later adapt automatically from behavior.
- **SMS-first field-service products (Podium ~$399/mo, NiceJob $75/mo):** the
  trigger is an event in the owner's existing system of record, the owner's only
  action is one tap in a text thread, and set-it-and-forget-it sells at both
  price points. Model for the Operator.
- **Concierge MVPs are a proven de-risking step:** Wealthfront ran pen-and-paper
  portfolio planning, Food on the Table sold manual meal plans, Airbnb founders
  photographed listings — all before building the software. Openly-human
  concierge ("your strategist prepared this") builds exactly the trust the
  Careful Professional needs.
- **NN/g caution:** wizards punish repeat expert users — every guided surface
  needs a visible escape hatch to the direct tool, or the Authority churns.

---

## 6. What we adopt, and where we push back on the deck

**Adopted wholesale:**
- The sorting model and the five personas (§2–3), including "stays/quits" as the
  design test for every future screen.
- The thinking order: screen last.
- "The backend does not change" — verified at code level. Context bundles, voice
  profiles, provenance, never-say constraints, atom review, magic-link auth are
  all mode-agnostic. This is a front-door problem.
- Guided Path as the next build, doubling as onboarding.
- The three first-login questions (goal-framed per §5.4).

**Pushback 1 — five screens must be three surfaces, or they rot.**
The deck proposes five different first screens. Research (§5.4) says parallel
modes split codebase/docs/budget and die of neglect; our team size makes this
certain, not just likely. The five *experiences* survive as **persona
configurations of three surfaces** (§7.1). The Professional's "Review & Control"
is the approval queue with the receipts panel expanded — a feature flag, not a
screen. The Delegator is the queue plus a report — roles, not screens.

**Pushback 2 — the Operator journey is 20% UI, 80% missing infrastructure.**
His deck journey assumes: a text arrives (no SMS/notifications exist), posts go
out (no publishing exists — today humans copy-paste), and "12 calls came from
your posts" (no call tracking/attribution exists). Building the approve screen
without that plumbing produces a button that does nothing. The publishing layer
is therefore a named, sequenced build item (§7.2) — mitigated by the research
finding that it can be reused rather than built.

**Pushback 3 — "12 calls came from your posts" is a promise we can't make yet.**
Direct lead attribution from organic social is genuinely hard; services that
promise it do it via outbound activity, not analytics (§5.3). The honest v1
report is: posts published, views/engagement, plus *manually logged* wins (the
concierge CSM narrative pattern). Call-tracking numbers are a later, deliberate
decision — not an implied freebie.

**Pushback 4 — the Newcomer's guided path should also FEED the engine.**
The deck treats the guided path as output UX ("post made for them"). Research
(§5.2, PostCast) shows the stronger move: the guided path's questions — ideally
voice-interview style later — are *input*. Every answer is a transcript the
engine atomises. The Newcomer's onboarding literally builds their knowledge
corpus. This is the point where our engine is structurally better than every
competitor surveyed, and no competitor connects the two.

---

## 7. The adopted direction

### 7.0 One sentence
One login, three goal-framed questions, **three surfaces** (guided path, approval
queue, workspace) on one codebase — with persona stored as an editable setting
that sets defaults and visibility, never a fork — backed by the existing engine,
with publishing reused from a vendor, and concierge operations covering the
unserved personas until their surface ships.

### 7.1 The three surfaces

**Surface A — Guided Path** (serves: Newcomer as default; everyone at first login)
- First login = the router: ≤3 goal-framed questions (what do you want to
  achieve · who will drive this, you or someone on your team · hands-on or done
  for you). Answers set the persona setting and land the user on their surface.
- Newcomer mode: "3 things this week — start with this one." One card, one next
  step, 2 simple questions per card, TurboTax rules (one question per screen,
  Back always, live payoff, never a blank box). Weekly cadence with small wins
  ("400 people saw it. Here's step 2.").
- Every answer is captured as engine input (paste-packet today; voice interview
  later — the PostCast pattern).
- Escape hatch to the Workspace is always visible (NN/g).

**Surface B — Approval Queue** (serves: Operator, Professional, Delegator)
- Reached by magic link — email, SMS, or WhatsApp — **no login**, per the
  industry-converged pattern. Queue of post cards with accurate previews,
  Approve / Reject / Comment, bulk approve, auto-reminders until action.
- **Operator dials:** mobile-first, batch cadence ("5 posts for August"),
  delivery by SMS, publish-on-silence with ~48h window (team decision, §10),
  report shows calls/jobs language.
- **Professional dials:** desktop-friendly, per-post **receipts panel** (source
  document, line numbers, speaker — the engine already stores all of it),
  never-say list visible, block-on-silence always, published archive.
- **Delegator dials:** the assistant gets a real seat in the Workspace
  (role-inverted: assistant creates, owner approves or just receives); the owner
  gets the queue link and/or only the monthly report.
- The queue is also the natural home of the existing atom-review trust story:
  "everything here traces to your own words."

**Surface C — Workspace** (serves: Authority, Delegator's assistant; exists today)
- Chat + guided generation + voice profile + library. Known gaps to close
  eventually: scheduling/calendar, performance view, saved-post persistence.
- No redesign needed now. It stays the escape-hatch destination from A and B.

### 7.2 The publishing layer (the keystone dependency)

Operator approval, Delegator reports, and Newcomer "400 people saw it" all
require posts to actually publish and metrics to come back. Today nothing
publishes — the app generates text.

**Decision: reuse, not build.** Candidates (team decision, §10):

| Option | Model | Licence/cost | Notes |
|---|---|---|---|
| Postiz | self-hosted, call its API | AGPL → side-car only (per licence rules); infra cost | Most control, most ops burden |
| Ayrshare | hosted unified API | commercial, per-account pricing | 13+ networks, fastest integration |
| Typefully API | hosted, LinkedIn+X focused | commercial API | Official agent-skills, matches our LinkedIn-first scope |

LinkedIn-only for v1 (matches generation scope). Metrics ingestion (views,
engagement) comes from the same vendor.

### 7.3 What explicitly does NOT change
- The engine (backend repo): no schema, pipeline, or API changes required by any
  of this. New consumers only.
- The `/internal` console remains the team's operating surface and grows into
  the concierge cockpit.
- Parked items stay parked (MCP, Drive auto-ingest, Whisper, self-signup/billing)
  unless explicitly unparked. Note: Whisper/transcription will become relevant
  when the voice-interview input ships — flag it then, don't unpark it now.

---

## 8. Alternatives considered (and why not)

1. **Five distinct first screens (deck as-is).** Maximum persona fit on paper;
   research says parallel surfaces split codebase/docs/budget and rot (Gmail
   Basic HTML precedent). At our team size the fifth screen would be dead within
   two quarters. Rejected in favor of surfaces × settings.
2. **Separate products per segment (the Adobe Express/Photoshop split).** Viable
   only when each product has its own P&L and team. We have neither. Rejected.
3. **One adaptive surface that infers the persona from behavior.** Lower
   configuration burden, but adaptive-only systems confuse users and hide the
   mental model; research favors adaptable-first (self-declared, editable),
   adaptive later. Rejected for v1; revisit after usage data exists.
4. **Concierge-only (no new surfaces at all).** Cheapest; proves demand; but it
   caps scale, and the Newcomer's weekly-win loop is impractical to run manually
   at volume. Adopted *as interim* (§9), rejected as destination.
5. **Chat as the universal surface ("everyone talks to the AI").** Tempting given
   our chat investment; directly contradicted by the deck (blank chat boxes are
   the Newcomer's named quit trigger and the Operator won't type) and by the
   competitor survey (chat is not the winning primary surface even in
   AI-writing tools). Chat stays a power-user tool inside the Workspace.

---

## 9. Interim: concierge coverage (starts now, no build)

While surfaces A and B don't exist, the team can serve the unserved personas
manually through the existing `/internal` console — openly human ("your content
strategist prepared this"), the Wealthfront/Food-on-the-Table pattern, which
also builds the trust the Professional needs:

- **Operator/Delegator:** team onboards the packet, generates and curates a
  monthly batch, sends drafts via the existing client login link (or plain
  email/WhatsApp), tracks approvals in a sheet, posts manually, emails a simple
  monthly summary. Publish-on-silence policy agreed per client, in writing.
- **Professional:** same, but every draft is sent with its source receipts
  (the engine provides them) and nothing ever publishes without explicit
  written approval.
- **Newcomer:** a team member runs the "3 things this week" cadence by email
  using guided-generation outputs.
- **What this buys:** validated approval-rates, real content for the eventual
  queue UI, refined batch prompts — and revenue continuity for the 75% while we
  build. It also generates the exact data §10's decisions need.

---

## 10. Open decisions for the team (each with a recommendation)

1. **Publishing vendor** (blocks Surface B's promise). *Recommendation:* start
   with Typefully API (LinkedIn-first, agent-skills maintained, minimal ops);
   revisit Postiz side-car if per-account costs bite at scale.
2. **Publish-on-silence vs block-on-silence defaults.** *Recommendation:*
   per-persona defaults — Operator: publish-on-silence, 48h window, first month
   block-on-silence to build trust; Professional: block-on-silence, always,
   non-negotiable; set per client in writing during onboarding.
3. **SMS provider & compliance** (Operator delivery channel; A2P registration
   lead time is weeks, not days). *Recommendation:* decide only after the queue
   exists; email + WhatsApp links first (GHL precedent shows channel-agnostic
   links work).
4. **What the monthly report claims.** *Recommendation:* v1 = published posts,
   views/engagement, manually-logged wins + human narrative; call-tracking
   numbers are a separate later decision with its own cost/benefit.
5. **Does the Authority get scheduling now or after Surface B?**
   *Recommendation:* after — the publishing layer serves both; don't build
   calendar UI twice.
6. **Pricing/packaging alignment with personas** (the $39/$69/seats ladder in
   §5.2). Out of scope for this doc; flag for a business session.

---

## 11. Risks

| Risk | Mitigation |
|---|---|
| Persona setting becomes five hidden forks anyway (flag sprawl) | Rule: a persona may set *defaults and visibility* only; any persona-specific component beyond that needs explicit sign-off |
| Publishing vendor lock-in / API changes | Isolate behind our own thin publish interface from day one; LinkedIn-only v1 keeps the surface small |
| Concierge sets expectations software can't match | Keep the interim UI contract identical to the planned queue (event → draft → one-tap approve), so the software swap is invisible |
| Newcomer cadence needs content ops discipline, not just UI | Weekly-win loop is a team SOP first (concierge phase proves it), software second |
| Voice-interview input pulls in transcription (parked Whisper) | Ship guided path with typed/pasted answers first; unpark transcription as its own decision |
| "Calls came from your posts" promised implicitly by the deck | §6 pushback 3 is the agreed line: don't claim attribution we don't have |

---

## 12. Success criteria (the deck's stays/quits, made checkable)

- **Operator:** can go from magic link to all-posts-approved in under 60 seconds
  on a phone, and his monthly report leads with jobs/calls language. Never asked
  to type more than a rejection reason.
- **Professional:** every draft shows its sources one tap away; zero posts ever
  publish without explicit approval; archive answers "what went out, when."
- **Authority:** existing workspace untouched or better; voice-fidelity
  complaints trend to zero; scheduling arrives with Surface B's plumbing.
- **Newcomer:** never sees a blank input on their default surface; receives a
  concrete win message in week 1; week-2 return rate becomes the number we watch.
- **Delegator:** assistant completes a monthly batch in one sitting; owner
  receives a report without logging in; renewal conversation references the
  report.
- **Team:** one codebase; the persona setting has exactly three surfaces behind
  it; adding persona #6 someday costs a configuration, not a screen.

---

## Appendix A — Research sources

**Competitor UX:** Taplio (ghostwriting-ai.com, coldiq, connectsafely reviews) ·
Supergrow (pricing + agency/ghostwriter + PostCast docs) · MagicPost (pricing,
Validation Mode) · AuthoredUp · Typefully (collaboration/share-drafts docs) ·
Kleo · EasyGen · Jasper Brand Voice · Copy.ai Brand Voice.
**Approval workflows:** Gain (approver access docs) · HeyOrca (+ 100 Pound
Social) · Planable · Vista Social (no-login shared calendars, multi-step
approval) · Buffer (agency setup, draft approval) · Hootsuite · Sendible
(white-label, automated reports) · Cloud Campaign · Kontentino · GoHighLevel
(magic-links changelog + ideas board) · SocialBee (approval + concierge) ·
Verblio · Cleverly ghostwriting · ApproveThis.
**Cross-industry:** Notion (Candu teardown) · Duolingo (UserGuiding) · Headspace
(GoodUX) · Canva (Raw.Studio) · Figma role selector (Appcues) · TurboTax
(Appcues, NN/g wizards, UX Collective) · Nielsen progressive disclosure
(UX Tigers) · Gmail Basic HTML retirement (TechCrunch, The Register) ·
adaptable-vs-adaptive (Springer) · Podium/NiceJob (Contractor ToolStack,
business.com) · concierge MVPs (LogRocket, Learning Loop, Upsilon).
**GitHub prior-art (Precedent, 2026-08-01):** 7 query angles + 1 refinement
round, 39 candidates screened, 8 deep-dived: Postiz, builderz-labs/
marketing-dashboard, Vibra-Labs/Atrium, Anil-matcha/Free-AI-Social-Media-
Scheduler, SamurAIGPT/social-post, mehmetkirkoca/social-media-manager,
AgriciDaniel/linkedin-content-creator, typefully/agent-skills.

## Appendix B — Epistemics

Competitor first-run details come from reviews and vendor docs, not hands-on
signups (flows change often). GitHub research proves what exists, never what
doesn't. The activation-lift figure (22–48%) is a single vendor source —
directional only. Persona percentages are our own base and should be re-cut
when the base grows. Everything else marked "flagged" in the research stays
unverified until someone checks it directly.
