from sqlmodel import Session
import typer
from crawler.crawler import crawl
from models.models import Post
from database.database import create_db_and_tables, engine


def main(file: str):
    create_db_and_tables()
    with Session(engine) as session:
        crawl(session, file)


if __name__ == "__main__":
    typer.run(main)
