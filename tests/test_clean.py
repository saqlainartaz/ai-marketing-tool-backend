from pathlib import Path

from content_engine.pipeline.clean import CLEANER_VERSION, clean_transcript

FIXTURES = Path(__file__).parent / "fixtures"


def test_transcript_cleaning_matches_golden_file() -> None:
    raw = (FIXTURES / "transcript_raw.txt").read_text(encoding="utf-8")
    golden = (FIXTURES / "transcript_cleaned.golden.txt").read_text(encoding="utf-8")
    assert clean_transcript(raw) == golden


def test_cleaning_is_deterministic() -> None:
    raw = (FIXTURES / "transcript_raw.txt").read_text(encoding="utf-8")
    assert clean_transcript(raw) == clean_transcript(raw)


def test_pii_redaction() -> None:
    cleaned = clean_transcript("Ana Reyes: Email me at ana@corp.io or +1 (222) 333-4444.")
    assert "ana@corp.io" not in cleaned
    assert "[email]" in cleaned
    assert "333-4444" not in cleaned
    assert "[phone]" in cleaned


def test_cleaner_version_is_pinned() -> None:
    # Lineage records depend on this; bump it whenever cleaning rules change.
    assert CLEANER_VERSION.startswith("transcript-cleaner/")
