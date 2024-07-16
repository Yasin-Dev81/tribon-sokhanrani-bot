from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
import asyncio
import datetime

from config import ADMINS_LIST_ID, SQLALCHEMY_DATABASE_URL
from .home import send_home_message_admin
from .pagination import (
    get_paginated_keyboard,
    users_paginated_keyboard,
    teachers_paginated_keyboard,
)
import db.crud as db
from db.models import (
    Practice as PracticeModel,
    UserPractice as UserPracticeModel,
    User as UserModel,
    Teacher as TeacherModel,
)


class DB:
    @property
    def session(self):
        engine = create_engine(SQLALCHEMY_DATABASE_URL)
        Session = sessionmaker(bind=engine)
        return Session()


# تعریف تمرین جدید
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
        "<i>\nexample-title\nexample-caption\n10/3/2024-15/3/2024</i>",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("exit!", callback_data="back_home")]]
        ),
    )
    await message.reply_text(
        "<b>***Just send as a reply to this message***</b>",
        reply_markup=ForceReply(selective=True),
    )

    async def admin_create_new_practice_task(client, message):
        data = message.text.split("\n")

        if len(data) == 3 and 1 <= len(data[2].split("-")) <= 2:
            title = data[0]
            caption = data[1]

            all_date = data[2].split("-")
            if len(all_date) == 2:
                db.Practice().add(
                    title, caption, start_date=all_date[0], end_date=all_date[1]
                )
            else:
                db.Practice().add(title, caption, end_date=all_date[0])

            await message.reply_to_message.delete()

            client.remove_handler(message_handler)
            await message.reply_text("تمرین با موفقیت اضافه شد.")

            await send_home_message_admin(message)
            return

        await message.reply_text(
            "No!, try again.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )

    message_handler = client.on_message(
        filters.reply & filters.text & filters.user(user_tell_id)
    )(admin_create_new_practice_task)


# ویرایش تمرین
async def admin_update_practice(client, callback_query):
    user_tell_id = callback_query.from_user.id
    practice_id = int(callback_query.data.split("_")[-1])

    await callback_query.message.delete()

    await callback_query.message.reply_text(
        "با فرمت زیر اطلاعات را وارد کنید:\n"
        "عنوان\n"
        "متن سوال\n"
        "تاریخ شروع - تاریخ پایان\n"
        "اگه فقط یک تاریخ وارد شود امروز بعنوان تاریخ شروع درنظر گرفته میشود!"
        "\n<b>فرمت تاریخ: روز/ماه/سال</b>\n\n"
        "مثال:"
        "<i>\nexample-title\nexample-caption\n10/3/2024-15/3/2024</i>",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("exit!", callback_data="back_home")]]
        ),
    )
    await callback_query.message.reply_text(
        "<b>***Just send as a reply to this message***</b>",
        reply_markup=ForceReply(selective=True),
    )

    async def get_update_practice(client, message):
        data = message.text.split("\n")

        if len(data) == 3 and 1 <= len(data[2].split("-")) <= 2:
            title = data[0]
            caption = data[1]

            all_date = data[2].split("-")
            if len(all_date) == 2:
                db.Practice().update(
                    practice_id,
                    title,
                    caption,
                    start_date=all_date[0],
                    end_date=all_date[1],
                )
            else:
                db.Practice().update(practice_id, title, caption, end_date=all_date[0])

            await message.reply_to_message.delete()

            client.remove_handler(message_handler)
            await message.reply_text("تمرین با موفقیت ویرایش شد.")

            await send_home_message_admin(message)
            return

        await message.reply_text(
            "No!, try again.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )

    message_handler = client.on_message(
        filters.reply & filters.text & filters.user(user_tell_id)
    )(get_update_practice)


# --------------------------------------------------------------------------------------------------------------------------------------------------


class ActivePractice(DB):
    def __init__(self, app):
        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(
            filters.regex("تمرین‌های فعال") & filters.user(ADMINS_LIST_ID)
        )(self.list)
        self.app.on_callback_query(
            filters.regex(r"admin_active_practice_paginate_list_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.paginate_list)
        self.app.on_callback_query(
            filters.regex(r"admin_active_practice_select_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.select)
        self.app.on_callback_query(
            filters.regex(r"admin_active_practice_user_practice_list_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.user_practice_list)
        self.app.on_callback_query(
            filters.regex(r"admin_active_practice_user_practice_select_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.user_practice_select)
        self.app.on_callback_query(
            filters.regex(r"admin_active_practice_user_practice_teacher_selection_list_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.teacher_selection_list)
        self.app.on_callback_query(
            filters.regex(r"admin_active_practice_user_practice_set_teacher_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.set_teacher_for_user_practice)

    @property
    def practices(self):
        current_time = datetime.datetime.now()
        practices = (
            self.session.query(PracticeModel.id, PracticeModel.title)
            .filter(
                PracticeModel.start_date <= current_time,
                PracticeModel.end_date >= current_time,
            )
            .all()
        )
        return practices

    async def list(self, client, message):
        if not self.practices:
            await message.reply_text("هیچ تمرین فعالی موجود نیست!")
            return

        await message.reply_text(
            "تمارین فعال:",
            reply_markup=get_paginated_keyboard(
                self.practices,
                0,
                "admin_active_practice_paginate_list",
                "admin_active_practice_select",
            ),
        )

    async def paginate_list(self, client, callback_query):
        page = int(callback_query.data.split("_")[-1])

        if not self.practices:
            await callback_query.message.reply_text("هیچ تمرین فعالی موجود نیست!")
            return

        if page == 0:
            await callback_query.message.delete()
            await callback_query.message.reply_text(
                "تمارین فعال:",
                reply_markup=get_paginated_keyboard(
                    self.practices,
                    page,
                    "admin_active_practice_paginate_list",
                    "admin_active_practice_select",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                self.practices,
                page,
                "admin_active_practices_page",
                "admin_active_practice_select",
            )
        )

    def report_practice(self, pk):
        total_count_subquery = (
            self.session.query(func.count(UserPracticeModel.id))
            .filter(UserPracticeModel.practice_id == pk)
            .scalar_subquery()
        )
        teacher_caption_count_subquery = (
            self.session.query(func.count(UserPracticeModel.id))
            .filter(
                UserPracticeModel.practice_id == pk,
                UserPracticeModel.teacher_caption.isnot(None),
            )
            .scalar_subquery()
        )
        practice = (
            self.session.query(
                PracticeModel.title,
                PracticeModel.caption,
                total_count_subquery.label("total_count"),
                teacher_caption_count_subquery.label("teacher_caption_count"),
            )
            .filter(PracticeModel.id == pk)
            .first()
        )
        return practice

    async def select(self, client, callback_query):
        practice_id = int(callback_query.data.split("_")[-1])

        # db
        practice = self.report_practice(pk=practice_id)

        await callback_query.message.delete()

        await callback_query.message.reply_text(
            f"عنوان: {practice.title}\nمتن سوال: {practice.caption}\n"
            f"تعداد یوزرهایی که پاسخ داده‌اند: {practice.total_count}\n"
            f"تعداد پاسخ‌هایی که تصحیح شده‌اند: {practice.teacher_caption_count}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "حذف تمرین",
                            callback_data=f"admin_delete_practice_{practice_id}",
                        ),
                        InlineKeyboardButton(
                            "ویرایش تمرین",
                            callback_data=f"admin_update_practice_{practice_id}",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "مشاهده تکالیف",
                            callback_data=f"admin_active_practice_user_practice_list_{practice_id}_0",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "back",
                            callback_data="admin_active_practice_paginate_list_0",
                        ),
                        InlineKeyboardButton("exit!", callback_data="back_home"),
                    ],
                ]
            ),
        )

    def user_practices(self, pk):
        query = (
            self.session.query(
                UserPracticeModel.id.label("id"),
                UserModel.name.label("title"),
                UserPracticeModel.teacher_caption,
            )
            .join(PracticeModel, UserPracticeModel.practice_id == PracticeModel.id)
            .join(UserModel, UserPracticeModel.user_id == UserModel.id)
            .filter(UserPracticeModel.practice_id == pk)
        )
        return query.all()

    async def user_practice_list(self, client, callback_query):
        practice_id, page = [int(i) for i in (callback_query.data.split("_")[6:8])]
        user_practices = self.user_practices(practice_id)

        if not user_practices:
            await callback_query.message.reply_text("هیچ تکلیفی ارسال نشده!")
            return

        if page == 0:
            practice = self.report_practice(pk=practice_id)
            await callback_query.message.delete()
            await callback_query.message.reply_text(
                f"عنوان: {practice.title}\nمتن سوال: {practice.caption}\n"
                f"تعداد یوزرهایی که پاسخ داده‌اند: {practice.total_count}\n"
                f"تعداد پاسخ‌هایی که تصحیح شده‌اند: {practice.teacher_caption_count}",
                reply_markup=get_paginated_keyboard(
                    user_practices,
                    page,
                    "admin_active_practice_user_practice_list",
                    "admin_active_practice_user_practice_select",
                    back_query=f"admin_active_practice_select_{practice_id}",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                user_practices,
                page,
                "admin_active_practice_user_practice_list",
                "admin_active_practice_user_practice_select",
                back_query=f"admin_active_practice_select_{practice_id}",
            )
        )

    def user_practice(self, pk):
        query = (
            self.session.query(
                UserPracticeModel.id.label("id"),
                UserModel.name.label("username"),
                UserPracticeModel.file_link.label("file_link"),
                UserPracticeModel.user_caption.label("user_caption"),
                UserPracticeModel.teacher_caption.label("teacher_caption"),
                PracticeModel.title.label("title"),
                PracticeModel.caption.label("practice_caption"),
                UserPracticeModel.practice_id.label("practice_id"),
            )
            .join(PracticeModel, PracticeModel.id == UserPracticeModel.practice_id)
            .join(UserModel, UserModel.id == UserPracticeModel.user_id)
            .filter(UserPracticeModel.id == pk)
        )
        return query.first()

    async def user_practice_select(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])
        user_practice = self.user_practice(user_practice_id)

        await callback_query.message.delete()

        capt = "تصحیح نشده!"
        markup = InlineKeyboardMarkup(
            [
                [
                    # fix
                    InlineKeyboardButton(
                        "عوض کردن معلم",
                        callback_data=f"admin_select_active_teacher_user_{user_practice_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "back",
                        callback_data=f"admin_active_practice_user_practice_list_{user_practice.practice_id}_0",
                    ),
                    InlineKeyboardButton("exit!", callback_data="back_home"),
                ],
            ]
        )
        if user_practice.teacher_caption:
            capt = "تصحیح شده.\n" f"تصحیح: {user_practice.teacher_caption}"
            markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "back",
                            callback_data=f"admin_active_practice_user_practice_list_{user_practice.practice_id}_0",
                        ),
                        InlineKeyboardButton("exit!", callback_data="back_home"),
                    ]
                ]
            )

        await callback_query.message.reply_video(
            video=user_practice.file_link,
            caption=f"عنوان سوال: {user_practice.title}\n"
            f"متن سوال: {user_practice.practice_caption}\n"
            f"کاربر: {user_practice.practice_caption}\n"
            f"کپشن کاربر:\n {user_practice.user_caption}\n"
            f"وضعیت تصحیح: {capt}",
            reply_markup=markup,
        )

    async def teacher_selection_list(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])
        # user_practice = db.UserPractice().read(pk=user_practice_id)

        # print(user_practice.file_link)
        teacher_list = db.Teacher().availble()
        keyboard = []
        for teacher in teacher_list:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        teacher.name,
                        callback_data=f"admin_active_practice_user_practice_set_teacher_{teacher.id}_{user_practice_id}",
                    )
                ]
            )
        keyboard.append(
            [
                InlineKeyboardButton(
                    "back", callback_data=f"admin_active_practice_user_practice_select_{user_practice_id}"
                ),
                InlineKeyboardButton("exit!", callback_data="back_home"),
            ]
        )

        # await callback_query.message.delete()
        await callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    def set_teacher_for_user_practice_db(self, pk, teacher_id):
        user_practice = self.session.query(UserPracticeModel).get(pk)
        if user_practice:
            user_practice.teacher_id = teacher_id
            self.session.commit()

    async def set_teacher_for_user_practice(self, client, callback_query):
        teacher_id, new_assignment_id = [
            int(i) for i in (callback_query.data.split("_")[7:9])
        ]

        # self.set_teacher_for_user_practice_db(pk=new_assignment_id, teacher_id=teacher_id)
        db.UserPractice().set_teacher(pk=new_assignment_id, teacher_id=teacher_id)

        await callback_query.message.reply_text("تکلیف با موفقیت تخصیص یافت.")

        await callback_query.message.delete()

        async def send_assignment_notification(client, teacher_id):
            teacher = db.Teacher().read(pk=teacher_id)
            await client.send_message(
                chat_id=teacher.chat_id, text="تمرین جدیدی به شما اختصاص یافت"
            )

        asyncio.create_task(send_assignment_notification(client, teacher_id))


