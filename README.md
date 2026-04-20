# Design-aware agents

A small **LangGraph** pipeline that uses three agents—**analyze**, **refactor**, and **validate**—to study automated refactoring aimed at stated **design issues** while encouraging **behavior preservation**. Each dataset item is a code snippet plus a short design-issue label; the graph can **retry** the refactor/validate loop up to a configured maximum when validation does not meet a strict success bar.

## What it does

1. **Analyze** — Reads the snippet and design issues; returns JSON with root cause, violated principles, and explanation.
2. **Refactor** — Produces a refactoring technique, reasoning, and refactored source (JSON metadata + delimiter + plain code). On retries, **validator feedback** and the **previous refactored code** are injected into the prompt.
3. **Validate** — Judges the refactor against the design issues and original code; returns scores, behavior preservation, risks, and comments. The run may loop back to **refactor** or stop.

Persisted outputs use the **best iteration** (by preservation, then score, then lower attempt number) when multiple attempts exist.

## Requirements

- Python 3.10+ (tested in project with 3.13)
- Dependencies: see [`requirements.txt`](requirements.txt)

## Setup

```bash
cd design_aware_agents
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt
```

## CLI usage

| Mode | Command |
|------|---------|
| Single snippet | `python -m design_aware_agents --id snippet1` |
| First N snippets | `python -m design_aware_agents --first 5` |
| All snippets | `python -m design_aware_agents --all` |
| Verbose logging | add `--verbose` |


## Repository layout

```text
design_aware_agents/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── .env.example              # Example environment variables (copy to .env)
├── design_issues.json        # Default dataset: items with id, snippet_index, code, design_issues, …
├── code_snippets/            # Optional per-file copies of snippets (mirrors filenames in dataset)
├── prompts/                  # Agent prompt templates (placeholders filled at runtime)
│   ├── analyzer_agent_prompt.md
│   ├── refactoring_agent_prompt.md
│   └── validation_agent_prompt.md
├── docs/                     # Optional paper artifacts (e.g. LaTeX tables)
├── runs/                     # Default output root; often contains per-experiment subfolders
│   └── <batch_name>/         # e.g. gpt5.4_refactoring / gpt5.4mini_refactoring
│       └── <snippet_id>/
│           ├── metadata.json # Analysis, refactor summary, validation, token_usage, selection, …
│           └── *_refactored.*# Saved refactored source for the best iteration
└── src/design_aware_agents/  # Installable package
    ├── __main__.py           # python -m design_aware_agents
    ├── cli.py                # Argument parsing, batch runs, runs_dir / runs_subdir resolution
    ├── run.py                # load dataset, invoke graph, write metadata + refactored file
    ├── graph.py              # LangGraph: analyze → refactor → validate → (refactor | end)
    ├── nodes.py              # analyze / refactor / validate nodes, routing, iteration log
    ├── state.py              # AgentState schema
    ├── deps.py               # GraphDeps (LLM, models, prompts, limits)
    ├── llm.py                # OpenAI wrapper, usage accumulation, chat completion helpers
    ├── iteration_rank.py     # Pick best iteration for saved output
    └── config.py             # load_dotenv_if_present
```

## Outputs

For each snippet under **`runs/<optional_subdir>/<snippet_id>/`**:

- **`metadata.json`** — Final analysis/refactor/validation (best iteration), `iteration_log`, `selection`, `stop_reason`, optional **`token_usage`** (totals, per-model tokens, optional **estimated cost** if prices are configured).
- **`<stem>_refactored<ext>`** — Refactored code file for the chosen best iteration.
