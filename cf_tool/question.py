"""
question.py — Interactive browser for a single Codeforces contest.

Usage (called from cli.py):
    CFContest(contest_id).run(no_cache=False)

Launched by:
    cf get 2227        → browse contest 2227, Enter fetches selected problem
    cf get 2227 -n     → same but bypasses cache on fetch
"""

from __future__ import annotations

from prompt_toolkit import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.key_binding import KeyBindings

from .cache_problems import get_problems


class CFContest:

    def __init__(self, contest_id: str):
        self.contest_id = contest_id.strip()
        self.problems: list[dict] = []
        self.index = 0

    # ------------------------------------------------------------------
    # Load — filter global cache to this contest only
    # ------------------------------------------------------------------

    def load(self) -> None:
        all_problems = get_problems()
        self.problems = [
            {
                "id":     f"{p['contestId']}{p['index']}",
                "letter": p["index"],
                "name":   p["name"],
                "rating": p.get("rating", "?"),
                "tags":   p.get("tags", []),
            }
            for p in all_problems
            if str(p["contestId"]) == self.contest_id
        ]
        # Sort by problem letter: A, B, C, ...
        self.problems.sort(key=lambda p: p["letter"])

    # ------------------------------------------------------------------
    # Render list
    # ------------------------------------------------------------------

    def render(self, window: int = 20) -> str:
        if not self.problems:
            return f"  No problems found for contest {self.contest_id}."
    
        total = len(self.problems)
        start = max(0, min(self.index - window // 2, total - window))
        end   = min(start + window, total)
    
        lines = []
        for i in range(start, end):
            p      = self.problems[i]
            prefix = "➤ " if i == self.index else "  "
            lines.append(f"{prefix}{p['letter']}  {p['name']}")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self, no_cache: bool = False) -> None:
        self.load()

        header  = TextArea(height=1, focusable=False)
        results = TextArea(focusable=False)
        status  = TextArea(height=1, focusable=False)

        header.text = f"  Contest {self.contest_id} — {len(self.problems)} problem(s)"
        results.text = self.render()
        status.text  = "↑↓ navigate  Enter: fetch problem  Ctrl-C: quit"

        # ------------------------------------------------------------------
        # Key bindings
        # ------------------------------------------------------------------

        kb = KeyBindings()

        @kb.add("down")
        def _(event):
            if self.index < len(self.problems) - 1:
                self.index += 1
                results.text = self.render()

        @kb.add("up")
        def _(event):
            if self.index > 0:
                self.index -= 1
                results.text = self.render()

        @kb.add("enter")
        def _(event):
            if not self.problems:
                return
            event.app.exit(result=self.problems[self.index]["id"])

        @kb.add("c-c")
        def _(event):
            event.app.exit()

        # ------------------------------------------------------------------
        # Layout & run
        # ------------------------------------------------------------------

        app = Application(
            layout=Layout(HSplit([header, results, status])),
            key_bindings=kb,
            full_screen=True,
        )

        chosen_id = app.run()

        if chosen_id:
            from cf_tool.core import resolve_problem
            from cf_tool.formatter import print_problem, print_error
            try:
                parsed = resolve_problem(chosen_id, no_cache=no_cache)
                print_problem(parsed)
            except Exception as e:
                print_error(str(e))