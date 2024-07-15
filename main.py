from pyrogram import Client, filters
from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ForceReply


import db.crud as db
from config import ADMINS_LIST_ID, GROUP_CHAT_ID
from home import send_home_message_admin, send_home_message_teacher, send_home_message_user
from pagination import get_paginated_keyboard, users_paginated_keyboard, teachers_paginated_keyboard, none_teacher_paginated_keyboard


# BOT_TOKEN = "7005827895:AAEd4wtyF-oOftIoNG0PSV0dK4yGZR7fhek"
# api_id = 22868863
# api_hash = "6388e9db9f2febffe4ebf0955ccb8345"



app = Client(
    "./var/ah-score"
    # api_id=api_id, api_hash=api_hash,
    # bot_token=BOT_TOKEN
)


@app.on_message(filters.command("start"))
async def start(client, message):
    if message.from_user.id in ADMINS_LIST_ID:
        await send_home_message_admin(message)
        return

    teacher_row = db.Teacher().read_with_tell_id(tell_id=message.from_user.id)
    print(teacher_row)
    if teacher_row:
        await send_home_message_teacher(message)
        if not teacher_row.chat_id:
            name = []
            if message.from_user.first_name:
                name.append(message.from_user.first_name)
            if message.from_user.last_name:
                name.append(message.from_user.last_name)
            db.Teacher().update_with_tell_id(tell_id=message.from_user.id, chat_id=message.chat.id, name=" ".join(name))
        return

    user_row = db.User().read_with_tell_id(tell_id=message.from_user.id)
    if user_row:
        await send_home_message_user(message)
        return

    # Create a reply keyboard markup with a button to request the user's phone number
    reply_markup = ReplyKeyboardMarkup(
        [
            [KeyboardButton("Send your phone number", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    await message.reply_text("Please share your phone number with me.", reply_markup=reply_markup)


@app.on_message(filters.contact)
async def contact(client, message):
    # data
    user_phone_number = message.contact.phone_number
    name = []
    if message.from_user.first_name:
        name.append(message.from_user.first_name)
    if message.from_user.last_name:
        name.append(message.from_user.last_name)

    # db
    status = db.User().update_with_phone_number(
        phone_number=user_phone_number,
        tell_id=message.from_user.id,
        chat_id=message.chat.id,
        name=" ".join(name)
    )

    if status:
        await send_home_message_user(message)
    else:
        await message.reply_text("No Access, Please send message to admin!")


### back home
@app.on_callback_query(filters.regex(r"back_home"))
async def back_home(client, callback_query: CallbackQuery):
    # Acknowledge the callback query
    await callback_query.answer()
    await callback_query.message.delete()

    if callback_query.from_user.id in ADMINS_LIST_ID:
        await send_home_message_admin(callback_query.message)
    elif db.Teacher().read_with_tell_id(tell_id=callback_query.from_user.id):
        await send_home_message_teacher(callback_query.message)
    else:
        await send_home_message_user(callback_query.message)


####----------------------------------------------------------------------------- admin

@app.on_message(filters.regex("تعریف تمرین جدید") & filters.user(ADMINS_LIST_ID))
async def admin_create_new_practice(client, message):
    user_tell_id = message.from_user.id

    await message.reply_text(
        "با فرمت زیر اطلاعات را وارد کنید:\n"
        "عنوان\n"
        "متن سوال\n"
        "تاریخ شروع - تاریخ پایان\n"
        "اگه فقط یک تاریخ وارد شود امروز بعنوان تاریخ شروع درنظر گرفته میشود!"
        "\n<b>فرمت تاریخ: روز/ماه/سال</b>\n\n"
        "مثال:"
        "<i>\nexample-title\nexample-caption\n10/3/2024-15/3/2024</i>"
        "\n\n<b>***Just send as a reply to this message***</b>",
        reply_markup=ForceReply(selective=True)
    )

    @app.on_message(filters.reply & filters.text & filters.user(user_tell_id))
    async def get_new_practice(client, message):
        data = message.text.split("\n")

        if len(data) == 3 and 1 <= len(data[2].split("-")) <= 2:
            title = data[0]
            caption = data[1]

            all_date = data[2].split("-")
            if len(all_date) == 2:
                db.Practice().add(title, caption, start_date=all_date[0], end_date=all_date[1])
            else:
                db.Practice().add(title, caption, end_date=all_date[0])

            await message.reply_to_message.delete()

            app.remove_handler(get_new_practice)
            await message.reply_text("تمرین با موفقیت اضافه شد.")

            await send_home_message_admin(message)
            return

        await message.reply_text("No!, try again.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("exit!", callback_data=f"back_home")
        ]]))

    # Add the handler
    app.add_handler(get_new_practice)


@app.on_message(filters.regex("تمرین‌های فعال") & filters.user(ADMINS_LIST_ID))
async def admin_available_practices(client, message):
    practices = db.Practice().available()
    if not practices:
        await message.reply_text("هیچ تمرین فعالی موجود نیست!")
        return

    await message.reply_text("تمارین فعال:", reply_markup=get_paginated_keyboard(practices, 0, "admin_active_practices_page", "admin_select_practice"))


@app.on_callback_query(filters.regex(r"admin_active_practices_page_(\d+)"))
async def paginate_active_practices(client, callback_query):
    page = int(callback_query.data.split("_")[-1])
    practices = db.Practice().available()
    await callback_query.message.edit_reply_markup(reply_markup=get_paginated_keyboard(practices, page, "admin_active_practices_page", "admin_select_practice"))


@app.on_message(filters.regex("تمامی تمرین‌ها") & filters.user(ADMINS_LIST_ID))
async def admin_all_practices(client, message):
    practices = db.Practice().all()
    if not practices:
        await message.reply_text("هیچ تمرین فعالی موجود نیست!")
        return

    await message.reply_text("تمامی تمارین:", reply_markup=get_paginated_keyboard(practices, 0, "admin_all_practices_page", "admin_select_practice"))


@app.on_callback_query(filters.regex(r"admin_all_practices_page_(\d+)"))
async def paginate_all_practices(client, callback_query):
    page = int(callback_query.data.split("_")[-1])
    practices = db.Practice().all()
    await callback_query.message.edit_reply_markup(reply_markup=get_paginated_keyboard(practices, page, "admin_all_practices_page", "admin_select_practice"))


@app.on_callback_query(filters.regex(r"admin_select_practice_(\d+)") & filters.user(ADMINS_LIST_ID))
async def admin_select_practice(client, callback_query: CallbackQuery):
    practice_id = int(callback_query.data.split("_")[-1])
    practice = db.Practice().report(pk=practice_id)

    await callback_query.message.delete()

    await callback_query.message.reply_text(
        f"عنوان: {practice[0]}\nمتن سوال: {practice[1]}\n"
        f"تعداد یوزرهایی که پاسخ داده‌اند: {practice[2]}\n"
        f"تعداد پاسخ‌هایی که تصحیح شده‌اند: {practice[3]}",
        reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("حذف تمرین", callback_data=f"admin_delete_practice_{practice_id}")],
        [InlineKeyboardButton("exit!", callback_data=f"back_home")]
        ])
    )


