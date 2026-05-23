"""
explore.py — Stable interactive explorer (fixed: Enter shows details in-UI)
"""

from prompt_toolkit import Application
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import HSplit
from prompt_toolkit.widgets import TextArea
from prompt_toolkit.key_binding import KeyBindings

from rapidfuzz import fuzz
from .cache_problems import get_problems

class CFExplore:

    def __init__(self):
        self.all_problems = []
        self.filtered = []
        self.index = 0
        self._viewing_detail = False   # track whether we're in detail view

    # ------------------------------------------------------------------
    # Load problems
    # ------------------------------------------------------------------

    def load(self):
        problems = get_problems()

        self.all_problems = [
            {
                "id": f"{p['contestId']}{p['index']}",
                "name": p["name"],
                "rating": p.get("rating", 0),
                "tags": p.get("tags", []),
            }
            for p in problems
        ]

        self.filtered = self.all_problems[:50]

    # ------------------------------------------------------------------
    # Format list
    # ------------------------------------------------------------------

    def render(self, window: int = 20):
        lines = []
        total = len(self.filtered)
    
        # Calculate scroll window start so cursor stays visible
        start = max(0, min(self.index - window // 2, total - window))
        end   = min(start + window, total)
    
        for i in range(start, end):
            p      = self.filtered[i]
            prefix = "➤ " if i == self.index else "  "
            lines.append(f"{prefix}{p['id']}  {p['name']}")
    
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self, initial_query: str | None = None):
        self.load()
    
        search = TextArea(height=1, prompt="Search: ")
        status = TextArea(height=1, focusable=False)
        results = TextArea(focusable=False)
    
        def set_status(msg: str):
            status.text = msg
    
        def update():
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
                )[:200]
    
            self.index = 0
            self._viewing_detail = False
            results.text = self.render()
            set_status("↑↓ navigate  Enter: open  ESC: back  Ctrl-C: quit")
    
        search.buffer.on_text_changed += lambda _: update()

        # ------------------------------------------------------------------
        # Key bindings
        # ------------------------------------------------------------------

        kb = KeyBindings()

        @kb.add("down")
        def _(event):
            if self._viewing_detail:
                return
            if self.index < len(self.filtered) - 1:
                self.index += 1
                results.text = self.render()

        @kb.add("up")
        def _(event):
            if self._viewing_detail:
                return
            if self.index > 0:
                self.index -= 1
                results.text = self.render()

        @kb.add("enter")
        def _(event):
            if not self.filtered:
                return
        
            problem = self.filtered[self.index]
        
            event.app.exit(result=problem["id"])

        @kb.add("escape")
        def _(event):
            # Go back to list view from detail view
            if self._viewing_detail:
                self._viewing_detail = False
                results.text = self.render()
                set_status("↑↓ navigate  Enter: open  Ctrl-C: quit")

        @kb.add("c-c")
        def _(event):
            event.app.exit()

        # ------------------------------------------------------------------
        # Layout
        # ------------------------------------------------------------------

        layout = Layout(HSplit([search, results, status]))
        app = Application(layout=layout, key_bindings=kb, full_screen=True)


        if initial_query:
            search.text = initial_query   # triggers on_text_changed → update()
        else:
            update()
    
        chosen_id = app.run()
    
        if chosen_id:
            from cf_tool.core import resolve_problem
            from cf_tool.formatter import print_problem
            try:
                parsed = resolve_problem(chosen_id)
                print_problem(parsed)
            except Exception as e:
                from cf_tool.formatter import print_error
                print_error(str(e))