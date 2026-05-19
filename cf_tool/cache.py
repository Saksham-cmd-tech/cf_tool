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


def _get_cache_dir(base_dir: Path | None = None) -> Path:
    """Resolve the cache directory."""
    if base_dir is None:
        base_dir = Path.cwd()
    return base_dir / ".cf_cache"


def _cache_file(problem_id: str, base_dir: Path | None = None) -> Path:
    """Return the Path for a problem's cache file."""
    cache_dir = _get_cache_dir(base_dir)
    return cache_dir / f"{problem_id.upper()}.json"


def load(problem_id: str, base_dir: Path | None = None) -> Optional[Problem]:
    """
    Load a Problem from the local cache.

    Args:
        problem_id: The problem ID (e.g. "1829A").

    Returns:
        The cached Problem, or None if no valid cache entry exists.
    """
    path = _cache_file(problem_id, base_dir)
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return Problem.from_dict(data)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def save(problem: Problem, base_dir: Path | None = None) -> None:
    """
    Persist a Problem to the local cache as JSON.

    Creates .cf_cache/ if it doesn't already exist.

    Args:
        problem: The Problem to cache.
    """
    cache_dir = _get_cache_dir(base_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    path = _cache_file(problem.id, base_dir)
    path.write_text(
        json.dumps(problem.to_dict(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def clear(problem_id: Optional[str] = None, base_dir: Path | None = None) -> int:
    """
    Remove cached problem(s).

    Args:
        problem_id: If provided, delete only that problem's cache file.
                    If None, delete all .json files in the cache directory.

    Returns:
        The number of files deleted.
    """
    cache_dir = _get_cache_dir(base_dir)

    if not cache_dir.exists():
        return 0

    if problem_id is not None:
        path = _cache_file(problem_id, base_dir)
        if path.exists():
            path.unlink()
            return 1
        return 0

    deleted = 0
    for entry in cache_dir.glob("*.json"):
        entry.unlink()
        deleted += 1

    return deleted


def list_cached(base_dir: Path | None = None) -> list[str]:
    """
    Return a sorted list of all cached problem IDs.

    Returns:
        e.g. ["1829A", "2227D"]
    """
    cache_dir = _get_cache_dir(base_dir)

    if not cache_dir.exists():
        return []

    return sorted(
        p.stem for p in cache_dir.glob("*.json") if p.stem != "config"
    )


# ---------------------------------------------------------------------------
# Config storage — persists user preferences (e.g. preferred language)
# ---------------------------------------------------------------------------


def _config_path(base_dir: Path | None = None) -> Path:
    return _get_cache_dir(base_dir) / "config.json"


def _load_config_raw(base_dir: Path | None = None) -> dict:
    """Load the raw config dict from disk, or return empty dict."""
    path = _config_path(base_dir)
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_config_raw(data: dict, base_dir: Path | None = None) -> None:
    """Write a raw config dict to disk."""
    path = _config_path(base_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def get_config(key: str, base_dir: Path | None = None) -> str | None:
    """
    Read a single config value by key.

    Returns:
        The stored string value, or None if the key doesn't exist.
    """
    return _load_config_raw(base_dir).get(key)


def set_config(key: str, value: str, base_dir: Path | None = None) -> None:
    """
    Write a single config value, merging with existing config.

    Args:
        key:   Config key, e.g. "preferred_lang".
        value: Value to store, e.g. "py".
    """
    data = _load_config_raw(base_dir)
    data[key] = value
    _save_config_raw(data, base_dir)