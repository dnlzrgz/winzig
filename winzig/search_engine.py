from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from winzig.models import Post, Occurrence, Keyword
from winzig.utils import update_url_scores, normalize_text
from winzig.console import console


class SearchEngine:
    def __init__(
        self,
        session: AsyncSession,
        filters: dict[str, str] = {},
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.session = session
        self.filters = filters
        self.k1 = k1
        self.b = b

        self._avdl = None

    async def avdl(self) -> float | None:
        if self._avdl is not None:
            return self._avdl

        statement = select(func.count()).select_from(Post)
        result = await self.session.execute(statement)
        total_posts = result.scalar()
        if not total_posts:
            console.log("[red bold]Error[/red bold]: No posts found")
            return None

        statement = select(func.sum(Post.length)).select_from(Post)
        result = await self.session.execute(statement)
        total_length = result.scalar()
        if not total_length:
            console.log(
                "[red bold]Error[/red bold]: Something went wrong while calculating the total length of the posts."
            )
            return None

        self._avdl = total_length / total_posts
        return self._avdl

    async def get_kw_score(self, kw: str) -> float:
        statement = select(Keyword).where(Keyword.keyword == kw)
        results = await self.session.execute(statement)
        keyword = results.scalar()
        if not keyword:
            return 0.0

        return keyword.score

    async def bm25(self, kw: str) -> dict[str, float]:
        avdl = await self.avdl()
        statement = select(Occurrence, Post).join(Post).where(Occurrence.word == kw)
        if "domain" in self.filters:
            domain_filters = self.filters["domain"].split(",")
            conditions = [Post.domain == domain.strip() for domain in domain_filters]
            statement = statement.filter(or_(*conditions))

        results = await self.session.execute(statement)
        occurrences = results.fetchall()

        search_results = {}
        for occurrence, post in occurrences:
            kw_score = await self.get_kw_score(kw)
            numerator = occurrence.count * (self.k1 + 1)
            denominator = occurrence.count + self.k1 * (
                1 - self.b + self.b * (post.length / avdl)
            )

            score = kw_score * numerator / denominator
            search_results[post.url] = score

        return search_results

    async def search(self, query: str) -> dict[str, float]:
        keywords = normalize_text(query).split(" ")
        url_scores: dict[str, float] = {}
        for kw in keywords:
            kw_urls_scores = await self.bm25(kw)
            url_scores = update_url_scores(url_scores, kw_urls_scores)

        return url_scores
