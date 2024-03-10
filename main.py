import asyncio
from functools import wraps
import typer
from sqlmodel import Session
from rich.progress import Progress, SpinnerColumn, TextColumn
from crawler.crawler import crawl
from models.models import Post
from database.database import create_db_and_tables, engine


def typer_async(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper


@typer_async
async def main(file: str):
    create_db_and_tables()
    progress = Progress(
        SpinnerColumn(spinner_name="dots"),
        TextColumn("[progress.description]{task.description}"),
    )
    task = progress.add_task(
        description="[cyan]Crawling...",
        total=1,
    )
    with Session(engine) as session:
        with progress:
            await crawl(session, file)
            progress.update(task, completed=1)


if __name__ == "__main__":
    typer.run(main)