@app.on_callback_query(filters.regex(r"admin_delete_practice_(\d+)") & filters.user(ADMINS_LIST_ID))
async def admin_delete_practice(client, callback_query: CallbackQuery):
    practice_id = int(callback_query.data.split("_")[-1])
    await callback_query.message.delete()

    await callback_query.message.reply_text(
        f"مطمئنی مرد؟",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("بله", callback_data=f"admin_confirm_delete_practice_{practice_id}"),
            InlineKeyboardButton("نه!", callback_data=f"back_home")
        ]])
    )


@app.on_callback_query(filters.regex(r"admin_confirm_delete_practice_(\d+)") & filters.user(ADMINS_LIST_ID))
async def admin_confirm_delete_practice(client, callback_query: CallbackQuery):
    practice_id = (callback_query.data.split("_")[-1])
    db.Practice().delete(pk=practice_id)

    await callback_query.message.delete()
    await callback_query.message.reply_text("حذف شد.")
    await send_home_message_admin(callback_query.message)


@app.on_message(filters.regex("یوزرها") & filters.user(ADMINS_LIST_ID))
async def admin_all_users(client, message):
    users = db.User().all()
    if not users:
        await message.reply_text("هیچ یوزری نیست!")
        return

    await message.reply_text("تمامی یوزرها:", reply_markup=users_paginated_keyboard(users, 0, "admin_user_page", "admin_select_user"))


