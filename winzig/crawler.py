import asyncio
from collections import Counter
from itertools import batched
import httpx
import feedparser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from selectolax.parser import HTMLParser
from winzig.models import Feed, Occurrence, Post
from winzig.utils import normalize_text
from winzig.console import console

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-GB,en;q=0.6",
}


async def fetch_content(client: httpx.AsyncClient, url: str) -> bytes | None:
    try:
        async with client.stream("GET", url) as response:
            if response.status_code >= 400:
                console.log(
                    f"[red bold]Error[/red bold]: Bad status from '{url}': {response.status_code}"
                )
                return None

            return await response.aread()
    except httpx.HTTPError:
        console.log(f"[red bold]Error[/red bold]: Got HTTP error from '{url}'")
        return None
    except ValueError as e:
        console.log(f"[red bold]Error[/red bold]: Failed to fetch '{url}': {e}")
        return None


def clean_content(html: bytes) -> str:
    tree = HTMLParser(html)
    for tag in tree.css(
        "script, style, link, noscript, object, img, embed, iframe, svg, canvas, form, audio, video"
    ):
        tag.decompose()
    text = "".join(node.text(deep=True) for node in tree.css("main"))
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split(" "))
    cleaned_text = " ".join(chunk for chunk in chunks if chunk)

    return cleaned_text


def is_feed(url: str) -> bool:
    try:
        feed = feedparser.parse(url)
        return True if feed.version else False
    except Exception as e:
        console.log(f"[red bold]Error[/red bold]: Parsing feed '{url}': {e}")
        return False


async def get_posts_from_feed(
    session: AsyncSession, feed_id: int, url: str, max: int | None
) -> list[str]:
    try:
        feed = feedparser.parse(url)
        statement = select(Post).where(Post.feed_id == feed_id)
        results = await session.execute(statement)
        results = results.scalars()
        posts_db_urls = {post.url for post in results}

        if max:
            return [
                entry.link
                for entry in feed.entries[:max]
                if entry.link not in posts_db_urls
            ]
        else:
            return [
                entry.link for entry in feed.entries if entry.link not in posts_db_urls
            ]
    except Exception as e:
        console.log(f"[red bold]Error[/red bold]: Parsing feed '{url}': {e}")
        return []


async def process_post(
    session: AsyncSession,
    client: httpx.AsyncClient,
    feed: Feed | None,
    url: str,
) -> None:
    try:
        response_text = await fetch_content(client, url)
        if not response_text:
            return None
    except Exception as e:
        console.log(
            f"[red bold]Error[/red bold]: Failed to extract content from '{url}': {e}"
        )
        return None

    try:
        cleaned_content = clean_content(response_text)
        if not cleaned_content:
            return
    except Exception as e:
        console.log(
            f"[red bold]Error[/red bold]: Failed to clean content from '{url}': {e}"
        )
        return None

    post = Post(
        url=url,
        content=cleaned_content,
        feed=feed,
        length=len(cleaned_content),
    )
    session.add(post)

    words = Counter(normalize_text(post.content).split(" "))
    occurrences = [
        Occurrence(word=word, count=count, post=post)
        for word, count in words.items()
        if len(word) > 2
    ]
    session.add_all(occurrences)


async def process_feed(session: AsyncSession, url: str) -> None:
    if not is_feed(url):
        console.log(
            f"[bold red]ERROR[/bold red]: URL '{url}' doesn't seem to be a valid RSS feed"
        )
        return None

    session.add(Feed(url=url))
    console.log(f"[bold green]SUCCESS[/bold green]: New feed '{url}' added")


async def check_feeds_urls(session: AsyncSession, urls: list[str]) -> None:
    tasks = []
    for url in urls:
        url = url.strip()
        feed = await session.execute(select(Feed).where(Feed.url == url))
        feed = feed.scalar()
        if not feed:
            tasks.append(process_feed(session, url))

    with console.status("Processing feeds...", spinner="earth"):
        await asyncio.gather(*tasks)
        await session.commit()

    console.log("[green bold]SUCCESS[/green bold]: Feeds processed")


async def crawl_links(session: AsyncSession, urls: list[str], batch_size: int = 20):
    if len(urls) == 0:
        console.log("[red bold]Error[/red bold]: No URLs received")
        return

    post_urls = []
    for url in urls:
        url = url.strip()
        post = await session.execute(select(Post).where(Post.url == url))
        post = post.scalar()
        if not post:
            post_urls.append(url)

    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        with console.status("Fetching posts...", spinner="earth") as status:
            for batch in batched(post_urls, batch_size):
                tasks = [process_post(session, client, None, url) for url in batch]

                status.update("Fetching posts...")
                await asyncio.gather(*tasks)
                await session.commit()

        console.log("[green bold]SUCCESS[/green bold]: Posts fetched")


async def crawl_from_feeds(
    session: AsyncSession,
    urls: list[str],
    max: int | None = None,
):
    if len(urls) > 0:
        await check_feeds_urls(session, urls)

    feeds = await session.execute(select(Feed))
    feeds = feeds.scalars().all()
    if not feeds:
        console.log("[red]Error[/red]: No feeds found!")
        return

    async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
        with console.status("Fetching posts...", spinner="earth") as status:
            for idx, feed in enumerate(feeds):
                posts = await get_posts_from_feed(session, feed.id, feed.url, max)
                tasks = [process_post(session, client, feed, post) for post in posts]

                status.update(
                    f"[bold][{idx + 1}/{len(feeds)}][/bold] Fetching posts from '{feed.url}'"
                )
                await asyncio.gather(*tasks)

        await session.commit()
        console.log("[green bold]SUCCESS[/green bold]: Posts fetched")
