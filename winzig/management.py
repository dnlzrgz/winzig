from sqlalchemy import delete
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
