"""OpenAI Chat Completions API — used by analyze (JSON), refactor (plain), validate (JSON)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from openai import OpenAI


def _default_max_completion_tokens_refactor() -> int:
    return int(os.getenv("OPENAI_MAX_TOKENS_REFACTOR", "16384"))


def _default_max_completion_tokens_json() -> int:
    return int(os.getenv("OPENAI_MAX_TOKENS_JSON", "8192"))


def _temperature() -> float:
    t = os.getenv("OPENAI_TEMPERATURE")
    if t is not None and str(t).strip() != "":
        return float(str(t).strip())
    return 0.2


@dataclass
class OpenAiClient:
    """Thin wrapper; API key from OPENAI_API_KEY (or client passed in tests)."""

    _client: OpenAI

    @classmethod
    def from_env(cls) -> OpenAiClient:
        from design_aware_agents.config import load_dotenv_if_present

        load_dotenv_if_present()
        return cls(_client=OpenAI())

    def complete_json(self, model: str, user: str, *, temperature: float | None = None) -> str:
        temp = _temperature() if temperature is None else temperature
        r = self._client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": user}],
            temperature=temp,
            max_completion_tokens=_default_max_completion_tokens_json(),
            response_format={"type": "json_object"},
        )
        text = r.choices[0].message.content
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Empty OpenAI JSON completion")
        return text

    def complete_text(self, model: str, user: str, *, temperature: float | None = None) -> str:
        temp = _temperature() if temperature is None else temperature
        r = self._client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": user}],
            temperature=temp,
            max_completion_tokens=_default_max_completion_tokens_refactor(),
        )
        text = r.choices[0].message.content
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Empty OpenAI text completion")
        return text

    def close(self) -> None:
        # OpenAI SDK sync client has no close; no-op for symmetry with callers.
        return None
