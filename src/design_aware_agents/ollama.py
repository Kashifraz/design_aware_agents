from __future__ import annotations

from dataclasses import dataclass
import json
import os
from typing import Any

import httpx


@dataclass(frozen=True)
class OllamaSettings:
    base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")


class OllamaClient:
    def __init__(self, settings: OllamaSettings | None = None, *, timeout_s: float = 600.0) -> None:
        self._settings = settings or OllamaSettings()
        self._http = httpx.Client(timeout=timeout_s)

    def close(self) -> None:
        self._http.close()

    def chat_json(self, model: str, user_prompt: str, *, temperature: float = 0.2) -> str:
        url = f"{self._settings.base_url.rstrip('/')}/api/chat"
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": user_prompt}],
            "stream": False,
            "format": "json",
            "options": {"temperature": temperature},
        }
        resp = self._http.post(url, json=payload)
        resp.raise_for_status()
        data = resp.json()
        content = (data.get("message") or {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError(f"Unexpected Ollama response: {json.dumps(data)[:500]}")
        return content
