"""
runner.py — Run a solution file against sample test cases.

Supports interpreted and compiled languages:
  Interpreted: Python, JavaScript (Node), TypeScript (ts-node), Ruby, Go
  Compiled:    C++, C, Java, Rust

For compiled languages, a build step runs first. If compilation fails,
all tests are immediately returned as failed with the compiler output
as the error message — no point running nothing.
"""

from __future__ import annotations

import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .models import TestCase
from .utils import normalize_output

# ---------------------------------------------------------------------------
# Data
# ---------------------------------------------------------------------------


@dataclass
class TestResult:
    """The outcome of running one test case."""

    test_case: TestCase
    passed: bool
    actual: Optional[str] = None
    expected: Optional[str] = None
    error: Optional[str] = None       # Runtime/compile error message
    elapsed_ms: float = 0.0


# ---------------------------------------------------------------------------
# Language detection
# ---------------------------------------------------------------------------

# Suffixes that need a compile step before running
_COMPILED = frozenset({".cpp", ".c", ".java", ".rs"})

# Suffixes that are run directly via an interpreter
_INTERPRETED: dict[str, list[str]] = {
    ".py":  ["python3"],
    ".js":  ["node"],
    ".ts":  ["ts-node"],
    ".rb":  ["ruby"],
    ".go":  ["go", "run"],
}


def _is_supported(suffix: str) -> bool:
    s = suffix.lower()
    return s in _COMPILED or s in _INTERPRETED


# ---------------------------------------------------------------------------
# Compile step
# ---------------------------------------------------------------------------


def _compile(file: Path) -> tuple[Optional[Path], Optional[str]]:
    """
    Compile a source file if the language requires it.

    Args:
        file: Path to the source file.

    Returns:
        (executable, error_message) — exactly one will be None.
        For interpreted languages, returns (file, None) unchanged.
    """
    suffix = file.suffix.lower()

    if suffix == ".cpp":
        out = file.with_suffix("")
        r = subprocess.run(
            ["g++", "-O2", "-std=c++17", "-o", str(out), str(file)],
            capture_output=True, text=True,
        )
        return (out, None) if r.returncode == 0 else (None, r.stderr.strip())

    if suffix == ".c":
        out = file.with_suffix("")
        r = subprocess.run(
            ["gcc", "-O2", "-o", str(out), str(file)],
            capture_output=True, text=True,
        )
        return (out, None) if r.returncode == 0 else (None, r.stderr.strip())

    if suffix == ".java":
        r = subprocess.run(
            ["javac", str(file)],
            capture_output=True, text=True,
        )
        # Return the .class sentinel path; run step handles java -cp
        return (file.with_suffix(".class"), None) if r.returncode == 0 else (None, r.stderr.strip())

    if suffix == ".rs":
        out = file.with_suffix("")
        r = subprocess.run(
            ["rustc", "-O", "-o", str(out), str(file)],
            capture_output=True, text=True,
        )
        return (out, None) if r.returncode == 0 else (None, r.stderr.strip())

    # Interpreted — no compile step needed
    return file, None


# ---------------------------------------------------------------------------
# Command builder
# ---------------------------------------------------------------------------


def _run_command(file: Path, executable: Path) -> list[str]:
    """
    Build the shell command list to execute a solution.

    Args:
        file:       Original source file (for suffix detection).
        executable: Compiled binary path (or same as file for interpreted).

    Returns:
        A list suitable for subprocess.run(cmd, ...).

    Raises:
        ValueError: For unsupported file types.
    """
    suffix = file.suffix.lower()

    if suffix in _INTERPRETED:
        base = _INTERPRETED[suffix]
        return [*base, str(file)]

    if suffix == ".java":
        return ["java", "-cp", str(file.parent), file.stem]

    if suffix in (".cpp", ".c", ".rs"):
        return [str(executable)]

    raise ValueError(f"Unsupported file extension: '{file.suffix}'")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def run_tests(
    file: Path,
    test_cases: list[TestCase],
    time_limit_ms: int = 5000,
) -> list[TestResult]:
    """
    Execute a solution file against every test case.

    Compilation (if required) happens once before any tests run.
    If compilation fails, every test is immediately marked as failed
    with the compiler output as the error.

    Args:
        file:          Path to the solution source file.
        test_cases:    Sample tests to run.
        time_limit_ms: Per-test time limit in milliseconds.

    Returns:
        One TestResult per test case, in order.

    Raises:
        FileNotFoundError: If the solution file doesn't exist.
        ValueError:        If the file extension is unsupported.
    """
    if not file.exists():
        raise FileNotFoundError(f"Solution file not found: {file}")

    suffix = file.suffix.lower()
    if not _is_supported(suffix):
        raise ValueError(
            f"Unsupported language '{file.suffix}'. "
            f"Supported: .py .cpp .c .java .js .ts .rb .go .rs"
        )

    # ---- Compilation ----
    executable, compile_err = _compile(file)
    if compile_err:
        return [
            TestResult(
                test_case=tc,
                passed=False,
                expected=tc.expected_output,
                error=f"Compilation failed:\n{compile_err}",
            )
            for tc in test_cases
        ]

    cmd = _run_command(file, executable)  # type: ignore[arg-type]
    timeout_s = time_limit_ms / 1000.0
    results: list[TestResult] = []

    for tc in test_cases:
        t_start = time.perf_counter()
        try:
            proc = subprocess.run(
                cmd,
                input=tc.input,
                capture_output=True,
                text=True,
                timeout=timeout_s,
            )
            elapsed_ms = (time.perf_counter() - t_start) * 1000.0

            actual = normalize_output(proc.stdout)
            expected = normalize_output(tc.expected_output)

            if proc.returncode != 0:
                # Non-zero exit: runtime error
                stderr_snippet = proc.stderr[:600].strip() if proc.stderr else ""
                results.append(TestResult(
                    test_case=tc,
                    passed=False,
                    actual=actual,
                    expected=expected,
                    error=f"Runtime error (exit {proc.returncode})"
                          + (f":\n{stderr_snippet}" if stderr_snippet else ""),
                    elapsed_ms=elapsed_ms,
                ))
            else:
                results.append(TestResult(
                    test_case=tc,
                    passed=(actual == expected),
                    actual=actual,
                    expected=expected,
                    elapsed_ms=elapsed_ms,
                ))

        except subprocess.TimeoutExpired:
            elapsed_ms = (time.perf_counter() - t_start) * 1000.0
            results.append(TestResult(
                test_case=tc,
                passed=False,
                expected=tc.expected_output,
                error=f"Time limit exceeded (> {time_limit_ms} ms)",
                elapsed_ms=elapsed_ms,
            ))

    return results
