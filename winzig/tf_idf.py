import asyncio
import logging
from math import log
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from winzig.models import Post, Keyword, Occurrence


async def calculate_score(
    session: AsyncSession,
    kw: str,
    total_posts: int,
    frequency: int,
):
    results = await session.execute(select(Occurrence).filter(Occurrence.word == kw))
    occurrences = results.scalars().all()
    score = log(total_posts / (frequency + 1))
    keyword = Keyword(
        keyword=kw,
        score=score,
        frequency=frequency,
        occurrences=occurrences,
    )

    session.add(keyword)


async def calculate_tf_idfs(session: AsyncSession):
    statement = select(func.count()).select_from(Post)
    result = await session.execute(statement)
    total_posts = result.scalar()
    if not total_posts:
        print("No posts found.")
        return

    statement = select(Occurrence.word, func.sum(Occurrence.count)).group_by(
        Occurrence.word
    )
    results = await session.execute(statement)
    tasks = [calculate_score(session, row[0], total_posts, row[1]) for row in results]
    await asyncio.gather(*tasks)
    await session.commit()


async def delete_old_scores(session: AsyncSession):
    statement = delete(Keyword)
    await session.execute(statement)
    await session.commit()


async def recalculate_tf_idf(session: AsyncSession):
    logging.debug("Deleting previous TF-IDF scores.")
    await delete_old_scores(session)
    logging.debug("Previous TF-IDF scores deleted.")
    logging.info("Recalculating TF-IDF scores.")
    await calculate_tf_idfs(session)
