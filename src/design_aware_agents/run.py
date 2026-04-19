from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from design_aware_agents import __version__ as package_version
from design_aware_agents.config import load_dotenv_if_present
from design_aware_agents.deps import GraphDeps
from design_aware_agents.graph import build_app
from design_aware_agents.iteration_rank import pick_best_iteration
from design_aware_agents.llm import OpenAiClient, UsageAccumulator

METADATA_FILENAME = "metadata.json"


def _load_model_prices_usd() -> dict[str, dict[str, float]] | None:
    """
    OPENAI_MODEL_PRICES_JSON: {"model-id": {"prompt_per_million_usd": ..., "completion_per_million_usd": ...}}
    Aliases: input_per_million_usd / output_per_million_usd for prompt/completion.
    Keys must match Chat Completions model ids exactly. Estimates use list prompt/output rates only;
    cached-input pricing is not applied (token usage does not split cached vs uncached prompt).
    """
    raw = os.getenv("OPENAI_MODEL_PRICES_JSON")
    if not raw or not str(raw).strip():
        return None
    try:
        data = json.loads(str(raw).strip())
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    out: dict[str, dict[str, float]] = {}
    for model_id, v in data.items():
        if not isinstance(v, dict):
            continue
        pr = v.get("prompt_per_million_usd")
        cr = v.get("completion_per_million_usd")
        if pr is None:
            pr = v.get("input_per_million_usd")
        if cr is None:
            cr = v.get("output_per_million_usd")
        try:
            if pr is not None and cr is not None:
                out[str(model_id)] = {
                    "prompt_per_million_usd": float(pr),
                    "completion_per_million_usd": float(cr),
                }
        except (TypeError, ValueError):
            continue
    return out or None


def _estimate_cost_by_model(
    calls: list[dict[str, Any]],
    prices: dict[str, dict[str, float]] | None,
) -> tuple[float | None, dict[str, float], list[str]]:
    """
    Sum cost per API call using that call's model id.
    Returns (total, per_model_cost, models_that_had_calls_but_no_price_entry).
    """
    if not calls:
        return None, {}, []

    if not prices:
        models = sorted({str(c.get("model") or "") for c in calls if c.get("model")})
        return None, {}, models

    per_model: dict[str, float] = {}
    missing: set[str] = set()
    total = 0.0

    for c in calls:
        m = str(c.get("model") or "")
        if not m:
            continue
        pt = int(c.get("prompt_tokens") or 0)
        ct = int(c.get("completion_tokens") or 0)
        rate = prices.get(m)
        if not rate:
            missing.add(m)
            continue
        p_rate = float(rate["prompt_per_million_usd"])
        c_rate = float(rate["completion_per_million_usd"])
        part = (pt / 1_000_000.0) * p_rate + (ct / 1_000_000.0) * c_rate
        total += part
        per_model[m] = per_model.get(m, 0.0) + part

    if not per_model:
        return None, {}, sorted(missing)

    return (round(total, 6), {k: round(v, 6) for k, v in per_model.items()}, sorted(missing))


def _build_token_usage_metadata(token_usage: UsageAccumulator) -> dict[str, Any]:
    """Totals + by_model + optional cost; never includes per-call rows."""
    prices = _load_model_prices_usd()
    est, by_cost, missing = _estimate_cost_by_model(token_usage.calls, prices)
    out: dict[str, Any] = {
        "totals": token_usage.totals(),
        "by_model": token_usage.totals_by_model(),
    }
    if est is not None:
        out["estimated_cost_usd"] = est
        out["estimated_cost_by_model_usd"] = by_cost
    if missing:
        out["pricing_missing_for_models"] = missing
    if prices and est is not None:
        out["pricing_source"] = "OPENAI_MODEL_PRICES_JSON"
    elif not prices:
        out["pricing_note"] = "Set OPENAI_MODEL_PRICES_JSON for per-model estimated_cost_usd."
    return out


def refactored_code_filename(item: dict[str, Any], snippet_id: str) -> str:
    """``{file_stem}_refactored{suffix}`` from ``file_name``, e.g. ``snippet4_refactored.php``."""
    fn = item.get("file_name")
    if isinstance(fn, str) and fn.strip():
        p = Path(fn.strip())
        if p.suffix:
            return f"{p.stem}_refactored{p.suffix}"
    ext = item.get("extension") or ""
    if isinstance(ext, str) and ext.strip():
        e = ext.strip()
        if not e.startswith("."):
            e = "." + e
    else:
        e = ".txt"
    return f"{snippet_id}_refactored{e}"