@app.on_callback_query(filters.regex(r"admin_user_page_(\d+)"))
async def paginate_active_practices(client, callback_query):
    page = int(callback_query.data.split("_")[-1])
    practices = db.User().all()
    await callback_query.message.edit_reply_markup(reply_markup=users_paginated_keyboard(practices, page, "admin_user_page", "admin_select_user"))


@app.on_callback_query(filters.regex(r"admin_select_user_(\d+)") & filters.user(ADMINS_LIST_ID))
async def admin_select_user(client, callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[-1])
    user = db.User().read(pk=user_id)
    await callback_query.message.delete()

    await callback_query.message.reply_text(
        f"id #{user.id}\nPhone: {user.phone_number}\nTelegram ID: {user.tell_id}\n"
        "تعداد تمارینی که تحویل داده: xxx",
        reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("حذف یوزر", callback_data=f"admin_delete_user_{user_id}")],
        ]+[[InlineKeyboardButton("exit!", callback_data=f"back_home")]])
    )


@app.on_callback_query(filters.regex(r"admin_delete_user_(\d+)") & filters.user(ADMINS_LIST_ID))
async def admin_delete_practice(client, callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[-1])
    await callback_query.message.delete()

    await callback_query.message.reply_text(
        f"مطمئنی مرد؟",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("بله", callback_data=f"admin_confirm_delete_user_{user_id}"),
            InlineKeyboardButton("نه!", callback_data=f"back_home")
        ]])
    )


@app.on_callback_query(filters.regex(r"admin_confirm_delete_user_(\d+)") & filters.user(ADMINS_LIST_ID))
async def admin_confirm_delete_user(client, callback_query: CallbackQuery):
    user_id = (callback_query.data.split("_")[-1])
    db.User().delete(pk=user_id)

    await callback_query.message.delete()
    await callback_query.message.reply_text("حذف شد.")
    await send_home_message_admin(callback_query.message)


@app.on_message(filters.regex("اضافه کردن یوزر جدید") & filters.user(ADMINS_LIST_ID))
async def admin_add_user(client, message):
    user_tell_id = message.from_user.id

    await message.reply_text(
        "شماره تلفن یوزر جدید را به این پیام ریپلای کن\n"
        "فرمت صحیح:\n"
        "+989150000000"
        "\n\n"
        "\n\n<b>***Just send as a reply to this message***</b>",
        reply_markup=ForceReply(selective=True)
    )

    # Create a filter for the specific user and assignment
    # user_filter = filters.create(lambda _, __, m: m.from_user.id == user_tell_id)

    @app.on_message(filters.reply & filters.text & filters.user(user_tell_id))
    async def get_new_user_phone(client, message):
        phone_num = message.text
        # +989154797706

        if "+" in phone_num and phone_num[1:].isdigit():
            db.User().add(phone_number=message.text)
            await message.reply_text(f"کاربر {message.text} با موفقیت اضافه شد.")

            await message.reply_to_message.delete()
            app.remove_handler(get_new_user_phone)

            await send_home_message_admin(message)
            return

        await message.reply_text("No!, try again.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("exit!", callback_data=f"back_home")
        ]]))

    # Add the handler
    app.add_handler(get_new_user_phone)


@app.on_message(filters.regex("معلم‌ها") & filters.user(ADMINS_LIST_ID))
async def admin_all_teachers(client, message):
    users = db.Teacher().all()
    if not users:
        await message.reply_text("هیچ معلمی نیست!")
        return

    await message.reply_text("تمامی معلم‌ها:", reply_markup=teachers_paginated_keyboard(users, 0, "admin_teacher_page", "admin_select_teacher"))


