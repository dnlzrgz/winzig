import asyncio
from pathlib import Path
import click
from sqlalchemy.ext.asyncio import AsyncSession
from winzig.crawler import crawl_from_feeds, crawl_links
from winzig.tf_idf import recalculate_tf_idf


@click.group(
    invoke_without_command=True,
    help="Crawl and extract content from feeds and posts. If no subcommand is provided, it automatically crawls previously saved feeds by default.",
)
@click.pass_context
def crawl(ctx):
    if ctx.invoked_subcommand is None:
        asyncio.run(_crawl_feeds(ctx.obj["engine"], None))


@click.command(
    name="feeds",
    help="Crawl and extract content from the posts of the specified feeds.",
)
@click.option(
    "-f",
    "--file",
    type=Path,
    default=None,
    help="Path to the file containing feed sources. If empty, previous feeds added to the database will be used.",
)
@click.pass_context
def crawl_feeds(ctx, file: Path):
    asyncio.run(_crawl_feeds(ctx.obj["engine"], file))


async def _crawl_feeds(engine, file: Path | None):
    async with AsyncSession(engine) as session:
        await crawl_from_feeds(session, file)
        await recalculate_tf_idf(session)


@click.command(
    name="posts",
    help="Crawl and extract content from the posts specified in a file.",
)
@click.option(
    "-f",
    "--file",
    type=Path,
    help="Path to the file containing the links to crawl.",
)
@click.pass_context
def crawl_posts(ctx, file: Path):
    asyncio.run(_crawl_posts(ctx.obj["engine"], file))


async def _crawl_posts(engine, file: Path):
    async with AsyncSession(engine) as session:
        await crawl_links(session, file)
        await recalculate_tf_idf(session)


crawl.add_command(crawl_posts)
crawl.add_command(crawl_feeds)