# --------------------------------------------------------------------------------------------------------------------------------------------------


class AllPractice(DB):
    def __init__(self, app):
        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(
            filters.regex("تمامی تمرین‌ها") & filters.user(ADMINS_LIST_ID)
        )(self.list)
        self.app.on_callback_query(
            filters.regex(r"admin_all_practice_paginate_list_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.paginate_list)
        self.app.on_callback_query(
            filters.regex(r"admin_all_practice_select_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.select)
        self.app.on_callback_query(
            filters.regex(r"admin_all_practice_user_practice_list_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.user_practice_list)
        self.app.on_callback_query(
            filters.regex(r"admin_all_practice_user_practice_select_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.user_practice_select)
        self.app.on_callback_query(
            filters.regex(r"admin_all_practice_user_practice_teacher_selection_list_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.teacher_selection_list)
        self.app.on_callback_query(
            filters.regex(r"admin_all_practice_user_practice_set_teacher_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.set_teacher_for_user_practice)

    @property
    def practices(self):
        practices = self.session.query(PracticeModel.id, PracticeModel.title).all()
        return practices

    async def list(self, client, message):
        if not self.practices:
            await message.reply_text("هیچ تمرینی موجود نیست!")
            return

        await message.reply_text(
            "تمامی تمارین:",
            reply_markup=get_paginated_keyboard(
                self.practices,
                0,
                "admin_all_practice_paginate_list",
                "admin_all_practice_select",
            ),
        )

    async def paginate_list(self, client, callback_query):
        page = int(callback_query.data.split("_")[-1])

        if not self.practices:
            await callback_query.message.reply_text("هیچ تمرین فعالی موجود نیست!")
            return

        if page == 0:
            await callback_query.message.delete()
            await callback_query.message.reply_text(
                "تمارین فعال:",
                reply_markup=get_paginated_keyboard(
                    self.practices,
                    page,
                    "admin_all_practice_paginate_list",
                    "admin_all_practice_select",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                self.practices,
                page,
                "admin_all_practices_page",
                "admin_all_practice_select",
            )
        )

    def report_practice(self, pk):
        total_count_subquery = (
            self.session.query(func.count(UserPracticeModel.id))
            .filter(UserPracticeModel.practice_id == pk)
            .scalar_subquery()
        )
        teacher_caption_count_subquery = (
            self.session.query(func.count(UserPracticeModel.id))
            .filter(
                UserPracticeModel.practice_id == pk,
                UserPracticeModel.teacher_caption.isnot(None),
            )
            .scalar_subquery()
        )
        practice = (
            self.session.query(
                PracticeModel.title,
                PracticeModel.caption,
                total_count_subquery.label("total_count"),
                teacher_caption_count_subquery.label("teacher_caption_count"),
            )
            .filter(PracticeModel.id == pk)
            .first()
        )
        return practice

    async def select(self, client, callback_query):
        practice_id = int(callback_query.data.split("_")[-1])

        # db
        practice = self.report_practice(pk=practice_id)

        await callback_query.message.delete()

        await callback_query.message.reply_text(
            f"عنوان: {practice.title}\nمتن سوال: {practice.caption}\n"
            f"تعداد یوزرهایی که پاسخ داده‌اند: {practice.total_count}\n"
            f"تعداد پاسخ‌هایی که تصحیح شده‌اند: {practice.teacher_caption_count}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "حذف تمرین",
                            callback_data=f"admin_delete_practice_{practice_id}",
                        ),
                        InlineKeyboardButton(
                            "ویرایش تمرین",
                            callback_data=f"admin_update_practice_{practice_id}",
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                            "مشاهده تکالیف",
                            callback_data=f"admin_all_practice_user_practice_list_{practice_id}_0",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "back",
                            callback_data="admin_all_practice_paginate_list_0",
                        ),
                        InlineKeyboardButton("exit!", callback_data="back_home"),
                    ],
                ]
            ),
        )

    def user_practices(self, pk):
        query = (
            self.session.query(
                UserPracticeModel.id.label("id"),
                UserModel.name.label("title"),
                UserPracticeModel.teacher_caption,
            )
            .join(PracticeModel, UserPracticeModel.practice_id == PracticeModel.id)
            .join(UserModel, UserPracticeModel.user_id == UserModel.id)
            .filter(UserPracticeModel.practice_id == pk)
        )
        return query.all()

    async def user_practice_list(self, client, callback_query):
        practice_id, page = [int(i) for i in (callback_query.data.split("_")[6:8])]
        user_practices = self.user_practices(practice_id)

        if not user_practices:
            await callback_query.message.reply_text("هیچ تکلیفی ارسال نشده!")
            return

        if page == 0:
            practice = self.report_practice(pk=practice_id)
            await callback_query.message.delete()
            await callback_query.message.reply_text(
                f"عنوان: {practice.title}\nمتن سوال: {practice.caption}\n"
                f"تعداد یوزرهایی که پاسخ داده‌اند: {practice.total_count}\n"
                f"تعداد پاسخ‌هایی که تصحیح شده‌اند: {practice.teacher_caption_count}",
                reply_markup=get_paginated_keyboard(
                    user_practices,
                    page,
                    "admin_all_practice_user_practice_list",
                    "admin_all_practice_user_practice_select",
                    back_query=f"admin_all_practice_select_{practice_id}",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                user_practices,
                page,
                "admin_all_practice_user_practice_list",
                "admin_all_practice_user_practice_select",
                back_query=f"admin_all_practice_select_{practice_id}",
            )
        )

    def user_practice(self, pk):
        query = (
            self.session.query(
                UserPracticeModel.id.label("id"),
                UserModel.name.label("username"),
                UserPracticeModel.file_link.label("file_link"),
                UserPracticeModel.user_caption.label("user_caption"),
                UserPracticeModel.teacher_caption.label("teacher_caption"),
                PracticeModel.title.label("title"),
                PracticeModel.caption.label("practice_caption"),
                UserPracticeModel.practice_id.label("practice_id"),
            )
            .join(PracticeModel, PracticeModel.id == UserPracticeModel.practice_id)
            .join(UserModel, UserModel.id == UserPracticeModel.user_id)
            .filter(UserPracticeModel.id == pk)
        )
        return query.first()

    async def user_practice_select(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])
        user_practice = self.user_practice(user_practice_id)

        await callback_query.message.delete()

        capt = "تصحیح نشده!"
        markup = InlineKeyboardMarkup(
            [
                [
                    # fix
                    InlineKeyboardButton(
                        "عوض کردن معلم",
                        callback_data=f"admin_select_all_teacher_user_{user_practice_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "back",
                        callback_data=f"admin_all_practice_user_practice_list_{user_practice.practice_id}_0",
                    ),
                    InlineKeyboardButton("exit!", callback_data="back_home"),
                ],
            ]
        )
        if user_practice.teacher_caption:
            capt = "تصحیح شده.\n" f"تصحیح: {user_practice.teacher_caption}"
            markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "back",
                            callback_data=f"admin_all_practice_user_practice_list_{user_practice.practice_id}_0",
                        ),
                        InlineKeyboardButton("exit!", callback_data="back_home"),
                    ]
                ]
            )

        await callback_query.message.reply_video(
            video=user_practice.file_link,
            caption=f"عنوان سوال: {user_practice.title}\n"
            f"متن سوال: {user_practice.practice_caption}\n"
            f"کاربر: {user_practice.practice_caption}\n"
            f"کپشن کاربر:\n {user_practice.user_caption}\n"
            f"وضعیت تصحیح: {capt}",
            reply_markup=markup,
        )

    async def teacher_selection_list(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])
        # user_practice = db.UserPractice().read(pk=user_practice_id)

        # print(user_practice.file_link)
        teacher_list = db.Teacher().availble()
        keyboard = []
        for teacher in teacher_list:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        teacher.name,
                        callback_data=f"admin_all_practice_user_practice_set_teacher_{teacher.id}_{user_practice_id}",
                    )
                ]
            )
        keyboard.append(
            [
                InlineKeyboardButton(
                    "back", callback_data=f"admin_all_practice_user_practice_select_{user_practice_id}"
                ),
                InlineKeyboardButton("exit!", callback_data="back_home"),
            ]
        )

        # await callback_query.message.delete()
        await callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    def set_teacher_for_user_practice_db(self, pk, teacher_id):
        user_practice = self.session.query(UserPracticeModel).get(pk)
        if user_practice:
            user_practice.teacher_id = teacher_id
            self.session.commit()

    async def set_teacher_for_user_practice(self, client, callback_query):
        teacher_id, new_assignment_id = [
            int(i) for i in (callback_query.data.split("_")[7:9])
        ]

        # self.set_teacher_for_user_practice_db(pk=new_assignment_id, teacher_id=teacher_id)
        db.UserPractice().set_teacher(pk=new_assignment_id, teacher_id=teacher_id)

        await callback_query.message.reply_text("تکلیف با موفقیت تخصیص یافت.")

        await callback_query.message.delete()

        async def send_assignment_notification(client, teacher_id):
            teacher = db.Teacher().read(pk=teacher_id)
            await client.send_message(
                chat_id=teacher.chat_id, text="تمرین جدیدی به شما اختصاص یافت"
            )

        asyncio.create_task(send_assignment_notification(client, teacher_id))

