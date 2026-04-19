from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from design_aware_agents import __version__ as package_version
from design_aware_agents.config import load_dotenv_if_present
from design_aware_agents.deps import GraphDeps
from design_aware_agents.graph import build_app
from design_aware_agents.iteration_rank import pick_best_iteration
from design_aware_agents.llm import OpenAiClient

METADATA_FILENAME = "metadata.json"


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

    llm = OpenAiClient.from_env()
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
        )
        out_path = out_dir / METADATA_FILENAME
        out_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return out_path
    finally:
        llm.close()
