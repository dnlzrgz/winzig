import asyncio
from pathlib import Path
import logging
import httpx
import feedparser
from sqlmodel import Session, select
from selectolax.parser import HTMLParser
from winzig.models import Feed, Post

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-GB,en;q=0.6",
}


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
    except ValueError as e:
        logging.error(f"Got exception while fetching'{url}': {e}")
        return None


def clean_content(url: str, html: bytes) -> str | None:
    logging.debug(f"Cleaning content from {url}")

    try:
        tree = HTMLParser(html)
        for tag in tree.css(
            "script, style, link, noscript, object, img, embed, iframe, svg, canvas, form, audio, video"
        ):
            tag.decompose()
        text = "".join(node.text(deep=True) for node in tree.css("body"))
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split(" "))
        cleaned_text = " ".join(chunk for chunk in chunks if chunk)

        return cleaned_text
    except Exception as e:
        logging.error(f"Error cleaning content from '{url}': {e}")
        return None


async def get_posts_from_feed(session: Session, id: int, url: str) -> list[str]:
    logging.debug(f"Getting posts from feed '{url}'")

    try:
        feed = feedparser.parse(url)
        statement = select(Post).where(Post.feed_id == id)
        results = session.exec(statement).all()
        posts_db_urls = {post.url for post in results}

        return [entry.link for entry in feed.entries if entry.link not in posts_db_urls]
    except Exception as e:
        logging.error(f"Error parsing feed '{url}': {e}")
        return []


async def process_post(
    session: Session,
    client: httpx.AsyncClient,
    feed: Feed,
    post: str,
) -> None:
    logging.debug(f"Processing post '{post}'")

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


def save_feeds_from_file(session: Session, feed_file: Path | None):
    if not feed_file:
        logging.debug("No file specified.")
        return

    if not feed_file.exists():
        print(f"File {feed_file} does not exist. Please specify a correct file.")
        return

    logging.debug(f"Reading file {feed_file}")
    with open(feed_file, "r") as f:
        for line in f:
            url = line.strip()
            feed_db = session.exec(select(Feed).where(Feed.url == url)).first()
            if not feed_db:
                feed = Feed(url=url)
                session.add(feed)

        session.commit()


async def crawl(session: Session, feed_file: Path | None = None):
    save_feeds_from_file(session, feed_file)

    logging.debug("Loading feeds from the database.")
    feeds = session.exec(select(Feed)).all()
    if not feeds:
        print("No feeds found. Please add feeds before crawling.")
        return

    async with httpx.AsyncClient(headers=headers) as client:
        for feed in feeds:
            posts = await get_posts_from_feed(session, feed.id, feed.url)
            tasks = [process_post(session, client, feed, post) for post in posts]

            await asyncio.gather(*tasks)
            session.commit()