@app.on_callback_query(filters.regex(r"admin_teacher_page_(\d+)"))
async def paginate_active_practices(client, callback_query):
    page = int(callback_query.data.split("_")[-1])
    practices = db.Teacher().all()
    await callback_query.message.edit_reply_markup(reply_markup=users_paginated_keyboard(practices, page, "admin_teacher_page", "admin_select_user"))


@app.on_callback_query(filters.regex(r"admin_select_teacher_(\d+)") & filters.user(ADMINS_LIST_ID))
async def admin_select_teacher(client, callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[-1])
    user = db.Teacher().read(pk=user_id)
    await callback_query.message.delete()

    await callback_query.message.reply_text(
        f"id #{user.id}\nTelegram ID: {user.tell_id}\n"
        "تعداد تمارینی که تصحیح کرده: xxx",
        reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("حذف معلم", callback_data=f"admin_delete_teacher_{user_id}")],
        [InlineKeyboardButton("exit!", callback_data=f"back_home")]
        ])
    )


@app.on_callback_query(filters.regex(r"admin_delete_teacher_(\d+)") & filters.user(ADMINS_LIST_ID))
async def admin_delete_teacher(client, callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[-1])
    await callback_query.message.delete()

    await callback_query.message.reply_text(
        f"مطمئنی مرد؟",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("بله", callback_data=f"admin_confirm_delete_teacher_{user_id}"),
            InlineKeyboardButton("نه!", callback_data=f"back_home")
        ]])
    )


@app.on_callback_query(filters.regex(r"admin_confirm_delete_teacher_(\d+)") & filters.user(ADMINS_LIST_ID))
async def admin_confirm_delete_teacher(client, callback_query: CallbackQuery):
    user_id = (callback_query.data.split("_")[-1])
    db.Teacher().delete(pk=user_id)

    await callback_query.message.delete()
    await callback_query.message.reply_text("حذف شد.")
    await send_home_message_admin(callback_query.message)


@app.on_message(filters.regex("اضافه کردن معلم جدید") & filters.user(ADMINS_LIST_ID))
async def admin_add_teacher(client, message):
    user_tell_id = message.from_user.id

    await message.reply_text(
        "یوزرآی‌دی تلگرام معلم جدید رو به این پیام ریپلای کن\n"
        "فرمت صحیح:\n"
        "123456789"
        "\n\n"
        "\n\n<b>***Just send as a reply to this message***</b>",
        reply_markup=ForceReply(selective=True)
    )

    # Create a filter for the specific user and assignment
    # user_filter = filters.create(lambda _, __, m: m.from_user.id == user_tell_id)

    @app.on_message(filters.reply & filters.text & filters.user(user_tell_id))
    async def get_new_teacher_id(client, message):
        phone_num = message.text

        if phone_num.isdigit():
            db.Teacher().add(tell_id=phone_num)
            await message.reply_text(f"کاربر {message.text} با موفقیت اضافه شد.")

            await message.reply_to_message.delete()
            app.remove_handler(get_new_teacher_id)

            await send_home_message_admin(message)
            return

        await message.reply_text("No!, try again.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("exit!", callback_data=f"back_home")
            ]])
        )

    # Add the handler
    app.add_handler(get_new_teacher_id)


@app.on_message(filters.regex("my settings") & filters.user(ADMINS_LIST_ID))
async def admin_my_settings(client, message):
    await message.reply(f"You are <b>admin</b> and your tell-id is <i>{message.from_user.id}</i>")


@app.on_message(filters.regex("تکالیف بدون معلم") & filters.user(ADMINS_LIST_ID))
async def admin_user_practice_none_teacher(client, message):
    practices = db.UserPractice().read_none_teacher()
    if not practices:
        await message.reply_text("هیچ تکلیفی موجود نیست!")
        return

    await message.reply_text("تکالیف بدون معلم:", reply_markup=none_teacher_paginated_keyboard(practices, 0, "admin_practices_none_teacher_page", "admin_select_none_teacher_user"))


