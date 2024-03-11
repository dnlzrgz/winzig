import asyncio
from pathlib import Path
from typing import Annotated
import typer
from sqlmodel import Session, select
from sqlalchemy import exc
from rich.console import Console
from winzig.database import create_db_and_tables, engine
from winzig.models import Post
from winzig.crawler import crawl
from winzig.search_engine import SearchEngine
from winzig.utils import get_top_urls

app = typer.Typer()
console = Console()


@app.command(
    name="crawl",
    help="Crawl links from a file and store them for later search.",
)
def crawl_links(
    file: Annotated[
        Path,
        typer.Argument(
            help="Path to the file containing URLs to crawl.",
            default=None,
        ),
    ]
):
    create_db_and_tables()

    with Session(engine) as session:
        asyncio.run(crawl(session, file))


@app.command(
    name="search",
    help="Search for links based on a query.",
)
def search(
    query: str = typer.Argument(..., help="Query to search for."),
    k1: float = typer.Argument(1.5, help="Term saturation."),
    b: float = typer.Argument(
        0.75,
        help="Effect of document length on the relevance score.",
    ),
    n: int = typer.Argument(5, help="Maximum number of search results to display."),
):
    create_db_and_tables()

    search_engine = SearchEngine(k1=k1, b=b)
    with Session(engine) as session:
        posts = []
        try:
            stmt = select(Post)
            posts = session.exec(stmt).all()
        except exc.SQLAlchemyError as e:
            print(f"Problem with the database: {e}")
            return

        data = [(post.url, post.normalized_content) for post in posts]
        search_engine.bulk_index(data)

    search_results = search_engine.search(query)
    search_results = get_top_urls(search_results, n)

    console.rule("Search results:", style="bold")
    for result in search_results:
        console.print(result, style="", justify="left", overflow="fold")


if __name__ == "__main__":
    app()
