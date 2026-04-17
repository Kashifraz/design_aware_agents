from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from design_aware_agents.deps import GraphDeps
from design_aware_agents.graph import build_app
from design_aware_agents.ollama import OllamaClient


def load_dataset(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def find_item(dataset: dict[str, Any], snippet_id: str) -> dict[str, Any]:
    for it in dataset.get("items", []):
        if it.get("id") == snippet_id:
            return it
    raise KeyError(f"Unknown snippet id: {snippet_id}")


def run_snippet(
    *,
    dataset_path: Path,
    snippet_id: str,
    prompts_dir: Path,
    model: str,
    max_refactor_retries: int,
    recursion_limit: int,
    runs_dir: Path,
    verbose: bool = False,
) -> Path:
    dataset = load_dataset(dataset_path)
    item = find_item(dataset, snippet_id)

    ollama = OllamaClient()
    try:
        deps = GraphDeps(
            ollama=ollama,
            model=model,
            prompts_dir=prompts_dir,
            max_refactor_retries=max_refactor_retries,
            verbose=verbose,
        )
        app = build_app()

        if verbose:
            print(f"\n=== run: {snippet_id} (model={model}) ===\n", flush=True)

        final = app.invoke(
            {"snippet_id": snippet_id, "hotspot": item, "attempt": 0},
            config={
                "recursion_limit": recursion_limit,
                "configurable": {"deps": deps},
            },
        )

        if verbose:
            print("\n=== done ===\n", flush=True)

        out_dir = runs_dir / snippet_id
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "run.json"
        out_path.write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding="utf-8")
        return out_path
    finally:
        ollama.close()
