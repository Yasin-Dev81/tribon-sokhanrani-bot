from pyrogram.types import ReplyKeyboardMarkup
from pyrogram import filters

from config import ADMINS_LIST_ID
import db.crud as db


async def send_home_message_admin(message):
    await message.reply_text(
        "Hi, admin!"
        "\n<b>AH-score</b> <i>v4.0</i>",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["تعریف تمرین جدید"],
                ["تمرین‌های فعال", "تکالیف بدون معلم", "تمامی تمرین‌ها"],
                ["یوزرها", "اضافه کردن یوزر جدید"],
                ["معلم‌ها", "اضافه کردن معلم جدید"],
                ["اطلاع‌رسانی به کاربران", "اطلاع‌رسانی به معلمان", "اطلاع‌رسانی به همه"],
                ["my settings"]
            ],
            resize_keyboard=True
        )
    )


async def send_home_message_teacher(message):
    await message.reply_text(
        "Hi, teacher!"
        "\n<b>AH-score</b> <i>v4.0</i>",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["تکالیف نیازمند به تصحیح"],
                ["تمرین‌های فعال", "تمامی تمرین‌ها", "تصحیح شده‌ها"],
                ["my settings"]
            ],
            resize_keyboard=True
        )
    )


async def send_home_message_user(message):
    await message.reply_text(
        "Hi, user!"
        "\n<b>AH-score</b> <i>v4.0</i>",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["تمرین‌های فعال", "تحویل داده شده‌ها"],
                ["my settings"]
            ],
            resize_keyboard=True
        )
    )


async def back_home(client, callback_query):
    # Acknowledge the callback query
    await callback_query.answer()
    await callback_query.message.delete()

    if callback_query.from_user.id in ADMINS_LIST_ID:
        await send_home_message_admin(callback_query.message)
    elif db.Teacher().read_with_tell_id(tell_id=callback_query.from_user.id):
        await send_home_message_teacher(callback_query.message)
    else:
        await send_home_message_user(callback_query.message)


def register_home_handlers(app):
    app.on_callback_query(filters.regex(r"back_home"))(back_home)
