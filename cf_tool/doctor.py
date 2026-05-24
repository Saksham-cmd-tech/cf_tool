"""
doctor.py — Environment diagnostics for cfmate
"""

from __future__ import annotations

import sys
import subprocess
from pathlib import Path

import requests
from rich.console import Console
from rich.live import Live
from rich.text import Text
from rich.padding import Padding

console = Console()


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def _check_python():
    ok = sys.version_info >= (3, 9)
    return ok, sys.version.split()[0]


def _check_playwright():
    try:
        import playwright  # noqa: F401
        return True, "installed"
    except Exception:
        return False, "pip install playwright"


def _check_chromium():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            browser.close()
        return True, "installed"
    except Exception:
        return False, "playwright install chromium"


def _check_local_cache():
    path = Path(".cf_cache")
    return path.exists(), str(path.resolve())


def _check_global_cache():
    path = Path.home() / ".cfmate" / "problems_cache.json"
    return path.exists(), str(path)


def _check_network():
    try:
        requests.get("https://codeforces.com", timeout=3)
        return True, "codeforces.com reachable"
    except Exception:
        return False, "check internet connection"


def _check_git():
    try:
        name  = subprocess.getoutput("git config user.name").strip()
        email = subprocess.getoutput("git config user.email").strip()
        if name and email:
            return True, f"{name} <{email}>"
        return False, "set git config user.name and user.email"
    except Exception:
        return False, "git not available"


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

def _row(label: str, state: str, detail: str) -> Text:
    """
    state: "checking" | "ok" | "warn" | "fail"
    """
    icons = {
        "checking": ("⠋", "#555555"),
        "ok":       ("✓", "#00d700"),
        "warn":     ("⚠", "#d7af00"),
        "fail":     ("✗", "#d70000"),
    }
    icon, color = icons[state]

    line = Text()
    line.append(f"  {icon} ", style=f"bold {color}")
    line.append(f"{label:<22}", style="#e0e0e0" if state != "checking" else "#555555")
    if detail:
        line.append(f"  {detail}", style="#555555" if state == "ok" else f"{color}")
    return line


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run_doctor(fix: bool = False):
    checks = [
        ("Python ≥ 3.9",    _check_python,       None),
        ("Playwright",       _check_playwright,   lambda: subprocess.run(["pip", "install", "playwright"], check=False)),
        ("Chromium",         _check_chromium,     lambda: subprocess.run(["playwright", "install", "chromium"], check=False)),
        ("Local cache",      _check_local_cache,  lambda: Path(".cf_cache").mkdir(exist_ok=True)),
        ("Global cache",     _check_global_cache, lambda: (Path.home() / ".cfmate").mkdir(parents=True, exist_ok=True)),
        ("Network",          _check_network,      None),
        ("Git config",       _check_git,          None),
    ]

    results: list[tuple[str, str, str]] = []   # (label, state, detail)

    console.print()
    console.print("  [bold #00afff]cfmate doctor[/bold #00afff]\n")

    for label, fn, fixer in checks:
        # Show spinner row
        with console.status(
            f"  [#555555]checking {label}…[/#555555]",
            spinner="dots",
            spinner_style="#00afff",
        ):
            ok, detail = fn()

        # Auto-fix if requested and possible
        if not ok and fix and fixer:
            console.print(_row(label, "checking", "fixing…"))
            fixer()
            ok, detail = fn()

        # Determine final state
        warns = {"Local cache", "Global cache", "Git config"}
        if ok:
            state = "ok"
        elif label in warns:
            state = "warn"
        else:
            state = "fail"

        console.print(_row(label, state, detail))
        results.append((label, state, detail))

    # ── Summary ──────────────────────────────────────────────────────────────
    console.print()
    failed = [r for r in results if r[1] == "fail"]
    warned = [r for r in results if r[1] == "warn"]

    if not failed and not warned:
        console.print("  [bold #00d700]All checks passed.[/bold #00d700]\n")
    else:
        if failed:
            console.print(f"  [bold #d70000]{len(failed)} check(s) failed.[/bold #d70000]")
        if warned:
            console.print(f"  [#d7af00]{len(warned)} warning(s).[/#d7af00]")
        if not fix:
            console.print("  [#555555]Run with --fix to auto-resolve where possible.[/#555555]")
        console.print()

    if fix:
        console.print("  [#00d700]Auto-fix completed.[/#00d700]\n")