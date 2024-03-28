import csv
import json
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from winzig.models import Feed
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
                writer.writerow(["id", "title", "url"])
                for feed in feeds:
                    writer.writerow([feed.id, f"{feed.title}", feed.url])

        console.log(f"[green bold]SUCCESS[/green bold]: Feeds exported to {output}")
    except Exception as e:
        console.log(f"[red bold]ERROR[/red bold]: Failed to export feeds: {e}")


async def export_feeds_to_json(session: AsyncSession, output: str):
    try:
        with console.status("Exporting feeds to JSON...", spinner="earth"):
            results = await session.execute(select(Feed))
            feeds = results.scalars().all()

            feed_data = [
                {"id": feed.id, "title": feed.title, "url": feed.url} for feed in feeds
            ]

            with open(output, "w", encoding="utf-8") as file:
                json.dump(feed_data, file, ensure_ascii=False, indent=4)

        console.log(f"[green bold]SUCCESS[/green bold]: Feeds exported to {output}")
    except Exception as e:
        console.log(f"[red bold]ERROR[/red bold]: Failed to export feeds: {e}")
