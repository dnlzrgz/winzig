import asyncio
import click
from sqlalchemy.ext.asyncio import AsyncSession

from winzig.management import (
    export_feeds_to_txt,
    export_feeds_to_csv,
    export_posts_to_txt,
    export_posts_to_csv,
)


@click.group(
    invoke_without_command=True,
    help="Export feeds and posts to plain text or CSV files. If no subcommand is provided, it exports the feeds to a CSV file called 'feeds.csv' in the current directory.",
)
@click.pass_context
def export(ctx):
    if ctx.invoked_subcommand is None:
        asyncio.run(_export_feeds(ctx.obj["engine"], "csv", "feeds"))


@click.command(
    name="feeds",
    help="Export feeds to a specified format (Plain text or CSV).",
)
@click.option(
    "--format",
    type=click.Choice(
        ["txt", "csv"],
        case_sensitive=False,
    ),
    show_default=True,
    default="txt",
    help="Specify the output format (Plain text or CSV).",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    default="feeds",
    help="Specify the path for the output file.",
)
@click.pass_context
def export_feeds(ctx, format: str, output: str):
    asyncio.run(_export_feeds(ctx.obj["engine"], format, output))


async def _export_feeds(engine, format: str, output: str):
    async with AsyncSession(engine) as session:
        if format == "txt":
            if output == "feeds":
                output = "feeds.txt"

            await export_feeds_to_txt(session, output)
        elif format == "csv":
            if output == "feeds":
                output = "feeds.csv"

            await export_feeds_to_csv(session, output)


@click.command(
    name="posts",
    help="Export posts to a specified format (Plain text or CSV).",
)
@click.option(
    "--format",
    type=click.Choice(
        ["txt", "csv"],
        case_sensitive=False,
    ),
    show_default=True,
    default="txt",
    help="Specify the output format (Plain text or CSV).",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(),
    default="posts",
    help="Specify the path for the output file.",
)
@click.pass_context
def export_posts(ctx, format: str, output: str):
    asyncio.run(_export_posts(ctx.obj["engine"], format, output))


async def _export_posts(engine, format: str, output: str):
    async with AsyncSession(engine) as session:
        if format == "txt":
            if output == "posts":
                output = "posts.txt"

            await export_posts_to_txt(session, output)
        elif format == "csv":
            if output == "posts":
                output = "posts.csv"

            await export_posts_to_csv(session, output)


export.add_command(export_feeds)
export.add_command(export_posts)
