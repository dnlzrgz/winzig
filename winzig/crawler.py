import asyncio
from collections import Counter
import aiohttp
import feedparser
import tldextract
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


async def fetch_content(client: aiohttp.ClientSession, url: str) -> str | None:
    try:
        async with client.get(url) as resp:
            if resp.status >= 400:
                console.log(
                    f"[red bold]ERROR[/red bold]: Bad status from '{url}': {resp.status}"
                )
                return None

            return await resp.text()
    except aiohttp.ClientError as e:
        console.log(f"[red bold]ERROR[/red bold]: Failed to fetch '{url}': {e}")
        return None


def clean_content(html: str) -> str:
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


async def get_posts_from_feed(
    session: AsyncSession,
    client: aiohttp.ClientSession,
    feed: Feed,
    max: int | None,
) -> list[str]:
    try:
        resp_text = await fetch_content(client, feed.url)
        if not resp_text:
            console.log(
                f"[bold red]ERROR[/bold red]: Failed to get posts from '{feed.url}'"
            )
            return []

        d = feedparser.parse(resp_text)
        statement = select(Post).where(Post.feed_id == feed.id)
        results = await session.execute(statement)
        results = results.scalars()
        posts_db_urls = {post.url for post in results}

        if max:
            return [
                entry.link
                for entry in d.entries[:max]
                if entry.link not in posts_db_urls
            ]
        else:
            return [
                entry.link for entry in d.entries if entry.link not in posts_db_urls
            ]
    except Exception as e:
        console.log(f"[red bold]ERROR[/red bold]: Parsing feed '{feed.url}': {e}")
        return []


async def process_post(
    session: AsyncSession,
    client: aiohttp.ClientSession,
    feed: Feed | None,
    url: str,
) -> None:
    try:
        resp_text = await fetch_content(client, url)
        if not resp_text:
            return None
    except Exception as e:
        console.log(
            f"[red bold]ERROR[/red bold]: Failed to extract content from '{url}': {e}"
        )
        return None

    try:
        cleaned_content = clean_content(resp_text)
        if not cleaned_content:
            return
    except Exception as e:
        console.log(
            f"[red bold]ERROR[/red bold]: Failed to clean content from '{url}': {e}"
        )
        return None

    post = Post(
        url=url,
        domain=tldextract.extract(url).domain,
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


async def save_feed(
    session: AsyncSession, client: aiohttp.ClientSession, url: str
) -> None:
    resp_text = await fetch_content(client, url)
    if not resp_text:
        console.log(
            f"[bold red]ERROR[/bold red]: URL '{url}' doesn't seem to be a valid RSS feed"
        )
        return None

    d = feedparser.parse(resp_text)
    feed_title = d.feed.get("title", None)
    feed_description = d.feed.get("description", None)

    session.add(
        Feed(
            url=url,
            title=feed_title,
            description=feed_description,
        )
    )
    console.log(f"[bold green]SUCCESS[/bold green]: New feed '{url}' added")


async def add_new_feeds(
    session: AsyncSession,
    client: aiohttp.ClientSession,
    urls: list[str],
) -> None:
    with console.status("Processing feeds...", spinner="earth"):
        tasks = []
        for url in urls:
            url = url.strip()
            feed = await session.execute(select(Feed).where(Feed.url == url))
            feed = feed.scalar()
            if feed:
                continue

            tasks.append(save_feed(session, client, url))

        if not tasks:
            console.log("[yellow bold]WARNING[/yellow bold]: No new feeds found")
        else:
            console.log(
                f"[green bold]SUCCESS[/green bold]: Found {len(tasks)} new feeds"
            )

        await asyncio.gather(*tasks)

    await session.commit()
    console.log("[green bold]SUCCESS[/green bold]: Feeds processed")


async def crawl_links(session: AsyncSession, urls: list[str]):
    if len(urls) == 0:
        console.log("[red bold]ERROR[/red bold]: No URLs received")
        return

    post_urls = []
    for url in urls:
        url = url.strip()
        post = await session.execute(select(Post).where(Post.url == url))
        post = post.scalar()
        if not post:
            post_urls.append(url)

    async with aiohttp.ClientSession(headers=headers) as client:
        with console.status("Fetching posts...", spinner="earth") as status:
            tasks = [process_post(session, client, None, url) for url in post_urls]

            status.update("Fetching posts...")
            await asyncio.gather(*tasks)

        await session.commit()
        console.log("[green bold]SUCCESS[/green bold]: Posts fetched")


async def crawl_from_feeds(
    session: AsyncSession,
    urls: list[str],
    max: int | None = None,
):
    async with aiohttp.ClientSession(headers=headers) as client:
        if len(urls) > 0:
            await add_new_feeds(session, client, urls)

        feeds = await session.execute(select(Feed))
        feeds = feeds.scalars().all()
        if not feeds:
            console.log("[red]ERROR[/red]: No feeds found!")
            return

        with console.status("Fetching posts...", spinner="earth") as status:
            for idx, feed in enumerate(feeds):
                posts = await get_posts_from_feed(session, client, feed, max)
                if not posts:
                    continue

                tasks = [process_post(session, client, feed, post) for post in posts]

                status.update(
                    f"[bold][{idx + 1}/{len(feeds)}][/bold] Fetching posts from '{feed.url}'"
                )
                await asyncio.gather(*tasks)

        await session.commit()
        console.log("[green bold]SUCCESS[/green bold]: Posts fetched")
