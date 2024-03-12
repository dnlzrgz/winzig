import asyncio
from pathlib import Path
import logging
import httpx
import feedparser
from sqlmodel import Session, select
from selectolax.parser import HTMLParser
from winzig.models import Feed, Post


async def fetch_content(client: httpx.AsyncClient, url: str) -> bytes | None:
    logging.debug(f"Fetching content from '{url}'")
    try:
        async with client.stream("GET", url) as response:
            if response.status_code != 200:
                logging.error(
                    f"Got bad status code from '{url}' - {response.status_code}"
                )
                return None

            return await response.aread()
    except httpx.HTTPError as e:
        logging.error(f"Got HTTP error for '{url}': {e}")
        return None


def clean_content(url: str, html: bytes) -> str | None:
    logging.debug(f"Cleaning content from {url}")

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
        logging.error(f"Error cleaning content from '{url}': {e}")
        return None


async def get_posts_from_feed(feed_url: str) -> list[str]:
    logging.debug(f"Getting posts from '{feed_url}'")

    try:
        feed = feedparser.parse(feed_url)
        return [entry.link for entry in feed.entries if entry.link]
    except Exception as e:
        logging.error(f"Error parsing feed '{feed_url}': {e}")
        return []


async def process_post(
    session: Session,
    client: httpx.AsyncClient,
    feed: Feed,
    post: str,
) -> None:
    logging.debug(f"Processing post '{post}'")

    stmt = select(Post).where(Post.url == post)
    post_db = session.exec(stmt).first()
    if post_db:
        logging.debug(f"Post '{post}' is already in the database")
        return

    response_text = await fetch_content(client, post)
    if response_text:
        cleaned_content = clean_content(post, response_text)
        if cleaned_content:
            post_obj = Post(
                url=post,
                content=cleaned_content,
                feed=feed,
            )

            logging.debug(f"Saving post '{post}' to the database")
            session.add(post_obj)


async def crawl(session: Session, feed_file: Path | None = None):
    if feed_file:
        with open(feed_file, "r") as f:
            for line in f:
                url = line.strip()
                feed_db = session.exec(select(Feed).where(Feed.url == url)).first()
                if not feed_db:
                    feed = Feed(url=url)
                    session.add(feed)

                session.commit()

    feeds = session.exec(select(Feed)).all()
    if not feeds:
        print("No feeds found. Please add feeds before crawling.")
        return

    async with httpx.AsyncClient() as client:
        for feed in feeds:
            posts = await get_posts_from_feed(feed.url)
            tasks = [process_post(session, client, feed, post) for post in posts]

            await asyncio.gather(*tasks)
            session.commit()
