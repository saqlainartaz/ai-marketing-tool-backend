"""Docling routing (Issue 9) — keyless & fast: the converter is stubbed so no
model weights load; the real conversion is covered by scripts/pdf_demo.py and
an opt-in test (RUN_DOCLING=1). Requires `docker compose up -d`.
"""

import os
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from content_engine.config import Settings
from content_engine.main import create_app
from content_engine.pipeline import docling_parse

KEY = "test-service-key-0123456789"
AUTH = {"X-API-Key": KEY}

# A minimal but valid single-page PDF with the text "Payback in six weeks".
MINIMAL_PDF = (
    b"%PDF-1.4\n"
    b"1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
    b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
    b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]"
    b"/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n"
    b"4 0 obj<</Length 60>>stream\n"
    b"BT /F1 24 Tf 72 700 Td (Payback in six weeks) Tj ET\n"
    b"endstream endobj\n"
    b"5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\n"
    b"trailer<</Root 1 0 R>>\n%%EOF\n"
)


@pytest.fixture()
def api(migrated_db, tmp_path: Path):
    settings = Settings(
        _env_file=None,
        service_api_key=KEY,
        database_url=migrated_db,
        raw_storage_root=str(tmp_path / "raw"),
        job_poll_interval=0.05,
    )
    with TestClient(create_app(settings)) as client:
        yield client


def _wait_atomised(api: TestClient, cid: str, doc_id: str) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        body = api.get(f"/v1/clients/{cid}/documents/{doc_id}", headers=AUTH).json()
        if body["status"] == "atomised":
            return
        assert body["status"] != "failed", body
        time.sleep(0.05)
    raise AssertionError("pipeline did not finish")


def test_pdf_routes_through_docling(api: TestClient, monkeypatch) -> None:
    calls: list[str] = []

    def stub_convert(data: bytes, filename: str) -> str:
        calls.append(filename)
        return "# Case Study\n\nCustomers see payback in six weeks with Acme.\n"

    monkeypatch.setattr(docling_parse, "convert_to_markdown", stub_convert)
    monkeypatch.setattr(docling_parse, "docling_version", lambda: "docling-parser/stub")

    cid = api.post("/v1/clients", json={"name": "PDF Inc"}, headers=AUTH).json()["id"]
    doc_id = api.post(
        f"/v1/clients/{cid}/documents",
        files={"file": ("case-study.pdf", MINIMAL_PDF, "application/pdf")},
        data={"source_type": "brand_doc"},
        headers=AUTH,
    ).json()["id"]
    _wait_atomised(api, cid, doc_id)

    assert calls == ["case-study.pdf"]
    atoms = api.get(f"/v1/clients/{cid}/atoms", headers=AUTH).json()
    assert any("payback" in a["text"].lower() for a in atoms)


def test_text_files_bypass_docling(api: TestClient, monkeypatch) -> None:
    def explode(data: bytes, filename: str) -> str:
        raise AssertionError("docling must not run for text files")

    monkeypatch.setattr(docling_parse, "convert_to_markdown", explode)

    cid = api.post("/v1/clients", json={"name": "Text Inc"}, headers=AUTH).json()["id"]
    doc_id = api.post(
        f"/v1/clients/{cid}/documents",
        files={"file": ("notes.md", b"# Notes\n\nPlain text still works.\n", "text/markdown")},
        data={"source_type": "brand_doc"},
        headers=AUTH,
    ).json()["id"]
    _wait_atomised(api, cid, doc_id)


@pytest.mark.skipif(not os.environ.get("RUN_DOCLING"), reason="set RUN_DOCLING=1 (slow)")
def test_real_docling_conversion() -> None:
    markdown = docling_parse.convert_to_markdown(MINIMAL_PDF, "mini.pdf")
    assert "payback" in markdown.lower()
