import asyncio
from pathlib import Path
import httpx
import feedparser
from sqlmodel import Session, select
from selectolax.parser import HTMLParser
from winzig.models import Post


async def fetch_content(client: httpx.AsyncClient, url: str) -> bytes | None:
    try:
        async with client.stream("GET", url) as response:
            return await response.aread()
    except httpx.HTTPError as e:
        print(f"HTTP error for '{url}' - {e}")
        return None


def clean_content(url: str, html: bytes) -> str | None:
    try:
        tree = HTMLParser(html)
        for tag in tree.css("script, style"):
            tag.decompose()
        text = "".join(node.text(deep=True) for node in tree.css("body"))
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split(" "))
        cleaned_text = " ".join(chunk for chunk in chunks if chunk)

        return cleaned_text
    except Exception as e:
        print(f"Error getting content from '{url}' - {e}")
        return None


async def get_posts_from_feed(feed_url: str) -> list[str]:
    try:
        feed = feedparser.parse(feed_url)
        return [entry.link for entry in feed.entries if entry.link]
    except Exception as e:
        print(f"Error parsing feed {feed_url} - {e}")
        return []


async def process_post(session: Session, client: httpx.AsyncClient, post: str) -> None:
    stmt = select(Post).where(Post.url == post)
    post_db = session.exec(stmt).first()
    if post_db:
        return

    response_text = await fetch_content(client, post)
    if response_text:
        cleaned_content = clean_content(post, response_text)
        if cleaned_content:
            post_obj = Post(
                url=post,
                content=cleaned_content,
            )

            session.add(post_obj)


async def crawl(session: Session, feed_file: Path):
    with open(feed_file, "r") as f:
        feeds_urls = [line.strip() for line in f]

    async with httpx.AsyncClient() as client:
        for feed_url in feeds_urls:
            posts = await get_posts_from_feed(feed_url)
            tasks = [process_post(session, client, post) for post in posts]

            await asyncio.gather(*tasks)
            session.commit()
