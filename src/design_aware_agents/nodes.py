from __future__ import annotations

import json
import re
from typing import Any, Literal

import json_repair
from langgraph.types import RunnableConfig
from pydantic import BaseModel, Field

from design_aware_agents.deps import GraphDeps
from design_aware_agents.state import AgentState


def _preview(text: str, *, max_chars: int = 1200) -> str:
    t = text.replace("\r\n", "\n").replace("\r", "\n")
    if len(t) <= max_chars:
        return t
    return t[:max_chars] + f"\n... ({len(t) - max_chars} more chars truncated)"


def _log_agent(deps: GraphDeps, agent: str, *, raw: str | None = None, parsed: dict[str, Any] | None = None) -> None:
    if not deps.verbose:
        return

    print(f"\n----- {agent} -----", flush=True)
    if raw is not None:
        print("[raw]", flush=True)
        print(_preview(raw), flush=True)
    if parsed is not None:
        print("[parsed JSON]", flush=True)
        print(json.dumps(parsed, ensure_ascii=False, indent=2), flush=True)


class AnalyzerOutput(BaseModel):
    root_cause: str
    violated_principle: list[str] = Field(default_factory=list)
    explanation: str


class RefactorOutput(BaseModel):
    refactoring_technique: str
    refactored_code: str
    reasoning: str = ""


class ValidationOutput(BaseModel):
    issue_resolved: bool
    improvement_score: int = Field(ge=0, le=100)
    preserves_behavior: Literal["yes", "no", "uncertain"]
    new_risks: list[str] = Field(default_factory=list)
    comments: str


_FENCE_RE = re.compile(r"```(?:json)?\s*([\s\S]*?)\s*```", re.IGNORECASE)

# Refactor agent: one metadata JSON object, delimiter, then plain code (see refactoring_agent_prompt.md).
REFACTOR_CODE_DELIMITER = "---REFACTORED_CODE---"

# Validation routing: retry refactor until strict success or max_refactor_retries.
IMPROVEMENT_SCORE_SUCCESS_MIN = 95


def _retry_feedback_for_refactor(
    validation: dict[str, Any] | None,
    prev_refactor: dict[str, Any] | None,
) -> str:
    """Block for the refactor prompt when retrying after validation (same graph run)."""
    if not validation:
        return ""
    prev_code = ""
    if isinstance(prev_refactor, dict):
        prev_code = str(prev_refactor.get("refactored_code", "") or "").strip()
    summary = {
        "issue_resolved": validation.get("issue_resolved"),
        "improvement_score": validation.get("improvement_score"),
        "preserves_behavior": validation.get("preserves_behavior"),
        "new_risks": validation.get("new_risks"),
        "comments": validation.get("comments"),
    }
    lines = [
        "--- Prior attempt (validator review) ---",
        "The last refactor did not yet meet the pipeline bar: behavior preservation should be "
        f"\"yes\" (not \"uncertain\"), and improvement_score should be >= {IMPROVEMENT_SCORE_SUCCESS_MIN}.",
        "Use the feedback below to revise your approach; address risks and uncertainty.",
        "",
        "Validation summary:",
        json.dumps(summary, ensure_ascii=False, indent=2),
    ]
    if prev_code:
        lines.extend(["", "Your previous refactored code (fix or replace):", prev_code, ""])
    lines.append("--- End prior attempt ---")
    return "\n".join(lines)


def _maybe_strip_outer_fence(code: str) -> str:
    c = code.strip()
    if not c.startswith("```"):
        return code
    first_nl = c.find("\n")
    if first_nl == -1:
        return code
    end_fence = c.rfind("\n```")
    if end_fence <= first_nl:
        return code
    return c[first_nl + 1 : end_fence]


def _try_load_json_object(s: str) -> dict[str, Any]:
    try:
        obj = json.loads(s)
    except json.JSONDecodeError:
        try:
            obj = json_repair.loads(s)
        except Exception as e:
            raise ValueError(f"json_repair.loads failed: {e}") from e
    if not isinstance(obj, dict):
        raise ValueError("Model output was not a JSON object")
    return obj


def _parse_json_object(text: str) -> dict[str, Any]:
    s = text.strip()
    m = _FENCE_RE.search(s)
    if m:
        s = m.group(1).strip()
    try:
        return _try_load_json_object(s)
    except (json.JSONDecodeError, ValueError, TypeError):
        start = s.find("{")
        end = s.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        return _try_load_json_object(s[start : end + 1])


