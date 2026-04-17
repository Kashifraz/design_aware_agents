from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from design_aware_agents.ollama import OllamaClient


@dataclass(frozen=True)
class GraphDeps:
    ollama: OllamaClient
    model: str
    prompts_dir: Path
    max_refactor_retries: int
    verbose: bool = False
