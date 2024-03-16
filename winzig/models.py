from typing import List
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.ext.asyncio import AsyncAttrs


class Base(AsyncAttrs, DeclarativeBase):
    pass


class Feed(Base):
    __tablename__ = "feeds"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(index=True)

    posts: Mapped[List["Post"]] = relationship(back_populates="feed")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(index=True)
    content: Mapped[str]

    feed_id: Mapped[int] = mapped_column(ForeignKey("feeds.id"))
    feed: Mapped[Feed] = relationship(back_populates="posts")

    occurrences: Mapped[List["Occurrence"]] = relationship(back_populates="post")


class Term(Base):
    __tablename__ = "terms"

    id: Mapped[int] = mapped_column(primary_key=True)
    term: Mapped[str] = mapped_column(index=True)
    score: Mapped[float] = mapped_column(default=0.0)
    frequency: Mapped[int] = mapped_column(default=0)

    occurrences: Mapped[List["Occurrence"]] = relationship(back_populates="term")


class Occurrence(Base):
    __tablename__ = "occurrences"

    id: Mapped[int] = mapped_column(primary_key=True)

    term_id: Mapped[int] = mapped_column(ForeignKey("terms.id"))
    term: Mapped[Term] = relationship(back_populates="occurrences")

    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    post: Mapped[Post] = relationship(back_populates="occurrences")
