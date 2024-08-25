from pyrogram import filters
from sqlalchemy import func, and_, case, desc
from sqlalchemy.sql.expression import over
from collections import defaultdict
import datetime

from config import ADMINS_LIST_ID, TIME_ZONE
import db


def is_user(_, __, update):
    with db.get_session() as session:
        return (
            session.query(db.UserModel).filter_by(tell_id=update.from_user.id).first()
            is not None
        )


def is_teacher(filter, client, update):
    with db.get_session() as session:
        return (
            session.query(db.TeacherModel)
            .filter_by(tell_id=update.from_user.id)
            .first()
            is not None
        )


class Report:
    current_time = datetime.datetime.now(TIME_ZONE)
    emojies = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]

    def __init__(self) -> None:
        with db.get_session() as session:
            self.session = session

    @property
    def users(self):
        return self.session.query(
            func.count(db.UserModel.id).label("users_count"),
            func.count(db.UserModel.chat_id.distinct()).label("active_users_count"),
        ).first()

    @property
    def teahcers(self):
        return self.session.query(
            func.count(db.TeacherModel.id).label("teachers_count"),
            func.count(db.TeacherModel.chat_id.distinct()).label(
                "active_teachers_count"
            ),
        ).first()

    @property
    def practices(self):
        return self.session.query(
            func.count(db.PracticeModel.id).label("practice_count"),
            func.sum(
                case(
                    (
                        and_(
                            db.PracticeModel.start_date <= self.current_time,
                            db.PracticeModel.end_date >= self.current_time,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("active_practice_count"),
        ).first()

    @property
    def user_practices(self):
        return (
            self.session.query(
                func.count(db.UserPracticeModel.id).label("user_practice_count"),
                func.sum(case((db.CorrectionModel.id.is_(None), 1), else_=0)).label(
                    "user_practice_none_teacher_count"
                ),
                func.sum(case((db.CorrectionModel.id.is_not(None), 1), else_=0)).label(
                    "user_practice_done_teacher_count"
                ),
                func.sum(
                    case((db.CorrectionModel.caption.is_(None), 1), else_=0)
                ).label("user_practice_done_count"),
                func.sum(
                    case((db.CorrectionModel.caption.is_not(None), 1), else_=0)
                ).label("user_practice_not_done_count"),
            )
            .outerjoin(
                db.CorrectionModel,
                db.CorrectionModel.user_practice_id == db.UserPracticeModel.id,
            )
            .first()
        )

    @property
    def top_users(self):
        subquery = (
            self.session.query(
                db.UserModel.id,
                db.UserModel.name,
                db.UserModel.user_type_id,
                func.count(db.UserPracticeModel.id).label("assignments_delivered"),
                over(
                    func.rank(),
                    order_by=desc(func.count(db.UserPracticeModel.id)),
                    partition_by=db.UserModel.user_type_id,
                ).label("rank"),
            )
            .join(db.UserPracticeModel, db.UserModel.id == db.UserPracticeModel.user_id)
            .group_by(db.UserModel.id, db.UserModel.user_type_id)
            .subquery()
        )

        top_users = (
            self.session.query(
                subquery.c.name,
                subquery.c.assignments_delivered,
                db.UserTypeModel.name.label("type_name"),
            )
            .filter(subquery.c.rank <= 3)
            .join(db.UserTypeModel, db.UserTypeModel.id == subquery.c.user_type_id)
            .all()
        )

        users_by_type = defaultdict(list)
        for user in top_users:
            users_by_type[user.type_name].append(
                {"name": user.name, "assignments_delivered": user.assignments_delivered}
            )

        top_user_capt = "".join(
            f"◾️ <b>{type_name}</b>\n<blockquote expandable>"
            + "".join(
                f"  {emj} <i>{user['name']}</i> | <code>{user['assignments_delivered']}</code>\n"
                for emj, user in zip(self.emojies, users_by_type[type_name])
            )
            + "</blockquote>"
            for type_name in users_by_type
        )

        return top_user_capt

    @property
    def top_teachers(self):
        top_teachers = (
            self.session.query(
                db.TeacherModel.id,
                db.TeacherModel.name,
                func.count(db.CorrectionModel.id).label("assignments_reviewed"),
            )
            .join(
                db.CorrectionModel,
                db.TeacherModel.id == db.CorrectionModel.teacher_id,
            )
            .filter(db.CorrectionModel.caption.isnot(None))
            .group_by(db.TeacherModel.id, db.TeacherModel.name)
            .order_by(desc("assignments_reviewed"))
            .limit(10)
            .all()
        )

        top_teacher_capt = ""
        # for i, teacher in enumerate(top_teachers):
        for emj, teacher in zip(self.emojies, top_teachers):
            top_teacher_capt += f"  {emj} <i>{teacher.name}</i> | <code>{teacher.assignments_reviewed}</code>\n"
        return top_teacher_capt


async def admin_report(client, message):
    data = Report()
    # data.top_users

    await message.reply_text(
        "🔷 <b>یوزرها</b>\n"
        f"🔹 تعداد یوزر ثبت شده: {data.users.users_count}\n"
        f"🔹 تعداد یوزر فعال: {data.users.active_users_count}\n"
        "➖➖➖➖➖➖➖➖➖\n"
        "▫️ بهترین یوزرها از نظر تحویل تکلیف:\n"
        f"{data.top_users}"
    )
    await message.reply_text(
        "🔶 <b>معلم‌ها</b>\n"
        f"🔸 تعداد معلم ثبت شده: {data.teahcers.teachers_count}\n"
        f"🔸 تعداد معلم فعال: {data.teahcers.active_teachers_count}\n"
        "➖➖➖➖➖➖➖➖➖\n"
        "▫️ بهترین معلم‌ها از نظر تحلیل تکلیف:\n"
        f"<blockquote expandable>{data.top_teachers}</blockquote>"
    )
    await message.reply_text(
        "🔷 <b>تمارین</b>\n"
        f"🔹 تعداد تمارین ثبت شده: {data.practices.practice_count}\n"
        f"🔹 تعداد تمارین فعال: {data.practices.active_practice_count or 0}\n"
        "➖➖➖➖➖➖➖➖➖\n"
        "🔶 <b>تکالیف</b>\n"
        f"🔸 تعداد تکلیف ثبت شده: {data.user_practices.user_practice_count}\n"
        f"🔸 تعداد تکالیف تخصیص داده نشده: {data.user_practices.user_practice_none_teacher_count or 0}\n"
        f"🔸 تعداد تکالیف تخصیص داده شده: {data.user_practices.user_practice_done_teacher_count or 0}\n"
        f"🔸 تعداد تکالیف تحلیل نشده: {data.user_practices.user_practice_done_count or 0}\n"
        f"🔸 تعداد تکالیف تحلیل شده: {data.user_practices.user_practice_not_done_count or 0}\n   "
    )


async def teacher_report(client, message):
    pass


async def user_report(client, message):
    pass


def register_report_handlers(app):
    app.on_message(filters.regex("گزارش عملکرد") & filters.user(ADMINS_LIST_ID))(
        admin_report
    )
    # app.on_message(filters.command("report") & filters.create(is_teacher))(
    #     teacher_report
    # )
    # app.on_message(filters.command("report") & filters.create(is_user))(user_report)
