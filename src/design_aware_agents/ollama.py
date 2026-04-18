from __future__ import annotations

from dataclasses import dataclass
import json
import os
import time
from typing import Any
from urllib.parse import urlparse

import httpx


@dataclass(frozen=True)
class OllamaSettings:
    base_url: str = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")


def _num_predict() -> int:
    """
    Max tokens to generate. Ollama defaults are often too small for JSON that embeds
    full code, which truncates mid-string and breaks parsing.
    """
    return int(os.getenv("OLLAMA_NUM_PREDICT", "8192"))


def _effective_num_predict(override: int | None) -> int:
    return override if override is not None else _num_predict()


def _ollama_options(temperature: float, num_predict: int | None, num_ctx: int | None = None) -> dict[str, Any]:
    opts: dict[str, Any] = {
        "temperature": temperature,
        "num_predict": _effective_num_predict(num_predict),
    }
    if num_ctx is not None:
        opts["num_ctx"] = num_ctx
    return opts


def _httpx_trust_env(base_url: str) -> bool:
    """
    httpx defaults to trust_env=True, so HTTP_PROXY / HTTPS_PROXY apply to every URL.
    Local Ollama is then sent through a corporate proxy and often returns 503 while
    curl (no proxy) works. Disable env proxies for loopback unless overridden.
    """
    if os.getenv("OLLAMA_HTTP_TRUST_ENV") is not None:
        return os.getenv("OLLAMA_HTTP_TRUST_ENV", "").lower() in ("1", "true", "yes")
    host = (urlparse(base_url).hostname or "").lower()
    return host not in ("127.0.0.1", "localhost", "::1")


