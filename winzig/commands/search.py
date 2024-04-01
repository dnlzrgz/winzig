import asyncio
from typing import Tuple
import click
from sqlalchemy.ext.asyncio import AsyncSession
from winzig.search_engine import SearchEngine
from winzig.utils import get_top_urls
from winzig.console import console


@click.command(
    name="search",
    help="Search for links based on a given query.",
)
@click.option(
    "-q",
    "--query",
    type=str,
    help="Query string to search for.",
    prompt="Search query",
    required=True,
)
@click.option(
    "--k1",
    type=float,
    default=1.5,
    help="Term saturation factor. Higher values prioritize the frequency of query terms in a document.",
    show_default=True,
)
@click.option(
    "--b",
    type=click.FloatRange(0.0, 1.0),
    default=0.75,
    help="Length normalization factor. on the relevance score. Lower values favor shorter documents.",
    show_default=True,
)
@click.option(
    "-n",
    type=int,
    default=5,
    help="Maximum number of search results to display.",
    show_default=True,
)
@click.option(
    "--filter",
    "-f",
    type=str,
    multiple=True,
    help="Filter search results by 'key=value' pairs.",
)
@click.pass_context
def search(ctx, query: str, k1: float, b: float, n: int, filter: Tuple[str]):
    filters = {}
    for f in filter:
        key, value = f.split("=")
        filters[key] = value

    asyncio.run(_search(ctx.obj["engine"], query, k1, b, n, filters))


async def _search(
    engine,
    query: str,
    k1: float,
    b: float,
    n: int,
    filters: dict[str, str],
):
    async with AsyncSession(engine) as session:
        search_engine = SearchEngine(session, filters=filters, k1=k1, b=b)
        search_results = await search_engine.search(query)
        search_results = get_top_urls(search_results, n)

        for result in search_results:
            console.print(f"- [green]{result}[/green]")
