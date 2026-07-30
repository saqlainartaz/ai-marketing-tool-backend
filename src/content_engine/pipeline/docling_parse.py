"""Docling adapter (Issue 9): binary documents (PDF/docx/pptx) → markdown.

Docling (MIT) is the reuse-list parser — we never write our own. Import is
lazy and the converter is a module singleton: model weights load once per
process, and keyless/test environments that never touch a binary file never
pay the import cost. The markdown output flows into the existing parse →
clean → atomise pipeline unchanged.
"""

from io import BytesIO
from typing import Any

BINARY_EXTENSIONS = frozenset({".pdf", ".docx", ".pptx", ".xlsx"})

_converter: Any = None


def docling_version() -> str:
    import importlib.metadata

    return f"docling-parser/{importlib.metadata.version('docling')}"


def convert_to_markdown(data: bytes, filename: str) -> str:
    global _converter
    try:
        from docling.datamodel.base_models import DocumentStream
        from docling.document_converter import DocumentConverter
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "docling package not installed. Run: python -m uv add docling"
        ) from exc

    if _converter is None:
        _converter = DocumentConverter()
    result = _converter.convert(DocumentStream(name=filename, stream=BytesIO(data)))
    return result.document.export_to_markdown()
