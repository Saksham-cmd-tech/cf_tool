from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

import browser_cookie3
from rich.console import Console

console = Console()

CF_DIR = Path.home() / ".cfmate"
SESSION_FILE = CF_DIR / "session.json"

REQUIRED_COOKIES = ["JSESSIONID", "39ce7", "cf_clearance"]


def _save_session(data: Dict[str, str]) -> None:
    CF_DIR.mkdir(parents=True, exist_ok=True)
    with open(SESSION_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    console.print("[green]✓ Session saved[/green]")


def create_session() -> None:
    """
    Create a session automatically from Chrome cookies.
    """
    console.print("[cyan]Creating session from Chrome cookies...[/cyan]")

    try:
        cj = browser_cookie3.chrome(domain_name="codeforces.com")
    except Exception as e:
        raise RuntimeError(f"Could not read Chrome cookies: {e}")

    cookies = {c.name: c.value for c in cj}

    session = {k: cookies[k] for k in REQUIRED_COOKIES if k in cookies}

    if "JSESSIONID" not in session:
        raise RuntimeError("No Codeforces session found in Chrome. Please log in first.")

    _save_session(session)
    console.print("[green]✓ Session created successfully[/green]")


def create_session_manual() -> None:
    """
    Manual fallback: paste cookies yourself.
    """
    console.print("[cyan]Manual session creation[/cyan]")
    jsession = input("JSESSIONID: ").strip()
    c39 = input("39ce7: ").strip()
    cf_clearance = input("cf_clearance: ").strip()

    if not jsession:
        raise RuntimeError("JSESSIONID is required")

    session = {
        "JSESSIONID": jsession,
        "39ce7": c39,
        "cf_clearance": cf_clearance,
    }

    _save_session(session)
    console.print("[green]✓ Session created successfully[/green]")


def load_session() -> Dict[str, str]:
    if not SESSION_FILE.exists():
        raise RuntimeError("Session not found. Run `cf login --auto` first.")
    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def delete_session() -> None:
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
        console.print("[green]✓ Session deleted[/green]")
    else:
        console.print("[yellow]No session found[/yellow]")