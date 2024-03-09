from sqlmodel import SQLModel, create_engine

sqlite_file_name = "sqlite.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

connect_args = {"check_same_thread": False}
engine = create_engine(
    sqlite_url,
    echo=False,
    connect_args=connect_args,
)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
