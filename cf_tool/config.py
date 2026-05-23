"""
config.py — Global configuration management for cfmate.

Stores user preferences and session data in:
~/.cfmate/

This ensures:
- persistent login
- saved preferences (language, handle)
- cross-project usage
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Global config directory (~/.cfmate)
# ---------------------------------------------------------------------------

CONFIG_DIR = Path.home() / ".cfmate"
CONFIG_FILE = CONFIG_DIR / "config.json"
SESSION_FILE = CONFIG_DIR / "session.json"


def _ensure_config_dir() -> None:
    """Ensure the global config directory exists."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Config (key-value storage)
# ---------------------------------------------------------------------------

def _load_config_raw() -> dict:
    """Load config JSON or return empty dict."""
    if not CONFIG_FILE.exists():
        return {}

    try:
        return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def _save_config_raw(data: dict) -> None:
    """Write config JSON to disk."""
    _ensure_config_dir()
    CONFIG_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def get_config(key: str) -> Optional[Any]:
    """
    Get a config value.

    Example:
        get_config("handle")
    """
    return _load_config_raw().get(key)


def set_config(key: str, value: Any) -> None:
    """
    Set a config value.

    Example:
        set_config("handle", "tourist")
    """
    data = _load_config_raw()
    data[key] = value
    _save_config_raw(data)


def delete_config(key: str) -> None:
    """Remove a key from config."""
    data = _load_config_raw()
    if key in data:
        del data[key]
        _save_config_raw(data)


# ---------------------------------------------------------------------------
# Session handling (Playwright)
# ---------------------------------------------------------------------------

def get_session_path() -> Path:
    """
    Return path to session file.

    Used by Playwright:
        browser.new_context(storage_state=path)
    """
    _ensure_config_dir()
    return SESSION_FILE


def has_session() -> bool:
    """Check if user is logged in (session exists)."""
    return SESSION_FILE.exists()


def clear_session() -> None:
    """Delete stored session (logout)."""
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()