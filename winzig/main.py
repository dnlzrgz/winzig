import asyncio
import logging
from pathlib import Path
import click
from sqlmodel import Session, select
from sqlalchemy import exc
from winzig.idf import recalculate_idf
from winzig.models import Post
from winzig.database import create_db_and_tables, get_engine
from winzig.crawler import crawl
from winzig.search_engine import SearchEngine
from winzig.utils import get_top_urls
from winzig.config import Config

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S %z",
)

engine = get_engine(Config().sqlite_url)


@click.command(
    name="crawl",
    help="Crawl links.",
)
@click.option(
    "-f",
    "--file",
    type=Path,
    default=None,
    help="Path to the file containing the URLs to crawl. If this file is not provided, the crawler will load URLs from the database.",
    show_default=True,
)
@click.option(
    "--verbose",
    type=bool,
    is_flag=True,
    help="Enable verbose logging.",
    show_default=True,
)
def crawl_links(file: Path, verbose: bool):
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    with Session(engine) as session:
        asyncio.run(crawl(session, file))
        recalculate_idf(session)


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
def search_links(query: str, k1: float, b: float, n: int, verbose: bool):
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    with Session(engine) as session:
        search_engine = SearchEngine(session, k1=k1, b=b)
        posts = []
        try:
            stmt = select(Post)
            posts = session.exec(stmt).all()
        except exc.SQLAlchemyError as e:
            print(f"Problem with the database: {e}")
            return

        if len(posts) == 0:
            print(
                "No posts found in the database. You may need to crawl some links first."
            )
            return

        data = [(post.url, post.content) for post in posts]
        search_engine.bulk_index(data)

        search_results = search_engine.search(query)
        search_results = get_top_urls(search_results, n)

        for result in search_results:
            print(result)


@click.group()
def cli():
    create_db_and_tables(engine)


cli.add_command(crawl_links)
cli.add_command(search_links)

if __name__ == "__main__":
    cli()
