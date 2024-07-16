from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..models import Teacher as TeacherModel
from config import SQLALCHEMY_DATABASE_URL


class Teacher:
    def __init__(self):
        self.engine = create_engine(SQLALCHEMY_DATABASE_URL)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def add(self, tell_id, chat_id=None):
        new_teacher = TeacherModel(tell_id=tell_id, chat_id=chat_id)
        self.session.add(new_teacher)
        self.session.commit()

    def delete(self, pk):
        teacher = self.session.query(TeacherModel).get(pk)
        if teacher:
            self.session.delete(teacher)
            self.session.commit()

    def read(self, pk):
        return self.session.query(TeacherModel).get(pk)

    def all(self):
        return self.session.query(TeacherModel).all()

    def availble(self):
        return self.session.query(TeacherModel).filter(TeacherModel.chat_id.is_not(None)).all()

    def read_with_tell_id(self, tell_id):
        return self.session.query(TeacherModel).filter_by(tell_id=tell_id).first()

    def update_with_tell_id(self, tell_id, chat_id, name):
        teacher = self.session.query(TeacherModel).filter_by(tell_id=tell_id).first()
        if teacher:
            teacher.chat_id = chat_id
            teacher.name = name
            self.session.commit()