def _parse_refactor_block(text: str) -> dict[str, Any]:
    head, _, body = text.partition(REFACTOR_CODE_DELIMITER)
    head = head.strip()
    if not head:
        raise ValueError("Missing metadata JSON before refactor delimiter")
    meta = _parse_json_object(head)
    code = _maybe_strip_outer_fence(body.lstrip("\n\r"))
    return {
        "refactoring_technique": str(meta.get("refactoring_technique", "")),
        "reasoning": str(meta.get("reasoning", "")),
        "refactored_code": code,
    }


def _parse_refactor_output(raw: str) -> dict[str, Any]:
    """Single metadata JSON object, delimiter, then plain code (see refactoring_agent_prompt.md)."""
    text = raw.replace("\r\n", "\n").replace("\r", "\n").strip()
    if REFACTOR_CODE_DELIMITER not in text:
        raise ValueError(
            f"Refactor output must contain the line {REFACTOR_CODE_DELIMITER!r} followed by code."
        )
    return _parse_refactor_block(text)


def _coerce_validation_dict(obj: dict[str, Any]) -> dict[str, Any]:
    """Normalize improvement_score and preserves_behavior for schema validation."""
    out = dict(obj)
    pb = out.get("preserves_behavior")
    if isinstance(pb, bool):
        out["preserves_behavior"] = "yes" if pb else "no"
    elif isinstance(pb, str):
        s = pb.strip().lower()
        if s in ("yes", "no", "uncertain"):
            out["preserves_behavior"] = s
        else:
            out["preserves_behavior"] = "uncertain"
    else:
        out["preserves_behavior"] = "uncertain"

    raw = out.get("improvement_score", 0)
    try:
        if isinstance(raw, bool):
            score = int(raw)
        elif isinstance(raw, (int, float)):
            score = int(round(float(raw)))
        elif isinstance(raw, str) and raw.strip():
            score = int(round(float(raw.strip())))
        else:
            score = 0
    except (ValueError, TypeError, OverflowError):
        score = 0
    out["improvement_score"] = max(0, min(100, score))
    return out


def _validation_improvement_score(validation: dict[str, Any]) -> int:
    raw = validation.get("improvement_score", 0)
    try:
        score = int(round(float(raw)))
    except (TypeError, ValueError):
        score = 0
    return max(0, min(100, score))


def _pipeline_success(validation: dict[str, Any]) -> bool:
    """Strict finish: issue resolved, behavior preserved with confidence, score at/above threshold."""
    if not bool(validation.get("issue_resolved")):
        return False
    pb = str(validation.get("preserves_behavior") or "").strip().lower()
    if pb != "yes":
        return False
    return _validation_improvement_score(validation) >= IMPROVEMENT_SCORE_SUCCESS_MIN


def _validation_scores_retry(validation: dict[str, Any]) -> bool:
    """True unless strict success is met (retry on uncertain / not yes / low score / issue open)."""
    return not _pipeline_success(validation)


def _render(template: str, variables: dict[str, str]) -> str:
    out = template
    for k, v in variables.items():
        out = out.replace("{" + k + "}", v)
    return out


def _read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def _hotspot_json(item: dict[str, Any]) -> str:
    payload = {
        "id": item.get("id"),
        "snippet_index": item.get("snippet_index"),
        "file_name": item.get("file_name"),
        "language": item.get("language"),
        "extension": item.get("extension"),
        "design_issues": item.get("design_issues"),
        "code_snippet": item.get("code_snippet"),
    }
    return json.dumps(payload, ensure_ascii=False)


def _design_issues(item: dict[str, Any]) -> str:
    prompt = item.get("design_issues")
    if isinstance(prompt, str) and prompt.strip():
        return prompt.strip()
    return ""


def analyze_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    deps: GraphDeps = config["configurable"]["deps"]
    item = state["hotspot"]

    design_issues = state.get("design_issues") or _design_issues(item)
    code_snippet = str(item.get("code_snippet", ""))

    template = _read_text(str(deps.prompts_dir / "analyzer_agent_prompt.md"))
    prompt = _render(
        template,
        {
            "hotspot_json": _hotspot_json(item),
            "design_issues": design_issues,
        },
    )

    raw = deps.llm.complete_json(deps.model_analyze, prompt)
    analysis = AnalyzerOutput.model_validate(_parse_json_object(raw)).model_dump()
    _log_agent(deps, "analyze", raw=raw, parsed=analysis)

    return {
        "design_issues": design_issues,
        "code_snippet": code_snippet,
        "analysis": analysis,
    }