def _build_metadata_payload(
    *,
    final: dict[str, Any],
    item: dict[str, Any],
    snippet_id: str,
    dataset_path: Path,
    model_analyze: str,
    model_validate: str,
    model_refactor: str,
    refactored_code_file: str | None,
    token_usage: UsageAccumulator | None,
) -> dict[str, Any]:
    log: list[dict[str, Any]] = list(final.get("iteration_log") or [])
    best = pick_best_iteration(log) if log else None

    if best:
        chosen_refactor = dict(best.get("refactor") or {})
        chosen_validation = best.get("validation")
        selected_attempt = best.get("attempt")
    else:
        chosen_refactor = dict(final.get("refactor") or {})
        chosen_validation = final.get("validation")
        selected_attempt = final.get("attempt")

    refactor = dict(chosen_refactor)
    refactor.pop("refactored_code", None)
    if refactored_code_file:
        refactor["refactored_code_file"] = refactored_code_file

    dataset_item = {
        "id": item.get("id"),
        "snippet_index": item.get("snippet_index"),
        "file_name": item.get("file_name"),
        "language": item.get("language"),
        "extension": item.get("extension"),
        "design_issues": item.get("design_issues"),
    }

    selection: dict[str, Any] | None = None
    if log:
        selection = {
            "policy": (
                "best iteration: preserves_behavior (yes > uncertain > no), "
                "then higher improvement_score, then lower attempt number"
            ),
            "selected_attempt": selected_attempt,
            "last_graph_attempt": final.get("attempt"),
            "iterations": [
                {
                    "attempt": e.get("attempt"),
                    "preserves_behavior": (e.get("validation") or {}).get("preserves_behavior"),
                    "improvement_score": (e.get("validation") or {}).get("improvement_score"),
                    "issue_resolved": (e.get("validation") or {}).get("issue_resolved"),
                }
                for e in log
            ],
        }

    out: dict[str, Any] = {
        "output_format_version": 2,
        "finished_at": datetime.now(timezone.utc).isoformat(),
        "run": {
            "snippet_id": snippet_id,
            "dataset_path": str(dataset_path),
            "models": {
                "analyze": model_analyze,
                "validate": model_validate,
                "refactor": model_refactor,
            },
            "package_version": package_version,
        },
        "dataset_item": dataset_item,
        "analysis": final.get("analysis"),
        "refactor": refactor,
        "validation": chosen_validation,
        "attempt": final.get("attempt"),
        "stop_reason": final.get("stop_reason"),
    }
    if selection is not None:
        out["selection"] = selection

    if token_usage is not None and token_usage.calls:
        out["token_usage"] = _build_token_usage_metadata(token_usage)

    return out


def load_dataset(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_item(dataset: dict[str, Any], snippet_id: str) -> dict[str, Any]:
    for it in dataset.get("items", []):
        if it.get("id") == snippet_id:
            return it
    raise KeyError(f"Unknown snippet id: {snippet_id}")


def ordered_dataset_items(dataset: dict[str, Any]) -> list[dict[str, Any]]:
    """Items sorted by ``snippet_index`` (then id), for stable ``--first N`` / ``--all`` order."""
    items = [it for it in (dataset.get("items") or []) if isinstance(it, dict)]

    def sort_key(it: dict[str, Any]) -> tuple[int, str]:
        raw = it.get("snippet_index")
        n = 10**9
        if isinstance(raw, bool):
            n = int(raw)
        elif isinstance(raw, int):
            n = raw
        elif isinstance(raw, float) and raw == int(raw):
            n = int(raw)
        elif raw is not None:
            try:
                n = int(str(raw).strip())
            except (TypeError, ValueError):
                pass
        return (n, str(it.get("id") or ""))

    return sorted(items, key=sort_key)


def run_snippet(
    *,
    dataset_path: Path,
    snippet_id: str,
    prompts_dir: Path,
    model_analyze: str,
    model_validate: str,
    model_refactor: str,
    max_refactor_retries: int,
    recursion_limit: int,
    runs_dir: Path,
    verbose: bool = False,
) -> Path:
    load_dotenv_if_present()
    dataset = load_dataset(dataset_path)
    item = find_item(dataset, snippet_id)

    usage = UsageAccumulator()
    llm = OpenAiClient.from_env(usage=usage)
    try:
        deps = GraphDeps(
            llm=llm,
            model_analyze=model_analyze,
            model_validate=model_validate,
            model_refactor=model_refactor,
            prompts_dir=prompts_dir,
            max_refactor_retries=max_refactor_retries,
            verbose=verbose,
        )
        app = build_app()

        if verbose:
            print(
                f"\n=== run: {snippet_id} "
                f"(analyze={model_analyze} validate={model_validate} refactor={model_refactor}) ===\n",
                flush=True,
            )

        final = app.invoke(
            {"snippet_id": snippet_id, "hotspot": item, "attempt": 0},
            config={
                "recursion_limit": recursion_limit,
                "configurable": {"deps": deps},
            },
        )

        if verbose:
            print("\n=== done ===\n", flush=True)
            _log = list(final.get("iteration_log") or [])
            if _log:
                _best = pick_best_iteration(_log)
                if _best is not None:
                    print(
                        f"[selection] Saved output uses attempt {_best.get('attempt')} "
                        f"(best of {len(_log)}); see metadata.json \"selection\".\n",
                        flush=True,
                    )

        out_dir = runs_dir / snippet_id
        out_dir.mkdir(parents=True, exist_ok=True)

        code_name = refactored_code_filename(item, snippet_id)
        log = list(final.get("iteration_log") or [])
        best = pick_best_iteration(log) if log else None
        if best:
            ref_src = best.get("refactor") or {}
            refactored_body = ref_src.get("refactored_code")
        else:
            refactor_fb = final.get("refactor") or {}
            refactored_body = refactor_fb.get("refactored_code")
        ref_file: str | None = None
        if isinstance(refactored_body, str):
            code_path = out_dir / code_name
            code_path.write_text(refactored_body, encoding="utf-8")
            ref_file = code_name

        meta = _build_metadata_payload(
            final=final,
            item=item,
            snippet_id=snippet_id,
            dataset_path=dataset_path,
            model_analyze=model_analyze,
            model_validate=model_validate,
            model_refactor=model_refactor,
            refactored_code_file=ref_file,
            token_usage=usage,
        )
        out_path = out_dir / METADATA_FILENAME
        out_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return out_path
    finally:
        llm.close()
