import asyncio
import click
from sqlalchemy.ext.asyncio import AsyncSession

from winzig.management import (
    export_feeds_to_txt,
    export_feeds_to_csv,
    export_feeds_to_json,
)


@click.group(
    invoke_without_command=True,
    help="Export feeds to a CSV file called 'feeds.csv' in the current directory.",
)
@click.pass_context
def export(ctx):
    if ctx.invoked_subcommand is None:
        asyncio.run(_export_feeds(ctx.obj["engine"], "csv", "feeds"))


@click.command(
    name="feeds",
    help="Export feeds to a specified format (Plain text, CSV or JSON).",
)
@click.option(
    "--format",
    type=click.Choice(
        ["txt", "csv", "json"],
        case_sensitive=False,
    ),
    show_default=True,
    default="txt",
    help="Specify the output format (Plain text, CSV or JSON).",
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
        elif format == "json":
            if output == "feeds":
                output = "feeds.json"

            await export_feeds_to_json(session, output)


export.add_command(export_feeds)
