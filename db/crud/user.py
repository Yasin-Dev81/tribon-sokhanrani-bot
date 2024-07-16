import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from ..models import User as UserModel, UserPractice as UserPracticeModel, Practice as PracticeModel
from config import SQLALCHEMY_DATABASE_URL


class User:
    def __init__(self):
        self.engine = create_engine(SQLALCHEMY_DATABASE_URL)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def add(self, phone_number, tell_id=None, chat_id=None):
        new_user = UserModel(phone_number=phone_number, tell_id=tell_id, chat_id=chat_id)
        self.session.add(new_user)
        self.session.commit()

    def delete(self, pk):
        user = self.session.query(UserModel).get(pk)
        if user:
            self.session.delete(user)
            self.session.commit()

    def read(self, pk):
        return self.session.query(UserModel).get(pk)

    def read_with_phone_number(self, phone_number):
        return self.session.query(UserModel).filter_by(phone_number=phone_number).first()

    def read_with_tell_id(self, tell_id):
        return self.session.query(UserModel).filter_by(tell_id=tell_id).first()

    def update(self, pk, tell_id, chat_id, name):
        user = self.session.query(UserModel).get(pk)
        if user:
            user.tell_id = tell_id
            user.chat_id = chat_id
            user.name = name
            self.session.commit()

    def available_practice(self, pk):
        now = datetime.datetime.now()
        query = self.session.query(
            PracticeModel.id, PracticeModel.title, PracticeModel.end_date
        ).join(
            UserPracticeModel, PracticeModel.id == UserPracticeModel.practice_id
        ).filter(
            UserPracticeModel.user_id == pk
        ).filter(
            ~self.session.query(UserPracticeModel).filter(
                UserPracticeModel.practice_id == PracticeModel.id,
                UserPracticeModel.user_id == pk,
                UserPracticeModel.file_link.isnot(None)
            ).exists()
        ).order_by(PracticeModel.end_date)

        return query.all()

    def all(self):
        return self.session.query(UserModel).all()

    def read_chat_id_user_with_user_practice_id(self, user_practice_id):
        query = self.session.query(
            UserModel.chat_id
        ).join(
            UserPracticeModel, UserModel.id == UserPracticeModel.user_id
        ).filter(
            UserPracticeModel.id == user_practice_id
        )
        return query.scalar()

    def update_with_phone_number(self, phone_number, tell_id, chat_id, name):
        user = self.session.query(UserModel).filter_by(phone_number=phone_number).first()
        if user:
            user.tell_id = tell_id
            user.chat_id = chat_id
            user.name = name
            self.session.commit()
            return True
        else :
            return False
