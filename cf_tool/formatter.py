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
    meta = f"[dim]⏱  {problem.time_limit}    💾  {problem.memory_limit}[/dim]"
    console.print(Panel(
        f"[bold white]{problem.title}[/bold white]\n"
        f"{meta}\n"
        f"[dim link={problem.url}]{problem.url}[/dim link={problem.url}]",
        title=f"[bold cyan]{problem.id}[/bold cyan]",
        border_style="cyan",
        padding=(1, 2),
    ))

    # ── Statement ────────────────────────────────────────────────────────────
    if problem.statement:
        console.print(Panel(
            problem.statement,
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
            problem.input_format or "[dim]N/A[/dim]",
            title="[bold green]Input Format[/bold green]",
            border_style="green",
            padding=(1, 2),
        ),
        Panel(
            problem.output_format or "[dim]N/A[/dim]",
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
        Panel(tc.input or "[dim](empty)[/dim]",
              title="[bold]Input[/bold]",
              border_style="dim",
              padding=(0, 1)),
        Panel(tc.expected_output or "[dim](empty)[/dim]",
              title="[bold]Expected Output[/bold]",
              border_style="dim",
              padding=(0, 1)),
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


def _print_failure(result) -> None:
    """Render expected vs. actual output (or a runtime error) for a failed test."""
    if result.error:
        console.print(Panel(
            f"[red]{result.error}[/red]",
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
