import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..models import UserPractice as UserPracticeModel, Practice as PracticeModel, Teacher as TeacherModel, User as UserModel
from config import SQLALCHEMY_DATABASE_URL


class UserPractice:
    def __init__(self):
        self.engine = create_engine(SQLALCHEMY_DATABASE_URL)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def add(self, user_id, file_link, practice_id, user_caption=None):
        new_user_practice = UserPracticeModel(
            user_id=user_id,
            file_link=file_link,
            practice_id=practice_id,
            user_caption=user_caption
        )
        self.session.add(new_user_practice)
        self.session.commit()
        return new_user_practice.id

    def delete(self, pk):
        user_practice = self.session.query(UserPracticeModel).get(pk)
        if user_practice:
            self.session.delete(user_practice)
            self.session.commit()

    def read(self, pk):
        query = self.session.query(
            UserPracticeModel.id.label("id"),
            UserModel.name.label("username"),
            UserPracticeModel.file_link.label("file_link"),
            UserPracticeModel.user_caption.label("user_caption"),
            UserPracticeModel.teacher_caption.label("teacher_caption"),
            PracticeModel.title.label("title"),
            PracticeModel.caption.label("practice_caption"),
            UserPracticeModel.practice_id.label("practice_id")
        ).join(
            PracticeModel, PracticeModel.id == UserPracticeModel.practice_id
        ).join(
            UserModel, UserModel.id == UserPracticeModel.user_id
        ).filter(UserPracticeModel.id == pk)
        return query.first()

    def read_with_practice_id_single(self, practice_id, tell_id):
        query = self.session.query(
            PracticeModel.title, PracticeModel.caption,
            UserPracticeModel.user_caption, UserPracticeModel.teacher_caption
        ).join(
            PracticeModel, PracticeModel.id == UserPracticeModel.practice_id
        ).join(
            UserModel, UserModel.id == UserPracticeModel.user_id
        ).filter(
            UserPracticeModel.practice_id == practice_id
        ).filter(
            UserModel.tell_id == tell_id
        )
        return query.first()

    def set_teacher(self, pk, teacher_id):
        user_practice = self.session.query(UserPracticeModel).get(pk)
        if user_practice:
            user_practice.teacher_id = teacher_id
            self.session.commit()

    def set_teacher_caption(self, pk, teacher_caption):
        user_practice = self.session.query(UserPracticeModel).get(pk)
        if user_practice:
            user_practice.teacher_caption = teacher_caption
            self.session.commit()

    def update(self, pk, file_link, user_caption=None):
        user_practice = self.session.query(UserPracticeModel).get(pk)
        if user_practice:
            user_practice.file_link = file_link
            if user_caption is not None:
                user_practice.user_caption = user_caption
            self.session.commit()
        return pk

    def read_with_teacher_tell_id(self, teacher_tell_id, practice_id=None, correction=False):
        query = self.session.query(
            UserPracticeModel
        ).join(
            TeacherModel, TeacherModel.id == UserPracticeModel.teacher_id
        ).filter(TeacherModel.tell_id == teacher_tell_id)

        if practice_id:
            query = query.filter(UserPracticeModel.practice_id == practice_id)

        if correction:
            query = query.filter(UserPracticeModel.teacher_caption.isnot(None))
        else:
            query = query.filter(UserPracticeModel.teacher_caption.is_(None))

        return query.all()

    def read_with_user_tell_id(self, user_tell_id):
        query = self.session.query(
            PracticeModel.id, PracticeModel.title
        ).join(
            UserPracticeModel, PracticeModel.id == UserPracticeModel.practice_id
        ).join(
            UserModel, UserModel.id == UserPracticeModel.user_id
        ).filter(UserModel.tell_id == user_tell_id)

        return query.all()

    def read_none_teacher(self):
        query = self.session.query(
            UserPracticeModel.id,
            UserModel.name,
            PracticeModel.title,
            UserPracticeModel.file_link,
            UserPracticeModel.user_caption
        ).join(PracticeModel, UserPracticeModel.practice_id == PracticeModel.id, isouter=True)\
        .join(UserModel, UserPracticeModel.user_id == UserModel.id, isouter=True)\
        .filter(UserPracticeModel.teacher_id.is_(None))

        return query.all()

    def read_with_practice_id_all(self, practice_id):
        query = self.session.query(
            UserPracticeModel.id,
            UserModel.name.label("title"),
            UserPracticeModel.teacher_caption
        ).join(
            PracticeModel, UserPracticeModel.practice_id == PracticeModel.id
        ).join(
            UserModel, UserPracticeModel.user_id == UserModel.id
        ).filter(
            UserPracticeModel.practice_id == practice_id
        )
        return query.all()
