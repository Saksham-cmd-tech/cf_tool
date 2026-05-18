"""
cli.py — CLI entry point for the CF tool.

Commands:
    cf get <problem_id>           Fetch and display a problem
    cf run <file> [-p problem_id] Run solution against sample tests
    cf cache list                 Show cached problems
    cf cache clear [problem_id]   Clear cache (one or all)

Usage examples:
    cf get 1829A
    cf get 2227D --no-cache
    cf run solution.py -p 1829A
    cf run 1829A.cpp
    cf cache list
    cf cache clear 1829A
    cf cache clear
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import cache as cache_module
from .formatter import (
    console,
    print_cache_list,
    print_cached,
    print_error,
    print_info,
    print_problem,
    print_results,
)
from .parser import parse_problem
from .runner import run_tests
from .scraper import fetch_problem_page
from .utils import build_problem_url, parse_problem_id

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="cf",
    help="A developer Codeforces CLI tool.",
    add_completion=False,
    no_args_is_help=True,
)

cache_app = typer.Typer(help="Manage the local problem cache.")
app.add_typer(cache_app, name="cache")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


def _resolve_problem(
    problem_id: str,
    *,
    no_cache: bool = False,
) -> "Problem":  # type: ignore[name-defined]  # noqa: F821
    """
    Resolve a problem ID to a Problem object.

    Checks the local cache first (unless no_cache=True), then fetches
    and parses from Codeforces, saving the result to cache.

    Calls sys.exit(1) on any error, printing a clean message.
    """
    from .models import Problem  # local import to avoid circular

    try:
        contest_id, problem_letter = parse_problem_id(problem_id)
    except ValueError as exc:
        print_error(str(exc))
        raise typer.Exit(1)

    normalized = f"{contest_id}{problem_letter}"

    # ── Cache hit ────────────────────────────────────────────────────────────
    if not no_cache:
        cached = cache_module.load(normalized)
        if cached:
            print_cached(normalized)
            return cached

    # ── Fetch from Codeforces ────────────────────────────────────────────────
    url = build_problem_url(contest_id, problem_letter)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task(
            f"Fetching [bold cyan]{normalized}[/bold cyan] from Codeforces…",
            total=None,
        )
        try:
            html = fetch_problem_page(url)
        except (ConnectionError, ValueError) as exc:
            print_error(str(exc))
            raise typer.Exit(1)

    try:
        problem = parse_problem(html, normalized, url)
    except ValueError as exc:
        print_error(str(exc))
        raise typer.Exit(1)

    cache_module.save(problem)
    return problem


def _infer_problem_id_from_filename(file: Path) -> Optional[str]:
    """
    Try to infer a problem ID from a filename.

    e.g. "1829A.py" → "1829A", "sol_2227D.cpp" → "2227D"
    Returns None if no match is found.
    """
    stem = file.stem.upper()
    # Exact match: "1829A"
    if re.match(r"^\d+[A-Z]\d?$", stem):
        return stem
    # Embedded match: "sol_1829A", "cf_2227D_v2"
    match = re.search(r"\b(\d+[A-Z]\d?)\b", stem)
    return match.group(1) if match else None


# ---------------------------------------------------------------------------
# cf get
# ---------------------------------------------------------------------------


@app.command("get")
def get_problem(
    problem_id: str = typer.Argument(
        ...,
        help="Problem ID, e.g. [bold]1829A[/bold] or [bold]2227D[/bold].",
        metavar="PROBLEM_ID",
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", "-n",
        help="Bypass cache and re-fetch from Codeforces.",
    ),
) -> None:
    """
    Fetch and display a Codeforces problem.

    \b
    Examples:
        cf get 1829A
        cf get 2227D --no-cache
    """
    problem = _resolve_problem(problem_id, no_cache=no_cache)
    print_problem(problem)


# ---------------------------------------------------------------------------
# cf run
# ---------------------------------------------------------------------------


@app.command("run")
def run_solution(
    file: Path = typer.Argument(
        ...,
        help="Path to your solution file (e.g. [bold]solution.py[/bold], [bold]sol.cpp[/bold]).",
        metavar="FILE",
    ),
    problem_id: Optional[str] = typer.Option(
        None, "--problem", "-p",
        help="Problem ID (e.g. [bold]1829A[/bold]). Inferred from filename if omitted.",
        metavar="PROBLEM_ID",
    ),
    no_cache: bool = typer.Option(
        False, "--no-cache", "-n",
        help="Re-fetch the problem even if it's cached.",
    ),
    time_limit: int = typer.Option(
        5000, "--time-limit", "-t",
        help="Per-test time limit in milliseconds.",
        metavar="MS",
    ),
) -> None:
    """
    Run your solution against sample test cases.

    \b
    Examples:
        cf run solution.py -p 1829A
        cf run 1829A.cpp
        cf run sol.py -p 2227D --time-limit 2000
    """
    # ── Validate file ────────────────────────────────────────────────────────
    if not file.exists():
        print_error(f"File not found: [bold]{file}[/bold]")
        raise typer.Exit(1)

    # ── Resolve problem ID ───────────────────────────────────────────────────
    if not problem_id:
        problem_id = _infer_problem_id_from_filename(file)
        if not problem_id:
            print_error(
                "Could not infer problem ID from filename. "
                "Use [bold]--problem 1829A[/bold] to specify it."
            )
            raise typer.Exit(1)
        print_info(f"Inferred problem ID: {problem_id}")

    problem = _resolve_problem(problem_id, no_cache=no_cache)

    if not problem.sample_tests:
        print_error(f"No sample tests found for [bold]{problem.id}[/bold].")
        raise typer.Exit(1)

    n = len(problem.sample_tests)
    console.print(
        f"\n  Running [bold]{file.name}[/bold] "
        f"on [bold cyan]{problem.id}[/bold cyan] "
        f"([dim]{n} test{'s' if n != 1 else ''}[/dim])…\n"
    )

    # ── Run ──────────────────────────────────────────────────────────────────
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Running tests…", total=None)
        try:
            results = run_tests(file, problem.sample_tests, time_limit_ms=time_limit)
        except (FileNotFoundError, ValueError) as exc:
            print_error(str(exc))
            raise typer.Exit(1)

    print_results(results)

    # Non-zero exit code if any test failed (useful for CI / scripts)
    if not all(r.passed for r in results):
        raise typer.Exit(1)


# ---------------------------------------------------------------------------
# cf cache
# ---------------------------------------------------------------------------


@cache_app.command("list")
def cache_list() -> None:
    """List all locally cached problems."""
    ids = cache_module.list_cached()
    print_cache_list(ids)


@cache_app.command("clear")
def cache_clear(
    problem_id: Optional[str] = typer.Argument(
        None,
        help="Problem ID to clear. Omit to clear all cached problems.",
        metavar="PROBLEM_ID",
    ),
) -> None:
    """
    Remove cached problem(s).

    \b
    Examples:
        cf cache clear 1829A   # clear one problem
        cf cache clear         # clear everything
    """
    count = cache_module.clear(problem_id)
    if count:
        noun = "problem" if count == 1 else "problems"
        console.print(f"[green]Cleared {count} cached {noun}.[/green]")
    else:
        console.print("[dim]Nothing to clear.[/dim]")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Package entry point (registered in pyproject.toml)."""
    app()


if __name__ == "__main__":
    main()
