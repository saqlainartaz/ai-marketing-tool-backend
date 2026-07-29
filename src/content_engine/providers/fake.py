"""Deterministic keyless providers. Pure functions of their inputs — no
randomness, no network — so CI assertions are stable (brand-loom pattern)."""

import hashlib
import json
import struct

from content_engine.models import EMBEDDING_DIM


class FakeLLM:
    name = "fake"

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str:
        if "json" in prompt.lower():
            return json.dumps({"result": "fake-response", "prompt_length": len(prompt)})
        flat = prompt.replace("\n", " ")[:120]
        return f"[fake-provider] Response for: {flat}"


class FakeEmbedder:
    """Hash-based vectors: deterministic, content-sensitive, unit-normalized,
    dimension-matched to the real provider (EMBEDDING_DIM)."""

    name = "fake"

    def embed(self, texts: list[str], *, input_type: str = "document") -> list[list[float]]:
        return [self._one(text) for text in texts]

    @staticmethod
    def _one(text: str) -> list[float]:
        values: list[float] = []
        counter = 0
        seed = hashlib.sha256(text.encode("utf-8")).digest()
        while len(values) < EMBEDDING_DIM:
            block = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
            for i in range(0, len(block) - 3, 4):
                (n,) = struct.unpack(">I", block[i : i + 4])
                values.append((n / 0xFFFFFFFF) * 2.0 - 1.0)  # [-1, 1]
            counter += 1
        values = values[:EMBEDDING_DIM]
        norm = sum(v * v for v in values) ** 0.5 or 1.0
        return [v / norm for v in values]
