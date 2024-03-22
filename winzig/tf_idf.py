from math import log
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from winzig.models import Post, Keyword, Occurrence
from winzig.console import console


async def calculate_tf_idfs(session: AsyncSession):
    statement = select(func.count()).select_from(Post)
    result = await session.execute(statement)
    total_posts = result.scalar()
    if not total_posts:
        console.log("[red bold]Error[/red bold]: No posts found")
        return

    statement = select(Occurrence.word, func.sum(Occurrence.count)).group_by(
        Occurrence.word
    )
    results = await session.execute(statement)
    keywords = [
        Keyword(keyword=row[0], score=log(total_posts / (row[1] + 1)), frequency=row[1])
        for row in results
    ]
    session.add_all(keywords)
    await session.commit()


async def delete_old_scores(session: AsyncSession):
    statement = delete(Keyword)
    await session.execute(statement)
    await session.commit()


async def recalculate_tf_idf(session: AsyncSession):
    console.log("[yellow bold]WARNING[/yellow bold]: Deleting previous TF-IDF scores")
    await delete_old_scores(session)

    console.log("[green bold]SUCCESS[/green bold]: Previous TF-IDF scores deleted")
    with console.status("Calculating tf-idf scores...", spinner="earth"):
        await calculate_tf_idfs(session)

    console.log("[green bold]SUCCESS[/green bold]: TF-IDF scores calculated")
