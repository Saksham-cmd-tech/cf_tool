"""
formatter.py — Terminal UI using Rich.

All output goes through this module. Nothing else should print directly.

Public API:
    console          — shared Rich Console (import it to show spinners etc.)
    print_problem()  — render a Problem in full
    print_results()  — render test run results with pass/fail
    print_error()    — clean one-line error
    print_info()     — dim informational line
    print_cached()   — "loaded from cache" notice
    print_cache_list() — list cached problem IDs
"""

from __future__ import annotations

from rich import box
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import Problem, TestCase

# Shared console — import this in other modules to show spinners inline.
console = Console(highlight=False)


# ---------------------------------------------------------------------------
# Problem display
# ---------------------------------------------------------------------------


def print_problem(problem: Problem) -> None:
    """Render the full problem statement, formatted with Rich panels."""
    console.print()

    # ── Title / meta panel ──────────────────────────────────────────────────
    # Escape all external strings before interpolating into Rich markup.
    safe_title    = escape(problem.title)
    safe_limits   = escape(f"⏱  {problem.time_limit}    💾  {problem.memory_limit}")
    safe_url      = escape(problem.url)
    safe_id       = escape(problem.id)

    console.print(Panel(
        f"[bold white]{safe_title}[/bold white]\n"
        f"[dim]{safe_limits}[/dim]\n"
        f"[dim link={safe_url}]{safe_url}[/dim link={safe_url}]",
        title=f"[bold cyan]{safe_id}[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))

    # ── Statement ────────────────────────────────────────────────────────────
    # Use Text() so Rich never interprets the problem content as markup tags.
    if problem.statement:
        console.print(Panel(
            Text(problem.statement),
            title="[bold yellow]Problem Statement[/bold yellow]",
            border_style="yellow",
            padding=(1, 2),
        ))

    # ── Input / Output side-by-side ──────────────────────────────────────────
    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)
    grid.add_row(
        Panel(
            Text(problem.input_format) if problem.input_format else "[dim]N/A[/dim]",
            title="[bold green]Input Format[/bold green]",
            border_style="green",
            padding=(1, 2),
        ),
        Panel(
            Text(problem.output_format) if problem.output_format else "[dim]N/A[/dim]",
            title="[bold green]Output Format[/bold green]",
            border_style="green",
            padding=(1, 2),
        ),
    )
    console.print(grid)

    # ── Sample tests ─────────────────────────────────────────────────────────
    if problem.sample_tests:
        console.print()
        console.rule("[bold magenta]Sample Tests[/bold magenta]", style="magenta")
        for i, tc in enumerate(problem.sample_tests, 1):
            _print_sample(i, tc)

    console.print()


def _print_sample(index: int, tc: TestCase) -> None:
    """Render one sample test as a two-column Input / Expected Output panel."""
    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)
    grid.add_row(
        Panel(
            Text(tc.input) if tc.input else "[dim](empty)[/dim]",
            title="[bold]Input[/bold]",
            border_style="dim",
            padding=(0, 1),
        ),
        Panel(
            Text(tc.expected_output) if tc.expected_output else "[dim](empty)[/dim]",
            title="[bold]Expected Output[/bold]",
            border_style="dim",
            padding=(0, 1),
        ),
    )
    console.print(Panel(
        grid,
        title=f"[dim]Sample {index}[/dim]",
        border_style="dim",
        padding=(0, 0),
    ))


# ---------------------------------------------------------------------------
# Test results
# ---------------------------------------------------------------------------


def print_results(results: list) -> None:  # results: list[TestResult]
    """
    Render test-runner results.

    Shows a per-test pass/fail line, expands failures with an
    expected-vs-actual diff, then prints a summary banner.
    """
    console.print()

    passed = sum(1 for r in results if r.passed)
    total = len(results)

    for i, result in enumerate(results, 1):
        elapsed = f"[dim]{result.elapsed_ms:.0f} ms[/dim]"

        if result.passed:
            console.print(f"  [bold green]✓[/bold green]  Test {i}  {elapsed}")
        else:
            console.print(f"  [bold red]✗[/bold red]  Test {i}  {elapsed}")
            _print_failure(result)

    console.print()

    # ── Summary banner ────────────────────────────────────────────────────────
    if passed == total:
        style, icon, label = "green", "✓", f"All {total} tests passed"
    elif passed == 0:
        style, icon, label = "red", "✗", f"0 / {total} tests passed"
    else:
        style, icon, label = "yellow", "~", f"{passed} / {total} tests passed"

    console.print(Panel(
        f"[bold {style}]{icon}  {label}[/bold {style}]",
        border_style=style,
        padding=(0, 2),
    ))
    console.print()


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[bold green]✔ {message}[/bold green]")

def _print_failure(result) -> None:
    """Render expected vs. actual output (or a runtime error) for a failed test."""
    if result.error:
        console.print(Panel(
            escape(result.error),
            title="[bold red]Error[/bold red]",
            border_style="red",
            padding=(0, 1),
        ))
        return

    expected_text = Text(result.expected or "")
    actual_text = _build_diff_text(result.expected or "", result.actual or "")

    grid = Table.grid(expand=True, padding=(0, 1))
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)
    grid.add_row(
        Panel(expected_text,
              title="[yellow]Expected[/yellow]",
              border_style="yellow",
              padding=(0, 1)),
        Panel(actual_text,
              title="[red]Got[/red]",
              border_style="red",
              padding=(0, 1)),
    )
    console.print(grid)


