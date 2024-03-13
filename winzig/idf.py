from collections import defaultdict
import logging
from math import log
from sqlmodel import Session, func, select
from sqlalchemy import delete
from winzig.models import Post, IDF
from winzig.utils import normalize_text


def get_terms_from_content(content: str) -> dict[str, int]:
    normalized_content = normalize_text(content)

    terms = normalized_content.split()
    terms_count = defaultdict(int)
    for term in terms:
        terms_count[term] += 1

    return terms_count


def calculate_idf(session: Session, total_docs: int, batch_size: int):
    current_offset = 0
    while current_offset < total_docs:
        limit = min(batch_size, total_docs - current_offset)
        statement = select(Post).offset(current_offset).limit(limit)
        posts_db = session.exec(statement).all()

        doc_freqs = defaultdict(int)
        for post in posts_db:
            terms = get_terms_from_content(post.content)
            for term in terms:
                doc_freqs[term] += 1

        for term, freq in doc_freqs.items():
            score = log(total_docs / (freq + 1))
            statement = select(IDF).where(IDF.term == term)
            idf_db = session.exec(statement).first()
            if idf_db is not None:
                logging.info(f"IDF score for term '{term}' already in the database.")
                continue

            idf = IDF(term=term, score=score)
            session.add(idf)
            logging.info(f"Added IDF score for term '{term}'")

        session.commit()
        current_offset += batch_size


def recalculate_idf(session: Session, batch_size: int = 100):
    logging.info("Recalculating IDF scores.")
    statement = delete(IDF)
    session.exec(statement)
    session.commit()
    logging.info("Previous IDF scores deleted.")

    statement = select(func.count()).select_from(Post)
    total_docs = session.scalar(statement)
    if total_docs == 0 or total_docs is None:
        # TODO: Exception
        return None

    calculate_idf(session, total_docs, batch_size)
