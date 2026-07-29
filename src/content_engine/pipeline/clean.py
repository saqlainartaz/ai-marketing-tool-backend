"""Type-aware transcript cleaner — deterministic, versioned, PII-redacting.

Raw files are never modified; this produces derived canonical text. Bump
CLEANER_VERSION whenever rules change so lineage stays honest and the corpus
can be re-cleaned reproducibly.
"""

import re

CLEANER_VERSION = "transcript-cleaner/0.1.0"

_TIMESTAMP = re.compile(r"^\s*\[?\d{1,2}:\d{2}(?::\d{2})?\]?\s*")
_SPEAKER = re.compile(r"^([A-Z][A-Za-z .'\-]{0,60}?)\s*:\s*")
_FILLER = re.compile(r"\b(?:um+|uh+|erm+)\b[,.]?\s*", re.IGNORECASE)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE = re.compile(r"(?:\+?\d{1,2}\s*)?(?:\(\d{3}\)\s*|\d{3}[-. ])\d{3}[-. ]\d{4}")

# Small-talk/audio-check utterances dropped entirely (documented, conservative).
_SMALL_TALK = re.compile(
    r"can you hear me|you'?re on mute|loud and clear|^(?:hi|hey|hello)[!,. ]",
    re.IGNORECASE,
)


def _normalize_speaker(name: str) -> str:
    return " ".join(part.capitalize() for part in name.split())


def _capitalize_first(text: str) -> str:
    for i, ch in enumerate(text):
        if ch.isalpha():
            return text[:i] + ch.upper() + text[i + 1 :]
    return text


def clean_transcript(raw: str) -> str:
    lines: list[str] = []
    for line in raw.splitlines():
        line = _TIMESTAMP.sub("", line).strip()
        if not line:
            continue

        speaker = None
        match = _SPEAKER.match(line)
        if match:
            speaker = _normalize_speaker(match.group(1))
            line = line[match.end() :]

        if _SMALL_TALK.search(line):
            continue

        line = _FILLER.sub("", line)
        line = _EMAIL.sub("[email]", line)
        line = _PHONE.sub("[phone]", line)
        line = re.sub(r"\s{2,}", " ", line).strip()
        if not line:
            continue
        line = _capitalize_first(line)

        lines.append(f"{speaker}: {line}" if speaker else line)
    return "\n".join(lines) + ("\n" if lines else "")


def clean_for(source_type: str, raw: str) -> tuple[str, str]:
    """Route to the type-aware cleaner. Returns (cleaned_text, cleaner_actor)."""
    if source_type in ("sales_call_transcript", "meeting_transcript"):
        return clean_transcript(raw), CLEANER_VERSION
    return raw, "passthrough-cleaner/0.1.0"
