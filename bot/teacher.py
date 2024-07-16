from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ForceReply
import asyncio

from .pagination import get_paginated_keyboard, none_teacher_paginated_keyboard_t
from .home import send_home_message_teacher
import db.crud as db


def is_teacher(filter, client, update):
    return db.Teacher().read_with_tell_id(tell_id=update.from_user.id) is not None


async def teacher_available_practices(client, message):
    practices = db.Practice().available()
    if not practices:
        await message.reply_text("هیچ تمرین فعالی موجود نیست!")
        return

    await message.reply_text(
        "تمارین فعال:",
        reply_markup=get_paginated_keyboard(
            practices, 0, "teacher_active_practices_page", "teacher_select_practice"
        ),
    )


async def teacher_paginate_active_practices(client, callback_query):
    page = int(callback_query.data.split("_")[-1])
    practices = db.Practice().available()
    if page == 1000000:
        page = 0
        await callback_query.message.delete()
        await callback_query.message.reply_text(
            "تمامی تمرین‌ها:",
            reply_markup=get_paginated_keyboard(
                practices,
                page,
                "teacher_active_practices_page",
                "teacher_select_practice",
            ),
        )
        return
    await callback_query.message.edit_reply_markup(
        reply_markup=get_paginated_keyboard(
            practices, page, "teacher_active_practices_page", "teacher_select_practice"
        )
    )


async def teacher_all_practices(client, message):
    practices = db.Practice().all()
    if not practices:
        await message.reply_text("هیچ تمرین فعالی موجود نیست!")
        return

    await message.reply_text(
        "تمامی تمارین:",
        reply_markup=get_paginated_keyboard(
            practices, 0, "teacher_all_practices_page", "teacher_select_practice"
        ),
    )


async def teacher_paginate_all_practices(client, callback_query):
    page = int(callback_query.data.split("_")[-1])
    practices = db.Practice().available()
    if page == 1000000:
        page = 0
        await callback_query.message.delete()
        await callback_query.message.reply_text(
            "تمامی تمرین‌ها:",
            reply_markup=get_paginated_keyboard(
                practices, page, "teacher_all_practices_page", "teacher_select_practice"
            ),
        )
        return
    await callback_query.message.edit_reply_markup(
        reply_markup=get_paginated_keyboard(
            practices, page, "teacher_all_practices_page", "teacher_select_practice"
        )
    )


#### optimize
async def teacher_select_practice(client, callback_query: CallbackQuery):
    practice_id = int(callback_query.data.split("_")[-1])
    practice = db.Practice().read(pk=practice_id)
    users_practice = db.UserPractice().read_with_teacher_tell_id(
        teacher_tell_id=callback_query.from_user.id, practice_id=practice_id
    )
    await callback_query.message.delete()
    # print(users_practice)

    await callback_query.message.reply_text(
        f"عنوان: {practice.title}\nمتن سوال: {practice.caption}" "\nتصحیح نشده‌ها:",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        f"user {i.user_id}",
                        callback_data=f"teacher_user_practice_{i.id}",
                    )
                ]
                for i in users_practice
            ]
            + [
                [
                    InlineKeyboardButton(
                        "back", callback_data="teacher_all_practices_page_1000000"
                    ),
                    InlineKeyboardButton("exit!", callback_data="back_home"),
                ]
            ]
        ),
    )


#### optimize
async def teacher_user_practice(client, callback_query: CallbackQuery):
    user_practice_id = int(callback_query.data.split("_")[-1])
    user_practice = db.UserPractice().read(pk=user_practice_id)
    await callback_query.message.delete()

    capt = "تصحیح نشده!"
    if user_practice.teacher_caption:
        capt = "تصحیح شده.\n" f"تصحیح: {user_practice.teacher_caption}"

    await callback_query.message.reply_video(
        video=user_practice.file_link,
        caption=f"عنوان سوال: {user_practice.title}\n"
        f"متن سوال: {user_practice.practice_caption}\n"
        f"کاربر: {user_practice.practice_caption}\n"
        f"کپشن کاربر:\n {user_practice.user_caption}\n"
        f"وضعیت تصحیح: {capt}",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "تصحیح مجدد" if user_practice.teacher_caption else "تصحیح",
                        callback_data=f"teacher_correction_{user_practice_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "back",
                        callback_data=f"teacher_select_practice_{user_practice.practice_id}",
                    ),
                    InlineKeyboardButton("exit!", callback_data="back_home"),
                ],
            ]
        ),
    )


#### optimize and pagination
async def teacher_create_new_practice(client, message):
    users_practice = db.UserPractice().read_with_teacher_tell_id(
        teacher_tell_id=message.from_user.id, correction=True
    )

    await message.reply_text(
        "\nتصحیح شده‌ها:",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        f"user {i.user_id}",
                        callback_data=f"teacher_user_practice_{i.id}",
                    )
                ]
                for i in users_practice
            ]
            + [
                [
                    InlineKeyboardButton("back", callback_data="back_home"),
                    InlineKeyboardButton("exit!", callback_data="back_home"),
                ]
            ]
        ),
    )


#### optimize and pagination
async def teacher_non_correction_practice(client, message):
    users_practice = db.UserPractice().read_with_teacher_tell_id(
        teacher_tell_id=message.from_user.id
    )

    await message.reply_text(
        "\nتصحیح نشده‌ها:",
        reply_markup=none_teacher_paginated_keyboard_t(
            users_practice,
            0,
            "teacher_all_practices_non_page",
            "teacher_user_practice_non",
        ),
    )


