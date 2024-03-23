import asyncio
from pathlib import Path
import click
from sqlalchemy.ext.asyncio import AsyncSession
from winzig.crawler import crawl_from_feeds, crawl_links
from winzig.tf_idf import recalculate_tf_idf
from winzig.search_engine import SearchEngine
from winzig.utils import get_top_urls
from winzig.tui import TuiApp
from winzig.console import console


@click.command(
    name="crawl",
    help="Crawl links and store the contents of the posts found.",
)
@click.option(
    "-f",
    "--file",
    type=Path,
    default=None,
    help="Path to the file containing the URLs to crawl. If this file is not provided, the crawler will load URLs from the database.",
)
@click.pass_context
def crawl(ctx, file: Path):
    asyncio.run(_crawl_links(ctx.obj["engine"], file))


async def _crawl_links(engine, file: Path):
    async with AsyncSession(engine) as session:
        await crawl_from_feeds(session, file)
        await recalculate_tf_idf(session)


@click.command(
    name="fetch",
    help="Fetch links directly and store the contents.",
)
@click.option(
    "-f",
    "--file",
    type=Path,
    help="Path to the file containing the URLs to crawl.",
)
@click.pass_context
def fetch(ctx, file: Path):
    asyncio.run(_fetch_links(ctx.obj["engine"], file))


async def _fetch_links(engine, file: Path):
    async with AsyncSession(engine) as session:
        await crawl_links(session, file)
        await recalculate_tf_idf(session)


@click.command(
    name="tui",
    help="Start tui for search engine.",
)
@click.pass_context
def start_tui(ctx):
    asyncio.run(_start_tui(ctx.obj["engine"]))


async def _start_tui(engine):
    async with AsyncSession(engine) as session:
        search_engine = SearchEngine(session)
        tui_app = TuiApp(search_engine)
        await tui_app.run_async()


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
@click.pass_context
def search(ctx, query: str, k1: float, b: float, n: int):
    asyncio.run(_search(ctx.obj["engine"], query, k1, b, n))


async def _search(engine, query: str, k1: float, b: float, n: int):
    async with AsyncSession(engine) as session:
        search_engine = SearchEngine(session, k1=k1, b=b)
        search_results = await search_engine.search(query)
        search_results = get_top_urls(search_results, n)

        for result in search_results:
            console.print(f"- [green]{result}[/green]")
