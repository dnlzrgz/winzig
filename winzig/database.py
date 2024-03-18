from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from winzig.models import Base


def get_engine(sqlite_url: str) -> AsyncEngine:
    connect_args = {"check_same_thread": False}
    engine = create_async_engine(
        sqlite_url,
        echo=False,
        future=True,
        connect_args=connect_args,
    )

    return engine


async def create_db_and_tables(engine):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
