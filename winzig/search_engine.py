from functools import cached_property
from sqlmodel import Session, select
from winzig.models import Occurrence, Term, Post
from winzig.utils import normalize_text, update_url_scores


class SearchEngine:
    def __init__(
        self,
        session: Session,
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.k1 = k1
        self.b = b
        self.session = session

    @cached_property
    def avdl(self) -> float:
        posts_db = self.session.exec(select(Post)).all()
        total_content_length = sum(len(post.content) for post in posts_db)
        return total_content_length / len(posts_db)

    def get_tf_idf(self, kw: str) -> float:
        statement = select(Term).where(Term.term == kw)
        idf_db = self.session.exec(statement).first()
        if not idf_db:
            return 0.0

        return idf_db.score

    def bm25(self, kw: str) -> dict[str, float]:
        results = {}
        tf_idf_score = self.get_tf_idf(kw)
        avldl = self.avdl
        occurrences = self.session.exec(
            select(Occurrence, Post).join(Post).join(Term).where(Term.term == kw)
        ).all()
        for occurrence, post in occurrences:
            url = occurrence.post.url
            term_db = self.session.exec(select(Term).where(Term.term == kw)).first()
            term_freq = term_db.frequency
            numerator = term_freq * (self.k1 + 1)
            denominator = term_freq + self.k1 * (
                1 - self.b + self.b * len(post.content) / avldl
            )

            results[url] = tf_idf_score * numerator / denominator
        return results

    def search(self, query: str) -> dict[str, float]:
        keywords = normalize_text(query).split(" ")
        url_scores: dict[str, float] = {}
        for kw in keywords:
            kw_urls_scores = self.bm25(kw)
            url_scores = update_url_scores(url_scores, kw_urls_scores)

        return url_scores