# --------------------------------------------------------------------------------------------------------------------------------------------------


class NONEPractice(DB):
    def __init__(self, app):
        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(
            filters.regex("تکالیف بدون معلم") & filters.user(ADMINS_LIST_ID)
        )(self.list)
        self.app.on_callback_query(
            filters.regex(r"admin_none_practice_paginate_list_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.paginate_list)
        self.app.on_callback_query(
            filters.regex(r"admin_none_practice_user_practice_select_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.user_practice_select)
        self.app.on_callback_query(
            filters.regex(r"admin_none_practice_user_practice_teacher_selection_list_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.teacher_selection_list)
        self.app.on_callback_query(
            filters.regex(r"admin_none_practice_user_practice_set_teacher_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.set_teacher_for_user_practice)

    @property
    def user_practices(self):
        query = (
            self.session.query(
                UserPracticeModel.id,
                UserModel.name.label("title"),
                PracticeModel.title.label("practice_title"),
                UserPracticeModel.file_link,
                UserPracticeModel.user_caption,
            )
            .join(
                PracticeModel,
                UserPracticeModel.practice_id == PracticeModel.id,
                isouter=True,
            )
            .join(UserModel, UserPracticeModel.user_id == UserModel.id, isouter=True)
            .filter(UserPracticeModel.teacher_id.is_(None))
        )

        return query.all()

    async def list(self, client, message):
        if not self.user_practices:
            await message.reply_text("هیچ تکلیفی موجود نیست!")
            return

        await message.reply_text(
            "تمامی تمارین:",
            reply_markup=get_paginated_keyboard(
                self.user_practices,
                0,
                "admin_none_practice_paginate_list",
                "admin_none_practice_user_practice_select",
            ),
        )

    async def paginate_list(self, client, callback_query):
        page = int(callback_query.data.split("_")[-1])

        if not self.practices:
            await callback_query.message.reply_text("هیچ تمرین فعالی موجود نیست!")
            return

        if page == 0:
            await callback_query.message.delete()
            await callback_query.message.reply_text(
                "تمارین فعال:",
                reply_markup=get_paginated_keyboard(
                    self.practices,
                    page,
                    "admin_none_practice_paginate_list",
                    "admin_none_practice_user_practice_select",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                self.practices,
                page,
                "admin_none_practice_paginate_list",
                "admin_none_practice_user_practice_select",
            )
        )

    def user_practice(self, pk):
        query = (
            self.session.query(
                UserPracticeModel.id.label("id"),
                UserModel.name.label("username"),
                UserPracticeModel.file_link.label("file_link"),
                UserPracticeModel.user_caption.label("user_caption"),
                UserPracticeModel.teacher_caption.label("teacher_caption"),
                PracticeModel.title.label("title"),
                PracticeModel.caption.label("practice_caption"),
                UserPracticeModel.practice_id.label("practice_id"),
                UserPracticeModel.teacher_id.label("techer_id")
            )
            .join(PracticeModel, PracticeModel.id == UserPracticeModel.practice_id)
            .join(UserModel, UserModel.id == UserPracticeModel.user_id)
            .filter(UserPracticeModel.id == pk)
        )
        return query.first()

    async def user_practice_select(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])
        user_practice = self.user_practice(user_practice_id)

        await callback_query.message.delete()

        capt = "تصحیح نشده!"
        x = "تخصیص معلم"
        if user_practice.techer_id:
            x = "عوض کردن معلم"
        markup = InlineKeyboardMarkup(
            [
                [
                    # fix
                    InlineKeyboardButton(
                        x,
                        callback_data=f"admin_none_practice_user_practice_teacher_selection_list_{user_practice_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "back",
                        callback_data=f"admin_none_practice_user_practice_list_{user_practice.practice_id}_0",
                    ),
                    InlineKeyboardButton("exit!", callback_data="back_home"),
                ],
            ]
        )
        if user_practice.teacher_caption:
            capt = "تصحیح شده.\n" f"تصحیح: {user_practice.teacher_caption}"
            markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "back",
                            callback_data=f"admin_none_practice_user_practice_list_{user_practice.practice_id}_0",
                        ),
                        InlineKeyboardButton("exit!", callback_data="back_home"),
                    ]
                ]
            )

        await callback_query.message.reply_video(
            video=user_practice.file_link,
            caption=f"عنوان سوال: {user_practice.title}\n"
            f"متن سوال: {user_practice.practice_caption}\n"
            f"کاربر: {user_practice.practice_caption}\n"
            f"کپشن کاربر:\n {user_practice.user_caption}\n"
            f"وضعیت تصحیح: {capt}",
            reply_markup=markup,
        )

    async def teacher_selection_list(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])
        # user_practice = db.UserPractice().read(pk=user_practice_id)

        # print(user_practice.file_link)
        teacher_list = db.Teacher().availble()
        keyboard = []
        for teacher in teacher_list:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        teacher.name,
                        callback_data=f"admin_none_practice_user_practice_set_teacher_{teacher.id}_{user_practice_id}",
                    )
                ]
            )
        keyboard.append(
            [
                InlineKeyboardButton(
                    "back", callback_data=f"admin_none_practice_user_practice_select_{user_practice_id}"
                ),
                InlineKeyboardButton("exit!", callback_data="back_home"),
            ]
        )

        # await callback_query.message.delete()
        await callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    def set_teacher_for_user_practice_db(self, pk, teacher_id):
        user_practice = self.session.query(UserPracticeModel).get(pk)
        if user_practice:
            user_practice.teacher_id = teacher_id
            self.session.commit()

    async def set_teacher_for_user_practice(self, client, callback_query):
        teacher_id, new_assignment_id = [
            int(i) for i in (callback_query.data.split("_")[7:9])
        ]

        # self.set_teacher_for_user_practice_db(pk=new_assignment_id, teacher_id=teacher_id)
        db.UserPractice().set_teacher(pk=new_assignment_id, teacher_id=teacher_id)

        await callback_query.message.reply_text("تکلیف با موفقیت تخصیص یافت.")

        await callback_query.message.delete()

        async def send_assignment_notification(client, teacher_id):
            teacher = db.Teacher().read(pk=teacher_id)
            await client.send_message(
                chat_id=teacher.chat_id, text="تمرین جدیدی به شما اختصاص یافت"
            )

        asyncio.create_task(send_assignment_notification(client, teacher_id))


