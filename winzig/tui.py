from sqlalchemy import select
from textual import work
from textual.reactive import reactive
from textual.app import App, ComposeResult
from textual.containers import Grid, VerticalScroll
from textual.validation import Number
from textual.widgets import Button, Header, Footer, Input, RadioSet, Static, RadioButton
from winzig.models import Post
from winzig.search_engine import SearchEngine
from winzig.utils import get_top_urls


class ResultCard(Static):
    def __init__(self, url, content, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.MAX_CONTENT_LENGTH = 512

        self.url = url
        self.content = content

    def compose(self) -> ComposeResult:
        yield Static(f"[b]{self.url}[/b]")
        yield Static(
            f"{self.content[:self.MAX_CONTENT_LENGTH] + "..." if len(self.content) > self.MAX_CONTENT_LENGTH else self.content}"
        )


class TuiApp(App):
    query_search = reactive('')
    number_results = reactive(10)
    variant=reactive('BM11')

    def __init__(self, session, k1, b, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = session
        self.search_engine = SearchEngine(self.session, filters={}, k1=k1, b=b)

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
                value='10',
                type="integer",
                classes="number_results",
                validators=[
                    Number(minimum=1, maximum=100),
                ],
                validate_on=["changed"],
            )
            with RadioSet(id="variants"):
                yield RadioButton("BM25", value=True)
                yield RadioButton("BM11")
                yield RadioButton("BM15")

        with VerticalScroll():
            pass

    async def on_input_submitted(self, _: Input.Submitted) -> None:
        if self.query_search:
            self.search()
        else:
            self.clear_search_results()

    async def on_input_changed(self, _: Input.Changed) -> None:
        self.clear_search_results()
        self.query_search = self.query_one(".query").value
        try:
            value = self.query_one(".number_results").value
            if value:
                self.number_of_results = int(value)
            else:
                self.number_of_results = 0
        except (ValueError, AttributeError):
            self.number_of_results = 0

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        self.variant = event.pressed.label

    @work(exclusive=True)
    async def search(self) -> None:
        results_container = self.query_one("VerticalScroll")
        results_container.loading = True

        if self.variant == 'BM25':
            self.search_engine.b = 0.75
        elif self.variant == 'BM15':
            self.search_engine.b = 0
        else:
            self.search_engine.b = 1

        search_results = await self.search_engine.search(self.query_search)
        search_results = get_top_urls(search_results, self.number_results)

        self.clear_search_results()
        await self.mount_search_results(search_results)

    def clear_search_results(self) -> None:
        result_cards = self.query("ResultCard")
        for card in result_cards:
            card.remove()

    async def mount_search_results(self, search_results: dict[str, float]) -> None:
        results_container = self.query_one("VerticalScroll")
        for result, _  in search_results.items():
            content = await self.session.execute(
                select(Post.content).where(Post.url == result)
            )
            results_container.mount(
                ResultCard(
                    result,
                    content.scalar(),
                )
            )
            results_container.loading = False
