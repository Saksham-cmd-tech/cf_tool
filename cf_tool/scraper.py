"""
scraper.py — Advanced stealth scraper for Codeforces

Features:
- Requests fast path
- Playwright fallback (stealth mode)
- OS + device profile simulation
- Rotating user-agents
- Anti-bot fingerprint patches
- Persistent browser session
- Automatic Chromium install
"""

from __future__ import annotations

import subprocess
import time
import random
from typing import Optional

import requests

# ---------------------------------------------------------------------------
# USER AGENTS (OS-level rotation)
# ---------------------------------------------------------------------------

USER_AGENTS = [
    # --- Windows ---
    # Chrome (Latest)
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    # Edge
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 Edg/142.0.0.0",
    # Firefox
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",

    # --- macOS ---
    # Chrome
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    # Safari
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.2 Safari/605.1.15",
    # Firefox
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:135.0) Gecko/20100101 Firefox/135.0",

    # --- Linux ---
    # Chrome
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
    # Firefox
    "Mozilla/5.0 (X11; Linux x86_64; rv:135.0) Gecko/20100101 Firefox/135.0",

    # --- Mobile (iOS / iPhone) ---
    # Safari on iPhone
    "Mozilla/5.0 (iPhone; CPU iPhone OS 19_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/19.2 Mobile/15E148 Safari/605.1.15",
    # Chrome on iPhone
    "Mozilla/5.0 (iPhone; CPU iPhone OS 19_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) CriOS/142.0.0.0 Mobile/15E148 Safari/604.1",

    # --- Mobile (Android) ---
    # Chrome on Android (Pixel 8/9 equivalent)
    "Mozilla/5.0 (Linux; Android 14; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Mobile Safari/537.36",
    # Firefox on Android
    "Mozilla/5.0 (Android 14; Mobile; rv:135.0) Gecko/135.0 Firefox/135.0"
]

# Device profiles
VIEWPORTS = [
    {"width": 1366, "height": 768},
    {"width": 1920, "height": 1080},
    {"width": 1440, "height": 900},
]

LOCALES = ["en-US", "en-GB"]

# ---------------------------------------------------------------------------
# GLOBAL BROWSER STATE
# ---------------------------------------------------------------------------

_playwright = None
_browser = None
_context = None
_page = None
_browser_checked = False


# ---------------------------------------------------------------------------
# Ensure Playwright installed
# ---------------------------------------------------------------------------

def ensure_playwright_browser():
    global _browser_checked

    if _browser_checked:
        return

    _browser_checked = True

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            b = p.chromium.launch(headless=True)
            b.close()
    except Exception:
        print("Installing Playwright Chromium...")
        subprocess.run(["playwright", "install", "chromium"], check=True)


# ---------------------------------------------------------------------------
# STEALTH PATCHES
# ---------------------------------------------------------------------------

STEALTH_JS = """
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });

window.chrome = { runtime: {} };

Object.defineProperty(navigator, 'languages', {
    get: () => ['en-US', 'en']
});

Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3]
});
"""


# ---------------------------------------------------------------------------
# Persistent browser (with stealth)
# ---------------------------------------------------------------------------

def _get_page():
    global _playwright, _browser, _context, _page

    if _page:
        return _page

    ensure_playwright_browser()

    from playwright.sync_api import sync_playwright

    _playwright = sync_playwright().start()

    ua = random.choice(USER_AGENTS)

    _browser = _playwright.chromium.launch(
        headless=False,
        args=[
            "--disable-blink-features=AutomationControlled",
        ],
    )

    _context = _browser.new_context(
        user_agent=ua,
        viewport=random.choice(VIEWPORTS),
        locale=random.choice(LOCALES),
    )

    _page = _context.new_page()

    # Inject stealth patches BEFORE page loads
    _page.add_init_script(STEALTH_JS)

    return _page


# ---------------------------------------------------------------------------
# FAST PATH (requests)
# ---------------------------------------------------------------------------

def _fetch_with_requests(url: str, timeout: int) -> str:
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://codeforces.com/",
    }

    response = requests.get(url, timeout=timeout, headers=headers)

    if response.status_code == 404:
        raise ValueError("404")

    if response.status_code == 403:
        raise ValueError("403")

    html = response.text

    if "Just a moment" in html or "Cloudflare" in html:
        raise ValueError("Blocked")

    return html


# ---------------------------------------------------------------------------
# PLAYWRIGHT FALLBACK (STEALTH)
# ---------------------------------------------------------------------------

def _fetch_with_playwright(url: str, timeout: int) -> str:
    page = _get_page()

    # Random human-like delay
    time.sleep(random.uniform(1.0, 2.5))

    page.goto(url, timeout=timeout * 1000, wait_until="domcontentloaded")

    page.wait_for_load_state("networkidle")

    # Simulate human scroll
    page.mouse.wheel(0, random.randint(200, 800))

    time.sleep(random.uniform(1.0, 2.0))

    html = page.content()

    if "Just a moment" in html:
        time.sleep(3)
        html = page.content()

    page.wait_for_selector(".problem-statement", timeout=20000)

    return page.content()


# ---------------------------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------------------------

def fetch_problem_page(url: str, retries: int = 3, timeout: int = 20) -> str:
    last_exc: Optional[Exception] = None

    for attempt in range(1, retries + 1):

        time.sleep(random.uniform(1.0, 2.0))

        # Fast path
        try:
            return _fetch_with_requests(url, timeout)
        except Exception as e:
            last_exc = e

        # Fallback
        try:
            print("↳ Using browser fallback...")
            return _fetch_with_playwright(url, timeout)
        except Exception as e:
            last_exc = e

        if attempt < retries:
            time.sleep(2 ** attempt)

    raise ConnectionError(f"Failed after {retries} attempts: {last_exc}")


# ---------------------------------------------------------------------------
# CLEANUP
# ---------------------------------------------------------------------------

def close_browser():
    global _playwright, _browser, _context, _page

    try:
        if _page:
            _page.close()
        if _context:
            _context.close()
        if _browser:
            _browser.close()
        if _playwright:
            _playwright.stop()
    finally:
        _playwright = None
        _browser = None
        _context = None
        _page = None