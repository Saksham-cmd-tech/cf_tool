"""
core.py — Shared core logic for fetching and resolving problems
"""

from __future__ import annotations

from . import cache as cache_module
from .parser import parse_problem
from .scraper import fetch_problem_page
from .utils import build_problem_url, parse_problem_id


# ---------------------------------------------------------------------------
# Core resolver
# ---------------------------------------------------------------------------

def resolve_problem(problem_id: str, *, no_cache: bool = False):
    contest_id, problem_letter = parse_problem_id(problem_id)
    normalized = f"{contest_id}{problem_letter}"

    if not no_cache:
        cached = cache_module.load(normalized)
        if cached:
            return cached

    url = build_problem_url(contest_id, problem_letter)

    html = fetch_problem_page(url)
    problem = parse_problem(html, normalized, url)

    cache_module.save(problem)
    return problem