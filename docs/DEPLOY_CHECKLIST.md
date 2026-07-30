# Deploy Checklist — Render

The repo ships a Render Blueprint (`render.yaml`): web service (Docker) +
managed Postgres 17 + a persistent disk for raw files. Frontend lives on
Vercel and calls this service server-side.

## 1. First deploy

- [ ] GitHub repo is **private** and CI is green.
- [ ] Render → New + → **Blueprint** → select `ai-marketing-tool-backend`.
- [ ] When prompted for env values, set the secrets:
  - `SERVICE_API_KEY` — generate a long random string (40+ chars). This is
    what the Vercel frontend will send as `X-API-Key`.
  - `ANTHROPIC_API_KEY`, `VOYAGE_API_KEY` — same values as local `.env`.
  - Leave `DATABASE_URL` / `WORKER_DATABASE_URL` **empty for now** (step 4).
- [ ] First build is slow (~3-4GB image, Docling/PyTorch). Expected.

## 2. Expect the first deploy to half-succeed

`preDeployCommand` runs migrations as the admin role — that works — but the
app itself boots fail-closed until step 4 fills the two role URLs. That's by
design (never serve requests as the admin/superuser role — it bypasses RLS).

## 3. Verify pgvector

Render Postgres supports pgvector. Migration 0001 runs
`CREATE EXTENSION IF NOT EXISTS vector` — if the deploy log shows a permission
error here, open a psql shell from the Render dashboard and run it once
manually, then redeploy.

## 4. Rotate the app/worker role passwords (REQUIRED)

Migrations create `engine_app` and `engine_worker` with dev passwords. From
the Render database's psql shell:

```sql
ALTER ROLE engine_app    WITH PASSWORD '<strong-random-1>';
ALTER ROLE engine_worker WITH PASSWORD '<strong-random-2>';
```

Then set on the web service (Environment tab), deriving host/db name from the
admin connection string:

```
DATABASE_URL        = postgresql+psycopg://engine_app:<strong-random-1>@<host>/<dbname>
WORKER_DATABASE_URL = postgresql+psycopg://engine_worker:<strong-random-2>@<host>/<dbname>
```

(`postgres://` prefixes also work — the app normalizes them.)

## 5. Smoke test

- [ ] `GET https://<service>.onrender.com/health` → `{"status":"ok"}`
- [ ] `POST /v1/clients` with header `X-API-Key: <SERVICE_API_KEY>` → 201
- [ ] Upload a small .txt via `POST /v1/clients/{id}/documents`, poll the
      document until `atomised`, then `POST /v1/clients/{id}/search`.
- [ ] Wrong/missing `X-API-Key` → 401 (fail-closed confirmed).

## 6. Ongoing

- [ ] Backups: Render Postgres daily backups are on by default — verify plan
      includes them. The raw-file disk has snapshots on paid plans.
- [ ] Deploys: push to `main` → CI runs → Render auto-deploys (migrations run
      pre-deploy). Keep breaking API changes versioned per docs/API_CONTRACT.md.
- [ ] Voyage: add a payment method (3 RPM otherwise).
- [ ] Note: persistent disk pins the service to one instance (fine for v1);
      moving raw storage to S3/R2 is the change that unlocks scaling out.
