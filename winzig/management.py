import csv
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from winzig.models import Feed, Post
from winzig.console import console


async def remove_empty_feeds(session: AsyncSession) -> None:
    try:
        with console.status("Searching for empty feeds...", spinner="earth"):
            statement = delete(Feed).where(~Feed.posts.any())
            results = await session.execute(statement)
            if results.rowcount:
                console.log(
                    f"[green bold]SUCCESS[/green bold]: {results.rowcount} empty feeds removed"
                )
            else:
                console.log("[yellow bold]WARNING[/yellow bold]: No feeds removed")

            await session.commit()
    except Exception as e:
        console.log(f"[red bold]ERROR[/red bold]: Failed to remove empty feeds: {e}")


async def export_feeds_to_txt(session: AsyncSession, output: str) -> None:
    try:
        with console.status("Exporting feeds to plain text...", spinner="earth"):
            results = await session.execute(select(Feed))
            feeds = results.scalars().all()

            with open(output, "w", encoding="utf-8") as f:
                for feed in feeds:
                    f.write(feed.url + "\n")

        console.log(f"[green bold]SUCCESS[/green bold]: Feeds exported to {output}")
    except Exception as e:
        console.log(f"[red bold]ERROR[/red bold]: Failed to export feeds: {e}")


async def export_feeds_to_csv(session: AsyncSession, output: str) -> None:
    try:
        with console.status("Exporting feeds to CSV...", spinner="earth"):
            results = await session.execute(select(Feed))
            feeds = results.scalars().all()

            with open(output, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["title", "url"])
                for feed in feeds:
                    writer.writerow([f"{feed.title}", feed.url])

        console.log(f"[green bold]SUCCESS[/green bold]: Feeds exported to {output}")
    except Exception as e:
        console.log(f"[red bold]ERROR[/red bold]: Failed to export feeds: {e}")


def get_feeds_from_csv(file) -> list[str]:
    with file as csvfile:
        reader = csv.reader(csvfile)
        next(reader)

        feeds = [row[1] for row in reader]
        return feeds


async def export_posts_to_txt(session: AsyncSession, output: str) -> None:
    try:
        with console.status("Exporting posts to plain text...", spinner="earth"):
            results = await session.execute(select(Post))
            posts = results.scalars().all()

            with open(output, "w", encoding="utf-8") as f:
                for post in posts:
                    f.write(post.url + "\n")

        console.log(f"[green bold]SUCCESS[/green bold]: Posts exported to {output}")
    except Exception as e:
        console.log(f"[red bold]ERROR[/red bold]: Failed to export posts: {e}")


async def export_posts_to_csv(session: AsyncSession, output: str) -> None:
    try:
        with console.status("Exporting posts to CSV...", spinner="earth"):
            results = await session.execute(select(Post))
            posts = results.scalars().all()

            with open(output, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["domain", "url"])
                for post in posts:
                    writer.writerow([post.domain, post.url])

        console.log(f"[green bold]SUCCESS[/green bold]: Posts exported to {output}")
    except Exception as e:
        console.log(f"[red bold]ERROR[/red bold]: Failed to export posts: {e}")


def get_posts_from_csv(file) -> list[str]:
    with file as csvfile:
        reader = csv.reader(csvfile)
        next(reader)

        posts = [row[1] for row in reader]
        return posts
