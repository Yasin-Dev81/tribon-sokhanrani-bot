from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.schema import PrimaryKeyConstraint, ForeignKeyConstraint
from sqlalchemy.sql import func
from sqlalchemy import types, Enum
from typing import NewType
from datetime import datetime
import enum

from config import TIME_ZONE


String100 = NewType("String100", str)
String50 = NewType("String50", str)
String13 = NewType("String13", str)
BigInteger = NewType("BigInteger", int)
CaptionText = NewType("CaptionText", str)
FileId = NewType("FileId", str)


class MediaType(enum.Enum):
    TEXT = "متن"
    PHOTO = "عکس"
    DOCUMENT = "فایل"
    VIDEO = "ویدئو"
    VOICE = "ویس"
    AUDIO = "فایل صوتی"
    VIDEO_NOTE = "ویدیو نوت (ویدیو مسیج)"


class UserLevel(enum.Enum):
    USER = "User"
    TEACHER = "Theacher"


class Base(DeclarativeBase):
    type_annotation_map = {
        String100: types.String(length=100),
        String50: types.String(length=50),
        String13: types.String(length=13),
        datetime: types.DateTime(timezone=True),
        MediaType: Enum(MediaType),
        UserLevel: Enum(UserLevel),
        BigInteger: types.BigInteger(),
        CaptionText: types.Text(length=4096),
        FileId: types.Text(length=100),
    }


class UserType(Base):
    __tablename__ = "user_type"
    __table_args__ = (PrimaryKeyConstraint("id", name="user_type_pk"),)

    id: Mapped[int]
    name: Mapped[String50]


class User(Base):
    __tablename__ = "user"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="user_pk"),
        ForeignKeyConstraint(["user_type_id"], ["user_type.id"], ondelete="SET NULL"),
    )

    id: Mapped[int]
    tell_id: Mapped[BigInteger | None]
    phone_number: Mapped[String13] = mapped_column(unique=True)
    chat_id: Mapped[BigInteger | None]
    name: Mapped[String50]

    user_type_id: Mapped[int | None]

    def __repr__(self):
        return f"user | {self.name} | {self.phone_number}"


class Practice(Base):
    __tablename__ = "practice"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="practice_pk"),
        ForeignKeyConstraint(["user_type_id"], ["user_type.id"], ondelete="SET NULL"),
    )

    id: Mapped[int]
    title: Mapped[String100]
    caption: Mapped[CaptionText]

    end_date: Mapped[datetime]
    start_date: Mapped[datetime]

    user_type_id: Mapped[int | None]

    @property
    def active(self):
        return (datetime.now(TIME_ZONE) <= self.end_date) and (
            datetime.now(TIME_ZONE) >= self.start_date
        )

    def __repr__(self):
        return self.title


class Teacher(Base):
    __tablename__ = "teacher"
    __table_args__ = (PrimaryKeyConstraint("id", name="teacher_pk"),)

    id: Mapped[int]
    tell_id: Mapped[BigInteger | None]
    phone_number: Mapped[String13] = mapped_column(unique=True)
    chat_id: Mapped[BigInteger | None]
    name: Mapped[String50]

    def __repr__(self):
        return f"teacher | {self.name} | {self.phone_number}"


class UserPractice(Base):
    __tablename__ = "user_practice"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="user_practice_pk"),
        ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        ForeignKeyConstraint(["practice_id"], ["practice.id"], ondelete="CASCADE"),
    )

    id: Mapped[int]
    user_id: Mapped[int]
    practice_id: Mapped[int]

    media_type: Mapped[MediaType | None]
    caption: Mapped[CaptionText | None]
    file_link: Mapped[FileId | None]

    datetime_created: Mapped[datetime] = mapped_column(
        types.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    datetime_modified: Mapped[datetime] = mapped_column(
        types.DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"{self.id} | practice: {self.practice_id} | user: {self.user_id}"


class Correction(Base):
    __tablename__ = "correction"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="correction_pk"),
        ForeignKeyConstraint(["teacher_id"], ["teacher.id"], ondelete="SET NULL"),
        ForeignKeyConstraint(
            ["user_practice_id"], ["user_practice.id"], ondelete="CASCADE"
        ),
    )

    id: Mapped[int]
    teacher_id: Mapped[int | None]
    user_practice_id: Mapped[int]

    media_type: Mapped[MediaType | None]
    caption: Mapped[CaptionText | None]
    file_link: Mapped[FileId | None]

    datetime_created: Mapped[datetime] = mapped_column(
        types.DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    datetime_modified: Mapped[datetime] = mapped_column(
        types.DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    def __repr__(self):
        return f"{self.id} | user-practice: {self.user_practice_id} | teacher: {self.teacher_id}"


class MediaAcsess(Base):
    __tablename__ = "media_acsess"
    __table_args__ = (
        PrimaryKeyConstraint("id", name="media_acsess_pk"),
        ForeignKeyConstraint(["practice_id"], ["practice.id"], ondelete="CASCADE"),
    )

    id: Mapped[int]
    media_type: Mapped[MediaType]
    practice_id: Mapped[int]

    user_level: Mapped[UserLevel]

    @property
    def is_user(self):
        return self.user_level == UserLevel.USER

    @property
    def is_teacher(self):
        return self.user_level == UserLevel.TEACHER
