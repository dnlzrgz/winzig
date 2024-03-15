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


async def calculate_score(session: Session, total_posts: int, term: str, freq: int):
    score = log(total_posts / (freq + 1))
    idf = IDF(term=term, score=score, frequency=freq)
    session.add(idf)


async def calculate_idfs(session: Session):
    posts_db = session.exec(select(Post)).all()
    total_posts = len(posts_db)
    if posts_db is None:
        print("No posts found.")
        return None

    logging.info("Calculating terms frequency")
    tasks = []
    # TODO: check methods to solve tf-idf memory consumption
    terms_freq = Counter()
    lock = asyncio.Lock()
    for post in posts_db:
        task = get_terms_freq(post.content, terms_freq, lock)
        tasks.append(task)

    await asyncio.gather(*tasks)

    logging.info("Calculating IDF scores")
    tasks = []
    for term, freq in terms_freq.items():
        tasks.append(calculate_score(session, total_posts, term, freq))

    await asyncio.gather(*tasks)
    session.commit()


async def recalculate_idfs(session: Session):
    statement = delete(IDF)
    session.exec(statement)
    session.commit()
    logging.info("Previous IDF scores deleted.")

    logging.info("Recalculating IDF scores.")
    await calculate_idfs(session)
