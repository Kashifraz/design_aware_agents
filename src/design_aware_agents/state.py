from __future__ import annotations

from typing import Any, Literal, TypedDict


class AgentState(TypedDict, total=False):
    snippet_id: str
    hotspot: dict[str, Any]

    design_issues: str
    code_snippet: str

    analysis: dict[str, Any]
    refactor: dict[str, Any]
    validation: dict[str, Any]

    attempt: int
    stop_reason: Literal["success", "max_retries"]

    # After each validate: log of {attempt, refactor, validation}; prior refactored code for next validate prompt
    iteration_log: list[dict[str, Any]]
    prior_refactored_code: str
