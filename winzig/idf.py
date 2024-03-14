import asyncio
import logging
from math import log
from collections import Counter
from sqlmodel import Session, select
from sqlalchemy import delete
from winzig.models import Post, IDF
from winzig.utils import normalize_text


def get_terms_freq_from_content(content: str) -> dict[str, int]:
    normalized_content = normalize_text(content)
    terms = normalized_content.split()
    return Counter(terms)


async def calculate_idf_score(session: Session, total_posts: int, idf: IDF):
    score = log(total_posts / (idf.frequency + 1))
    idf.score = score
    session.add(idf)


async def calculate_idfs(session: Session):
    posts_db = session.exec(select(Post)).all()
    total_posts = len(posts_db)
    if posts_db is None:
        # TODO: Exception
        return None

    count = 1
    for post in posts_db:
        logging.info(f"Calculating IDF for post {count}/{total_posts}")
        terms_freq = get_terms_freq_from_content(post.content)
        for term, freq in terms_freq.items():
            statement = select(IDF).where(IDF.term == term)
            idf = session.exec(statement).first()
            if idf is not None:
                idf.frequency += freq
            else:
                idf = IDF(term=term, frequency=freq)

            session.add(idf)

        session.commit()
        count += 1

    logging.info("Calculating IDF scores")
    idfs_db = session.exec(select(IDF)).all()
    tasks = [calculate_idf_score(session, total_posts, idf) for idf in idfs_db]
    await asyncio.gather(*tasks)

    session.commit()


async def recalculate_idfs(session: Session):
    logging.info("Recalculating IDF scores.")
    statement = delete(IDF)
    session.exec(statement)
    session.commit()
    logging.info("Previous IDF scores deleted.")

    await calculate_idfs(session)
