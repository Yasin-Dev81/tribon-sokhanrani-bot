from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


Base = declarative_base()


class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    tell_id = Column(Integer, nullable=True)
    phone_number = Column(String)
    chat_id = Column(Integer, nullable=True)
    name = Column(String, nullable=True)

class Teacher(Base):
    __tablename__ = 'teacher'
    id = Column(Integer, primary_key=True)
    tell_id = Column(Integer)
    chat_id = Column(Integer, nullable=True)
    name = Column(String, nullable=True)

class Practice(Base):
    __tablename__ = 'practice'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    caption = Column(Text)
    end_date = Column(DateTime)
    start_date = Column(DateTime)

class UserPractice(Base):
    __tablename__ = 'user_practice'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    user_caption = Column(Text, nullable=True)
    file_link = Column(Text)
    teacher_id = Column(Integer, ForeignKey('teacher.id'), nullable=True)
    practice_id = Column(Integer, ForeignKey('practice.id'))
    teacher_caption = Column(Text, nullable=True)

    user = relationship("User")
    teacher = relationship("Teacher")
    practice = relationship("Practice")
