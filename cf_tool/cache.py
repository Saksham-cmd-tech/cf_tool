"""
cache.py — Local JSON caching for fetched problems.

Problems are stored in .cf_cache/<PROBLEM_ID>.json relative to the
working directory. This keeps the cache close to where the tool is run,
similar to how git stores .git/ in the project root.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

from .models import Problem

CACHE_DIR = Path(".cf_cache")


def _cache_file(problem_id: str) -> Path:
    """Return the Path for a problem's cache file."""
    return CACHE_DIR / f"{problem_id.upper()}.json"


def load(problem_id: str) -> Optional[Problem]:
    """
    Load a Problem from the local cache.

    Args:
        problem_id: The problem ID (e.g. "1829A").

    Returns:
        The cached Problem, or None if no valid cache entry exists.
    """
    path = _cache_file(problem_id)
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Problem.from_dict(data)
    except (json.JSONDecodeError, KeyError, TypeError):
        # Cache entry is corrupt — treat as a cache miss, don't crash.
        return None


def save(problem: Problem) -> None:
    """
    Persist a Problem to the local cache as JSON.

    Creates .cf_cache/ if it doesn't already exist.

    Args:
        problem: The Problem to cache.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_file(problem.id)
    path.write_text(
        json.dumps(problem.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def clear(problem_id: Optional[str] = None) -> int:
    """
    Remove cached problem(s).

    Args:
        problem_id: If provided, delete only that problem's cache file.
                    If None, delete all .json files in the cache directory.

    Returns:
        The number of files deleted.
    """
    if not CACHE_DIR.exists():
        return 0

    if problem_id is not None:
        path = _cache_file(problem_id)
        if path.exists():
            path.unlink()
            return 1
        return 0

    deleted = 0
    for entry in CACHE_DIR.glob("*.json"):
        entry.unlink()
        deleted += 1
    return deleted


def list_cached() -> list[str]:
    """
    Return a sorted list of all cached problem IDs.

    Returns:
        e.g. ["1829A", "2227D"]
    """
    if not CACHE_DIR.exists():
        return []
    return sorted(p.stem for p in CACHE_DIR.glob("*.json"))
