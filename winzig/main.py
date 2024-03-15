import logging
import click
from winzig.database import create_db_and_tables, get_engine
from winzig.config import Config
from winzig.commands import crawl_links, search_links, start_tui

logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S %z",
)


@click.group()
@click.pass_context
def cli(ctx):
    if ctx.obj is None:
        ctx.obj = {}

    engine = get_engine(Config().sqlite_url)
    create_db_and_tables(engine)
    ctx.obj["engine"] = engine


cli.add_command(crawl_links)
cli.add_command(search_links)
cli.add_command(start_tui)

if __name__ == "__main__":
    cli()