@app.on_callback_query(filters.regex(r"admin_practices_none_teacher_page_(\d+)"))
async def paginate_practices_none_teacher(client, callback_query):
    page = int(callback_query.data.split("_")[-1])
    practices = db.UserPractice().read_none_teacher()
    await callback_query.message.edit_reply_markup(reply_markup=none_teacher_paginated_keyboard(practices, page, "admin_practices_none_teacher_page", "admin_select_none_teacher_user"))


@app.on_callback_query(filters.regex(r"admin_select_none_teacher_user_(\d+)") & filters.user(ADMINS_LIST_ID))
async def admin_select_user(client, callback_query: CallbackQuery):
    user_practice_id = int(callback_query.data.split("_")[-1])
    user_practice = db.UserPractice().read(pk=user_practice_id)
    await callback_query.message.delete()

    # print(user_practice.file_link)
    teacher_list = db.Teacher().availble()
    keyboard = []
    for teacher in teacher_list:
        keyboard.append([InlineKeyboardButton(teacher.name, callback_data=f"set_user_practice_teacher_{teacher.id}_{user_practice_id}")])
    keyboard.append([InlineKeyboardButton("exit!", callback_data=f"back_home")])

    await callback_query.message.reply_video(
        video=user_practice.file_link,
        caption="لطفا یک معلم برای این تمرین انتخاب کن:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

    # await callback_query.message.reply_text("بصبر داش")


@app.on_callback_query(filters.regex(r"^set_user_practice_teacher_(\d+)|teacher_pass$") and filters.user(ADMINS_LIST_ID))
async def admin_teacher_selection(client, callback_query):
    teacher_id, new_assignment_id = [int(i) for i in (callback_query.data.split("_")[4:6])]

    db.UserPractice().set_teacher(pk=new_assignment_id, teacher_id=teacher_id)

    # Update the message to remove the inline keyboard
    # await callback_query.message.edit_reply_markup(reply_markup=None)
    await callback_query.message.reply_text("تکلیف با موفقیت تخصیص یافت.")

    await callback_query.message.delete()

    # media_id = callback_query.message.video.file_id
    teacher = db.Teacher().read(pk=teacher_id)
    await app.send_message(chat_id=teacher.chat_id, text="تمرین جدیدی به شما اختصاص یافت")
    # await app.send_video(chat_id=teacher[-1], video=media_id, caption=capt)


##### ------------------------------------------------------------------------------------- teacher
def is_teacher(filter, client, update):
    return db.Teacher().read_with_tell_id(tell_id=update.from_user.id) is not None



@app.on_message(filters.regex("تمرین‌های فعال") & filters.create(is_teacher))
async def teacher_available_practices(client, message):
    practices = db.Practice().available()
    if not practices:
        await message.reply_text("هیچ تمرین فعالی موجود نیست!")
        return

    await message.reply_text("تمارین فعال:", reply_markup=get_paginated_keyboard(practices, 0, "teacher_active_practices_page", "teacher_select_practice"))


@app.on_callback_query(filters.regex(r"teacher_active_practices_page_(\d+)"))
async def teacher_paginate_active_practices(client, callback_query):
    page = int(callback_query.data.split("_")[-1])
    practices = db.Practice().available()
    await callback_query.message.edit_reply_markup(reply_markup=get_paginated_keyboard(practices, page, "teacher_active_practices_page", "teacher_select_practice"))


@app.on_message(filters.regex("تمامی تمرین‌ها") & filters.create(is_teacher))
async def teacher_all_practices(client, message):
    practices = db.Practice().all()
    if not practices:
        await message.reply_text("هیچ تمرین فعالی موجود نیست!")
        return

    await message.reply_text("تمامی تمارین:", reply_markup=get_paginated_keyboard(practices, 0, "teacher_all_practices_page", "teacher_select_practice"))


@app.on_callback_query(filters.regex(r"teacher_all_practices_page_(\d+)"))
async def teacher_paginate_all_practices(client, callback_query):
    page = int(callback_query.data.split("_")[-1])
    practices = db.Practice().available()
    await callback_query.message.edit_reply_markup(reply_markup=get_paginated_keyboard(practices, page, "teacher_all_practices_page", "teacher_select_practice"))


#### optimize
@app.on_callback_query(filters.regex(r"teacher_select_practice_(\d+)") & filters.create(is_teacher))
async def teacher_select_practice(client, callback_query: CallbackQuery):
    practice_id = int(callback_query.data.split("_")[-1])
    practice = db.Practice().read(pk=practice_id)
    users_practice = db.UserPractice().read_with_teacher_tell_id(teacher_tell_id=callback_query.from_user.id, practice_id=practice_id)
    await callback_query.message.delete()
    print(users_practice)

    await callback_query.message.reply_text(
        f"عنوان: {practice.title}\nمتن سوال: {practice.caption}"
        "\nتصحیح نشده‌ها:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"user {i.user_id}", callback_data=f"teacher_user_practice_{i.id}")] for i in users_practice
        ]+[[InlineKeyboardButton("exit!", callback_data=f"back_home")]])
    )


