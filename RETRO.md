# RETRO

Lessons from building this repo. Append after each issue/milestone; read before starting
a new one. Format: date · issue · what worked / what didn't / change for next time.

---

- 2026-07-29 · planning · Repo-mining agents (TribeAI, claude-repurpose, brand-loom,
  PharosRAG, WEBOS, openmelon, marketing-cli) materially improved the design: negative
  atom types, atom lifecycle, freshness windows, fail-closed tenancy, chunk sizing
  numbers. Change: before designing any new subsystem, check RESEARCH.md deep-dives
  first.
- 2026-07-30 · M1B/M1C (issues 7-13) · Worked: real-fixture prompt tuning beat synthetic
  guessing — two iterations against the Keira transcript surfaced that the model fills
  favorite atom types unless coverage is an explicit numbered rule. Worked: keyless stub-LLM
  tests let the atomizer be fully tested before any live call. Worked: "delete provisional
  only + skip surviving hashes" made review survival trivial compared to re-linking
  decisions. Watch: Voyage free tier is 3 RPM until a payment method exists — fine for dev,
  too slow for real onboarding. Watch: LLM extraction is non-deterministic across
  reprocesses (unlike the fake) — confirmed atoms pin the reviewed subset, which is the
  designed mitigation.
- 2026-07-29 · M1A (issues 1-6) · Worked: TDD caught two real bugs the design missed —
  the RLS `''::uuid` DataError on pooled connections (fixed with NULLIF in the policy)
  and detached-instance reads after session close. The zero-recall test earned its
  place immediately. Worked: deterministic fake providers made the whole spine testable
  in seconds with zero keys. Watch next: the golden-file cleaner test will churn as
  cleaning rules evolve — bump CLEANER_VERSION and regenerate goldens deliberately,
  never casually. Watch next: worker uses polling (0.5s) — fine for M1, revisit with
  LISTEN/NOTIFY if latency ever matters.
