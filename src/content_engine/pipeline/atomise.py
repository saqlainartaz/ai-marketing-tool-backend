"""Deterministic fake atomizer — M1A's keyless stand-in for LLM extraction.

Rule-based (pure function of its input): keyword heuristics over cleaned text
produce typed atoms with structural provenance. The M1B real atomizer replaces
the rules with type-specific extraction prompts behind the same signature, and
must treat document text strictly as data, never as instructions.

Composition guardrails (claude-repurpose): 5-15 atoms/doc target, always ≥1 tldr;
quotes capped at 125 chars (TribeAI).
"""

import hashlib
import re
from dataclasses import dataclass, field
from typing import Any

from content_engine.pipeline.parse import parse_text

ATOMIZER_VERSION = "fake-atomizer/0.1.0"
MAX_ATOMS = 15
MAX_QUOTE_CHARS = 125

_SPEAKER_LINE = re.compile(r"^([A-Z][A-Za-z .'\-]{0,60}?):\s*(.+)$")
_OBJECTION = re.compile(
    r"price|cost|expensive|steep|budget|compared to|competitor|worried|concern|risk",
    re.IGNORECASE,
)
_PROOF = re.compile(
    r"payback|roi|saved|results?|weeks|months|%|\d+x|customers?|case stud",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ExtractedAtom:
    atom_type: str
    text: str
    provenance: dict[str, Any]
    confidence: float
    impact: int
    evidence_kind: str
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def content_hash(self) -> str:
        return hashlib.sha256(f"{self.atom_type}\x00{self.text}".encode()).hexdigest()


def _transcript_atoms(cleaned: str) -> list[ExtractedAtom]:
    atoms: list[ExtractedAtom] = []
    for line_no, line in enumerate(cleaned.splitlines(), start=1):
        match = _SPEAKER_LINE.match(line.strip())
        if not match:
            continue
        speaker, utterance = match.group(1), match.group(2)
        provenance = {"line": line_no, "speaker": speaker}

        if not atoms:
            atoms.append(
                ExtractedAtom(
                    atom_type="tldr",
                    text=utterance,
                    provenance=provenance,
                    confidence=0.5,
                    impact=3,
                    evidence_kind="inferred",
                )
            )
        if _OBJECTION.search(utterance):
            atoms.append(
                ExtractedAtom(
                    atom_type="objection",
                    text=utterance[:MAX_QUOTE_CHARS],
                    provenance=provenance,
                    confidence=0.6,
                    impact=4,
                    evidence_kind="quoted",
                    payload={"speaker": speaker},
                )
            )
        if _PROOF.search(utterance):
            atoms.append(
                ExtractedAtom(
                    atom_type="proof_point",
                    text=utterance[:MAX_QUOTE_CHARS],
                    provenance=provenance,
                    confidence=0.6,
                    impact=4,
                    evidence_kind="quoted",
                    payload={"speaker": speaker},
                )
            )
    return atoms


def _document_atoms(cleaned: str) -> list[ExtractedAtom]:
    atoms: list[ExtractedAtom] = []
    parsed = parse_text(cleaned)
    for section in parsed.sections:
        body = section.text.strip()
        if not body:
            continue
        first_sentence = re.split(r"(?<=[.!?])\s+", body)[0][:MAX_QUOTE_CHARS]
        provenance = {
            "section_anchor": list(section.section_anchor),
            "breadcrumb": section.breadcrumb,
        }
        atom_type = "tldr" if not atoms else "insight"
        atoms.append(
            ExtractedAtom(
                atom_type=atom_type,
                text=first_sentence,
                provenance=provenance,
                confidence=0.5,
                impact=3,
                evidence_kind="quoted",
            )
        )
    return atoms


def extract_atoms(source_type: str, cleaned: str) -> list[ExtractedAtom]:
    if source_type in ("sales_call_transcript", "meeting_transcript"):
        atoms = _transcript_atoms(cleaned)
    else:
        atoms = _document_atoms(cleaned)

    seen: set[str] = set()
    unique: list[ExtractedAtom] = []
    for atom in atoms:
        if atom.content_hash not in seen:
            seen.add(atom.content_hash)
            unique.append(atom)
    return unique[:MAX_ATOMS]
