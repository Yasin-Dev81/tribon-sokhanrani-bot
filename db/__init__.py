from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base
from config import SQLALCHEMY_DATABASE_URL

from .models import (
    User as UserModel,
    Teacher as TeacherModel,
    Practice as PracticeModel,
    UserPractice as UserPracticeModel,
    UserType as UserTypeModel,
)


IS_SQLITE = SQLALCHEMY_DATABASE_URL.startswith("sqlite")
IS_MYSQL = SQLALCHEMY_DATABASE_URL.startswith("mysql")


if IS_SQLITE:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
elif IS_MYSQL:
    print("hiiiiiiiiiiiiiii")
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        pool_size=10,
        max_overflow=30,
        pool_recycle=3600,
        pool_timeout=10,
    )
else:
    raise ValueError("Unsupported database URL")

Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
session = Session()

__all__ = (
    "session",
    "UserModel",
    "TeacherModel",
    "PracticeModel",
    "UserPracticeModel",
    "UserTypeModel",
    "Base"
)
