"""Load `.env` into the process environment (optional `python-dotenv`)."""

from __future__ import annotations

from pathlib import Path

_LOADED = False


def load_dotenv_if_present() -> None:
    """Idempotent: load the first existing `.env` from repo root (editable install) or cwd."""
    global _LOADED
    if _LOADED:
        return
    _LOADED = True
    try:
        from dotenv import load_dotenv
    except ImportError:
        return

    here = Path(__file__).resolve()
    # Package at src/design_aware_agents/ -> repo root is parents[2]
    repo_root = here.parents[2]
    seen: set[Path] = set()
    for path in (repo_root / ".env", Path.cwd() / ".env"):
        resolved = path.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        if resolved.is_file():
            load_dotenv(resolved, override=True)
