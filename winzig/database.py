from sqlmodel import SQLModel, create_engine


def get_engine(sqlite_url: str, echo: bool = False):
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        sqlite_url,
        echo=echo,
        connect_args=connect_args,
    )

    return engine


def create_db_and_tables(engine):
    SQLModel.metadata.create_all(engine)
