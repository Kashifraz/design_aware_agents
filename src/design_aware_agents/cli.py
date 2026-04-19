from __future__ import annotations

import argparse
import os
from pathlib import Path

from design_aware_agents.config import load_dotenv_if_present
from design_aware_agents.run import run_snippet


def _env(name: str, default: str) -> str:
    v = os.getenv(name)
    if v is not None and str(v).strip() != "":
        return str(v).strip()
    return default


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None or str(v).strip() == "":
        return default
    return int(str(v).strip())


def main(argv: list[str] | None = None) -> int:
    load_dotenv_if_present()

    p = argparse.ArgumentParser(description="LangGraph refactor pipeline (OpenAI Chat Completions)")
    p.add_argument(
        "--dataset",
        type=Path,
        default=Path(_env("DESIGN_AWARE_DATASET", "design_issues.json")),
        help="Default: env DESIGN_AWARE_DATASET or design_issues.json",
    )
    p.add_argument(
        "--prompts-dir",
        type=Path,
        default=Path(_env("DESIGN_AWARE_PROMPTS_DIR", "prompts")),
        help="Default: env DESIGN_AWARE_PROMPTS_DIR or prompts",
    )
    p.add_argument(
        "--runs-dir",
        type=Path,
        default=Path(_env("DESIGN_AWARE_RUNS_DIR", "runs")),
        help="Default: env DESIGN_AWARE_RUNS_DIR or runs",
    )
    p.add_argument("--id", dest="snippet_id", required=True)
    p.add_argument(
        "--model-analyze",
        default=_env("OPENAI_MODEL_ANALYZE", "gpt-5.4-nano"),
        help="OpenAI model for analyzer (default: env OPENAI_MODEL_ANALYZE or gpt-5.4-nano)",
    )
    p.add_argument(
        "--model-validate",
        default=_env("OPENAI_MODEL_VALIDATE", "gpt-5.4-nano"),
        help="OpenAI model for validation (default: env OPENAI_MODEL_VALIDATE or gpt-5.4-nano)",
    )
    p.add_argument(
        "--model-refactor",
        default=_env("OPENAI_MODEL_REFACTOR", "gpt-5.4-mini"),
        help="OpenAI model for refactoring (default: env OPENAI_MODEL_REFACTOR or gpt-5.4-mini)",
    )
    p.add_argument(
        "--max-refactor-retries",
        type=int,
        default=_env_int("DESIGN_AWARE_MAX_REFACTOR_RETRIES", 2),
        help="Default: env DESIGN_AWARE_MAX_REFACTOR_RETRIES or 2",
    )
    p.add_argument(
        "--recursion-limit",
        type=int,
        default=_env_int("DESIGN_AWARE_RECURSION_LIMIT", 40),
        help="Default: env DESIGN_AWARE_RECURSION_LIMIT or 40",
    )
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
        model_analyze=args.model_analyze,
        model_validate=args.model_validate,
        model_refactor=args.model_refactor,
        max_refactor_retries=args.max_refactor_retries,
        recursion_limit=args.recursion_limit,
        runs_dir=args.runs_dir,
        verbose=args.verbose,
    )
    print(str(out))
    return 0
