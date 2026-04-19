"""OpenAI Chat Completions API — used by analyze (JSON), refactor (plain), validate (JSON)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

from openai import OpenAI


@dataclass
class UsageAccumulator:
    """Aggregates ``usage`` from each Chat Completions response (per snippet run)."""

    calls: list[dict[str, Any]] = field(default_factory=list)

    def record(self, label: str, model: str, usage: Any) -> None:
        if usage is None:
            return
        pt = int(getattr(usage, "prompt_tokens", None) or 0)
        ct = int(getattr(usage, "completion_tokens", None) or 0)
        tt = getattr(usage, "total_tokens", None)
        if tt is None:
            tt = pt + ct
        else:
            tt = int(tt)
        self.calls.append(
            {
                "label": label,
                "model": model,
                "prompt_tokens": pt,
                "completion_tokens": ct,
                "total_tokens": tt,
            }
        )

    def totals(self) -> dict[str, int]:
        p = sum(c["prompt_tokens"] for c in self.calls)
        c = sum(c["completion_tokens"] for c in self.calls)
        return {
            "prompt_tokens": p,
            "completion_tokens": c,
            "total_tokens": p + c,
            "api_calls": len(self.calls),
        }

    def totals_by_model(self) -> dict[str, dict[str, int]]:
        """Aggregate token counts per model id (for metadata, not per HTTP call)."""
        agg: dict[str, dict[str, int]] = {}
        for c in self.calls:
            m = str(c.get("model") or "")
            if m not in agg:
                agg[m] = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            agg[m]["prompt_tokens"] += int(c["prompt_tokens"])
            agg[m]["completion_tokens"] += int(c["completion_tokens"])
            agg[m]["total_tokens"] += int(c["total_tokens"])
        return agg


def _default_max_completion_tokens_refactor() -> int:
    return int(os.getenv("OPENAI_MAX_TOKENS_REFACTOR", "16384"))


def _default_max_completion_tokens_json() -> int:
    return int(os.getenv("OPENAI_MAX_TOKENS_JSON", "8192"))


def _temperature() -> float:
    t = os.getenv("OPENAI_TEMPERATURE")
    if t is not None and str(t).strip() != "":
        return float(str(t).strip())
    return 0.2


def _chat_completion_create(
    client: OpenAI,
    model: str,
    messages: list[dict[str, Any]],
    *,
    max_completion_tokens: int,
    response_format: dict[str, Any] | None,
    temperature: float | None,
) -> Any:
    m = model.strip().lower()
    kwargs: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "max_completion_tokens": max_completion_tokens,
    }
    if response_format is not None:
        kwargs["response_format"] = response_format

    temp = _temperature() if temperature is None else temperature
    # GPT-5.4 (incl. nano / mini / pro): sampling params require reasoning_effort "none".
    if m.startswith("gpt-5.4"):
        kwargs["reasoning_effort"] = "none"
        kwargs["temperature"] = temp
    else:
        kwargs["temperature"] = temp

    return client.chat.completions.create(**kwargs)


@dataclass
class OpenAiClient:
    """Thin wrapper; API key from OPENAI_API_KEY (or client passed in tests)."""

    _client: OpenAI
    _usage: UsageAccumulator | None = None

    @classmethod
    def from_env(cls, usage: UsageAccumulator | None = None) -> OpenAiClient:
        from design_aware_agents.config import load_dotenv_if_present

        load_dotenv_if_present()
        return cls(_client=OpenAI(), _usage=usage)

    def _record(self, label: str, model: str, usage: Any) -> None:
        if self._usage is not None:
            self._usage.record(label, model, usage)

    def complete_json(
        self,
        model: str,
        user: str,
        *,
        temperature: float | None = None,
        usage_label: str = "complete_json",
    ) -> str:
        r = _chat_completion_create(
            self._client,
            model,
            [{"role": "user", "content": user}],
            max_completion_tokens=_default_max_completion_tokens_json(),
            response_format={"type": "json_object"},
            temperature=temperature,
        )
        self._record(usage_label, model, getattr(r, "usage", None))
        text = r.choices[0].message.content
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Empty OpenAI JSON completion")
        return text

    def complete_text(
        self,
        model: str,
        user: str,
        *,
        temperature: float | None = None,
        usage_label: str = "complete_text",
    ) -> str:
        r = _chat_completion_create(
            self._client,
            model,
            [{"role": "user", "content": user}],
            max_completion_tokens=_default_max_completion_tokens_refactor(),
            response_format=None,
            temperature=temperature,
        )
        self._record(usage_label, model, getattr(r, "usage", None))
        text = r.choices[0].message.content
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("Empty OpenAI text completion")
        return text

    def close(self) -> None:
        # OpenAI SDK sync client has no close; no-op for symmetry with callers.
        return None
