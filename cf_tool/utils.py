"""
utils.py — Shared utility functions.

Covers:
- Problem ID parsing (e.g. "1829A" → contest_id, problem_letter)
- URL construction
- LaTeX/math cleaning (improved from original script)
- Output normalization for test comparison
"""

from __future__ import annotations

import re

# ---------------------------------------------------------------------------
# LaTeX → Unicode replacement table
# Expanded from the original script with common Codeforces symbols.
# ---------------------------------------------------------------------------
_LATEX_REPLACEMENTS: dict[str, str] = {
    r"\in": "∈",
    r"\notin": "∉",
    r"\dots": "…",
    r"\ldots": "…",
    r"\cdot": "·",
    r"\cdots": "⋯",
    r"\le": "≤",
    r"\leq": "≤",
    r"\ge": "≥",
    r"\geq": "≥",
    r"\neq": "≠",
    r"\ne": "≠",
    r"\times": "×",
    r"\div": "÷",
    r"\pm": "±",
    r"\infty": "∞",
    r"\to": "→",
    r"\rightarrow": "→",
    r"\leftarrow": "←",
    r"\leftrightarrow": "↔",
    r"\sum": "∑",
    r"\prod": "∏",
    r"\sqrt": "√",
    r"\lfloor": "⌊",
    r"\rfloor": "⌋",
    r"\lceil": "⌈",
    r"\rceil": "⌉",
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\delta": "δ",
    r"\epsilon": "ε",
    r"\varepsilon": "ε",
    r"\pi": "π",
    r"\sigma": "σ",
    r"\omega": "ω",
    r"\lambda": "λ",
    r"\mu": "μ",
    r"\nu": "ν",
    r"\phi": "φ",
    r"\psi": "ψ",
    r"\theta": "θ",
    r"\operatorname{mex}": "mex",
    r"\operatorname{lcm}": "lcm",
    r"\operatorname{gcd}": "gcd",
    r"\text{∗}": "*",
    r"\text{†}": "†",
    r"\bmod": "mod",
    r"\mod": "mod",
    r"\pmod": "mod",
}

# Pattern for Codeforces triple-dollar math: $$$...$$$
_CF_MATH_RE = re.compile(r"\$\$\$(.*?)\$\$\$", re.DOTALL)

# Pattern for collapsing excessive blank lines
_BLANK_LINES_RE = re.compile(r"\n{3,}")


def clean_latex(text: str) -> str:
    """
    Convert LaTeX math and special symbols into terminal-friendly Unicode.

    - Applies symbol replacements from _LATEX_REPLACEMENTS
    - Strips $$$ math delimiters (Codeforces-specific), keeping inner content
    - Collapses 3+ consecutive blank lines to 2
    """
    if not text:
        return ""

    for latex, symbol in _LATEX_REPLACEMENTS.items():
        text = text.replace(latex, symbol)

    # Strip $$$ delimiters but preserve the math content inside
    text = _CF_MATH_RE.sub(r"\1", text)

    # Collapse excessive whitespace
    text = _BLANK_LINES_RE.sub("\n\n", text)

    return text.strip()


def parse_problem_id(problem_id: str) -> tuple[str, str]:
    """
    Parse a Codeforces problem ID into (contest_id, problem_letter).

    Accepts formats like:
        "1829A"  → ("1829", "A")
        "2227D"  → ("2227", "D")
        "101A1"  → ("101",  "A1")   # sub-problems like A1, B2

    Raises:
        ValueError: If the format is unrecognized.
    """
    normalized = problem_id.strip().upper()
    match = re.match(r"^(\d+)([A-Z]\d?)$", normalized)
    if not match:
        raise ValueError(
            f"Invalid problem ID '{problem_id}'. "
            "Expected a contest number followed by a letter, e.g. '1829A' or '2227D'."
        )
    return match.group(1), match.group(2)


def build_problem_url(contest_id: str, problem_letter: str) -> str:
    """Build the canonical Codeforces URL for a problem."""
    return f"https://codeforces.com/contest/{contest_id}/problem/{problem_letter}"


def normalize_output(text: str) -> str:
    """
    Normalize program output for comparison against expected output.

    Rules:
    - Strip trailing whitespace from every line
    - Remove trailing blank lines at the end of output
    - Normalize line endings (CRLF → LF)
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = [line.rstrip() for line in text.splitlines()]
    # Drop trailing empty lines
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)
