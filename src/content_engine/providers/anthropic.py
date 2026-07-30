"""Anthropic LLM provider — lazy SDK import, env-gated key, fail-closed at
call time so keyless environments (CI) never construct a client.

Includes server-side refusal fallbacks by default: on a safety-classifier
decline the API re-runs the request on Anthropic's recommended fallback model
instead of returning an empty response (`fallbacks: "default"`, beta).
"""

import os
from typing import Any


class AnthropicLLM:
    name = "anthropic"

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self._api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self._model = model or os.environ.get("ENGINE_ANTHROPIC_MODEL", "claude-opus-5")
        self._client: Any = None

    def _get_client(self) -> Any:
        if not self._api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. The anthropic provider needs it at "
                "call time; tests and CI should use the fake provider instead."
            )
        if self._client is None:
            try:
                import anthropic
            except ImportError as exc:  # pragma: no cover - dep is installed here
                raise ImportError(
                    "anthropic package not installed. Run: python -m uv add anthropic"
                ) from exc
            self._client = anthropic.Anthropic(api_key=self._api_key)
        return self._client

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.0,  # accepted for Protocol parity; not sent (400 on Opus 5)
    ) -> str:
        client = self._get_client()
        kwargs: dict[str, Any] = {
            "model": self._model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            "betas": ["server-side-fallback-2026-07-01"],
            "fallbacks": "default",
        }
        if system is not None:
            kwargs["system"] = system
        # Stream + final message: large max_tokens would otherwise trip the
        # SDK's 10-minute non-streaming guard.
        with client.beta.messages.stream(**kwargs) as stream:
            response = stream.get_final_message()
        if response.stop_reason == "refusal":
            category = getattr(getattr(response, "stop_details", None), "category", None)
            raise RuntimeError(f"Model declined the request (refusal, category={category})")
        return "".join(block.text for block in response.content if block.type == "text")
