from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    "sqlite:///./database.sqlite3",
    connect_args={"check_same_thread": False}
)

Session = sessionmaker(
    engine,
    autocommit=False,
    autoflush=False
)