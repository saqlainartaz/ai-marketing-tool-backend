"""Provider registry — brand-loom pattern (Apache-2.0): lazy imports, env-var
resolution, fake-by-default so the whole system runs keyless in CI.

Real providers (anthropic, voyage) register here in M1B behind the same
Protocols; their SDK imports stay lazy with install-hint errors.
"""

import os
from typing import Protocol


class LLMProvider(Protocol):
    name: str

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,
    ) -> str: ...


class EmbeddingProvider(Protocol):
    name: str

    def embed(self, texts: list[str]) -> list[list[float]]: ...


def _build_fake_llm() -> LLMProvider:
    from content_engine.providers.fake import FakeLLM

    return FakeLLM()


def _build_fake_embedder() -> EmbeddingProvider:
    from content_engine.providers.fake import FakeEmbedder

    return FakeEmbedder()


_LLM_BUILDERS = {"fake": _build_fake_llm}
_EMBEDDING_BUILDERS = {"fake": _build_fake_embedder}


def get_llm_provider(name: str | None = None) -> LLMProvider:
    resolved = name or os.environ.get("ENGINE_LLM_PROVIDER", "fake")
    try:
        return _LLM_BUILDERS[resolved]()
    except KeyError:
        raise ValueError(f"Unknown LLM provider: {resolved!r}") from None


def get_embedding_provider(name: str | None = None) -> EmbeddingProvider:
    resolved = name or os.environ.get("ENGINE_EMBEDDING_PROVIDER", "fake")
    try:
        return _EMBEDDING_BUILDERS[resolved]()
    except KeyError:
        raise ValueError(f"Unknown embedding provider: {resolved!r}") from None
