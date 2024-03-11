from typing import Optional
from sqlmodel import Field, SQLModel


class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = Field(index=True)
    content: str
