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
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style

from .cache_problems import get_problems


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------

UI_STYLE = Style.from_dict({
    "header":        "bold #00afff",
    "status":        "bg:#1a1a1a #555555",
    "status.key":    "#00afff bold",

    "rating.gray":   "#555555",
    "rating.green":  "#00d700",
    "rating.cyan":   "#00afff",
    "rating.yellow": "#d7af00",
    "rating.orange": "#d75f00",
    "rating.red":    "#d70000 bold",

    "letter":        "#00afff bold",
    "name":          "#e0e0e0",
    "name.selected": "#ffffff bold",
    "cursor":        "#00afff bold",
    "tag":           "#5f5f87",
})


def _rating_style(rating) -> str:
    if not rating or rating == "?": return "class:rating.gray"
    r = int(rating)
    if r <= 1200: return "class:rating.green"
    if r <= 1600: return "class:rating.cyan"
    if r <= 2000: return "class:rating.yellow"
    if r <= 2400: return "class:rating.orange"
    return               "class:rating.red"


def _difficulty(rating) -> str:
    if not rating or rating == "?": return "—    "
    r = int(rating)
    if r <= 1000: return "★☆☆☆☆"
    if r <= 1400: return "★★☆☆☆"
    if r <= 1800: return "★★★☆☆"
    if r <= 2200: return "★★★★☆"
    return               "★★★★★"


# ---------------------------------------------------------------------------
# Contest browser
# ---------------------------------------------------------------------------

class CFContest:

    def __init__(self, contest_id: str):
        self.contest_id = contest_id.strip()
        self.problems: list[dict] = []
        self.index = 0

    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------

    def load(self) -> None:
        all_problems = get_problems()
        self.problems = [
            {
                "id":     f"{p['contestId']}{p['index']}",
                "letter": p["index"],
                "name":   p["name"],
                "rating": p.get("rating", 0),
                "tags":   p.get("tags", []),
            }
            for p in all_problems
            if str(p["contestId"]) == self.contest_id
        ]
        self.problems.sort(key=lambda p: p["letter"])

    # ------------------------------------------------------------------
    # Render → FormattedText
    # ------------------------------------------------------------------

    def render(self, window: int = 20) -> FormattedText:
        if not self.problems:
            return FormattedText([("class:rating.gray",
                                   f"  No problems found for contest {self.contest_id}.")])

        total  = len(self.problems)
        start  = max(0, min(self.index - window // 2, total - window))
        end    = min(start + window, total)

        tokens = []
        for i in range(start, end):
            p      = self.problems[i]
            sel    = i == self.index
            rating = p["rating"]
            tags   = p["tags"][:3]
            tag_str = "  " + "  ".join(f"#{t}" for t in tags) if tags else ""

            # cursor
            tokens.append(("class:cursor",  "▶ " if sel else "  "))

            # letter
            tokens.append(("class:letter",  f"{p['letter']:<4}"))

            # name
            name_style = "class:name.selected" if sel else "class:name"
            tokens.append((name_style,       f"{p['name']:<45}"))

            # rating + stars
            r_style = _rating_style(rating)
            r_label = f"{rating:>4}" if rating else "   —"
            tokens.append((r_style, f"  {r_label}  {_difficulty(rating)}"))

            # tags
            tokens.append(("class:tag", tag_str))

            tokens.append(("", "\n"))

        return FormattedText(tokens)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self, no_cache: bool = False) -> None:
        self.load()

        header_control = FormattedTextControl(
            text=lambda: FormattedText([
                ("class:header",
                 f"  Contest {self.contest_id} — {len(self.problems)} problem(s)  "),
            ])
        )
        header = Window(content=header_control, height=1)

        results_control = FormattedTextControl(
            text=lambda: self.render(),
            focusable=False,
        )
        results_window = Window(content=results_control)

        status_control = FormattedTextControl(
            text=lambda: FormattedText([
                ("", f"  ↑↓ navigate  Enter fetch problem  Ctrl-C quit  —  {self.index + 1}/{len(self.problems)}  "),
            ])
        )
        status = Window(content=status_control, height=1)

        # ------------------------------------------------------------------
        # Key bindings
        # ------------------------------------------------------------------

        kb = KeyBindings()

        @kb.add("down")
        def _(event):
            if self.index < len(self.problems) - 1:
                self.index += 1

        @kb.add("up")
        def _(event):
            if self.index > 0:
                self.index -= 1

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
            layout=Layout(HSplit([header, results_window, status])),
            key_bindings=kb,
            style=UI_STYLE,
            full_screen=True,
            mouse_support=True,
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