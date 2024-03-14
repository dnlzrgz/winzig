from typing import List, Optional
from sqlmodel import Field, SQLModel, Relationship


class Feed(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True)

    posts: List["Post"] = Relationship(back_populates="feed")


class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True)
    content: str

    feed_id: Optional[int] = Field(default=None, foreign_key="feed.id")
    feed: Optional[Feed] = Relationship(back_populates="posts")


class IDF(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    term: str = Field(index=True)
    score: float = Field(default=0.0)
    frequency: int = Field(default=0)
