from pyrogram import filters
from sqlalchemy import func, and_, case, desc
import datetime

from config import ADMINS_LIST_ID
import db


def is_user(_, __, update):
    return (
        db.session.query(db.UserModel).filter_by(tell_id=update.from_user.id).first()
        is not None
    )


def is_teacher(filter, client, update):
    with db.session as db_session:
        return (
            db_session.query(db.TeacherModel)
            .filter_by(tell_id=update.from_user.id)
            .first()
            is not None
        )


def report():
    current_time = datetime.datetime.now()
    return (
        db.session.query(
            func.count(db.UserModel.id).label("users_count"),
            func.count(db.UserModel.chat_id.distinct()).label("active_users_count"),
            func.count(db.TeacherModel.id).label("teachers_count"),
            func.count(db.TeacherModel.chat_id.distinct()).label(
                "active_teachers_count"
            ),
            func.count(db.PracticeModel.id).label("practice_count"),
            func.sum(
                case(
                    (
                        and_(
                            db.PracticeModel.start_date <= current_time,
                            db.PracticeModel.end_date >= current_time,
                        ),
                        1,
                    ),
                    else_=0,
                )
            ).label("active_practice_count"),
            func.count(db.UserPracticeModel.id).label("user_practice_count"),
            func.sum(
                case((db.UserPracticeModel.teacher_id.is_(None), 1), else_=0)
            ).label("user_practice_none_teacher_count"),
            func.sum(
                case((db.UserPracticeModel.teacher_id.is_not(None), 1), else_=0)
            ).label("user_practice_done_teacher_count"),
            func.sum(
                case((db.UserPracticeModel.teacher_caption.is_(None), 1), else_=0)
            ).label("user_practice_done_count"),
            func.sum(
                case((db.UserPracticeModel.teacher_caption.is_not(None), 1), else_=0)
            ).label("user_practice_not_done_count"),
        )
        .join(
            db.UserPracticeModel,
            db.UserModel.id == db.UserPracticeModel.user_id,
            isouter=True,
        )
        .join(
            db.PracticeModel,
            db.UserPracticeModel.practice_id == db.PracticeModel.id,
            isouter=True,
        )
        .join(
            db.TeacherModel,
            db.UserPracticeModel.teacher_id == db.TeacherModel.id,
            isouter=True,
        )
        .first()
    )


def top_users():
    top_users = (
        db.session.query(
            db.UserModel.id,
            db.UserModel.name,
            func.count(db.UserPracticeModel.id).label("assignments_delivered"),
        )
        .join(db.UserPracticeModel, db.UserModel.id == db.UserPracticeModel.user_id)
        .group_by(db.UserModel.id, db.UserModel.name)
        .order_by(desc("assignments_delivered"))
        .limit(3)
        .all()
    )
    return top_users


def top_teachers():
    top_teachers = (
        db.session.query(
            db.TeacherModel.id,
            db.TeacherModel.name,
            func.count(db.UserPracticeModel.id).label("assignments_reviewed"),
        )
        .join(
            db.UserPracticeModel, db.TeacherModel.id == db.UserPracticeModel.teacher_id
        )
        .filter(db.UserPracticeModel.teacher_caption.isnot(None))
        .group_by(db.TeacherModel.id, db.TeacherModel.name)
        .order_by(desc("assignments_reviewed"))
        .limit(3)
        .all()
    )
    return top_teachers


async def admin_report(client, message):
    data = report()

    top_user_capt = ""
    for i, user in enumerate(top_users()):
        top_user_capt += f"{i+1}. {user.name}\n"

    top_teacher_capt = ""
    for i, teacher in enumerate(top_teachers()):
        top_teacher_capt += f"{i+1}. {teacher.name}\n"

    await message.reply_text(
        "🔷 <b>یوزرها</b>\n"
        f"🔹 تعداد یوزر ثبت شده: {data.users_count}\n"
        f"🔹 تعداد یوزر فعال: {data.active_users_count}\n"
        "➖➖➖➖➖➖➖➖➖\n"
        "▫️ بهترین یوزرها از نظر تحویل تکلیف:\n"
        f"{top_user_capt}"
        "➖➖➖➖➖➖➖➖➖\n"
        "🔶 <b>معلم‌ها</b>\n"
        f"🔸 تعداد معلم ثبت شده: {data.teachers_count}\n"
        f"🔸 تعداد معلم فعال: {data.active_teachers_count}\n"
        "➖➖➖➖➖➖➖➖➖\n"
        "▫️ بهترین معلم‌ها از نظر تحلیل تکلیف:\n"
        f"{top_teacher_capt}"
        "➖➖➖➖➖➖➖➖➖\n"
        "🔷 <b>تمارین</b>\n"
        f"🔹 تعداد تمارین ثبت شده: {data.practice_count}\n"
        f"🔹 تعداد تمارین فعال: {data.active_practice_count}\n"
        "➖➖➖➖➖➖➖➖➖\n"
        "🔶 <b>تکالیف</b>\n"
        f"🔸 تعداد تکلیف ثبت شده: {data.user_practice_count}\n"
        f"🔸 تعداد تکالیف تخصیص داده نشده: {data.user_practice_none_teacher_count}\n"
        f"🔸 تعداد تکالیف تخصیص داده شده: {data.user_practice_done_teacher_count}\n"
        f"🔸 تعداد تکالیف تحلیل نشده: {data.user_practice_done_count}\n"
        f"🔸 تعداد تکالیف تحلیل شده: {data.user_practice_not_done_count}\n   "
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
