from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base
from config import SQLALCHEMY_DATABASE_URL

from .models import (
    User as UserModel,
    Teacher as TeacherModel,
    Practice as PracticeModel,
    UserPractice as UserPracticeModel,
    UserType
)


engine = create_engine(SQLALCHEMY_DATABASE_URL)
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
session = Session()


__all__ = (
    "session",
    "UserModel",
    "TeacherModel",
    "PracticeModel",
    "UserPracticeModel",
    "UserType"
)