async def admin_delete_practice(client, callback_query):
    practice_id = int(callback_query.data.split("_")[-1])
    await callback_query.message.delete()

    await callback_query.message.reply_text(
        "مطمئنی مرد؟",
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "بله",
                        callback_data=f"admin_confirm_delete_practice_{practice_id}",
                    ),
                    InlineKeyboardButton("نه!", callback_data="back_home"),
                ]
            ]
        ),
    )


async def admin_confirm_delete_practice(client, callback_query):
    practice_id = callback_query.data.split("_")[-1]
    db.Practice().delete(pk=practice_id)

    await callback_query.message.delete()
    await callback_query.message.reply_text("حذف شد.")
    await send_home_message_admin(callback_query.message)



# ------------------------------------------------------------------------------------------------------------------------------------
class Users(DB):
    def __init__(self, app):
        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(filters.regex("یوزرها") & filters.user(ADMINS_LIST_ID))(
            self.list
        )
        self.app.on_callback_query(
            filters.regex(r"admin_users_list_(\d+)") & filters.user(ADMINS_LIST_ID)
        )(self.paginate_list)
        self.app.on_callback_query(
            filters.regex(r"admin_users_select_(\d+)") & filters.user(ADMINS_LIST_ID)
        )(self.select)
        self.app.on_callback_query(
            filters.regex(r"admin_users_confirm_delete_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.confirm_delete)
        self.app.on_callback_query(
            filters.regex(r"admin_users_delete_(\d+)") & filters.user(ADMINS_LIST_ID)
        )(self.delete)
        self.app.on_message(
            filters.regex("اضافه کردن یوزر جدید") & filters.user(ADMINS_LIST_ID)
        )(self.add)

    @property
    def users(self):
        return self.session.query(UserModel).all()

    async def list(self, client, message):
        if not self.users:
            await message.reply_text("هیچ یوزری نیست!")
            return

        await message.reply_text(
            "تمامی یوزرها:",
            reply_markup=users_paginated_keyboard(
                self.users, 0, "admin_users_list", "admin_users_select"
            ),
        )

    async def paginate_list(self, client, callback_query):
        page = int(callback_query.data.split("_")[-1])

        if page == 0:
            await callback_query.message.delete()
            await callback_query.message.reply_text(
                "تمامی یوزرها:",
                reply_markup=users_paginated_keyboard(
                    self.users, 0, "admin_users_list", "admin_users_select"
                ),
            )
            return
        await callback_query.message.edit_reply_markup(
            reply_markup=users_paginated_keyboard(
                self.users, page, "admin_users_list", "admin_users_select"
            )
        )

    def user(self, pk):
        return self.session.query(UserModel).get(pk)

    async def select(self, client, callback_query):
        user_id = int(callback_query.data.split("_")[-1])
        user = self.user(user_id)
        await callback_query.message.delete()

        await callback_query.message.reply_text(
            f"id #{user.id}\nPhone: {user.phone_number}\nTelegram ID: {user.tell_id}\n",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "حذف یوزر",
                            callback_data=f"admin_users_confirm_delete_{user_id}",
                        )
                    ],
                ]
                + [
                    [
                        InlineKeyboardButton(
                            "back", callback_data="admin_users_list_0"
                        ),
                        InlineKeyboardButton("exit!", callback_data="back_home"),
                    ]
                ]
            ),
        )

    async def confirm_delete(self, client, callback_query):
        user_id = int(callback_query.data.split("_")[-1])
        await callback_query.message.delete()

        await callback_query.message.reply_text(
            "مطمئنی مرد؟",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "بله", callback_data=f"admin_users_delete_{user_id}"
                        ),
                        InlineKeyboardButton(
                            "نه!", callback_data=f"admin_users_select_{user_id}"
                        ),
                    ]
                ]
            ),
        )

    def delete_db(self, pk):
        user = self.session.query(UserModel).get(pk)
        if user:
            self.session.delete(user)
            self.session.commit()

    async def delete(self, client, callback_query):
        user_id = callback_query.data.split("_")[-1]
        # self.delete_db(user_id)
        db.User().delete(pk=user_id)

        await callback_query.message.delete()
        await callback_query.message.reply_text("حذف شد.")
        await send_home_message_admin(callback_query.message)

    async def add(self, client, message):
        user_tell_id = message.from_user.id

        await message.reply_text(
            "شماره تلفن یوزر جدید را به این پیام ریپلای کن\n"
            "فرمت صحیح:\n"
            "+989150000000"
            "\n\n"
            "\n\n<b>***Just send as a reply to this message***</b>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )
        await message.reply_text(
            "<b>***Just send as a reply to this message***</b>",
            reply_markup=ForceReply(selective=True),
        )

        async def get_new_user_phone(client, message):
            phone_num = message.text
            # print("=="*5, phone_num)
            # +989154797706

            if "+" in phone_num and phone_num[1:].isdigit():
                db.User().add(phone_number=phone_num)
                await message.reply_text(f"کاربر {message.text} با موفقیت اضافه شد.")

                await message.reply_to_message.delete()
                client.remove_handler(message_handler)

                await send_home_message_admin(message)
                return

            await message.reply_text(
                "No!, try again.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("exit!", callback_data="back_home")]]
                ),
            )

        message_handler = client.on_message(
            filters.reply & filters.text & filters.user(user_tell_id)
        )(get_new_user_phone)


