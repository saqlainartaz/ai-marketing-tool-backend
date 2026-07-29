"""Provider registry + deterministic fakes (brand-loom pattern, Apache-2.0)."""

from content_engine.models import EMBEDDING_DIM
from content_engine.providers import get_embedding_provider, get_llm_provider


def test_default_providers_are_fake_without_env(monkeypatch) -> None:
    monkeypatch.delenv("ENGINE_LLM_PROVIDER", raising=False)
    monkeypatch.delenv("ENGINE_EMBEDDING_PROVIDER", raising=False)
    assert get_llm_provider().name == "fake"
    assert get_embedding_provider().name == "fake"


def test_fake_llm_is_deterministic() -> None:
    llm = get_llm_provider("fake")
    a = llm.generate("Extract atoms from this transcript.")
    b = llm.generate("Extract atoms from this transcript.")
    assert a == b


def test_fake_llm_returns_json_when_prompt_asks() -> None:
    import json

    llm = get_llm_provider("fake")
    out = llm.generate("Return JSON with the extracted fields.")
    assert isinstance(json.loads(out), dict)


def test_fake_embedder_matches_pinned_dimension() -> None:
    embedder = get_embedding_provider("fake")
    [vector] = embedder.embed(["hello world"])
    assert len(vector) == EMBEDDING_DIM


def test_fake_embedder_is_deterministic_and_content_sensitive() -> None:
    embedder = get_embedding_provider("fake")
    v1, v2, v3 = embedder.embed(["alpha", "alpha", "beta"])
    assert v1 == v2
    assert v1 != v3
