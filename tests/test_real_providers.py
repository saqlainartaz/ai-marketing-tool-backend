"""Real provider adapters (Issue 7) — keyless by design.

Construction and registry resolution never require keys; missing keys fail
closed with a helpful error at call time. Live-call smoke tests self-skip
unless the relevant env key exists (parity-eval pattern, brand-loom).
"""

import os

import pytest

from content_engine.models import EMBEDDING_DIM
from content_engine.providers import get_embedding_provider, get_llm_provider


def test_registry_resolves_real_providers_by_env(monkeypatch) -> None:
    monkeypatch.setenv("ENGINE_LLM_PROVIDER", "anthropic")
    monkeypatch.setenv("ENGINE_EMBEDDING_PROVIDER", "voyage")
    assert get_llm_provider().name == "anthropic"
    assert get_embedding_provider().name == "voyage"


def test_fake_remains_the_default(monkeypatch) -> None:
    monkeypatch.delenv("ENGINE_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("ENGINE_EMBEDDING_PROVIDER", raising=False)
    assert get_llm_provider().name == "fake"
    assert get_embedding_provider().name == "fake"


def test_anthropic_without_key_fails_closed_at_call_time(monkeypatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    llm = get_llm_provider("anthropic")  # construction must not raise
    with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
        llm.generate("hello")


def test_voyage_without_key_fails_closed_at_call_time(monkeypatch) -> None:
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    embedder = get_embedding_provider("voyage")
    with pytest.raises(RuntimeError, match="VOYAGE_API_KEY"):
        embedder.embed(["hello"])


def test_fake_embedder_accepts_input_type() -> None:
    # Search (M1B) embeds queries vs documents differently; the fake must
    # accept the same signature so keyless tests cover the call path.
    embedder = get_embedding_provider("fake")
    [vector] = embedder.embed(["hello"], input_type="query")
    assert len(vector) == EMBEDDING_DIM


@pytest.mark.skipif(not os.environ.get("ANTHROPIC_API_KEY"), reason="no ANTHROPIC_API_KEY")
def test_anthropic_live_smoke() -> None:
    out = get_llm_provider("anthropic").generate("Reply with exactly: OK", max_tokens=64)
    assert out.strip()


@pytest.mark.skipif(not os.environ.get("VOYAGE_API_KEY"), reason="no VOYAGE_API_KEY")
def test_voyage_live_smoke() -> None:
    [vector] = get_embedding_provider("voyage").embed(["hello world"])
    assert len(vector) == EMBEDDING_DIM
