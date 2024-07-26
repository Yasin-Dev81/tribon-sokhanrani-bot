from config import SQLALCHEMY_DATABASE_URL
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine


# Event listener for disconnections
@event.listens_for(Engine, "engine_connect")
def handle_disconnect(connection, branch):
    if branch:
        return

    def ping_connection(connection):
        try:
            connection.scalar("SELECT 1")
        except Exception:
            connection.invalidate()
            connection.scalar("SELECT 1")

    connection.connection._checkout = ping_connection


IS_SQLITE = SQLALCHEMY_DATABASE_URL.startswith("sqlite")

if IS_SQLITE:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=10,
        max_overflow=30,
        pool_recycle=28000,
        pool_timeout=10,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()
session = SessionLocal()
