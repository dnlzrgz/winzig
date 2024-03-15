from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Header, Footer, Input, Markdown
from winzig.utils import get_top_urls


class TuiApp(App):
    def __init__(self, search_engine, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.search_engine = search_engine

    CSS_PATH = "./tui.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit application"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, name="winzig", id="header")
        yield Footer()
        yield Input(placeholder="Search", type="text", id="input")
        with VerticalScroll(id="results-container"):
            yield Markdown(id="results")

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        if message.value:
            self.search(query=message.value)
        else:
            self.query_one("#results", Markdown).update("")

    @work(exclusive=True)
    async def search(self, query: str) -> None:
        search_results = self.search_engine.search(query)
        search_results = get_top_urls(search_results, 10)

        markdown = self.make_word_markdown(search_results)
        self.query_one("#results", Markdown).update(markdown)

    def make_word_markdown(self, results: dict[str, int]) -> str:
        lines = []
        for result in results:
            lines.append(f"- [{result}]({result})")

        return "\n".join(lines)