def _build_diff_text(expected: str, actual: str) -> Text:
    """
    Line-by-line diff of actual vs expected.

    Matching lines are green; differing or extra lines are bold red.
    Truncated lines are shown in dim red.
    """
    exp_lines = expected.splitlines()
    act_lines = actual.splitlines()
    out = Text()

    for i, line in enumerate(act_lines):
        if i < len(exp_lines) and line == exp_lines[i]:
            out.append(line + "\n", style="green")
        else:
            out.append(line + "\n", style="bold red")

    missing = len(exp_lines) - len(act_lines)
    if missing > 0:
        out.append(f"  ({missing} missing line{'s' if missing != 1 else ''})", style="dim red")

    return out


# ---------------------------------------------------------------------------
# Status / info helpers
# ---------------------------------------------------------------------------


def print_error(message: str) -> None:
    """Print a formatted error line."""
    console.print(f"\n[bold red]Error:[/bold red] {message}\n")


def print_info(message: str) -> None:
    """Print a dim informational line."""
    console.print(f"[dim]{message}[/dim]")


def print_cached(problem_id: str) -> None:
    """Show a subtle 'loaded from cache' indicator."""
    console.print(f"[dim]  ↳ {problem_id} loaded from cache[/dim]")


def print_created(
    problem_id: str,
    filepath: "Path",  # type: ignore[name-defined]  # noqa: F821
    lang: str,
    folder_created: bool,
    already_inside: bool,
) -> None:
    """
    Print a clean summary after cf create succeeds.

    Example output:

        ✓ Created  contest2227/2227A.py
          Folder   contest2227/   (new)
          Lang     py
    """
    console.print()

    # Escape all dynamic values — paths can contain characters Rich
    # would otherwise interpret as markup tags (e.g. brackets).
    safe_path   = escape(str(filepath))
    safe_folder = escape(filepath.parent.name or ".")
    safe_lang   = escape(lang)

    console.print(f"  [bold green]✓[/bold green]  Created  [bold cyan]{safe_path}[/bold cyan]")

    # Keep everything inside a single [dim] block per line to avoid
    # mismatched open/close tag errors from combining styles.
    if already_inside:
        console.print(f"     [dim]Folder   {safe_folder}/  (already here)[/dim]")
    elif folder_created:
        console.print(f"     [dim]Folder   {safe_folder}/  (new)[/dim]")
    else:
        console.print(f"     [dim]Folder   {safe_folder}/  (exists)[/dim]")

    console.print(f"     [dim]Lang     [/dim][yellow]{safe_lang}[/yellow]")
    console.print()

def print_folder_created(name: str, already_existed: bool) -> None:
    """
    Print a message when a contest folder is created or reused.

    Example:

        ↳ Folder   contest2227/   (new)
        ↳ Folder   contest2227/   (exists)
    """
    safe_name = escape(name)

    if already_existed:
        console.print(f"     [dim]↳ Folder   {safe_name}/  (exists)[/dim]")
    else:
        console.print(f"     [dim]↳ Folder   {safe_name}/  (new)[/dim]")    

def print_lang_saved(lang: str) -> None:
    """Notify user that their language preference has been saved."""
    console.print(f"  [dim]↳ Saved [yellow]{lang}[/yellow] as your default language[/dim]")


def print_cache_list(problem_ids: list[str]) -> None:
    """Print a table of all cached problem IDs."""
    if not problem_ids:
        console.print("[dim]Cache is empty.[/dim]")
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
    table.add_column("Cached Problems", style="cyan")
    for pid in problem_ids:
        table.add_row(pid)

    console.print(table)

# ---------------------------------------------------------------------------
# ADDITIONS — SAFE (NO EXISTING CODE MODIFIED)
# ---------------------------------------------------------------------------

from contextlib import contextmanager


def print_ok(message: str) -> None:
    """
    Alternative success message using ✓ icon.

    Does NOT replace print_success.
    """
    console.print(f"[bold green]✓ {message}[/bold green]")


# ---------------------------------------------------------------------------
# Submit UI helpers (for cf submit)
# ---------------------------------------------------------------------------

def print_submit_start(problem_id: str, lang: str) -> None:
    """Show submission start message."""
    console.print(
        f"[dim]Submitting [cyan]{problem_id}[/cyan] ([yellow]{lang}[/yellow])...[/dim]"
    )


def print_submission_id(submission_id: str) -> None:
    """Display submission ID."""
    console.print(f"[dim]Submission ID: {submission_id}[/dim]")


def print_verdict_running() -> None:
    """Show running status."""
    console.print("[yellow]⏳ Running...[/yellow]")


def print_verdict_queue() -> None:
    """Show queue status."""
    console.print("[yellow]📦 In queue...[/yellow]")


def print_verdict_ok() -> None:
    """Accepted verdict."""
    console.print("[bold green]✓ Accepted[/bold green]")


def print_verdict_fail(verdict: str) -> None:
    """Failure verdict."""
    console.print(f"[bold red]✗ {verdict}[/bold red]")


# ---------------------------------------------------------------------------
# Spinner helper (for better UX)
# ---------------------------------------------------------------------------

@contextmanager
def spinner(message: str):
    """
    Context manager for showing a spinner.

    Example:
        with spinner("Submitting..."):
            do_work()
    """
    with console.status(f"[bold cyan]{message}[/bold cyan]"):
        yield