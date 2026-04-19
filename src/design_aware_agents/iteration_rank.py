"""Pick the best refactor/validation attempt from a run (for persisted output)."""

from __future__ import annotations

from typing import Any


def improvement_score_value(validation: dict[str, Any]) -> int:
    raw = validation.get("improvement_score", 0)
    try:
        return max(0, min(100, int(round(float(raw)))))
    except (TypeError, ValueError):
        return 0


def preserves_behavior_rank(validation: dict[str, Any]) -> int:
    """Lower is better: yes=0, uncertain=1, no=2, unknown=3."""
    pb = str(validation.get("preserves_behavior") or "").strip().lower()
    return {"yes": 0, "uncertain": 1, "no": 2}.get(pb, 3)


def pick_best_iteration(iteration_log: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    Rank attempts by:
      1) preserves_behavior (yes best, then uncertain, then no)
      2) higher improvement_score
      3) lower attempt number (earlier pass wins ties)
    """
    if not iteration_log:
        return None

    def sort_key(entry: dict[str, Any]) -> tuple[int, float, int]:
        v = entry.get("validation") or {}
        return (
            preserves_behavior_rank(v),
            -float(improvement_score_value(v)),
            int(entry.get("attempt", 0)),
        )

    return min(iteration_log, key=sort_key)
