"""Prompt-tuning loop: clean a real document and run the LLM atomizer on it.

Usage: python -m uv run python scripts/extract_demo.py <file> <source_type>
Requires ANTHROPIC_API_KEY (reads .env). Prints the extracted atoms; touches
no database. Real client files live in data/real-client/ (gitignored).
"""

import sys
from collections import Counter
from pathlib import Path

from content_engine.pipeline.atomise_llm import LLMAtomizer
from content_engine.pipeline.clean import clean_for
from content_engine.providers import get_llm_provider


def main() -> int:
    path, source_type = Path(sys.argv[1]), sys.argv[2]
    raw = path.read_text(encoding="utf-8", errors="replace")
    cleaned, cleaner = clean_for(source_type, raw)
    print(f"cleaned by {cleaner}: {len(raw)} -> {len(cleaned)} chars\n")

    llm = get_llm_provider("anthropic")
    atoms, prompt_hash = LLMAtomizer(llm).extract(source_type, cleaned)

    print(f"{len(atoms)} atoms  (prompt {prompt_hash[:12]})")
    print(Counter(a.atom_type for a in atoms).most_common(), "\n")
    for atom in atoms:
        speaker = atom.provenance.get("speaker", "")
        loc = f"L{atom.provenance['line']}" + (f" {speaker}" if speaker else "")
        print(f"[{atom.atom_type:<16}] c={atom.confidence:.1f} i={atom.impact} "
              f"{atom.evidence_kind:<10} ({loc})")
        print(f"  {atom.text}")
        if atom.payload:
            print(f"  payload: {atom.payload}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
