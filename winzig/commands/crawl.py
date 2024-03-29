import asyncio
import click
from sqlalchemy.ext.asyncio import AsyncSession
from winzig.crawler import crawl_from_feeds, crawl_links
from winzig.tf_idf import recalculate_tf_idf
from winzig.management import get_feeds_from_csv, get_posts_from_csv, remove_empty_feeds


@click.group(
    invoke_without_command=True,
    help="Crawl and extract content from feeds and posts. If no subcommand is provided, it automatically crawls previously saved feeds by default.",
)
@click.pass_context
def crawl(ctx):
    if ctx.invoked_subcommand is None:
        asyncio.run(_crawl_feeds(ctx.obj["engine"], [], None, False, True))


@click.command(
    name="feeds",
    help="Crawl and extract content from the posts of the specified feeds.",
)
@click.option(
    "-f",
    "--file",
    type=click.File(),
    default=None,
    help="Path to the file containing feed sources. If empty, previous feeds added to the database will be used.",
)
@click.option(
    "-m",
    "--max",
    type=int,
    default=None,
    help="Maximum number of posts to crawl from each feed.",
)
@click.option(
    "-p",
    "--prune",
    type=bool,
    is_flag=True,
    show_default=True,
    default=False,
    help="Remove feeds without any posts associated from the database after crawling.",
)
@click.option(
    "--fetch/--no-fetch",
    type=bool,
    is_flag=True,
    show_default=True,
    default=True,
    help="Toggle to enable or disable fetching content.",
)
@click.argument("urls", nargs=-1)
@click.pass_context
def crawl_feeds(ctx, file, urls, max, prune, fetch):
    feed_urls = []

    if file:
        if file.name.endswith(".csv"):
            feed_urls = get_feeds_from_csv(file)
        else:
            feed_urls = file.read().splitlines()

    if urls:
        feed_urls.extend(urls)

    asyncio.run(_crawl_feeds(ctx.obj["engine"], feed_urls, max, prune, fetch))


async def _crawl_feeds(engine, urls: list, max: int | None, prune: bool, fetch: bool):
    async with AsyncSession(engine) as session:
        if fetch:
            await crawl_from_feeds(session, urls, max)
            await recalculate_tf_idf(session)

        if prune:
            await remove_empty_feeds(session)


@click.command(
    name="posts",
    help="Crawl and extract content from the posts specified in a file.",
)
@click.option(
    "-f",
    "--file",
    type=click.File(),
    help="Path to the file containing the links to crawl.",
)
@click.argument("urls", nargs=-1)
@click.pass_context
def crawl_posts(ctx, file, urls):
    post_urls = []

    if file:
        if file.name.endswith(".csv"):
            post_urls = get_posts_from_csv(file)
        else:
            post_urls = file.read().splitlines()

    if urls:
        post_urls.extend(urls)

    asyncio.run(_crawl_posts(ctx.obj["engine"], post_urls))


async def _crawl_posts(engine, urls: list):
    async with AsyncSession(engine) as session:
        await crawl_links(session, urls)
        await recalculate_tf_idf(session)


crawl.add_command(crawl_posts)
crawl.add_command(crawl_feeds)
