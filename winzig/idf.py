import asyncio
import logging
from math import log
from collections import Counter
from sqlmodel import Session, select
from sqlalchemy import delete
from winzig.models import Post, IDF
from winzig.utils import normalize_text


async def get_terms_freq(content: str, term_freq: Counter, lock: asyncio.Lock) -> None:
    normalized_content = normalize_text(content)
    terms = normalized_content.split()
    async with lock:
        term_freq.update(terms)


async def calculate_idf_score(session: Session, total_posts: int, idf: IDF):
    score = log(total_posts / (idf.frequency + 1))
    idf.score = score
    session.add(idf)


async def calculate_idfs(session: Session):
    posts_db = session.exec(select(Post)).all()
    total_posts = len(posts_db)
    if posts_db is None:
        print("No posts found.")
        return None

    tasks = []
    terms_freq = Counter()
    lock = asyncio.Lock()
    for post in posts_db:
        logging.info("Calculating terms frequency")
        task = get_terms_freq(post.content, terms_freq, lock)
        tasks.append(task)

    await asyncio.gather(*tasks)

    for term, freq in terms_freq.items():
        logging.info(f"Adding term {term} to the database")
        idf = IDF(term=term, frequency=freq)
        session.add(idf)

    session.commit()

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
