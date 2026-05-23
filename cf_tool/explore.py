from prompt_toolkit import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit, Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style
 
from rapidfuzz import fuzz
from .cache_problems import get_problems
 
 
# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
 
UI_STYLE = Style.from_dict({
    "header":        "bold #00afff",
    "status":        "bg:#1a1a1a #555555",
    "status.key":    "#00afff bold",
    "status.sep":    "#333333",
 
    # rating bands
    "rating.gray":   "#555555",
    "rating.green":  "#00d700",
    "rating.cyan":   "#00afff",
    "rating.yellow": "#d7af00",
    "rating.orange": "#d75f00",
    "rating.red":    "#d70000 bold",
 
    "tag":           "#5f5f87",
    "id":            "#767676",
    "name":          "#e0e0e0",
    "name.selected": "#ffffff bold",
    "cursor":        "#00afff bold",
    "divider":       "#2a2a2a",
})
 
 
def _rating_style(rating: int) -> str:
    if not rating:         return "class:rating.gray"
    if rating <= 1200:     return "class:rating.green"
    if rating <= 1600:     return "class:rating.cyan"
    if rating <= 2000:     return "class:rating.yellow"
    if rating <= 2400:     return "class:rating.orange"
    return                        "class:rating.red"
 
 
def _rating_label(rating: int) -> str:
    if not rating: return "  —  "
    return f"{rating:>4} "
 
 
def _difficulty(rating: int) -> str:
    if not rating:     return ""
    if rating <= 1000: return "★☆☆☆☆"
    if rating <= 1400: return "★★☆☆☆"
    if rating <= 1800: return "★★★☆☆"
    if rating <= 2200: return "★★★★☆"
    return                    "★★★★★"
 
 
# ---------------------------------------------------------------------------
# Explorer class
# ---------------------------------------------------------------------------
 
class CFExplore:
 
    def __init__(self):
        self.all_problems = []
        self.filtered     = []
        self.index        = 0
 
    # ------------------------------------------------------------------
    # Load
    # ------------------------------------------------------------------
 
    def load(self):
        problems = get_problems()
        self.all_problems = [
            {
                "id":     f"{p['contestId']}{p['index']}",
                "name":   p["name"],
                "rating": p.get("rating", 0),
                "tags":   p.get("tags", []),
            }
            for p in problems
        ]
        self.filtered = self.all_problems[:]
 
    # ------------------------------------------------------------------
    # Render  →  FormattedText
    # ------------------------------------------------------------------
 
    def render(self, window: int = 30) -> FormattedText:
        total  = len(self.filtered)
        start  = max(0, min(self.index - window // 2, total - window))
        end    = min(start + window, total)
 
        tokens = []
 
        for i in range(start, end):
            p      = self.filtered[i]
            sel    = i == self.index
            rating = p["rating"]
            tags   = p["tags"][:3]          # show max 3 tags
            tag_str = "  " + "  ".join(f"#{t}" for t in tags) if tags else ""
 
            # cursor
            tokens.append(("class:cursor",  "▶ " if sel else "  "))
 
            # problem id
            tokens.append(("class:id",      f"{p['id']:<8}"))
 
            # name
            name_style = "class:name.selected" if sel else "class:name"
            tokens.append((name_style,       f"{p['name']:<45}"))
 
            # rating
            tokens.append((_rating_style(rating), _rating_label(rating)))
 
            # difficulty stars
            tokens.append((_rating_style(rating), f"  {_difficulty(rating)}"))
 
            # tags
            tokens.append(("class:tag",     tag_str))
 
            tokens.append(("",              "\n"))
 
        return FormattedText(tokens)
 
    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------
 
    def run(self, initial_query: str | None = None, no_cache: bool = False):
        self.load()
 
        # ── Widgets ──────────────────────────────────────────────────────
        search = TextArea(height=1, prompt="  🔍 Search: ", style="bold")
 
        results_control = FormattedTextControl(
            text=lambda: self.render(),
            focusable=False,
        )
        results_window = Window(
            content=results_control,
            dont_extend_height=False,
        )
 
        total_label = FormattedTextControl(
            text=lambda: FormattedText([
                ("class:header",
                 f"  CF Explorer — {len(self.filtered):,} / {len(self.all_problems):,} problems  "),
            ])
        )
        header = Window(content=total_label, height=1)
 
        status_control = FormattedTextControl(
            text=lambda: FormattedText([
                ("", f"  ↑↓ navigate  Enter open  Ctrl-C quit  —  {self.index + 1}/{len(self.filtered)}  "),
            ])
        )
        status = Window(content=status_control, height=1)
 
        # ── Key bindings ─────────────────────────────────────────────────
        kb = KeyBindings()
 
        def _refresh(_=None):
            query = search.text.strip().lower()
            if not query:
                self.filtered = self.all_problems
            else:
                self.filtered = sorted(
                    self.all_problems,
                    key=lambda p: fuzz.partial_ratio(
                        query,
                        p["name"] + " " + " ".join(p["tags"])
                    ),
                    reverse=True,
                )[:300]
            self.index = 0
 
        search.buffer.on_text_changed += _refresh
 
        @kb.add("down")
        def _(event):
            if self.index < len(self.filtered) - 1:
                self.index += 1
 
        @kb.add("up")
        def _(event):
            if self.index > 0:
                self.index -= 1
 
        @kb.add("enter")
        def _(event):
            if not self.filtered:
                return
            event.app.exit(result=self.filtered[self.index]["id"])
 
        @kb.add("c-c")
        def _(event):
            event.app.exit()
 
        # ── Layout ───────────────────────────────────────────────────────
        app = Application(
            layout=Layout(HSplit([header, search, results_window, status])),
            key_bindings=kb,
            style=UI_STYLE,
            full_screen=True,
            mouse_support=True,
        )
 
        if initial_query:
            search.text = initial_query
        else:
            _refresh()
 
        chosen_id = app.run()
 
        if chosen_id:
            from cf_tool.core import resolve_problem
            from cf_tool.formatter import print_problem, print_error
            try:
                parsed = resolve_problem(chosen_id, no_cache=no_cache)
                print_problem(parsed)
            except Exception as e:
                print_error(str(e))