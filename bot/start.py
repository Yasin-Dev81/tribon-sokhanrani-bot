from pyrogram import filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton

from .home import (
    send_home_message_admin,
    send_home_message_teacher,
    send_home_message_user,
)
from config import ADMINS_LIST_ID
import db.crud as db


async def start(client, message):
    if message.from_user.id in ADMINS_LIST_ID:
        await send_home_message_admin(message)
        return

    teacher_row = db.Teacher().read_with_tell_id(tell_id=message.from_user.id)
    # print(teacher_row)
    if teacher_row:
        await send_home_message_teacher(message)
        if not teacher_row.chat_id:
            name = []
            if message.from_user.first_name:
                name.append(message.from_user.first_name)
            if message.from_user.last_name:
                name.append(message.from_user.last_name)
            db.Teacher().update_with_tell_id(
                tell_id=message.from_user.id,
                chat_id=message.chat.id,
                name=" ".join(name),
            )
        return

    user_row = db.User().read_with_tell_id(tell_id=message.from_user.id)
    if user_row:
        await send_home_message_user(message)
        return

    # Create a reply keyboard markup with a button to request the user's phone number
    reply_markup = ReplyKeyboardMarkup(
        [[KeyboardButton("Send your phone number", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
    await message.reply_text(
        "Please share your phone number with me.", reply_markup=reply_markup
    )


async def contact(client, message):
    # data
    user_phone_number = message.contact.phone_number
    name = []
    if message.from_user.first_name:
        name.append(message.from_user.first_name)
    if message.from_user.last_name:
        name.append(message.from_user.last_name)

    # db
    status = db.User().read_with_phone_number(phone_number=user_phone_number)

    if status:
        db.User().update_with_phone_number(
            phone_number=user_phone_number,
            tell_id=message.from_user.id,
            chat_id=message.chat.id,
            name=" ".join(name),
        )
        await send_home_message_user(message)
    else:
        await message.reply_text("No Access, Please send message to admin!")


def register_start_handlers(app):
    app.on_message(filters.command("start"))(start)
    app.on_message(filters.contact)(contact)
