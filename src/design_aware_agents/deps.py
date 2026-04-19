from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from design_aware_agents.llm import OpenAiClient


@dataclass(frozen=True)
class GraphDeps:
    llm: OpenAiClient
    model_analyze: str
    model_validate: str
    model_refactor: str
    prompts_dir: Path
    max_refactor_retries: int
    verbose: bool = False