class Teachers(DB):
    def __init__(self, app):
        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(filters.regex("معلم‌ها") & filters.user(ADMINS_LIST_ID))(
            self.list
        )
        self.app.on_callback_query(
            filters.regex(r"admin_teachers_list_(\d+)") & filters.user(ADMINS_LIST_ID)
        )(self.paginate_list)
        self.app.on_callback_query(
            filters.regex(r"admin_teachers_select_(\d+)") & filters.user(ADMINS_LIST_ID)
        )(self.select)
        self.app.on_callback_query(
            filters.regex(r"admin_teachers_confirm_delete_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.confirm_delete)
        self.app.on_callback_query(
            filters.regex(r"admin_teachers_delete_(\d+)") & filters.user(ADMINS_LIST_ID)
        )(self.delete)
        self.app.on_message(
            filters.regex("اضافه کردن معلم جدید") & filters.user(ADMINS_LIST_ID)
        )(self.add)

    @property
    def teachers(self):
        return self.session.query(TeacherModel).all()

    async def list(self, client, message):
        if not self.teachers:
            await message.reply_text("هیچ معلمی در دسترس نیست!")
            return

        await message.reply_text(
            "تمامی معلم‌ها:",
            reply_markup=teachers_paginated_keyboard(
                self.teachers, 0, "admin_teachers_list", "admin_teachers_select"
            ),
        )

    async def paginate_list(self, client, callback_query):
        page = int(callback_query.data.split("_")[-1])

        if page == 0:
            await callback_query.message.delete()
            await callback_query.message.reply_text(
                "تمامی معلم‌ها:",
                reply_markup=teachers_paginated_keyboard(
                    self.teachers, 0, "admin_teachers_list", "admin_teachers_select"
                ),
            )
            return
        await callback_query.message.edit_reply_markup(
            reply_markup=teachers_paginated_keyboard(
                self.teachers, page, "admin_teachers_list", "admin_teachers_select"
            )
        )

    def user(self, pk):
        return self.session.query(TeacherModel).get(pk)

    async def select(self, client, callback_query):
        user_id = int(callback_query.data.split("_")[-1])
        user = self.user(user_id)
        await callback_query.message.delete()

        await callback_query.message.reply_text(
            f"id #{user.id}\nTelegram ID: {user.tell_id}\n",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "حذف معلم",
                            callback_data=f"admin_teachers_confirm_delete_{user_id}",
                        )
                    ],
                ]
                + [
                    [
                        InlineKeyboardButton(
                            "back", callback_data="admin_teachers_list_0"
                        ),
                        InlineKeyboardButton("exit!", callback_data="back_home"),
                    ]
                ]
            ),
        )

    async def confirm_delete(self, client, callback_query):
        user_id = int(callback_query.data.split("_")[-1])
        await callback_query.message.delete()

        await callback_query.message.reply_text(
            "مطمئنی مرد؟",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "بله", callback_data=f"admin_teachers_delete_{user_id}"
                        ),
                        InlineKeyboardButton(
                            "نه!", callback_data=f"admin_teachers_select_{user_id}"
                        ),
                    ]
                ]
            ),
        )

    def delete_db(self, pk):
        user = self.session.query(TeacherModel).get(pk)
        if user:
            self.session.delete(user)
            self.session.commit()

    async def delete(self, client, callback_query):
        user_id = callback_query.data.split("_")[-1]
        # self.delete_db(user_id)
        db.Teacher().delete(pk=user_id)

        await callback_query.message.delete()
        await callback_query.message.reply_text("حذف شد.")
        await send_home_message_admin(callback_query.message)

    async def add(self, client, message):
        user_tell_id = message.from_user.id

        await message.reply_text(
            "یوزرآی‌دی تلگرام معلم جدید رو به این پیام ریپلای کن\n"
            "فرمت صحیح:\n"
            "123456789"
            "\n\n"
            "\n\n<b>***Just send as a reply to this message***</b>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )
        await message.reply_text(
            "<b>***Just send as a reply to this message***</b>",
            reply_markup=ForceReply(selective=True),
        )

        async def get_new_user_phone(client, message):
            phone_num = message.text
            # print("=="*5, phone_num)
            # +989154797706

            if phone_num.isdigit():
                db.Teacher().add(tell_id=phone_num)
                await message.reply_text(f"معلم {message.text} با موفقیت اضافه شد.")

                await message.reply_to_message.delete()
                client.remove_handler(message_handler)

                await send_home_message_admin(message)
                return

            await message.reply_text(
                "No!, try again.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("exit!", callback_data="back_home")]]
                ),
            )

        message_handler = client.on_message(
            filters.reply & filters.text & filters.user(user_tell_id)
        )(get_new_user_phone)


