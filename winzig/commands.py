import asyncio
import logging
from pathlib import Path
import click
from sqlalchemy.ext.asyncio import AsyncSession
from winzig.crawler import crawl
from winzig.search_engine import SearchEngine

# from winzig.tui import TuiApp
from winzig.utils import get_top_urls


@click.command(
    name="crawl",
    help="Crawl links and store results.",
)
@click.option(
    "-f",
    "--file",
    type=Path,
    default=None,
    help="Path to the file containing the URLs to crawl. If this file is not provided, the crawler will load URLs from the database.",
)
@click.option(
    "--verbose",
    type=bool,
    is_flag=True,
    help="Enable verbose logging.",
    show_default=True,
)
@click.pass_context
def crawl_links(ctx, file: Path, verbose: bool):
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    asyncio.run(_crawl_links(ctx.obj["engine"], file))


async def _crawl_links(engine, file: Path):
    async with AsyncSession(engine) as session:
        await crawl(session, file)
        # await recalculate_tf_idf(session)


@click.command(
    name="tui",
    help="Start tui for search engine.",
)
@click.pass_context
def start_tui(ctx):
    # with AsyncSession(ctx.obj["engine"]) as session:
    # search_engine = SearchEngine(session)
    # tui_app = TuiApp(search_engine)
    # tui_app.run()
    # TODO: pass engine, let TUI handle session.
    pass


@click.command(
    name="search",
    help="Search for links.",
)
@click.option(
    "-q",
    "--query",
    type=str,
    help="Query to search for.",
    prompt="Your search query",
    required=True,
)
@click.option(
    "--k1",
    type=float,
    default=1.5,
    help="Term saturation. Higher values favor the frequency of query terms in a document.",
    show_default=True,
)
@click.option(
    "--b",
    type=float,
    default=0.75,
    help="Effect of document length on the relevance score. Lower values favor shorter documents.",
    show_default=True,
)
@click.option(
    "-n",
    type=int,
    default=5,
    help="Maximum number of search results.",
    show_default=True,
)
@click.option(
    "--verbose",
    type=bool,
    is_flag=True,
    help="Enable verbose logging.",
    show_default=True,
)
@click.pass_context
def search_links(ctx, query: str, k1: float, b: float, n: int, verbose: bool):
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    asyncio.run(_search_links(ctx.obj["engine"], query, k1, b, n))


async def _search_links(engine, query: str, k1: float, b: float, n: int):
    async with AsyncSession(engine) as session:
        search_engine = SearchEngine(session, k1=k1, b=b)
        search_results = search_engine.search(query)
        search_results = get_top_urls(search_results, n)

        for result in search_results:
            print(result)
