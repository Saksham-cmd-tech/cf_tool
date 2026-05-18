"""
models.py — Core data structures for the CF tool.

Defines Problem and TestCase dataclasses with JSON serialization
so they can be stored/loaded from the local cache.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TestCase:
    """A single sample test: one input string, one expected output string."""

    input: str
    expected_output: str

    def to_dict(self) -> dict[str, str]:
        return {"input": self.input, "expected_output": self.expected_output}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TestCase":
        return cls(
            input=data["input"],
            expected_output=data["expected_output"],
        )


@dataclass
class Problem:
    """
    A fully parsed Codeforces problem.

    Attributes:
        id:            Normalized problem ID, e.g. "1829A".
        title:         Full problem title from the page header.
        url:           Source URL.
        statement:     Main problem description (LaTeX-cleaned).
        input_format:  Input specification section.
        output_format: Output specification section.
        time_limit:    Raw time limit string from the header.
        memory_limit:  Raw memory limit string from the header.
        sample_tests:  Ordered list of (input, expected_output) pairs.
    """

    id: str
    title: str
    url: str
    statement: str
    input_format: str
    output_format: str
    time_limit: str
    memory_limit: str
    sample_tests: list[TestCase] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "statement": self.statement,
            "input_format": self.input_format,
            "output_format": self.output_format,
            "time_limit": self.time_limit,
            "memory_limit": self.memory_limit,
            "sample_tests": [tc.to_dict() for tc in self.sample_tests],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Problem":
        return cls(
            id=data["id"],
            title=data["title"],
            url=data["url"],
            statement=data["statement"],
            input_format=data["input_format"],
            output_format=data["output_format"],
            time_limit=data["time_limit"],
            memory_limit=data["memory_limit"],
            sample_tests=[
                TestCase.from_dict(tc) for tc in data.get("sample_tests", [])
            ],
        )