async def admin_my_settings(client, message):
    await message.reply(
        f"You are <b>admin</b> and your tell-id is <i>{message.from_user.id}</i>"
    )


async def send_notif_to_users(client, message):
    user_tell_id = message.from_user.id

    await message.reply_text(
        "متن اطلاعیه خود را ریپلی کنید:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("exit!", callback_data="back_home")]]
        ),
    )
    await message.reply_text(
        "<b>***Just send as a reply to this message***</b>",
        reply_markup=ForceReply(selective=True),
    )

    async def get_new_users_notif(client, message):
        data = message.text

        async def send_all_users_notification(client, data):
            users = db.User().all()
            for user in users:
                await client.send_message(chat_id=user.chat_id, text=data)

        asyncio.create_task(send_all_users_notification(client, data))
        await message.reply_to_message.delete()
        client.remove_handler(message_handler)
        await message.reply_text("متن شما با موفقیت در صف تسک‌ها قرار گرفت.")
        await send_home_message_admin(message)

    message_handler = client.on_message(
        filters.reply & filters.text & filters.user(user_tell_id)
    )(get_new_users_notif)


async def send_notif_to_teacher(client, message):
    user_tell_id = message.from_user.id

    await message.reply_text(
        "متن اطلاعیه خود را ریپلی کنید:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("exit!", callback_data="back_home")]]
        ),
    )
    await message.reply_text(
        "<b>***Just send as a reply to this message***</b>",
        reply_markup=ForceReply(selective=True),
    )

    async def get_new_users_notif(client, message):
        data = message.text

        async def send_all_users_notification(client, data):
            users = db.Teacher().all()
            for user in users:
                await client.send_message(chat_id=user.chat_id, text=data)

        asyncio.create_task(send_all_users_notification(client, data))
        await message.reply_to_message.delete()
        client.remove_handler(message_handler)
        await message.reply_text("متن شما با موفقیت در صف تسک‌ها قرار گرفت.")
        await send_home_message_admin(message)

    message_handler = client.on_message(
        filters.reply & filters.text & filters.user(user_tell_id)
    )(get_new_users_notif)


