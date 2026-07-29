from pathlib import Path

from content_engine.pipeline.atomise import ATOMIZER_VERSION, extract_atoms

FIXTURES = Path(__file__).parent / "fixtures"
CLEANED = (FIXTURES / "transcript_cleaned.golden.txt").read_text(encoding="utf-8")


def test_transcript_yields_tldr_and_objection() -> None:
    atoms = extract_atoms("sales_call_transcript", CLEANED)
    types = {a.atom_type for a in atoms}
    assert "tldr" in types  # composition guardrail: always at least one tldr
    assert "objection" in types

    objection = next(a for a in atoms if a.atom_type == "objection")
    assert "steep" in objection.text
    assert objection.provenance["speaker"] == "John Smith"
    assert isinstance(objection.provenance["line"], int)


def test_proof_point_detected() -> None:
    atoms = extract_atoms("sales_call_transcript", CLEANED)
    proof = [a for a in atoms if a.atom_type == "proof_point"]
    assert proof and "payback" in proof[0].text


def test_atoms_are_deterministic() -> None:
    first = extract_atoms("sales_call_transcript", CLEANED)
    second = extract_atoms("sales_call_transcript", CLEANED)
    assert [a.content_hash for a in first] == [a.content_hash for a in second]


def test_every_atom_has_provenance_and_lifecycle_fields() -> None:
    for atom in extract_atoms("sales_call_transcript", CLEANED):
        assert atom.provenance  # structural, never optional
        assert atom.evidence_kind in {"measured", "quoted", "inferred", "unverified"}
        assert atom.content_hash
        assert 1 <= atom.impact <= 5
        assert 0.0 <= atom.confidence <= 1.0


def test_atom_count_guardrails() -> None:
    atoms = extract_atoms("sales_call_transcript", CLEANED)
    assert 1 <= len(atoms) <= 15


def test_markdown_docs_yield_section_atoms() -> None:
    md = "# Brand\n\nWe promise honesty.\n\n## Voice\n\nPlain words. No hype ever.\n"
    atoms = extract_atoms("brand_doc", md)
    assert any(a.atom_type == "tldr" for a in atoms)
    section_atoms = [a for a in atoms if a.provenance.get("breadcrumb")]
    assert section_atoms, "markdown atoms carry breadcrumbs in provenance"


def test_atomizer_version_pinned() -> None:
    assert ATOMIZER_VERSION.startswith("fake-atomizer/")
