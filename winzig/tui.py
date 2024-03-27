from textual import work
from textual.app import App, ComposeResult
from textual.containers import Grid, VerticalScroll
from textual.validation import Number
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
        yield Static(
            f"{self.content[:self.MAX_CONTENT_LENGTH] + "..." if len(self.content) > self.MAX_CONTENT_LENGTH else self.content}"
        )


class TuiApp(App):
    def __init__(self, session, k1, b, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session
        self.search_engine = SearchEngine(self.session, k1=k1, b=b)

    TITLE = "winzig"
    CSS_PATH = "./tui.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit application"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, name="winzig")
        yield Footer()
        with Grid(classes="form"):
            yield Input(placeholder="Search", type="text", classes="query")
            yield Input(
                placeholder="10",
                value="10",
                type="integer",
                classes="number_results",
                validators=[
                    Number(minimum=1, maximum=100),
                ],
                validate_on=["changed"],
            )

        with VerticalScroll():
            pass

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        if message.value:
            query = self.query_one(".query").value
            number_of_results = int(self.query_one(".number_results").value)
            self.search(query, number_of_results)
        else:
            self.clear_search_results()

    async def on_input_changed(self, _: Input.Changed) -> None:
        self.clear_search_results()

    @work(exclusive=True)
    async def search(self, query: str, n: int) -> None:
        results_container = self.query_one("VerticalScroll")
        results_container.loading = True

        search_results = await self.search_engine.search(query)
        search_results = get_top_urls(search_results, n)

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
        results_container.loading = False