async def send_notif_to_all(client, message):
    user_tell_id = message.from_user.id

    await message.reply_text(
        "متن اطلاعیه خود را ریپلی کنید:",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("exit!", callback_data="back_home")]]
        ),
    )
    await message.reply_text(
        "<b>***Just send as a reply to this message***</b>",
        reply_markup=ForceReply(selective=True),
    )

    async def get_new_users_notif(client, message):
        data = message.text

        async def send_all_users_notification(client, data):
            for admin in ADMINS_LIST_ID:
                await client.send_message(chat_id=admin, text=data)
            teachers = db.Teacher().all()
            for user in teachers:
                await client.send_message(chat_id=user.chat_id, text=data)
            users = db.User().all()
            for user in users:
                await client.send_message(chat_id=user.chat_id, text=data)

        asyncio.create_task(send_all_users_notification(client, data))
        await message.reply_to_message.delete()
        client.remove_handler(message_handler)
        await message.reply_text("متن شما با موفقیت در صف تسک‌ها قرار گرفت.")
        await send_home_message_admin(message)

    message_handler = client.on_message(
        filters.reply & filters.text & filters.user(user_tell_id)
    )(get_new_users_notif)


def register_admin_handlers(app):
    app.on_message(filters.regex("تعریف تمرین جدید") & filters.user(ADMINS_LIST_ID))(
        admin_create_new_practice
    )
    app.on_callback_query(filters.regex(r"admin_update_practice_(\d+)"))(
        admin_update_practice
    )
    app.on_callback_query(
        filters.regex(r"admin_confirm_delete_practice_(\d+)")
        & filters.user(ADMINS_LIST_ID)
    )(admin_confirm_delete_practice)
    app.on_message(filters.regex("my settings") & filters.user(ADMINS_LIST_ID))(
        admin_my_settings
    )
    app.on_message(
        filters.regex("اطلاع‌رسانی به کاربران") & filters.user(ADMINS_LIST_ID)
    )(send_notif_to_users)
    app.on_message(
        filters.regex("اطلاع‌رسانی به معلمان") & filters.user(ADMINS_LIST_ID)
    )(send_notif_to_teacher)
    app.on_message(filters.regex("اطلاع‌رسانی به همه") & filters.user(ADMINS_LIST_ID))(
        send_notif_to_all
    )
