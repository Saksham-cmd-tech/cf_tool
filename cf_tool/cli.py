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
from rich.markup import escape
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import cache as cache_module
from .formatter import (
    console,
    print_cache_list,
    print_created,
    print_error,
    print_folder_created,
    print_info,
    print_lang_saved,
    print_problem,
    print_results,
)
from .parser import parse_problem
from .runner import run_tests
from .scraper import fetch_problem_page
from .templates import SUPPORTED_LANGS, get_extension, get_template, resolve_lang
from .utils import build_problem_url, parse_problem_id
from .question import CFContest
from .core import resolve_problem
from .doctor import run_doctor

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

app = typer.Typer(
    name="cf",
    help="A professional Codeforces CLI tool.",
    add_completion=False,
    no_args_is_help=True,
)

cache_app = typer.Typer(help="Manage the local problem cache.")
app.add_typer(cache_app, name="cache")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------


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
    problem_id: str = typer.Argument(..., metavar="PROBLEM_ID"),
    no_cache: bool = typer.Option(False, "--no-cache", "-n"),
) -> None:
    """
    Fetch and display a Codeforces problem.
    Pass a contest number to browse it interactively.

    \b
    Examples:
        cf get 1829A       # fetch directly
        cf get 2227        # browse contest 2227
    """
    if re.match(r'^\d+$', problem_id.strip()):
        CFContest(problem_id.strip()).run(no_cache=no_cache)
        return

    problem = resolve_problem(problem_id, no_cache=no_cache)
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
        print_error(f"File not found: [bold]{escape(str(file))}[/bold]")
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

    problem = resolve_problem(problem_id, no_cache=no_cache)

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
            results = run_tests(file, problem.sample_tests, time_limit_ms=time_limit, problem_id=problem.id)
        except (FileNotFoundError, ValueError) as exc:
            print_error(str(exc))
            raise typer.Exit(1)

    print_results(results)

    # Non-zero exit code if any test failed (useful for CI / scripts)
    if not all(r.passed for r in results):
        raise typer.Exit(1)


