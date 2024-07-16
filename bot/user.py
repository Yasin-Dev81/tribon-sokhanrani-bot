from pyrogram import filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from .pagination import get_paginated_keyboard
import db.crud as db


def is_user(_, __, update):
    return db.User().read_with_tell_id(tell_id=update.from_user.id) is not None


async def user_available_practices(client, message):
    practices = db.Practice().available()
    if not practices:
        await message.reply_text("هیچ تمرین فعالی موجود نیست!")
        return

    await message.reply_text(
        "تمارین فعال:",
        reply_markup=get_paginated_keyboard(
            practices, 0, "user_practices_page", "user_select_practice"
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
                practices, page, "user_practices_page", "user_select_practice"
            ),
        )
        return
    await callback_query.message.edit_reply_markup(
        reply_markup=get_paginated_keyboard(
            practices, page, "user_practices_page", "user_select_practice"
        )
    )


async def user_select_practice(client, callback_query: CallbackQuery):
    practice_id = int(callback_query.data.split("_")[-1])
    practice = db.Practice().read(pk=practice_id)
    user_practice = db.UserPractice().read_with_practice_id_single(
        practice_id=practice_id, tell_id=callback_query.from_user.id
    )
    await callback_query.message.delete()

    capt = "تحویل داده نشده!"
    markup = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "آپلود تمرین", callback_data=f"user_upload_{practice_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    "back", callback_data="user_practices_page_1000000"
                ),
                InlineKeyboardButton("exit!", callback_data=f"back_home"),
            ],
        ]
    )
    if user_practice:
        if user_practice.teacher_caption:
            capt = "تصحیح شده.\n" f"بازخورد استاد: {user_practice.teacher_caption}"
            markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "back", callback_data="user_practices_page_1000000"
                        ),
                        InlineKeyboardButton("exit!", callback_data=f"back_home"),
                    ],
                ]
            )
        else:
            capt = "در انتضار تصحیح"
            markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "ویرایش تمرین", callback_data=f"user_reupload_{practice_id}"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "back", callback_data="user_practices_page_1000000"
                        ),
                        InlineKeyboardButton("exit!", callback_data=f"back_home"),
                    ],
                ]
            )

    await callback_query.message.reply_text(
        f"عنوان: {practice.title}\nمتن سوال: {practice.caption}\n----"
        f"\nوضعیت نمره: {capt}",
        reply_markup=markup,
    )


def register_user_handlers(app):
    app.on_message(filters.regex("تمرین‌های فعال") & filters.create(is_user))(
        user_available_practices
    )
    app.on_callback_query(filters.regex(r"user_practices_page_(\d+)"))(
        teacher_paginate_all_practices
    )
    app.on_callback_query(
        filters.regex(r"user_select_practice_(\d+)") & filters.create(is_user)
    )(user_select_practice)
