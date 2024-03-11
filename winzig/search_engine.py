from collections import defaultdict
from math import log
from winzig.utils import normalize_text, update_url_scores


class SearchEngine:
    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self._idx: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self._docs: dict[str, str] = {}
        self.k1 = k1
        self.b = b

    @property
    def post(self) -> list[str]:
        return list(self._docs.keys())

    @property
    def num_of_docs(self) -> int:
        return len(self._docs)

    @property
    def avdl(self) -> float:
        if not hasattr(self, "_avdl"):
            self._avdl = (
                sum(self.num_of_docs for _ in self._docs.values()) / self.num_of_docs
            )
        return self._avdl

    def idf(self, kw: str) -> float:
        n_kw = len(self.get_urls(kw))
        return log((self.num_of_docs - n_kw + 0.5) / (n_kw + 0.5) + 1)

    def bm25(self, kw: str) -> dict[str, float]:
        result = {}
        idf_score = self.idf(kw)
        avldl = self.avdl
        for url, freq in self.get_urls(kw).items():
            numerator = freq * (self.k1 + 1)
            denominator = freq + self.k1 * (
                1 - self.b + self.b * len(self._docs[url]) / avldl
            )

            result[url] = idf_score * numerator / denominator
        return result

    def search(self, query: str) -> dict[str, float]:
        keywords = normalize_text(query).split(" ")
        url_scores: dict[str, float] = {}
        for kw in keywords:
            kw_urls_scores = self.bm25(kw)
            url_scores = update_url_scores(url_scores, kw_urls_scores)

        return url_scores

    def index(self, url: str, content: str) -> None:
        self._docs[url] = content
        words = normalize_text(content).split(" ")
        for word in words:
            self._idx[word][url] += 1
        if hasattr(self, "_avdl"):
            del self._avdl

    def bulk_index(self, docs: list[tuple[str, str]]):
        for url, content in docs:
            self.index(url, content)

    def get_urls(self, kw: str) -> dict[str, int]:
        normalized_kw = normalize_text(kw)
        return self._idx[normalized_kw]
