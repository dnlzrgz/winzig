import asyncio
from pathlib import Path
import typer
from sqlmodel import Session, select
from winzig.database import create_db_and_tables, engine
from winzig.models import Post
from winzig.crawler import crawl
from winzig.search_engine import SearchEngine
from winzig.utils import get_top_urls

app = typer.Typer()


@app.command(name="crawl")
def crawl_links(file: Path):
    with Session(engine) as session:
        asyncio.run(crawl(session, file))


@app.command()
def search(query: str):
    search_engine = SearchEngine()
    with Session(engine) as session:
        statement = select(Post)
        results = session.exec(statement).all()
        data = [(post.url, post.content) for post in results]
        search_engine.bulk_index(data)

    results = search_engine.search(query)
    results = get_top_urls(results, n=5)
    for result in results:
        print(result)


if __name__ == "__main__":
    create_db_and_tables()
    app()
