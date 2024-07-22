from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, BigInteger
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class UserType(Base):
    __tablename__ = "user_type"
    id = Column(Integer, primary_key=True)
    name = Column(String(50), nullable=False, unique=True)


class User(Base):
    __tablename__ = "user"
    id = Column(Integer, primary_key=True)
    tell_id = Column(BigInteger, nullable=True)
    phone_number = Column(String(13), nullable=False, unique=True)
    chat_id = Column(BigInteger, nullable=True)
    name = Column(String(100), nullable=True)
    user_type_id = Column(Integer, ForeignKey("user_type.id"))

    user_type = relationship("UserType")


class Teacher(Base):
    __tablename__ = "teacher"
    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), nullable=False, unique=True)
    tell_id = Column(BigInteger, nullable=True)
    chat_id = Column(BigInteger, nullable=True)
    name = Column(String(100), nullable=True)


class Practice(Base):
    __tablename__ = "practice"
    id = Column(Integer, primary_key=True)
    title = Column(String(100), nullable=False)
    caption = Column(Text)
    end_date = Column(DateTime)
    start_date = Column(DateTime)
    user_type_id = Column(Integer, ForeignKey("user_type.id"))

    user_type = relationship("UserType")


class UserPractice(Base):
    __tablename__ = "user_practice"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    user_caption = Column(Text, nullable=True)
    file_link = Column(Text, nullable=False)
    teacher_id = Column(Integer, ForeignKey("teacher.id"), nullable=True)
    practice_id = Column(Integer, ForeignKey("practice.id"))
    teacher_caption = Column(Text, nullable=True)
    teacher_voice_link = Column(Text, nullable=True)
    teacher_video_link = Column(Text, nullable=True)

    user = relationship("User")
    teacher = relationship("Teacher")
    practice = relationship("Practice")