def refactor_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    deps: GraphDeps = config["configurable"]["deps"]
    item = state["hotspot"]
    analysis = state.get("analysis") or {}

    design_issues = state.get("design_issues") or _design_issues(item)
    code_snippet = str(state.get("code_snippet") or item.get("code_snippet") or "")

    violated = analysis.get("violated_principle", [])
    if isinstance(violated, list):
        violated_principles = ", ".join(str(x) for x in violated)
    else:
        violated_principles = str(violated)

    template = _read_text(str(deps.prompts_dir / "refactoring_agent_prompt.md"))
    retry_feedback = _retry_feedback_for_refactor(
        state.get("validation"),
        state.get("refactor"),
    )
    prompt = _render(
        template,
        {
            "retry_feedback": retry_feedback,
            "code_snippet": code_snippet,
            "root_cause": str(analysis.get("root_cause", "")),
            "violated_principles": violated_principles,
            "explanation": str(analysis.get("explanation", "")),
            "design_issues": design_issues,
        },
    )

    raw = deps.llm.complete_text(deps.model_refactor, prompt)
    refactor = RefactorOutput.model_validate(_parse_refactor_output(raw)).model_dump()
    attempt = int(state.get("attempt", 0)) + 1
    _log_agent(deps, f"refactor (attempt {attempt})", raw=raw, parsed=refactor)

    return {"refactor": refactor, "attempt": attempt}


def validate_node(state: AgentState, config: RunnableConfig) -> dict[str, Any]:
    deps: GraphDeps = config["configurable"]["deps"]
    item = state["hotspot"]
    refactor = state.get("refactor") or {}

    design_issues = state.get("design_issues") or _design_issues(item)
    code_snippet = str(state.get("code_snippet") or item.get("code_snippet") or "")

    prev = str(state.get("prior_refactored_code") or "").strip()
    previous_block = (
        prev
        if prev
        else "(none — this is the first refactor candidate for this run.)"
    )

    template = _read_text(str(deps.prompts_dir / "validation_agent_prompt.md"))
    prompt = _render(
        template,
        {
            "design_issues": design_issues,
            "code_snippet": code_snippet,
            "previous_refactored_code": previous_block,
            "refactored_code": str(refactor.get("refactored_code", "")),
            "refactoring_technique": str(refactor.get("refactoring_technique", "")),
        },
    )

    raw = deps.llm.complete_json(deps.model_validate, prompt)
    validation = ValidationOutput.model_validate(_coerce_validation_dict(_parse_json_object(raw))).model_dump()
    _log_agent(deps, "validate", raw=raw, parsed=validation)

    attempt = int(state.get("attempt", 0))
    max_r = int(deps.max_refactor_retries)

    iteration_log: list[dict[str, Any]] = list(state.get("iteration_log") or [])
    iteration_log.append(
        {
            "attempt": attempt,
            "refactor": {
                "refactoring_technique": str(refactor.get("refactoring_technique", "")),
                "reasoning": str(refactor.get("reasoning", "")),
                "refactored_code": str(refactor.get("refactored_code", "")),
            },
            "validation": dict(validation),
        }
    )
    prior_refactored_code = str(refactor.get("refactored_code") or "")

    base: dict[str, Any] = {
        "validation": validation,
        "iteration_log": iteration_log,
        "prior_refactored_code": prior_refactored_code,
    }

    if _pipeline_success(validation):
        return {**base, "stop_reason": "success"}
    if attempt < max_r and _validation_scores_retry(validation):
        return base
    return {**base, "stop_reason": "max_retries"}


def route_after_validate(state: AgentState, config: RunnableConfig) -> str:
    deps: GraphDeps = config["configurable"]["deps"]
    validation = state.get("validation") or {}
    attempt = int(state.get("attempt", 0))
    max_r = int(deps.max_refactor_retries)

    if attempt < max_r and _validation_scores_retry(validation):
        if deps.verbose:
            print(
                f"\n[route] retry refactor (attempt={attempt}/{max_r}): "
                f"need stricter success (issue_resolved / not uncertain / "
                f"score>={IMPROVEMENT_SCORE_SUCCESS_MIN})\n",
                flush=True,
            )
        return "refactor"
    if deps.verbose:
        if _pipeline_success(validation):
            print("\n[route] strict success -> end\n", flush=True)
        else:
            print(f"\n[route] stop (attempt={attempt}, max={max_r}) -> end\n", flush=True)
    return "end"
