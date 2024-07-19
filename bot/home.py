from pyrogram.types import ReplyKeyboardMarkup
from pyrogram import filters

from config import ADMINS_LIST_ID
import db


async def send_home_message_admin(message):
    await message.reply_text(
        "Hi, admin! 👋\nwellcome to <b>tribon sokhanrani</b> 🤖 <i>v4.6</i>",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["تعریف تمرین جدید"],
                ["تمرین‌های فعال", "تکالیف بدون معلم", "تمامی تمرین‌ها"],
                ["یوزرها", "اضافه کردن یوزر جدید"],
                ["معلم‌ها", "اضافه کردن معلم جدید"],
                ["ارسال نوتیفیکیشن"],
                ["my settings"],
            ],
            resize_keyboard=True,
        ),
    )


async def send_home_message_teacher(message):
    await message.reply_text(
        "Hi, teacher! 👋\nwellcome to <b>tribon sokhanrani</b> 🤖 <i>v4.6</i>",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["تکالیف نیازمند به تحلیل سخنرانی"],
                ["تمرین‌های فعال", "تمامی تمرین‌ها"],
                ["my settings"],
            ],
            resize_keyboard=True,
        ),
    )


async def send_home_message_user(message):
    await message.reply_text(
        "Hi, user! 👋\nwellcome to <b>tribon sokhanrani</b> 🤖 <i>v4.6</i>",
        reply_markup=ReplyKeyboardMarkup(
            [["تمرین‌های فعال", "تحویل داده شده‌ها"], ["my settings"]],
            resize_keyboard=True,
        ),
    )


async def back_home(client, callback_query):
    # Acknowledge the callback query
    await callback_query.answer()
    await callback_query.message.delete()

    if callback_query.from_user.id in ADMINS_LIST_ID:
        await send_home_message_admin(callback_query.message)
    elif (
        db.session.query(db.TeacherModel)
        .filter_by(tell_id=callback_query.from_user.id)
        .first()
    ):
        await send_home_message_teacher(callback_query.message)
    else:
        await send_home_message_user(callback_query.message)


def register_home_handlers(app):
    app.on_callback_query(filters.regex(r"back_home"))(back_home)