#### optimize
@app.on_callback_query(filters.regex(r"teacher_user_practice_(\d+)") & filters.create(is_teacher))
async def teacher_user_practice(client, callback_query: CallbackQuery):
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
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("تصحیح مجدد" if user_practice.teacher_caption else "تصحیح", callback_data=f"teacher_correction_{user_practice_id}")],
            [InlineKeyboardButton("exit!", callback_data=f"back_home")]
        ])
    )

#### optimize and pagination
@app.on_message(filters.regex("تصحیح شده‌ها") & filters.create(is_teacher))
async def teacher_create_new_practice(client, message):
    users_practice = db.UserPractice().read_with_teacher_tell_id(teacher_tell_id=message.from_user.id, correction=True)

    await message.reply_text(
        "\nتصحیح شده‌ها:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"user {i.user_id}", callback_data=f"teacher_user_practice_{i.id}")] for i in users_practice
        ]+[[InlineKeyboardButton("exit!", callback_data=f"back_home")]])
    )


#### optimize and pagination
@app.on_message(filters.regex("تمرین‌های نیازمند به تصحیح") & filters.create(is_teacher))
async def teacher_create_new_practice(client, message):
    users_practice = db.UserPractice().read_with_teacher_tell_id(teacher_tell_id=message.from_user.id)

    await message.reply_text(
        "\nتصحیح نشده‌ها:",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton(f"user {i.user_id}", callback_data=f"teacher_user_practice_{i.id}")] for i in users_practice
        ]+[[InlineKeyboardButton("exit!", callback_data=f"back_home")]])
    )


@app.on_message(filters.regex("my settings") & filters.create(is_teacher))
async def teacher_create_new_practice(client, message):
    teacher = db.Teacher().read_with_tell_id(tell_id=message.from_user.id)
    await message.reply(f"You are <b>teacher</b> and your id is {teacher[0]}")


@app.on_callback_query(filters.regex(r"teacher_correction_(\d+)") & filters.create(is_teacher))
async def teacher_correction(client, callback_query):
    user_practice_id = int(callback_query.data.split("_")[-1])
    user_tell_id = callback_query.from_user.id


    await callback_query.message.reply_text(
        "پیام خود را ریپلی کنید."
        "\n\n"
        "<b>***Just send as a reply to this message***</b>",
        reply_markup=ForceReply(selective=True)
    )

    @app.on_message(filters.reply & filters.text & filters.user(user_tell_id))
    async def set_teacher_caption(client, message):

        db.UserPractice().set_teacher_caption(pk=user_practice_id, teacher_caption=message.text)
        await message.reply_text(f"با موفقیت ثبت شد.")

        await message.reply_to_message.delete()
        app.remove_handler(set_teacher_caption)

        await app.send_message(
            chat_id=db.User().read_chat_id_user_with_user_practice_id(user_practice_id),
            text=f"تمرین {user_practice_id} شما تصحیح شد."
        )

        await send_home_message_teacher(message)

    await callback_query.message.delete()
    # Add the handler
    app.add_handler(set_teacher_caption)


