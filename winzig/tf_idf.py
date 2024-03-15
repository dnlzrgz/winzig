import asyncio
import logging
from math import log
from collections import Counter
from sqlmodel import Session, select
from sqlalchemy import delete
from winzig.models import Post, Term, Occurrence
from winzig.utils import normalize_text


async def get_occurrences_per_post(session: Session, post: Post):
    terms = Counter(normalize_text(post.content).split(" "))
    for term in terms:
        statement = select(Term).where(Term.term == term)
        term_db = session.exec(statement).first()
        if not term_db:
            continue

        occurrence = Occurrence(term_id=term_db.id, post_id=post.id)
        session.add(occurrence)


async def get_terms_freq(content: str, term_freq: Counter, lock: asyncio.Lock) -> None:
    normalized_content = normalize_text(content)
    terms = normalized_content.split()
    async with lock:
        term_freq.update(terms)


async def calculate_score(session: Session, total_posts: int, term: str, freq: int):
    score = log(total_posts / (freq + 1))
    term_db = Term(term=term, score=score, frequency=freq)
    session.add(term_db)


async def calculate_tf_idfs(session: Session):
    logging.info("Getting posts from the database")
    posts_db = session.exec(select(Post)).all()
    if not posts_db:
        print("No posts found.")
        return None

    logging.info("Getting terms frequency")
    tasks = []
    # TODO: check methods to solve tf-idf memory consumption
    terms_freq = Counter()
    lock = asyncio.Lock()
    for post in posts_db:
        task = get_terms_freq(post.content, terms_freq, lock)
        tasks.append(task)

    await asyncio.gather(*tasks)

    logging.info("Calculating TF-IDF")
    total_posts = len(posts_db)
    tasks = []
    for term, freq in terms_freq.items():
        tasks.append(calculate_score(session, total_posts, term, freq))

    await asyncio.gather(*tasks)
    session.commit()

    logging.info("Getting occurences of terms per post")
    tasks = []
    for post in posts_db:
        tasks.append(get_occurrences_per_post(session, post))

    await asyncio.gather(*tasks)
    session.commit()


async def recalculate_tf_idf(session: Session):
    statement = delete(Term)
    session.exec(statement)
    session.commit()
    logging.info("Previous TF-IDF scores deleted.")

    statement = delete(Occurrence)
    session.exec(statement)
    session.commit()
    logging.info("Previous terms occurrences deleted.")

    logging.info("Recalculating TF-IDF scores and getting occurrences.")
    await calculate_tf_idfs(session)
