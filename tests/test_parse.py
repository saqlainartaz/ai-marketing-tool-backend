from content_engine.pipeline.parse import parse_text

MD = """# Playbook

Intro paragraph.

## Table of Contents

- [Pricing](#pricing)
- [Objections](#objections)

## Pricing

We charge per seat.

### Discounts

Annual plans save 20%.

## Objections

Common pushback and answers.
"""


def test_markdown_sections_carry_breadcrumbs() -> None:
    parsed = parse_text(MD)
    crumbs = [s.breadcrumb for s in parsed.sections]
    assert ["Playbook"] in crumbs
    assert ["Playbook", "Pricing"] in crumbs
    assert ["Playbook", "Pricing", "Discounts"] in crumbs
    assert ["Playbook", "Objections"] in crumbs


def test_toc_sections_are_stripped() -> None:
    parsed = parse_text(MD)
    titles = [s.breadcrumb[-1] for s in parsed.sections if s.breadcrumb]
    assert "Table of Contents" not in titles


def test_headings_are_level_reliable() -> None:
    parsed = parse_text(MD)
    assert all(s.level_reliable for s in parsed.sections)


def test_section_anchors_point_into_raw_text() -> None:
    parsed = parse_text(MD)
    pricing = next(s for s in parsed.sections if s.breadcrumb[-1:] == ["Pricing"])
    start, end = pricing.section_anchor
    assert "We charge per seat." in MD[start:end]


def test_plain_text_is_one_unreliable_section() -> None:
    parsed = parse_text("just a flat transcript line\nanother line\n")
    assert len(parsed.sections) == 1
    section = parsed.sections[0]
    assert section.breadcrumb == []
    assert section.level_reliable is False
    assert section.section_anchor == (0, len("just a flat transcript line\nanother line\n"))
