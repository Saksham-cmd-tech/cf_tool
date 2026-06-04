from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Tuple
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from rich.console import Console

from .auth import load_session

console = Console()

CF_BASE = "https://codeforces.com"

LANG_MAP = {
    "py": "31",    # Python 3.7.2
    "cpp": "54",   # GNU G++17 7.3.0
    "c": "43",     # GNU GCC C11 5.1.0
    "java": "36",  # Java 1.8.0_162
}


def _detect_lang(file: Path) -> str:
    ext = file.suffix.lower().lstrip(".")
    if ext not in LANG_MAP:
        raise RuntimeError(f"Unsupported language: {ext}")
    return LANG_MAP[ext]


def _parse_problem_from_filename(file: Path) -> Tuple[str, str]:
    """
    Supports:
      2227A.py -> ("2227", "A")
      1829A.cpp -> ("1829", "A")
      A.py inside contest2227/ -> ("2227", "A")
    """
    stem = file.stem.upper()

    m = re.match(r"^(\d+)([A-Z]\d?)$", stem)
    if m:
        return m.group(1), m.group(2)

    m = re.match(r"^([A-Z]\d?)$", stem)
    if m:
        contest_dir = file.parent.name.upper()
        c = re.match(r"^CONTEST(\d+)$", contest_dir)
        if c:
            return c.group(1), m.group(1)

    raise RuntimeError(
        "Cannot infer problem id from filename. "
        "Use a file like 2227A.py or A.py inside contest2227/."
    )


def _extract_csrf_and_form(html: str, page_url: str) -> tuple[str, dict, str]:
    """
    Parse the submit form exactly as rendered by Codeforces.
    Returns:
      csrf_token, hidden_fields, post_url
    """
    soup = BeautifulSoup(html, "html.parser")
    form = soup.find("form", class_="submit-form")
    if not form:
        raise RuntimeError("Submit form not found on page.")

    # The form action is relative, like "?csrf_token=..."
    action = form.get("action", "")
    post_url = urljoin(page_url, action)

    # CSRF token can be in hidden input or meta tag depending on page version
    csrf = None
    csrf_input = form.find("input", {"name": "csrf_token"})
    if csrf_input and csrf_input.get("value"):
        csrf = csrf_input["value"].strip()

    if not csrf:
        meta = soup.find("meta", attrs={"name": "X-Csrf-Token"})
        if meta and meta.get("content"):
            csrf = meta["content"].strip()

    if not csrf:
        raise RuntimeError("Failed to extract CSRF token from submit page.")

    hidden_fields: dict[str, str] = {}
    for inp in form.find_all("input"):
        name = inp.get("name")
        if not name:
            continue
        if name == "sourceFile":
            continue
        hidden_fields[name] = inp.get("value", "")

    return csrf, hidden_fields, post_url


def submit(file_path: str) -> None:
    file = Path(file_path)

    if not file.exists():
        raise RuntimeError(f"File not found: {file}")

    contest_id, problem = _parse_problem_from_filename(file)
    lang_id = _detect_lang(file)
    code = file.read_text(encoding="utf-8")

    console.print(f"[cyan]Submitting {contest_id}{problem}...[/cyan]")

    session = requests.Session()
    session.cookies.update(load_session())

    # Browser-like headers help Codeforces accept the request more reliably.
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/142.0.0.0 Safari/537.36"
            ),
            "Accept": (
                "text/html,application/xhtml+xml,application/xml;q=0.9,"
                "image/avif,image/webp,image/apng,*/*;q=0.8"
            ),
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": f"{CF_BASE}/contest/{contest_id}/submit",
            "Origin": CF_BASE,
        }
    )

    submit_page_url = f"{CF_BASE}/contest/{contest_id}/submit"
    r = session.get(submit_page_url, allow_redirects=True)

    if "/enter" in r.url:
        raise RuntimeError("Not logged in. Run `cf login --auto` again.")

    if "Just a moment" in r.text or "Cloudflare" in r.text:
        raise RuntimeError("Blocked by Cloudflare. Refresh your cookies and try again.")

    csrf, hidden_fields, post_url = _extract_csrf_and_form(r.text, r.url)

    # Put CSRF in the header as well as the form body.
    session.headers["X-Csrf-Token"] = csrf

    # Build multipart/form-data exactly like the browser form.
    # The current form includes:
    # csrf_token, ftaa, bfaa, action, submittedProblemCode, programTypeId, source,
    # tabSize, sourceFile
    #
    # Codeforces currently shows:
    # - submittedProblemCode input
    # - source textarea
    # - tabSize input
    # - sourceFile file input
    # and the form has enctype="multipart/form-data".
    multipart: dict[str, tuple[str | None, str]] = {}

    # Keep hidden fields from the page.
    for k, v in hidden_fields.items():
        multipart[k] = (None, v)

    # Override the fields we care about.
    multipart["csrf_token"] = (None, csrf)
    multipart["action"] = (None, "submitSolutionFormSubmitted")
    multipart["submittedProblemCode"] = (None, problem)
    multipart["programTypeId"] = (None, lang_id)
    multipart["source"] = (None, code)
    multipart["tabSize"] = (None, "4")

    # The page contains a file input named sourceFile; keep it empty.
    # This mirrors the browser form and keeps multipart/form-data behavior.
    multipart["sourceFile"] = ("", "")

    response = session.post(post_url, files=multipart, allow_redirects=True)

    if response.status_code != 200:
        raise RuntimeError(f"Submission failed with HTTP {response.status_code}")

    text = response.text

    # Better error visibility for CF's server-side form validation.
    if "error for__" in text or "error__" in text:
        snippet = text[:1500]
        raise RuntimeError(
            "Submission was rejected by Codeforces.\n"
            f"Response snippet:\n{snippet}"
        )

    console.print("[green]✔ Submitted successfully![/green]")

    m = re.search(r"/submission/(\d+)", text)
    if m:
        console.print(f"[dim]Submission ID: {m.group(1)}[/dim]")