@app.command("create")
def create_solution(
    target: str = typer.Argument(
        ...,
        help=(
            "What to create:  "
            "[bold]2227[/bold] = folder only,  "
            "[bold]A[/bold] = file only (inside contest folder),  "
            "[bold]2227A[/bold] = folder + file"
        ),
        metavar="TARGET",
    ),
    lang: Optional[str] = typer.Argument(
        None,
        help="Language: py, cpp, c, java, js, ts, rb, go, rs. Saved as default after first use.",
        metavar="LANG",
    ),
    no_fetch: bool = typer.Option(
        False, "--no-fetch",
        help="Skip fetching the problem into cache.",
    ),
) -> None:
    """
    Create a contest folder, a solution file, or both.

    \b
    Examples:
        cf create 2227          # create contest2227/ folder only
        cf create A py          # inside contest2227/, create 2227A.py
        cf create 2227A py      # create folder + file in one shot
        cf create B             # reuse saved language preference
    """
    target_upper = target.strip().upper()

    # ── Determine mode from argument shape ────────────────────────────────────
    _full   = re.match(r'^(\d+)([A-Z]\d?)$', target_upper)  # "2227A"
    _num    = re.match(r'^\d+$',             target_upper)   # "2227"
    _letter = re.match(r'^([A-Z]\d?)$',      target_upper)   # "A" or "A1"

    if _full:
        mode, contest_id, problem_letter = "full",   _full.group(1),   _full.group(2)
    elif _num:
        mode, contest_id, problem_letter = "folder", target_upper,     None
    elif _letter:
        mode, contest_id, problem_letter = "file",   None,             _letter.group(1)
    else:
        print_error(
            f"Invalid argument [bold]{escape(target)}[/bold]. "
            "Use a contest number ([bold]2227[/bold]), "
            "a problem letter ([bold]A[/bold]), "
            "or a full ID ([bold]2227A[/bold])."
        )
        raise typer.Exit(1)

    # ══════════════════════════════════════════════════════════════════════════
    # FOLDER MODE — cf create 2227
    # ══════════════════════════════════════════════════════════════════════════
    if mode == "folder":
        folder = Path.cwd() / f"contest{contest_id}"
        already_existed = folder.exists()
        if not already_existed:
            folder.mkdir()
        print_folder_created(folder.name, already_existed=already_existed)
        return

    # ══════════════════════════════════════════════════════════════════════════
    # FILE MODE — cf create A [py]
    # Must be run from inside a contest<digits> folder.
    # ══════════════════════════════════════════════════════════════════════════
    if mode == "file":
        cwd_match = re.match(r'^contest(\d+)$', Path.cwd().name)
        if not cwd_match:
            print_error(
                "You're not inside a contest folder. "
                "Navigate into one first ([bold]cd contest2227[/bold]), "
                "or use a full ID: [bold]cf create 2227A[/bold]."
            )
            raise typer.Exit(1)
        contest_id = cwd_match.group(1)

    # ══════════════════════════════════════════════════════════════════════════
    # FILE CREATION — shared by "full" and "file" modes
    # ══════════════════════════════════════════════════════════════════════════
    normalized_id = f"{contest_id}{problem_letter}"

    # ── Resolve language ──────────────────────────────────────────────────────
    lang_is_new = False
    if lang:
        resolved_lang = resolve_lang(lang)
        if resolved_lang is None:
            print_error(
                f"Unrecognized language '[bold]{escape(lang)}[/bold]'. "
                f"Supported: {', '.join(SUPPORTED_LANGS)}"
            )
            raise typer.Exit(1)
        lang_is_new = True
    else:
        resolved_lang = cache_module.get_config("preferred_lang")
        if resolved_lang is None:
            print_error(
                "No language specified and no default saved yet. "
                "Add one: [bold]cf create A py[/bold]."
            )
            raise typer.Exit(1)

    # ── Determine target directory ────────────────────────────────────────────
    cwd = Path.cwd()
    contest_folder = f"contest{contest_id}"
    already_inside = cwd.name == contest_folder

    if already_inside:
        target_dir = cwd
        folder_created = False
    else:
        target_dir = cwd / contest_folder
        folder_created = not target_dir.exists()
        target_dir.mkdir(exist_ok=True)

    # ── Create the file ───────────────────────────────────────────────────────
    ext = get_extension(resolved_lang)
    filepath = target_dir / f"{normalized_id}{ext}"

    if filepath.exists():
        print_error(f"[bold]{escape(str(filepath))}[/bold] already exists.")
        raise typer.Exit(1)

    filepath.write_text(
        get_template(resolved_lang, problem_id=normalized_id),
        encoding="utf-8",
    )

    # ── Save language preference ──────────────────────────────────────────────
    if lang_is_new:
        old = cache_module.get_config("preferred_lang", base_dir=target_dir)
        cache_module.set_config("preferred_lang", resolved_lang, base_dir=target_dir)
        if old != resolved_lang:
            print_lang_saved(resolved_lang)

    # ── Display result ────────────────────────────────────────────────────────
    try:
        display_path = filepath.relative_to(cwd)
    except ValueError:
        display_path = filepath

    print_created(
        problem_id=normalized_id,
        filepath=display_path,
        lang=resolved_lang,
        folder_created=folder_created,
        already_inside=already_inside,
    )

    # ── Warm the cache ────────────────────────────────────────────────────────
    if not no_fetch:
        url = build_problem_url(str(contest_id), str(problem_letter))
        if not cache_module.load(normalized_id, base_dir=target_dir):
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
                transient=True,
            ) as progress:
                progress.add_task(
                    f"Fetching [bold cyan]{normalized_id}[/bold cyan] into cache…",
                    total=None,
                )
                try:
                    html = fetch_problem_page(url)
                    problem = parse_problem(html, normalized_id, url)
        
                    # 🔥 THIS LINE IS CRITICAL
                    cache_module.save(problem, base_dir=target_dir)
        
                    print_info(
                        f"  ↳ Problem cached — run "
                        f"[bold]cf run {escape(str(display_path))}[/bold] when ready"
                    )
                except Exception as e:
                    print_info(
                        f"  ↳ Failed to fetch problem: [dim]{str(e)}[/dim]\n"
                        f"     File created anyway."
                    )
        else:
            print_info(
                f"  ↳ Problem already cached — run "
                f"[bold]cf run {escape(str(display_path))}[/bold] when ready"
            )


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

@app.command("explore")
def explore(
    query: Optional[str] = typer.Option(
        None, "-e", "--filter",
        help="Pre-filter problems by tag or name (e.g. dp, greedy, graphs).",
        metavar="QUERY",
    ),
) -> None:
    """
    Interactively explore Codeforces problems.

    \b
    Examples:
        cf explore             # open with no filter
        cf explore -e dp       # open pre-filtered to 'dp'
        cf explore -e greedy
    """
    from cf_tool.explore import CFExplore
    CFExplore().run(initial_query=query)

@app.command("update")
def update(
    problems: bool = typer.Option(
        False, "-p", "--problems",
        help="Re-fetch the full problem list from Codeforces API.",
    ),
) -> None:
    """
    Update cached data.

    \b
    Examples:
        cf update -p       # refresh global problem list
    """
    if not problems:
        console.print("[dim]Nothing to update. Use [bold]cf update -p[/bold] to refresh the problem list.[/dim]")
        return

    from .cache_problems import fetch_and_cache_problems

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("Fetching problem list from Codeforces…", total=None)
        try:
            problems_list = fetch_and_cache_problems()
        except (ConnectionError, ValueError) as exc:
            print_error(str(exc))
            raise typer.Exit(1)

    console.print(f"[green]✓[/green]  Updated — [cyan]{len(problems_list)}[/cyan] problems cached.")

@app.command("doctor")
def doctor(
    fix: bool = typer.Option(False, "--fix", help="Automatically fix issues")
):
    """
    Diagnose cfmate environment.
    """
    run_doctor(fix=fix)
    
# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Package entry point (registered in pyproject.toml)."""
    app()


if __name__ == "__main__":
    main()