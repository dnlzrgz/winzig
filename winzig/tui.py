from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Header, Footer, Input, Static
from sqlalchemy import select
from winzig.models import Post
from winzig.search_engine import SearchEngine
from winzig.utils import get_top_urls


class ResultCard(Static):
    def __init__(self, url, score, content, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.MAX_CONTENT_LENGTH = 512

        self.url = url
        self.score = score
        self.content = content

    def compose(self) -> ComposeResult:
        yield Static(f"[b]{self.url}[/b]")
        yield Static(f"{self.score}")
        yield Static(f"{self.content[:self.MAX_CONTENT_LENGTH] + "..." if len(self.content) > self.MAX_CONTENT_LENGTH else self.content}")


class TuiApp(App):
    def __init__(self, session, k1, b, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session
        self.search_engine = SearchEngine(self.session, k1=k1, b=b)

    CSS_PATH = "./tui.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit application"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, name="winzig", id="header")
        yield Footer()
        yield Input(placeholder="Search", type="text", id="search-terms")
        with VerticalScroll(id="results"):
            pass

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        if message.value:
            self.search(query=message.value)
        else:
            self.clear_search_results()

    @work(exclusive=True)
    async def search(self, query: str) -> None:
        search_results = await self.search_engine.search(query)
        search_results = get_top_urls(search_results, 10)

        self.clear_search_results()
        await self.mount_search_results(search_results)

    def clear_search_results(self) -> None:
        result_cards = self.query("ResultCard")
        for card in result_cards:
            card.remove()

    async def mount_search_results(self, search_results: dict[str, float]) -> None:
        results_container = self.query_one("VerticalScroll")
        for result, score in search_results.items():
            content = await self.session.execute(
                select(Post.content).where(Post.url == result)
            )
            results_container.mount(
                ResultCard(
                    result,
                    round(score, 2),
                    content.scalar(),
                )
            )
