import datetime
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from ..models import Practice as PracticeModel, UserPractice as UserPracticeModel
from config import SQLALCHEMY_DATABASE_URL


class Practice:
    def __init__(self):
        self.engine = create_engine(SQLALCHEMY_DATABASE_URL)
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def add(self, title, caption, end_date, start_date=datetime.datetime.now()):
        # Convert start_date and end_date to datetime if they are strings
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, "%d/%m/%Y")
        end_date = datetime.datetime.strptime(end_date, "%d/%m/%Y")

        new_practice = PracticeModel(
            title=title,
            caption=caption,
            start_date=start_date,
            end_date=end_date
        )
        self.session.add(new_practice)
        self.session.commit()

    def delete(self, pk):
        practice = self.session.query(PracticeModel).get(pk)
        if practice:
            self.session.delete(practice)
            self.session.commit()

    def read(self, pk):
        return self.session.query(PracticeModel).get(pk)

    def available(self):
        current_time = datetime.datetime.now()
        query = self.session.query(PracticeModel.id, PracticeModel.title).filter(
            PracticeModel.start_date <= current_time,
            PracticeModel.end_date >= current_time
        )
        return query.all()

    def all(self):
        return self.session.query(PracticeModel.id, PracticeModel.title).all()

    def report(self, pk):
        total_count_subquery = self.session.query(func.count(UserPracticeModel.id)).filter(UserPracticeModel.practice_id == pk).scalar_subquery()
        teacher_caption_count_subquery = self.session.query(func.count(UserPracticeModel.id)).filter(UserPracticeModel.practice_id == pk, UserPracticeModel.teacher_caption.isnot(None)).scalar_subquery()

        query = self.session.query(
            PracticeModel.title,
            PracticeModel.caption,
            total_count_subquery.label('total_count'),
            teacher_caption_count_subquery.label('teacher_caption_count')
        ).filter(PracticeModel.id == pk).first()

        return query

    def update(self, pk, title, caption, end_date, start_date=datetime.datetime.now()):
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, "%d/%m/%Y")
        end_date = datetime.datetime.strptime(end_date, "%d/%m/%Y")

        practice = self.session.query(PracticeModel).get(pk)
        if practice:
            practice.title = title
            practice.caption = caption
            practice.end_date = end_date
            practice.start_date = start_date
            self.session.commit()
            return True
        return False
