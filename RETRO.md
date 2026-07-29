# RETRO

Lessons from building this repo. Append after each issue/milestone; read before starting
a new one. Format: date · issue · what worked / what didn't / change for next time.

---

- 2026-07-29 · planning · Repo-mining agents (TribeAI, claude-repurpose, brand-loom,
  PharosRAG, WEBOS, openmelon, marketing-cli) materially improved the design: negative
  atom types, atom lifecycle, freshness windows, fail-closed tenancy, chunk sizing
  numbers. Change: before designing any new subsystem, check RESEARCH.md deep-dives
  first.
- 2026-07-29 · M1A (issues 1-6) · Worked: TDD caught two real bugs the design missed —
  the RLS `''::uuid` DataError on pooled connections (fixed with NULLIF in the policy)
  and detached-instance reads after session close. The zero-recall test earned its
  place immediately. Worked: deterministic fake providers made the whole spine testable
  in seconds with zero keys. Watch next: the golden-file cleaner test will churn as
  cleaning rules evolve — bump CLEANER_VERSION and regenerate goldens deliberately,
  never casually. Watch next: worker uses polling (0.5s) — fine for M1, revisit with
  LISTEN/NOTIFY if latency ever matters.
