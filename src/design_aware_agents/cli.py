from __future__ import annotations

import argparse
from pathlib import Path

from design_aware_agents.run import run_snippet


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Minimal LangGraph refactor pipeline (Ollama)")
    p.add_argument("--dataset", type=Path, default=Path("design_issues.json"))
    p.add_argument("--prompts-dir", type=Path, default=Path("prompts"))
    p.add_argument("--runs-dir", type=Path, default=Path("runs"))
    p.add_argument("--id", dest="snippet_id", required=True)
    p.add_argument(
        "--model",
        required=True,
        help="Ollama model tag (built-in presets: starcoder2:7b, deepseek-coder:6.7b, qwen3.5:9b; see model_presets.py)",
    )
    p.add_argument("--max-refactor-retries", type=int, default=2)
    p.add_argument("--recursion-limit", type=int, default=40)
    p.add_argument(
        "--verbose",
        action="store_true",
        help="Print each agent's raw/parsed outputs to the terminal while running",
    )

    args = p.parse_args(argv)
    out = run_snippet(
        dataset_path=args.dataset,
        snippet_id=args.snippet_id,
        prompts_dir=args.prompts_dir,
        model=args.model,
        max_refactor_retries=args.max_refactor_retries,
        recursion_limit=args.recursion_limit,
        runs_dir=args.runs_dir,
        verbose=args.verbose,
    )
    print(str(out))
    return 0
