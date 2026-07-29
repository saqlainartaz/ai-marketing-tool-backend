"""Text/markdown parser with an eager heading tree (PharosRAG findings:
eager costs ~1ms/doc; per-section breadcrumb + anchor + reliability flag).

Docling handles PDF/docx in M1B behind this same output shape.
"""

import re
from dataclasses import dataclass

PARSER_VERSION = "text-parser/0.1.0"

_HEADING = re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE)
_TOC_TITLES = {"table of contents", "contents", "toc"}


@dataclass(frozen=True)
class Section:
    text: str
    breadcrumb: list[str]
    section_anchor: tuple[int, int]  # (start, end) char offsets into raw text
    level_reliable: bool

    # dataclass with list field can't be frozen+hashable; keep eq only
    def __hash__(self) -> int:  # pragma: no cover
        return hash((self.section_anchor, tuple(self.breadcrumb)))


@dataclass(frozen=True)
class ParsedDoc:
    sections: list[Section]
    parser_version: str = PARSER_VERSION


def parse_text(raw: str) -> ParsedDoc:
    """Split markdown into heading-anchored sections; plain text becomes a
    single section with an unreliable level."""
    matches = list(_HEADING.finditer(raw))
    if not matches:
        return ParsedDoc(
            sections=[
                Section(
                    text=raw,
                    breadcrumb=[],
                    section_anchor=(0, len(raw)),
                    level_reliable=False,
                )
            ]
        )

    sections: list[Section] = []
    ancestors: list[tuple[int, str]] = []  # (level, title)
    for i, match in enumerate(matches):
        level = len(match.group(1))
        title = match.group(2)
        while ancestors and ancestors[-1][0] >= level:
            ancestors.pop()
        ancestors.append((level, title))

        start = match.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(raw)
        if title.strip().lower() in _TOC_TITLES:
            continue  # strip TOCs at ingest — they pollute the index
        sections.append(
            Section(
                text=raw[match.end() : end].strip("\n"),
                breadcrumb=[t for _, t in ancestors],
                section_anchor=(start, end),
                level_reliable=True,
            )
        )
    return ParsedDoc(sections=sections)
