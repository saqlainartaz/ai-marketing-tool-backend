"""Voyage embedding provider (Anthropic's recommended embeddings vendor).

voyage-4: 1024-dim default — matches EMBEDDING_DIM, no column migration.
Lazy import, env-gated key, fail-closed at call time.
"""

import os
from typing import Any

from content_engine.models import EMBEDDING_DIM


class VoyageEmbedder:
    name = "voyage"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("VOYAGE_API_KEY", "")
        self._model = model or os.environ.get("ENGINE_VOYAGE_MODEL", "voyage-4")
        self._client: Any = None

    def _get_client(self) -> Any:
        if not self._api_key:
            raise RuntimeError(
                "VOYAGE_API_KEY is not set. The voyage provider needs it at call "
                "time; tests and CI should use the fake provider instead."
            )
        if self._client is None:
            try:
                import voyageai
            except ImportError as exc:  # pragma: no cover - dep is installed here
                raise ImportError(
                    "voyageai package not installed. Run: python -m uv add voyageai"
                ) from exc
            self._client = voyageai.Client(api_key=self._api_key)
        return self._client

    def embed(self, texts: list[str], *, input_type: str = "document") -> list[list[float]]:
        client = self._get_client()
        result = client.embed(
            texts,
            model=self._model,
            input_type=input_type,
            output_dimension=EMBEDDING_DIM,
        )
        return result.embeddings