async def teacher_non_correction_practice_page(client, callback_query):
    page = int(callback_query.data.split("_")[-1])
    users_practice = db.UserPractice().read_with_teacher_tell_id(
        teacher_tell_id=callback_query.from_user.id
    )
    if page == 1000000:
        page = 0
        await callback_query.message.delete()
        await callback_query.message.reply_text(
            "تمامی تمرین‌ها:",
            reply_markup=none_teacher_paginated_keyboard_t(
                users_practice,
                page,
                "teacher_all_practices_non_page",
                "teacher_user_practice_non",
            ),
        )
        return
    await callback_query.message.edit_reply_markup(
        reply_markup=none_teacher_paginated_keyboard_t(
            users_practice,
            page,
            "teacher_all_practices_non_page",
            "teacher_user_practice_non",
        )
    )


async def teacher_user_practice_non(client, callback_query: CallbackQuery):
    user_practice_id = int(callback_query.data.split("_")[-1])
    user_practice = db.UserPractice().read(pk=user_practice_id)
    await callback_query.message.delete()

    capt = "تصحیح نشده!"
    if user_practice.teacher_caption:
        capt = (
            "تصحیح شده.\n"
            f"تصحیح: {user_practice.teacher_caption}"
        )

    await callback_query.message.reply_video(
        video=user_practice.file_link,
        caption=f"عنوان سوال: {user_practice.title}\n"
        f"متن سوال: {user_practice.practice_caption}\n"
        f"کاربر: {user_practice.practice_caption}\n"
        f"کپشن کاربر:\n {user_practice.user_caption}\n"
        f"وضعیت تصحیح: {capt}",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "تصحیح مجدد" if user_practice.teacher_caption else "تصحیح",
                        callback_data=f"teacher_correction_{user_practice_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "back", callback_data="teacher_all_practices_non_page_1000000"
                    ),
                    InlineKeyboardButton("exit!", callback_data="back_home"),
                ],
            ]
        ),
    )


async def teacher_my_settings(client, message):
    teacher = db.Teacher().read_with_tell_id(tell_id=message.from_user.id)
    await message.reply(f"You are <b>teacher</b> and your id is <i>{teacher.id}</i>")


async def teacher_correction(client, callback_query):
    user_practice_id = int(callback_query.data.split("_")[-1])
    user_tell_id = callback_query.from_user.id

    await callback_query.message.reply_text(
        "پیام خود را ریپلی کنید."
        "\n\n"
        "<b>***Just send as a reply to this message***</b>",
        reply_markup=ForceReply(selective=True),
    )

    async def set_teacher_caption(client, message):
        db.UserPractice().set_teacher_caption(
            pk=user_practice_id, teacher_caption=message.text
        )
        await message.reply_text("با موفقیت ثبت شد.")

        await message.reply_to_message.delete()
        client.remove_handler(message_handler)

        async def send_user_correction_notification(user_practice_id):
            await client.send_message(
                chat_id=db.User().read_chat_id_user_with_user_practice_id(
                    user_practice_id
                ),
                text=f"تمرین {user_practice_id} شما تصحیح شد.",
            )

        asyncio.create_task(send_user_correction_notification(user_practice_id))

        await send_home_message_teacher(message)

    await callback_query.message.delete()
    # Add the handler
    message_handler = client.on_message(filters.reply & filters.text & filters.user(user_tell_id))(set_teacher_caption)


def register_teacher_handlers(app):
    app.on_message(filters.regex("تمرین‌های فعال") & filters.create(is_teacher))(
        teacher_available_practices
    )
    app.on_callback_query(filters.regex(r"teacher_active_practices_page_(\d+)"))(
        teacher_paginate_active_practices
    )
    app.on_message(filters.regex("تمامی تمرین‌ها") & filters.create(is_teacher))(
        teacher_all_practices
    )
    app.on_callback_query(filters.regex(r"teacher_all_practices_page_(\d+)"))(
        teacher_paginate_all_practices
    )
    app.on_callback_query(
        filters.regex(r"teacher_select_practice_(\d+)") & filters.create(is_teacher)
    )(teacher_select_practice)
    app.on_callback_query(
        filters.regex(r"teacher_user_practice_(\d+)") & filters.create(is_teacher)
    )(teacher_user_practice)
    app.on_message(filters.regex("تصحیح شده‌ها") & filters.create(is_teacher))(
        teacher_create_new_practice
    )
    app.on_message(
        filters.regex("تکالیف نیازمند به تصحیح") & filters.create(is_teacher)
    )(teacher_non_correction_practice)
    app.on_callback_query(filters.regex(r"teacher_all_practices_non_page_(\d+)"))(
        teacher_non_correction_practice_page
    )
    app.on_callback_query(
        filters.regex(r"teacher_user_practice_non_(\d+)") & filters.create(is_teacher)
    )(teacher_user_practice_non)
    app.on_message(filters.regex("my settings") & filters.create(is_teacher))(
        teacher_my_settings
    )
    app.on_callback_query(
        filters.regex(r"teacher_correction_(\d+)") & filters.create(is_teacher)
    )(teacher_correction)
