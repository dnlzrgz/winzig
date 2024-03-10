import asyncio
import httpx
import feedparser
from sqlmodel import select
from selectolax.parser import HTMLParser
from winzig.models import Post


async def fetch_content(client, url):
    try:
        async with client.stream("GET", url) as response:
            if response.status_code != 200:
                return ""
            return await response.aread()
    except httpx.HTTPError as e:
        print(f"HTTP error for '{url}' - {e}")
        return ""


def clean_content(url, html):
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


async def get_posts_from_feed(feed_url):
    try:
        feed = feedparser.parse(feed_url)
        return [entry.link for entry in feed.entries]
    except Exception as e:
        print(f"Error parsing feed {feed_url} - {e}")
        return []


async def process_post(session, client, post):
    stmt = select(Post).where(Post.url == post)
    post_db = session.exec(stmt).first()
    if post_db:
        return

    response_text = await fetch_content(client, post)
    if response_text:
        cleaned_content = clean_content(post, response_text)
        post_obj = Post(
            url=post,
            content=cleaned_content,
        )
        session.add(post_obj)


async def crawl(session, feed_file):
    with open(feed_file, "r") as f:
        feeds_urls = [line.strip() for line in f]

    async with httpx.AsyncClient() as client:
        for feed_url in feeds_urls:
            posts = await get_posts_from_feed(feed_url)
            tasks = []
            for post in posts:
                tasks.append(process_post(session, client, post))

            await asyncio.gather(*tasks)
            session.commit()