class OllamaClient:
    def __init__(self, settings: OllamaSettings | None = None, *, timeout_s: float = 600.0) -> None:
        self._settings = settings or OllamaSettings()
        self._http = httpx.Client(
            timeout=timeout_s,
            trust_env=_httpx_trust_env(self._settings.base_url),
        )

    def close(self) -> None:
        self._http.close()

    def _post_json(self, url: str, payload: dict[str, Any]) -> httpx.Response:
        """POST JSON; retry a few times on 503 (Ollama sometimes returns transient 503 / semaphore busy)."""
        retries = max(1, int(os.getenv("OLLAMA_HTTP_503_RETRIES", "2")))
        delay_s = float(os.getenv("OLLAMA_HTTP_503_DELAY_S", "1"))
        last: httpx.Response | None = None
        for attempt in range(retries):
            last = self._http.post(url, json=payload)
            if last.status_code != 503:
                return last
            if attempt < retries - 1:
                time.sleep(delay_s)
        assert last is not None
        return last

    def _raise_http(self, resp: httpx.Response, url: str) -> None:
        if not resp.is_error:
            return
        detail = resp.text.strip() or "(empty body)"
        raise httpx.HTTPStatusError(
            f"{resp.status_code} {resp.reason_phrase} for {url}: {detail}",
            request=resp.request,
            response=resp,
        )

    def _chat_content(
        self,
        model: str,
        user_prompt: str,
        *,
        temperature: float,
        use_json_format: bool,
        num_predict: int | None = None,
        num_ctx: int | None = None,
    ) -> str:
        base = self._settings.base_url.rstrip("/")
        url = f"{base}/api/chat"
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": user_prompt}],
            "stream": False,
            "options": _ollama_options(temperature, num_predict, num_ctx),
        }
        if use_json_format:
            payload["format"] = "json"
        resp = self._post_json(url, payload)
        self._raise_http(resp, url)
        data = resp.json()
        content = (data.get("message") or {}).get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError(f"Unexpected Ollama /api/chat response: {json.dumps(data)[:500]}")
        return content

    def _generate_content(
        self, model: str, user_prompt: str, *, temperature: float, num_predict: int | None = None, num_ctx: int | None = None
    ) -> str:
        base = self._settings.base_url.rstrip("/")
        url = f"{base}/api/generate"
        payload: dict[str, Any] = {
            "model": model,
            "prompt": user_prompt,
            "stream": False,
            "format": "json",
            "options": _ollama_options(temperature, num_predict, num_ctx),
        }
        resp = self._post_json(url, payload)
        self._raise_http(resp, url)
        data = resp.json()
        content = data.get("response")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError(f"Unexpected Ollama /api/generate response: {json.dumps(data)[:500]}")
        return content

    def _openai_chat_content(
        self,
        model: str,
        user_prompt: str,
        *,
        temperature: float,
        json_mode: bool,
        num_predict: int | None = None,
    ) -> str:
        """OpenAI-compatible route; some Ollama builds behave differently from /api/chat."""
        base = self._settings.base_url.rstrip("/")
        url = f"{base}/v1/chat/completions"
        payload: dict[str, Any] = {
            "model": model,
            "messages": [{"role": "user", "content": user_prompt}],
            "stream": False,
            "temperature": temperature,
            "max_tokens": _effective_num_predict(num_predict),
        }
        if json_mode:
            payload["response_format"] = {"type": "json_object"}
        resp = self._post_json(url, payload)
        self._raise_http(resp, url)
        data = resp.json()
        choices = data.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError(f"Unexpected Ollama /v1/chat/completions response: {json.dumps(data)[:500]}")
        msg = choices[0].get("message") if isinstance(choices[0], dict) else None
        content = msg.get("content") if isinstance(msg, dict) else None
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError(f"Unexpected Ollama /v1/chat/completions response: {json.dumps(data)[:500]}")
        return content

    def chat_json(
        self,
        model: str,
        user_prompt: str,
        *,
        temperature: float = 0.2,
        num_predict: int | None = None,
        num_ctx: int | None = None,
        prefer_plain_before_json: bool = False,
    ) -> str:
        """
        Ask for JSON-shaped output. Tries several Ollama endpoints/modes because some
        installs return 503 on /api/chat while /api/generate or /v1/chat/completions still work.

        num_predict: max tokens to generate (Ollama option); None uses OLLAMA_NUM_PREDICT.
        num_ctx: optional context length (Ollama); None omits the option.
        prefer_plain_before_json: try unconstrained chat before strict JSON mode (helps code-heavy JSON).
        """
        chat_fmt = lambda: self._chat_content(
            model,
            user_prompt,
            temperature=temperature,
            use_json_format=True,
            num_predict=num_predict,
            num_ctx=num_ctx,
        )
        chat_plain = lambda: self._chat_content(
            model,
            user_prompt,
            temperature=temperature,
            use_json_format=False,
            num_predict=num_predict,
            num_ctx=num_ctx,
        )
        gen = lambda: self._generate_content(
            model, user_prompt, temperature=temperature, num_predict=num_predict, num_ctx=num_ctx
        )
        v1_json = lambda: self._openai_chat_content(
            model, user_prompt, temperature=temperature, json_mode=True, num_predict=num_predict
        )
        v1_plain = lambda: self._openai_chat_content(
            model, user_prompt, temperature=temperature, json_mode=False, num_predict=num_predict
        )

        if prefer_plain_before_json:
            attempts: list[tuple[str, Any]] = [
                ("/api/chat (no format)", chat_plain),
                ("/api/chat + format=json", chat_fmt),
                ("/api/generate + format=json", gen),
                ("/v1/chat/completions + response_format=json_object", v1_json),
                ("/v1/chat/completions (plain)", v1_plain),
            ]
        else:
            attempts = [
                ("/api/chat + format=json", chat_fmt),
                ("/api/chat (no format)", chat_plain),
                ("/api/generate + format=json", gen),
                ("/v1/chat/completions + response_format=json_object", v1_json),
                ("/v1/chat/completions (plain)", v1_plain),
            ]
        errors: list[str] = []
        for label, fn in attempts:
            try:
                return fn()
            except (httpx.HTTPStatusError, httpx.RequestError, RuntimeError) as e:
                errors.append(f"{label}: {e}")
                continue
        hint = (
            "\n\nIf every line shows 503 with an empty body, the Ollama server is not accepting "
            "inference over HTTP (stuck runner, overload, or bad install). Restart Ollama, run "
            "`ollama ps` / `ollama stop --all`, update Ollama, and POST the same URL with curl or "
            "Invoke-RestMethod to confirm outside Python."
        )
        raise RuntimeError("Ollama request failed on all fallbacks:\n" + "\n".join(errors) + hint)
