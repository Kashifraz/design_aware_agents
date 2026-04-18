"""Minimal Ollama /api/chat checks (no format vs format=json). Run from repo root: python scripts/test_ollama_chat.py"""

from __future__ import annotations

import json
import os
import sys

import httpx

BASE = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
MODEL = os.getenv("OLLAMA_TEST_MODEL", "qwen2.5-coder:3b")
PROMPT = "say hi in one word"


def main() -> int:
    url = f"{BASE}/api/chat"
    common = {
        "model": MODEL,
        "messages": [{"role": "user", "content": PROMPT}],
        "stream": False,
    }

    for label, extra in [
        ("1) /api/chat without format", {}),
        ('2) /api/chat with format "json"', {"format": "json"}),
    ]:
        payload = {**common, **extra}
        print(f"\n=== {label} ===", flush=True)
        print(json.dumps(payload, indent=2), flush=True)
        try:
            r = httpx.post(url, json=payload, timeout=120.0)
        except httpx.RequestError as e:
            print(f"request error: {e}", flush=True)
            continue
        print(f"status: {r.status_code}", flush=True)
        text = r.text.strip() or "(empty body)"
        print(text[:4000], flush=True)
        if len(text) > 4000:
            print(f"... ({len(text) - 4000} more chars truncated)", flush=True)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