### ------------------------------------------------------------------------------------------------------ user
def is_user(filter, client, update):
    return db.User().read_with_tell_id(tell_id=update.from_user.id) is not None


@app.on_message(filters.regex("تمرین‌های فعال") & filters.create(is_user))
async def user_available_practices(client, message):
    practices = db.Practice().available()
    if not practices:
        await message.reply_text("هیچ تمرین فعالی موجود نیست!")
        return

    await message.reply_text("تمارین فعال:", reply_markup=get_paginated_keyboard(practices, 0, "user_practices_page", "user_select_practice"))


@app.on_callback_query(filters.regex(r"user_practices_page_(\d+)"))
async def teacher_paginate_all_practices(client, callback_query):
    page = int(callback_query.data.split("_")[-1])
    practices = db.Practice().available()
    await callback_query.message.edit_reply_markup(reply_markup=get_paginated_keyboard(practices, page, "user_practices_page", "user_select_practice"))


@app.on_callback_query(filters.regex(r"user_select_practice_(\d+)") & filters.create(is_user))
async def user_select_practice(client, callback_query: CallbackQuery):
    practice_id = int(callback_query.data.split("_")[-1])
    practice = db.Practice().read(pk=practice_id)
    user_practice = db.UserPractice().read_with_practice_id(practice_id=practice_id, tell_id=callback_query.from_user.id)
    await callback_query.message.delete()

    capt = "تحویل داده نشده!"
    markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("آپلود تمرین", callback_data=f"user_upload_{practice_id}")],
                [InlineKeyboardButton("exit!", callback_data=f"back_home")],
            ])
    if user_practice:
        if user_practice.teacher_caption:
            capt = (
                "تصحیح شده.\n"
                f"بازخورد استاد: {user_practice.teacher_caption}"
            )
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("exit!", callback_data=f"back_home")],
            ])
        else:
            capt = "در انتضار تصحیح"
            markup = InlineKeyboardMarkup([
                [InlineKeyboardButton("ویرایش تمرین", callback_data=f"user_reupload_{practice_id}")],
                [InlineKeyboardButton("exit!", callback_data=f"back_home")],
            ])

    await callback_query.message.reply_text(
        f"عنوان: {practice.title}\nمتن سوال: {practice.caption}\n----"
        f"\nوضعیت نمره: {capt}",
        reply_markup=markup
    )


@app.on_callback_query(filters.regex(r"user_upload_(\d+)") & filters.create(is_user))
async def user_upload(client, callback_query):
    practice_id = int(callback_query.data.split("_")[-1])
    user_tell_id = callback_query.from_user.id

    await callback_query.message.delete()

    await callback_query.message.reply_text(
        "تمرین خود را بصورت ویدیو به این پیام ریپلای کنید."
        "\n\n"
        "<b>***Just send as a reply to this message***</b>",
        reply_markup=ForceReply(selective=True)
    )

    # Create a filter for the specific user and assignment
    # user_filter = filters.create(lambda _, __, m: m.from_user.id == user_tell_id)

    @app.on_message(filters.reply & filters.video & filters.user(user_tell_id))
    async def get_upload(client, message):
        media_id = message.video.file_id

        capt = (
            f"message id: <i>{message.id}</i>\n---\n"
            f"from user @{message.from_user.username}\n"
            f"user caption:\n{message.caption or 'No Caption!'}"
        )

        # Forward the video to the channel
        forwarded_message = await app.send_video(chat_id=GROUP_CHAT_ID, video=media_id, caption=capt)
        telegram_link = forwarded_message.video.file_id
        user_id = db.User().read_with_tell_id(tell_id=user_tell_id).id

        # Store the Telegram link in the database
        new_assignment_id = db.UserPractice().add(
            user_id=user_id,
            practice_id=practice_id,
            file_link=telegram_link,
            user_caption=message.caption
        )

        await message.reply_to_message.delete()
        await message.reply_text("تمرین با موفقیت ثبت شد.")
        await send_home_message_user(message)
        app.remove_handler(get_upload)

        # teacher_list = db.Teacher().all()
        # keyboard = []
        # for teacher in teacher_list:
        #     keyboard.append([InlineKeyboardButton(teacher[-1], callback_data=f"set_user_practice_teacher_{teacher[0]}_{new_assignment_id}")])

        # reply_markup = InlineKeyboardMarkup(keyboard)
        for i in ADMINS_LIST_ID:
            # await app.send_video(chat_id=i, video=media_id, caption="لطفا برای این تمرین معلم تعیین کنید:", reply_markup=reply_markup)
            await app.send_message(chat_id=i, text="تکلیف جدیدی آپلود شد!")

    # Add the handler
    app.add_handler(get_upload)



