"""Parity eval — proves every provider passes the same well-formedness checks.

brand-loom pattern (Apache-2.0): fake always runs; real providers join only
when their env key exists, so the same script works keyless and fully-keyed.
Exit 1 on any failure. Run: python -m uv run python scripts/eval_parity.py
"""

import os
import sys

from content_engine.models import EMBEDDING_DIM
from content_engine.providers import get_embedding_provider, get_llm_provider

CHECKS = {
    "generate": lambda llm: bool(llm.generate("Reply with exactly: OK", max_tokens=64).strip()),
    "generate_json": lambda llm: llm.generate(
        "Return JSON with a single key 'ok'.", max_tokens=128
    ).strip().startswith(("{", "[")),
}
EMBED_CHECKS = {
    "embed_dim": lambda e: len(e.embed(["hello world"])[0]) == EMBEDDING_DIM,
    "embed_query": lambda e: len(e.embed(["hello"], input_type="query")[0]) == EMBEDDING_DIM,
}


def main() -> int:
    llm_names = ["fake"] + (["anthropic"] if os.environ.get("ANTHROPIC_API_KEY") else [])
    embed_names = ["fake"] + (["voyage"] if os.environ.get("VOYAGE_API_KEY") else [])

    failures = 0
    for name in llm_names:
        llm = get_llm_provider(name)
        for check, fn in CHECKS.items():
            try:
                ok = fn(llm)
                status = "PASS" if ok else "FAIL (empty)"
            except Exception as exc:
                ok, status = False, f"FAIL ({type(exc).__name__})"
            failures += not ok
            print(f"llm/{name:<10} {check:<14} {status}")

    for name in embed_names:
        embedder = get_embedding_provider(name)
        for check, fn in EMBED_CHECKS.items():
            try:
                ok = fn(embedder)
                status = "PASS" if ok else "FAIL (dim mismatch)"
            except Exception as exc:
                ok, status = False, f"FAIL ({type(exc).__name__})"
            failures += not ok
            print(f"embed/{name:<8} {check:<14} {status}")

    skipped = [p for p in ("ANTHROPIC_API_KEY", "VOYAGE_API_KEY") if not os.environ.get(p)]
    if skipped:
        print(f"(real providers skipped — set {', '.join(skipped)} to include them)")
    print(f"\n{'ALL PASS' if failures == 0 else f'{failures} FAILURE(S)'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
