import asyncio
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
    type=float,
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
