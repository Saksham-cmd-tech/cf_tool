"""
progress.py — Track which problems have been solved locally.
Stores a simple JSON set at ~/.cfmate/solved.json
"""
from __future__ import annotations
import json
from pathlib import Path

_SOLVED_FILE = Path.home() / ".cfmate" / "solved.json"


def _load() -> set[str]:
    if not _SOLVED_FILE.exists():
        return set()
    try:
        return {s.strip().upper() for s in json.loads(_SOLVED_FILE.read_text())}
    except Exception:
        return set()


def _save(solved: set[str]) -> None:
    _SOLVED_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SOLVED_FILE.write_text(json.dumps(sorted(solved), indent=2))


def mark_solved(problem_id: str) -> None:
    solved = _load()
    solved.add(problem_id.strip().upper())
    _save(solved)


def is_solved(problem_id: str) -> bool:
    return problem_id.strip().upper() in _load()


def all_solved() -> set[str]:
    return _load()