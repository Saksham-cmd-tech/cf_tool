"""
scraper.py — HTML fetching via cloudscraper.

Wraps cloudscraper in a reusable module with:
- Singleton scraper instance (avoid re-initializing on every call)
- Automatic retries with exponential backoff
- Clean, typed error hierarchy
"""

from __future__ import annotations

import time
from typing import Optional

import cloudscraper

# ---------------------------------------------------------------------------
# Module-level singleton so we don't re-initialize the scraper on every call.
# ---------------------------------------------------------------------------
_scraper: Optional[cloudscraper.CloudScraper] = None


def _get_scraper() -> cloudscraper.CloudScraper:
    """Return (or create) the module-level cloudscraper instance."""
    global _scraper
    if _scraper is None:
        _scraper = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "mobile": False,
            }
        )
    return _scraper


def fetch_problem_page(
    url: str,
    *,
    retries: int = 3,
    timeout: int = 15,
) -> str:
    """
    Fetch the HTML content of a Codeforces problem page.

    Args:
        url:     Full URL of the problem page.
        retries: Number of attempts before giving up (default 3).
        timeout: Per-request timeout in seconds (default 15).

    Returns:
        The page HTML as a UTF-8 string.

    Raises:
        ValueError:      On a definitive HTTP error (404, 403, etc.).
        ConnectionError: On network failure after all retries are exhausted.
    """
    scraper = _get_scraper()
    last_exc: Exception = RuntimeError("Unknown error")

    for attempt in range(1, retries + 1):
        try:
            response = scraper.get(url, timeout=timeout)
        except Exception as exc:
            last_exc = exc
            if attempt < retries:
                time.sleep(1.5 ** attempt)  # 1.5s, 2.25s, …
            continue

        # --- Definitive errors: no point retrying ---
        if response.status_code == 404:
            raise ValueError(
                f"Problem not found (404). Check the problem ID and try again.\n  URL: {url}"
            )
        if response.status_code == 403:
            raise ValueError(
                f"Access denied (403). You may be rate-limited.\n  URL: {url}"
            )
        if response.status_code != 200:
            raise ValueError(
                f"Unexpected HTTP {response.status_code} from Codeforces.\n  URL: {url}"
            )

        return response.text

    raise ConnectionError(
        f"Failed to fetch problem page after {retries} attempt(s): {last_exc}\n  URL: {url}"
    )
