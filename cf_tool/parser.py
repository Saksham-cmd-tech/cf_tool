"""
parser.py — HTML parsing layer.

Converts raw Codeforces HTML into a typed Problem object.
All logic is derived from and improves upon the original getProblem.py:

Original strengths preserved:
- extract_pre_text: handles modern div-per-line AND legacy br-tag layouts
- Section filtering: excludes header/specs/samples from statement body
- clean_latex integration

Improvements:
- Returns structured data instead of printing
- Title and limits extracted from header
- All helpers are private; only parse_problem() is public
- Full type hints and docstrings
"""

from __future__ import annotations

from typing import Optional

from bs4 import BeautifulSoup, Tag

from .models import Problem, TestCase
from .utils import clean_latex

# ---------------------------------------------------------------------------
# Classes that belong to "other" sections and should be stripped from the
# main statement body.
# ---------------------------------------------------------------------------
_EXCLUDED_SECTION_CLASSES = frozenset(
    {
        "header",
        "input-specification",
        "output-specification",
        "sample-tests",
        "note",
    }
)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _extract_pre_text(pre: Optional[Tag]) -> str:
    """
    Extract plain text from a <pre> block, preserving newlines correctly.

    Handles two Codeforces layouts:
    1. Modern: each line is a <div> child inside <pre>
    2. Legacy: lines separated by <br> tags
    """
    if pre is None:
        return ""

    inner_divs = pre.find_all("div")
    if inner_divs:
        # Modern layout — join each div's text as its own line
        return "\n".join(div.get_text() for div in inner_divs)

    # Legacy layout — swap <br> for real newlines, then get text
    for br in pre.find_all("br"):
        br.replace_with("\n")

    return pre.get_text().strip()


def _section_text(div: Tag) -> str:
    """
    Extract clean text from a section div (input-spec, output-spec, note).

    Strips the section title element so it isn't duplicated in the output,
    then applies LaTeX cleaning.
    """
    title_el = div.find("div", class_="section-title")
    raw = div.get_text()
    if title_el:
        raw = raw.replace(title_el.get_text(), "", 1)
    return clean_latex(raw.strip())


def _parse_limits(header: Optional[Tag]) -> tuple[str, str]:
    """
    Extract (time_limit, memory_limit) from the problem header div.

    Returns ("N/A", "N/A") if the header is absent or the elements
    can't be found.
    """
    if header is None:
        return "N/A", "N/A"

    time_el = header.find("div", class_="time-limit")
    memory_el = header.find("div", class_="memory-limit")

    def _strip_label(el: Optional[Tag], label: str) -> str:
        if el is None:
            return "N/A"
        return el.get_text(strip=True).replace(label, "").strip()

    time_limit = _strip_label(time_el, "time limit per test")
    memory_limit = _strip_label(memory_el, "memory limit per test")
    return time_limit, memory_limit


def _parse_title(header: Optional[Tag]) -> str:
    """Extract the problem title from the header div."""
    if header is None:
        return "Unknown"
    title_el = header.find("div", class_="title")
    return title_el.get_text(strip=True) if title_el else "Unknown"


def _parse_statement_body(statement_div: Tag) -> str:
    """
    Collect the main problem description, excluding all known sub-sections.

    Iterates direct children of the problem-statement div and gathers text
    from any div whose class list doesn't overlap with _EXCLUDED_SECTION_CLASSES.
    """
    parts: list[str] = []
    for child in statement_div.find_all("div", recursive=False):
        classes = set(child.get("class", []))
        if not classes & _EXCLUDED_SECTION_CLASSES:
            parts.append(child.get_text())
    return clean_latex("\n\n".join(parts))


def _parse_sample_tests(statement_div: Tag) -> list[TestCase]:
    """Extract all (input, expected_output) pairs from the sample-tests section."""
    sample_div = statement_div.find("div", class_="sample-tests")
    if sample_div is None:
        return []

    inputs = sample_div.find_all("div", class_="input")
    outputs = sample_div.find_all("div", class_="output")

    return [
        TestCase(
            input=_extract_pre_text(inp.find("pre")),
            expected_output=_extract_pre_text(outp.find("pre")),
        )
        for inp, outp in zip(inputs, outputs)
    ]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_problem(html: str, problem_id: str, url: str) -> Problem:
    """
    Parse raw Codeforces problem page HTML into a typed Problem object.

    Args:
        html:       Raw HTML string of the problem page.
        problem_id: Normalized problem ID, e.g. "1829A".
        url:        Source URL (stored on the Problem for reference).

    Returns:
        A fully populated Problem dataclass.

    Raises:
        ValueError: If the problem-statement div cannot be found, which
                    typically means the URL was wrong or the page changed.
    """
    soup = BeautifulSoup(html, "html.parser")
    statement_div = soup.find("div", class_="problem-statement")

    if statement_div is None:
        raise ValueError(
            "Could not locate the problem statement on the page. "
            "The problem ID may be incorrect, or Codeforces may have changed its layout."
        )

    header = statement_div.find("div", class_="header")
    title = _parse_title(header)
    time_limit, memory_limit = _parse_limits(header)

    input_div = statement_div.find("div", class_="input-specification")
    output_div = statement_div.find("div", class_="output-specification")

    return Problem(
        id=problem_id,
        title=title,
        url=url,
        statement=_parse_statement_body(statement_div),
        input_format=_section_text(input_div) if input_div else "",
        output_format=_section_text(output_div) if output_div else "",
        time_limit=time_limit,
        memory_limit=memory_limit,
        sample_tests=_parse_sample_tests(statement_div),
    )
