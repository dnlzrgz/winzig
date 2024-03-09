import httpx
import feedparser
from selectolax.parser import HTMLParser
from rich.progress import track
from models.models import Post


def fetch_content(client, url):
    try:
        r = client.get(url)
        return r
    except Exception as e:
        print(f"There was an error while fetching content from '{url}': {e}")
        return httpx.Response(status_code=404)


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
        print(f"There was an error while extracting content from '{url}': {e}")


def get_posts_from_feed(feed_url):
    try:
        feed = feedparser.parse(feed_url)
        return [entry.link for entry in feed.entries]
    except Exception as e:
        print(f"There was an error while parsing feed {feed_url}: {e}")
        return []


def crawl(session, feed_file):
    with open(feed_file, "r") as f:
        feeds_urls = [line.strip() for line in f]

    client = httpx.Client()
    try:
        for feed_url in feeds_urls:
            posts = get_posts_from_feed(feed_url)

            for post in track(posts, description=f"fetching posts from {feed_url}..."):
                response = fetch_content(client, post)
                if response.status_code != 200:
                    response.close()
                    continue

                cleaned_content = clean_content(post, response.text)
                post = Post(
                    url=post,
                    content=cleaned_content,
                )
                session.add(post)

                response.close()

            session.commit()
    finally:
        client.close()