@app.on_callback_query(filters.regex(r"user_reupload_(\d+)") & filters.create(is_user))
async def user_reupload(client, callback_query):
    user_practice_id = int(callback_query.data.split("_")[-1])
    user_tell_id = callback_query.from_user.id

    await callback_query.message.delete()

    await callback_query.message.reply_text(
        "تمرین خود را بصورت ویدیو به این پیام ریپلای کنید."
        "\n\n"
        "<b>***Just send as a reply to this message***</b>",
        reply_markup=ForceReply(selective=True)
    )

    # Create a filter for the specific user and assignment
    # user_filter = filters.create(lambda _, __, m: m.from_user.id == user_tell_id)

    @app.on_message(filters.reply & filters.video & filters.user(user_tell_id))
    async def get_upload(client, message):
        media_id = message.video.file_id

        capt = (
            f"message id: <i>{message.id}</i>\n---\n"
            f"from user @{message.from_user.username}\n"
            f"user caption:\n{message.caption or 'No Caption!'}"
        )

        # Forward the video to the channel
        forwarded_message = await app.send_video(chat_id=GROUP_CHAT_ID, video=media_id, caption=capt)
        telegram_link = forwarded_message.video.file_id

        # Store the Telegram link in the database
        db.UserPractice().update(
            pk=user_practice_id,
            file_link=telegram_link,
            user_caption=message.caption or None
        )

        await message.reply_to_message.delete()
        await message.reply_text("تمرین با موفقیت ثبت شد.")
        await send_home_message_user(message)
        app.remove_handler(get_upload)

        # teacher_list = db.Teacher().all()
        # keyboard = []
        # for teacher in teacher_list:
        #     keyboard.append([InlineKeyboardButton(str(teacher[1]), callback_data=f"set_user_practice_teacher_{teacher[0]}_{user_practice_id}")])

        # reply_markup = InlineKeyboardMarkup(keyboard)
        # for i in ADMINS_LIST_ID:
        #     await app.send_video(chat_id=i, video=media_id, caption=capt+"لطفا برای این تمرین معلم تعیین کنید:", reply_markup=reply_markup)

    # Add the handler
    app.add_handler(get_upload)


@app.on_message(filters.regex("تحویل داده شده‌ها") & filters.create(is_user))
async def uploaded_practices(client, message):
    user_practices = db.UserPractice().read_with_user_tell_id(message.from_user.id)
    if not user_practices:
        await message.reply_text("هیچ تمرین تحویل داده شده‌ای موجود نیست!")
        return

    await message.reply_text("تکالیف تحویل داده شده:", reply_markup=get_paginated_keyboard(user_practices, 0, "user_user_practices_page", "user_select_practice"))


@app.on_callback_query(filters.regex(r"user_user_practices_page_(\d+)"))
async def teacher_paginate_all_practices(client, callback_query):
    page = int(callback_query.data.split("_")[-1])
    practices = db.UserPractice().read_with_user_tell_id(callback_query.from_user.id)
    await callback_query.message.edit_reply_markup(reply_markup=get_paginated_keyboard(practices, page, "user_user_practices_page", "user_select_practice"))



@app.on_message(filters.regex("my settings") & filters.create(is_user))
async def user_settings(client, message):
    user = db.User().read_with_tell_id(tell_id=message.from_user.id)
    await message.reply(f"You are <b>user</b> and your id is <i>{user.id}</i>")


app.run()
