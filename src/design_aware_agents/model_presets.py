"""
Per-model defaults for Ollama (temperature, num_predict, num_ctx).

Env vars still win when set: OLLAMA_TEMPERATURE, OLLAMA_NUM_PREDICT, OLLAMA_REFACTOR_NUM_PREDICT,
OLLAMA_VALIDATE_NUM_PREDICT, OLLAMA_NUM_CTX.

Set DESIGN_AWARE_FAST=1 (or use CLI --fast) to cap context/output for quicker runs on consumer GPUs.

Matched models (substring, lowercased):
  - starcoder2:7b  → StarCoder 2
  - deepseek-coder:6.7b → DeepSeek Coder
  - qwen3.5:9b (any qwen*) → Qwen family
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class InferenceConfig:
    temperature: float
    """Ollama num_ctx; None = let Ollama use the model card default."""
    num_ctx: int | None
    analyze_num_predict: int
    refactor_num_predict: int
    validate_num_predict: int
    prefer_plain_refactor: bool


# --- Presets tuned for: speed vs quality, JSON+code in refactor, VRAM-friendly ctx ---

_DEFAULT = InferenceConfig(
    temperature=0.2,
    num_ctx=None,
    analyze_num_predict=8192,
    refactor_num_predict=32768,
    validate_num_predict=3072,
    prefer_plain_refactor=True,
)

_STARCODER2 = InferenceConfig(
    temperature=0.1,
    num_ctx=16384,
    analyze_num_predict=6144,
    refactor_num_predict=16384,
    validate_num_predict=2048,
    prefer_plain_refactor=True,
)

_DEEPSEEK_CODER = InferenceConfig(
    temperature=0.12,
    num_ctx=16384,
    analyze_num_predict=6144,
    refactor_num_predict=20480,
    validate_num_predict=2048,
    prefer_plain_refactor=True,
)

# Qwen 7B–9B: large num_ctx / refactor caps make the refactor step slow on 8–12GB GPUs.
_QWEN = InferenceConfig(
    temperature=0.15,
    num_ctx=16384,
    analyze_num_predict=6144,
    refactor_num_predict=10240,
    validate_num_predict=2048,
    prefer_plain_refactor=False,
)


def _base_preset(model: str) -> InferenceConfig:
    m = model.lower()
    if "starcoder2" in m or "starcoder" in m:
        return _STARCODER2
    if "deepseek" in m:
        return _DEEPSEEK_CODER
    if "qwen" in m:
        # Small Qwen tags (e.g. qwen2.5-coder:3b) stay on defaults to avoid huge num_ctx on weak GPUs.
        if any(x in m for x in ("3b", "1.8b", "0.5b", "1.5b")):
            return _DEFAULT
        return _QWEN
    return _DEFAULT


def inference_config(model: str) -> InferenceConfig:
    """Resolve preset with env overrides (env wins)."""
    p = _base_preset(model)

    temperature = p.temperature
    ot = os.getenv("OLLAMA_TEMPERATURE")
    if ot is not None and str(ot).strip() != "":
        temperature = float(str(ot).strip())

    nctx: int | None
    ox = os.getenv("OLLAMA_NUM_CTX")
    if ox is not None and str(ox).strip() != "":
        nctx = int(str(ox).strip())
    else:
        nctx = p.num_ctx

    analyze = p.analyze_num_predict
    if os.getenv("OLLAMA_NUM_PREDICT") is not None and str(os.getenv("OLLAMA_NUM_PREDICT", "")).strip() != "":
        analyze = int(os.getenv("OLLAMA_NUM_PREDICT", "").strip())

    refactor = p.refactor_num_predict
    if os.getenv("OLLAMA_REFACTOR_NUM_PREDICT") is not None and str(os.getenv("OLLAMA_REFACTOR_NUM_PREDICT", "")).strip() != "":
        refactor = int(os.getenv("OLLAMA_REFACTOR_NUM_PREDICT", "").strip())

    validate = p.validate_num_predict
    if os.getenv("OLLAMA_VALIDATE_NUM_PREDICT") is not None and str(os.getenv("OLLAMA_VALIDATE_NUM_PREDICT", "")).strip() != "":
        validate = int(os.getenv("OLLAMA_VALIDATE_NUM_PREDICT", "").strip())

    cfg = InferenceConfig(
        temperature=temperature,
        num_ctx=nctx,
        analyze_num_predict=analyze,
        refactor_num_predict=refactor,
        validate_num_predict=validate,
        prefer_plain_refactor=p.prefer_plain_refactor,
    )
    return _apply_fast_mode(cfg)


def _apply_fast_mode(cfg: InferenceConfig) -> InferenceConfig:
    """Tighter limits when DESIGN_AWARE_FAST=1 (CLI --fast)."""
    if os.getenv("DESIGN_AWARE_FAST", "").lower() not in ("1", "true", "yes"):
        return cfg
    nctx = cfg.num_ctx
    if nctx is None:
        nctx = 8192
    else:
        nctx = max(8192, nctx // 2)
    return InferenceConfig(
        temperature=cfg.temperature,
        num_ctx=nctx,
        analyze_num_predict=min(cfg.analyze_num_predict, 4096),
        refactor_num_predict=min(cfg.refactor_num_predict, 6144),
        validate_num_predict=min(cfg.validate_num_predict, 1536),
        prefer_plain_refactor=False,
    )
