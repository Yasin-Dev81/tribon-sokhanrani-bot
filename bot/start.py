from pyrogram import filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton

from .home import (
    send_home_message_admin,
    send_home_message_teacher,
    send_home_message_user,
)
from config import ADMINS_LIST_ID
import db


def user_update_with_phone_number(phone_number, tell_id, chat_id):
    user = db.session.query(db.UserModel).filter_by(phone_number=phone_number).first()
    if user:
        user.tell_id = tell_id
        user.chat_id = chat_id
        # user.name = name
        db.session.commit()
        return True
    else:
        return False


def teacher_update_with_phone_number(phone_number, tell_id, chat_id):
    user = db.session.query(db.UserModel).filter_by(phone_number=phone_number).first()
    if user:
        user.tell_id = tell_id
        user.chat_id = chat_id
        db.session.commit()
        return True
    else:
        return False


async def start(client, message):
    # print(message)
    if message.from_user.id in ADMINS_LIST_ID:
        await send_home_message_admin(message)
        return

    teacher_row = (
        db.session.query(db.TeacherModel)
        .filter_by(tell_id=message.from_user.id)
        .first()
    )
    # print(teacher_row)
    if teacher_row:
        await send_home_message_teacher(message)
        return

    user_row = (
        db.session.query(db.UserModel).filter_by(tell_id=message.from_user.id).first()
    )
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
    if "+" not in user_phone_number:
        user_phone_number = "+%s" % user_phone_number

    # name = []
    # if message.from_user.first_name:
    #     name.append(message.from_user.first_name)
    # if message.from_user.last_name:
    #     name.append(message.from_user.last_name)

    # db
    user_status = user_update_with_phone_number(
        phone_number=user_phone_number,
        tell_id=message.from_user.id,
        chat_id=message.chat.id
    )
    print("----- login user", user_phone_number, user_status)

    if user_status:
        await send_home_message_user(message)
    else:
        teacher_status = teacher_update_with_phone_number(
            phone_number=user_phone_number,
            tell_id=message.from_user.id,
            chat_id=message.chat.id,
        )
        print("----- login teacher", user_phone_number, teacher_status)

        if teacher_status:
            await send_home_message_teacher(message)
        else:
            await message.reply_text("No Access, Please send message to admin!")


def register_start_handlers(app):
    app.on_message(filters.command("start"))(start)
    app.on_message(filters.contact)(contact)
