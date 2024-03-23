import asyncio
import click
from winzig.config import Config
from winzig.database import create_db_and_tables, get_engine
from winzig.commands import crawl, fetch, search, start_tui


@click.group()
@click.pass_context
def cli(ctx):
    if ctx.obj is None:
        ctx.obj = {}

    engine = get_engine(Config().sqlite_url)
    asyncio.run(create_db_and_tables(engine))
    ctx.obj["engine"] = engine


cli.add_command(crawl)
cli.add_command(fetch)
cli.add_command(search)
cli.add_command(start_tui)

if __name__ == "__main__":
    cli()
