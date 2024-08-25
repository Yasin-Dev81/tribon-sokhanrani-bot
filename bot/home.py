from pyrogram.types import ReplyKeyboardMarkup
from pyrogram import filters

from config import ADMINS_LIST_ID, BOT_VERSION, LEARN_URL
import db


async def send_home_message_admin(message):
    await message.reply_text(
        "سلام <b>ادمین</b> عزیز 👋\n"
        "به ربات سخنرانی تریبون خوش اومدی!\n\n"
        f"<b>tribon sokhanrani</b> 🤖 <i>v{BOT_VERSION}</i>\n",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["تعریف تمرین جدید"],
                ["تکالیف بدون معلم", "منتور‌های تمام نکرده"],
                ["تکالیف تحلیل شده", "تکالیف تحلیل نشده"],
                ["تمرین‌های فعال", "تمامی تمرین‌ها", "تمامی تکالیف"],
                ["یوزرها", "اضافه کردن یوزر جدید"],
                ["منتورها", "اضافه کردن منتور جدید"],
                ["ارسال نوتیفیکیشن 📢", "سرچ 🔎"],
                ["گزارش عملکرد"],
            ],
            resize_keyboard=True,
        ),
    )


async def send_home_message_teacher(message, teacher_name="معلم"):
    await message.reply_text(
        f"سلام <b>{teacher_name}</b> عزیز 👋\n"
        "به ربات سخنرانی تریبون خوش اومدی!\n\n"
        f"<b>tribon sokhanrani</b> 🤖 <i>v{BOT_VERSION}</i>",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["تکالیف نیازمند به تحلیل سخنرانی"],
                ["تمرین‌های فعال", "تمامی تمرین‌ها"],
                ["اطلاعات من ℹ️"],
            ],
            resize_keyboard=True,
        ),
    )


async def send_home_message_user(message, user_name="کاربر"):
    await message.reply_text(
        f"سلام <b>{user_name}</b> عزیز 👋\n"
        "به ربات سخنرانی تریبون خوش اومدی!\n"
        f"<b>tribon sokhanrani</b> 🤖 <i>v{BOT_VERSION}</i>\n\n"
        f"<a href='{LEARN_URL}'>ℹ️ ویدیو آموزشی نحوه ارسال تمرینات</a>",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["تمرین‌های فعال"],
                ["تصحیح شده‌ها", "تحویل داده شده‌ها"],
                ["قوانین 📝"],
                ["اطلاعات من ℹ️"],
            ],
            resize_keyboard=True,
        ),
    )


class BackHome:
    def __init__(self, app):
        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_callback_query(filters.regex(r"back_home"))(self.back_home)

    async def back_home(self, client, callback_query):
        # Acknowledge the callback query
        # await callback_query.answer()
        await self.app.unregister_steps(callback_query.from_user.id)
        try:
            await callback_query.message.delete()
        except Exception:
            pass

        with db.get_session() as session:
            admin_st = callback_query.from_user.id in ADMINS_LIST_ID
            if admin_st:
                await send_home_message_admin(callback_query.message)
                return

            teahcer_st = (
                session.query(db.TeacherModel)
                .filter_by(tell_id=callback_query.from_user.id)
                .first()
            )
            if teahcer_st:
                await send_home_message_teacher(
                    callback_query.message, teacher_name=teahcer_st.name
                )
                return
            user = (
                session.query(db.UserModel)
                .filter_by(tell_id=callback_query.from_user.id)
                .first()
            )
            if user:
                await send_home_message_user(callback_query.message, user.name)
                return

        await callback_query.answer("error!")


def register_home_handlers(app):
    BackHome(app)
