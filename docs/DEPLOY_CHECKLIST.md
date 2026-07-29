# Deploy Checklist (stub)

Nothing deploys during M1A. Fill this in when the first hosted environment is set up
(expected around M1B/M1C). Must cover, at minimum:

- [ ] Postgres with pgvector extension; RLS policies verified post-migration
- [ ] Service token provisioned (fail-closed startup check passes)
- [ ] Raw-file storage bucket (S3-compatible) + credentials
- [ ] ANTHROPIC_API_KEY / VOYAGE_API_KEY set (M1B+)
- [ ] Alembic migrations run; zero-recall regression test run against the deployed DB
- [ ] Backup policy for Postgres + raw storage
- [ ] CORS locked to the frontend origin
