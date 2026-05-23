"""
cache_problems.py — Global cache for Codeforces problem metadata
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import List, Dict

import requests

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

CACHE_DIR = Path.home() / ".cfmate"
CACHE_FILE = CACHE_DIR / "problems_cache.json"

API_URL = "https://codeforces.com/api/problemset.problems"

# Cache expiry (24 hours)
CACHE_TTL = 60 * 60 * 24


# ---------------------------------------------------------------------------
# Fetch + Save
# ---------------------------------------------------------------------------

def fetch_and_cache_problems() -> List[Dict]:
    """Fetch problems from API and store locally."""
    res = requests.get(API_URL).json()

    problems = res["result"]["problems"]

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    with open(CACHE_FILE, "w") as f:
        json.dump(problems, f)

    return problems


# ---------------------------------------------------------------------------
# Load cache
# ---------------------------------------------------------------------------

def load_cached_problems() -> List[Dict] | None:
    """Load cached problems if available."""
    if not CACHE_FILE.exists():
        return None

    try:
        with open(CACHE_FILE) as f:
            return json.load(f)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Smart loader (main function)
# ---------------------------------------------------------------------------

def get_problems() -> List[Dict]:
    """
    Get problems with smart caching:
    - use cache if fresh
    - refresh if expired
    """

    if CACHE_FILE.exists():
        age = time.time() - CACHE_FILE.stat().st_mtime

        if age < CACHE_TTL:
            cached = load_cached_problems()
            if cached:
                return cached

    # fallback → fetch new
    return fetch_and_cache_problems()