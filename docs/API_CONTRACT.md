# API Contract — /v1

**The API contract is the product.** Downstream tools bind to it. Breaking changes are
significant events (version bump + migration notes in docs/DECISIONS.md), never
refactors. FastAPI auto-generates the OpenAPI spec; the Next.js frontend generates a
typed client from it.

## Auth (v1 trust model — explicit decision)

- A **static service API key** authenticates the calling *service* (the Next.js server).
  End users never call this API directly.
- The frontend passes `client_id` per request; **the engine trusts the frontend's client
  scoping in v1.** RLS enforces that whatever `client_id` the request carries is the only
  tenant whose rows are reachable for that request.
- This trust boundary is the thing that changes at self-signup time (per-user tokens
  mapped to client_id server-side). Recorded here so it is a decision, not an accident.
- Startup is **fail-closed**: no valid service-token config → refuse to boot.

## Endpoints

```
POST /v1/clients                                create client
GET  /v1/clients
POST /v1/clients/{id}/documents                 multipart upload + source_type + source_authority
GET  /v1/clients/{id}/documents                 list + statuses
GET  /v1/clients/{id}/documents/{doc}           status, provenance detail
POST /v1/clients/{id}/documents/{doc}/reprocess
GET  /v1/clients/{id}/atoms?type=&limit=        list/filter                      [M1A]
POST /v1/clients/{id}/search                    hybrid semantic+keyword          [M1B]
POST /v1/clients/{id}/context                   context-injection bundle         [M1B]
POST /v1/clients/{id}/atoms/{atom}/decision     confirm/override/deprecate       [M1C]
GET  /health
```

## Response invariants

- Every atom in any response carries **provenance**: source document id + sha256,
  location-in-source (section anchor / speaker / timestamp where applicable),
  confidence, `evidence_kind`, authority tier, `client_id`.
- Retrieved source text is labeled `trust: untrusted`.
- `/context` bundles are ordered by authority: confirmed canon → constraints/blacklists
  → personas → supporting atoms; each atom carries a staleness flag; a voice-snapshot
  section uses the brand-loom shape (`tone`, `audience`, `do_phrases`, `avoid_phrases`
  — every field optional).
- A belt-and-braces `client_id` assertion runs at the response layer (RLS is the real
  guard; this is defense-in-depth).
