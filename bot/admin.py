from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from sqlalchemy import func
import asyncio
import datetime
import re

from config import ADMINS_LIST_ID
from .home import send_home_message_admin
from .pagination import (
    get_paginated_keyboard,
    users_paginated_keyboard,
    teachers_paginated_keyboard,
)
import db


class Practice:
    def __init__(self, app):
        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(
            filters.regex("تعریف تمرین جدید") & filters.user(ADMINS_LIST_ID)
        )(self.add)
        self.app.on_message(
            filters.reply
            & filters.text
            & filters.user(ADMINS_LIST_ID)
            & filters.create(self.is_new_practice_msg)
        )(self.get_new_practice)

    def is_new_practice_msg(filter, client, update):
        return (
            "Just send new practice as a reply to this message"
            in update.reply_to_message.text
        )

    # تعریف تمرین جدید
    async def add(self, client, message):
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
            "<b>Just send new practice as a reply to this message</b>",
            reply_markup=ForceReply(selective=True),
        )

    def add_db(self, title, caption, end_date, start_date=datetime.datetime.now()):
        if isinstance(start_date, str):
            start_date = datetime.datetime.strptime(start_date, "%d/%m/%Y")
        end_date = datetime.datetime.strptime(end_date, "%d/%m/%Y")

        new_practice = db.PracticeModel(
            title=title, caption=caption, start_date=start_date, end_date=end_date
        )
        db.session.add(new_practice)
        db.session.commit()
        return new_practice.id

    async def get_new_practice(self, client, message):
        data = message.text.split("\n")

        if len(data) == 3 and 1 <= len(data[2].split("-")) <= 2:
            title = data[0]
            caption = data[1]

            all_date = data[2].split("-")
            if len(all_date) == 2:
                new_practice_id = self.add_db(
                    title, caption, start_date=all_date[0], end_date=all_date[1]
                )
            else:
                new_practice_id = self.add_db(title, caption, end_date=all_date[0])

            await message.reply_to_message.delete()

            await message.reply_text("تمرین با موفقیت اضافه شد.")
            asyncio.create_task(
                self.send_alls_notification(
                    client, new_practice_id, "تمرین جدید بارگذاری شد!"
                )
            )

            await send_home_message_admin(message)
            return

        await message.reply_text(
            "No!, try again.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )

    @property
    def users(self):
        return (
            db.session.query(db.UserModel)
            .filter(db.UserModel.chat_id.is_not(None))
            .all()
        )

    @property
    def teachers(self):
        return (
            db.session.query(db.TeacherModel)
            .filter(db.TeacherModel.chat_id.is_not(None))
            .all()
        )

    async def send_alls_notification(self, client, new_practice_id, data):
        for admin in ADMINS_LIST_ID:
            await client.send_message(
                chat_id=admin,
                text=data,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "مشاهده",
                                callback_data=f"admin_all_practice_select_{new_practice_id}",
                            )
                        ]
                    ]
                ),
            )
        for user in self.teachers:
            await client.send_message(
                chat_id=user.chat_id,
                text=data,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "مشاهده",
                                callback_data=f"teacher_all_practice_select_{new_practice_id}",
                            )
                        ]
                    ]
                ),
            )
        for user in self.users:
            await client.send_message(
                chat_id=user.chat_id,
                text=data,
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("مشاهده", callback_data="back_home")]]
                ),
            )


class BasePractice:
    def __init__(self, app, type="all") -> None:
        self.app = app
        self.type = type
        self.base_register_handlers()

    def base_register_handlers(self):
        self.app.on_callback_query(
            filters.regex(rf"admin_{self.type}_practice_select_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.select)
        self.app.on_callback_query(
            filters.regex(rf"admin_{self.type}_practice_user_practice_list_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.user_practice_list)
        self.app.on_callback_query(
            filters.regex(rf"admin_{self.type}_practice_user_practice_select_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.user_practice_select)
        self.app.on_callback_query(
            filters.regex(
                rf"admin_{self.type}_practice_user_practice_teacher_selection_list_(\d+)"
            )
            & filters.user(ADMINS_LIST_ID)
        )(self.teacher_selection_list)
        self.app.on_callback_query(
            filters.regex(
                rf"admin_{self.type}_practice_user_practice_set_teacher_(\d+)"
            )
            & filters.user(ADMINS_LIST_ID)
        )(self.set_teacher_for_user_practice)
        self.app.on_callback_query(
            filters.regex(rf"admin_{self.type}_practice_practice_confirm_delete_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.confirm_delete)
        self.app.on_callback_query(
            filters.regex(rf"admin_{self.type}_practice_practice_delete_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.delete)

    @staticmethod
    def report_practice(pk):
        total_count_subquery = (
            db.session.query(func.count(db.UserPracticeModel.id))
            .filter(db.UserPracticeModel.practice_id == pk)
            .scalar_subquery()
        )
        teacher_caption_count_subquery = (
            db.session.query(func.count(db.UserPracticeModel.id))
            .filter(
                db.UserPracticeModel.practice_id == pk,
                db.UserPracticeModel.teacher_caption.isnot(None),
            )
            .scalar_subquery()
        )
        practice = (
            db.session.query(
                db.PracticeModel.title,
                db.PracticeModel.caption,
                total_count_subquery.label("total_count"),
                teacher_caption_count_subquery.label("teacher_caption_count"),
            )
            .filter(db.PracticeModel.id == pk)
            .first()
        )
        return practice

    async def select(self, client, callback_query):
        practice_id = int(callback_query.data.split("_")[-1])

        # db
        practice = self.report_practice(pk=practice_id)

        await callback_query.message.delete()

        await callback_query.message.reply_text(
            f"📌 عنوان: {practice.title}\n🔖 متن سوال: {practice.caption}\n"
            f"تعداد یوزرهایی که پاسخ داده‌اند: {practice.total_count}\n"
            f"تعداد پاسخ‌هایی که تحلیل سخنرانی شده‌اند: {practice.teacher_caption_count}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🗑 حذف تمرین",
                            callback_data=f"admin_{self.type}_practice_practice_confirm_delete_{practice_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "مشاهده تکالیف",
                            callback_data=f"admin_{self.type}_practice_user_practice_list_{practice_id}_0",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔙 بازگشت",
                            callback_data=f"admin_{self.type}_practice_paginate_list_0",
                        ),
                        InlineKeyboardButton("exit!", callback_data="back_home"),
                    ],
                ]
            ),
        )

    @staticmethod
    def user_practices(pk):
        query = (
            db.session.query(
                db.UserPracticeModel.id.label("id"),
                db.UserModel.name.label("title"),
                db.UserPracticeModel.teacher_caption,
            )
            .join(
                db.PracticeModel,
                db.UserPracticeModel.practice_id == db.PracticeModel.id,
            )
            .join(db.UserModel, db.UserPracticeModel.user_id == db.UserModel.id)
            .filter(db.UserPracticeModel.practice_id == pk)
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
                f"📌 عنوان: {practice.title}\n🔖 متن سوال: {practice.caption}\n"
                f"تعداد یوزرهایی که پاسخ داده‌اند: {practice.total_count}\n"
                f"تعداد پاسخ‌هایی که تحلیل سخنرانی شده‌اند: {practice.teacher_caption_count}",
                reply_markup=get_paginated_keyboard(
                    user_practices,
                    page,
                    f"admin_{self.type}_practice_user_practice_list",
                    f"admin_{self.type}_practice_user_practice_select",
                    back_query=f"admin_{self.type}_practice_select_{practice_id}",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                user_practices,
                page,
                f"admin_{self.type}_practice_user_practice_list",
                f"admin_{self.type}_practice_user_practice_select",
                back_query=f"admin_{self.type}_practice_select_{practice_id}",
            )
        )

    @staticmethod
    def user_practice(pk):
        query = (
            db.session.query(
                db.UserPracticeModel.id.label("id"),
                db.UserModel.name.label("username"),
                db.UserPracticeModel.file_link.label("file_link"),
                db.UserPracticeModel.user_caption.label("user_caption"),
                db.UserPracticeModel.teacher_caption.label("teacher_caption"),
                db.PracticeModel.title.label("title"),
                db.PracticeModel.caption.label("practice_caption"),
                db.UserPracticeModel.practice_id.label("practice_id"),
                db.UserModel.user_type,
                db.UserModel.phone_number,
            )
            .join(
                db.PracticeModel,
                db.PracticeModel.id == db.UserPracticeModel.practice_id,
            )
            .join(db.UserModel, db.UserModel.id == db.UserPracticeModel.user_id)
            .filter(db.UserPracticeModel.id == pk)
        )
        return query.first()

    async def user_practice_select(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])
        user_practice = self.user_practice(user_practice_id)

        await callback_query.message.delete()

        capt = "تحلیل سخنرانی نشده!"
        markup = InlineKeyboardMarkup(
            [
                [
                    # fix
                    InlineKeyboardButton(
                        "عوض کردن معلم",
                        callback_data=f"admin_{self.type}_practice_user_practice_teacher_selection_list_{user_practice_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🔙 بازگشت",
                        callback_data=f"admin_{self.type}_practice_user_practice_list_{user_practice.practice_id}_0",
                    ),
                    InlineKeyboardButton("exit!", callback_data="back_home"),
                ],
            ]
        )
        if user_practice.teacher_caption:
            capt = (
                "تحلیل سخنرانی شده.\n" f"تحلیل سخنرانی: {user_practice.teacher_caption}"
            )
            markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 بازگشت",
                            callback_data=f"admin_{self.type}_practice_user_practice_list_{user_practice.practice_id}_0",
                        ),
                        InlineKeyboardButton("exit!", callback_data="back_home"),
                    ]
                ]
            )

        await callback_query.message.reply_video(
            video=user_practice.file_link,
            caption=f"📌 عنوان سوال: {user_practice.title}\n"
            f"🔖 متن سوال: {user_practice.practice_caption}\n"
            f"👤 کاربر: {user_practice.username}\n"
            f"نوع کاربر: {user_practice.user_type.value}\n"
            f"شماره کاربر: {user_practice.phone_number}\n"
            f"کپشن کاربر:\n {user_practice.user_caption}\n"
            f"وضعیت تحلیل سخنرانی: {capt}",
            reply_markup=markup,
        )

    async def teacher_selection_list(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])
        teacher_list = (
            db.session.query(db.TeacherModel)
            .filter(db.TeacherModel.chat_id.is_not(None))
            .all()
        )
        keyboard = []
        for teacher in teacher_list:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        teacher.name,
                        callback_data=f"admin_{self.type}_practice_user_practice_set_teacher_{teacher.id}_{user_practice_id}",
                    )
                ]
            )
        keyboard.append(
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data=f"admin_{self.type}_practice_user_practice_select_{user_practice_id}",
                ),
                InlineKeyboardButton("exit!", callback_data="back_home"),
            ]
        )

        # await callback_query.message.delete()
        await callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @staticmethod
    def set_teacher_for_user_practice_db(pk, teacher_id):
        user_practice = db.session.query(db.UserPracticeModel).get(pk)
        if user_practice:
            user_practice.teacher_id = teacher_id
            db.session.commit()
            return True
        return False

    async def set_teacher_for_user_practice(self, client, callback_query):
        teacher_id, new_assignment_id = [
            int(i) for i in (callback_query.data.split("_")[7:9])
        ]

        if self.set_teacher_for_user_practice_db(
            pk=new_assignment_id, teacher_id=teacher_id
        ):
            await callback_query.message.reply_text("تکلیف با موفقیت تخصیص یافت.")

            await callback_query.message.delete()

            async def send_assignment_notification(
                client, teacher_id, user_practice_id
            ):
                # teacher = db.Teacher().read(pk=teacher_id)
                teacher = db.session.query(db.TeacherModel).get(teacher_id)
                await client.send_message(
                    chat_id=teacher.chat_id,
                    text="تمرین جدیدی به شما اختصاص یافت",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "مشاهده",
                                    callback_data=f"teacher_none_practice_user_practice_select_{user_practice_id}",
                                )
                            ]
                        ]
                    ),
                )

            asyncio.create_task(
                send_assignment_notification(client, teacher_id, new_assignment_id)
            )
        else:
            await callback_query.message.reply_text("error!")

            await callback_query.message.delete()

    async def confirm_delete(self, client, callback_query):
        practice_id = int(callback_query.data.split("_")[-1])
        await callback_query.message.delete()

        await callback_query.message.reply_text(
            "مطمئنی مرد؟",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "بله",
                            callback_data=f"admin_{self.type}_practice_practice_delete_{practice_id}",
                        ),
                        InlineKeyboardButton(
                            "نه!",
                            callback_data=f"admin_{self.type}_practice_select_{practice_id}",
                        ),
                    ]
                ]
            ),
        )

    async def delete(self, client, callback_query):
        practice_id = callback_query.data.split("_")[-1]
        # db.Practice().delete(pk=practice_id)
        if self.delete_db(practice_id):
            await callback_query.message.delete()
            await callback_query.message.reply_text("🗑 حذف شد.")
            await send_home_message_admin(callback_query.message)
        else:
            await callback_query.message.delete()
            await callback_query.message.reply_text("error!")
            await send_home_message_admin(callback_query.message)

    @staticmethod
    def delete_db(pk):
        practice = db.session.query(db.PracticeModel).get(pk)
        if practice:
            db.session.delete(practice)
            db.session.commit()
            return True
        return False


class ActivePractice(BasePractice):
    def __init__(self, app, type="active") -> None:
        super().__init__(app, type)

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

    @property
    def practices(self):
        current_time = datetime.datetime.now()
        practices = (
            db.session.query(db.PracticeModel.id, db.PracticeModel.title)
            .filter(
                db.PracticeModel.start_date <= current_time,
                db.PracticeModel.end_date >= current_time,
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
                "admin_active_practice_paginate_list",
                "admin_active_practice_select",
            )
        )


class AllPractice(BasePractice):
    def __init__(self, app, type="all") -> None:
        super().__init__(app, type)
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

    @property
    def practices(self):
        practices = db.session.query(db.PracticeModel.id, db.PracticeModel.title).all()
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
                "admin_all_practice_paginate_list",
                "admin_all_practice_select",
            )
        )


class NONEPractice:
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
            filters.regex(
                r"admin_none_practice_user_practice_teacher_selection_list_(\d+)"
            )
            & filters.user(ADMINS_LIST_ID)
        )(self.teacher_selection_list)
        self.app.on_callback_query(
            filters.regex(r"admin_none_practice_user_practice_set_teacher_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.set_teacher_for_user_practice)

    @property
    def user_practices(self):
        query = (
            db.session.query(
                db.UserPracticeModel.id,
                (db.UserModel.name + " - " + db.PracticeModel.title).label("title"),
            )
            .join(
                db.PracticeModel,
                db.UserPracticeModel.practice_id == db.PracticeModel.id,
                isouter=True,
            )
            .join(
                db.UserModel,
                db.UserPracticeModel.user_id == db.UserModel.id,
                isouter=True,
            )
            .filter(db.UserPracticeModel.teacher_id.is_(None))
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

        if not self.user_practices:
            await callback_query.message.delete()
            await callback_query.message.reply_text("هیچ تمرین فعالی موجود نیست!")
            return

        if page == 0:
            await callback_query.message.delete()
            await callback_query.message.reply_text(
                "تمارین فعال:",
                reply_markup=get_paginated_keyboard(
                    self.user_practices,
                    page,
                    "admin_none_practice_paginate_list",
                    "admin_none_practice_user_practice_select",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                self.user_practices,
                page,
                "admin_none_practice_paginate_list",
                "admin_none_practice_user_practice_select",
            )
        )

    @staticmethod
    def user_practice(pk):
        query = (
            db.session.query(
                db.UserPracticeModel.id.label("id"),
                db.UserModel.name.label("username"),
                db.UserPracticeModel.file_link.label("file_link"),
                db.UserPracticeModel.user_caption.label("user_caption"),
                db.UserPracticeModel.teacher_caption.label("teacher_caption"),
                db.PracticeModel.title.label("title"),
                db.PracticeModel.caption.label("practice_caption"),
                db.UserPracticeModel.practice_id.label("practice_id"),
                db.UserPracticeModel.teacher_id.label("techer_id"),
                db.UserModel.user_type,
                db.UserModel.phone_number,
            )
            .join(
                db.PracticeModel,
                db.PracticeModel.id == db.UserPracticeModel.practice_id,
            )
            .join(db.UserModel, db.UserModel.id == db.UserPracticeModel.user_id)
            .filter(db.UserPracticeModel.id == pk)
        )
        return query.first()

    async def user_practice_select(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])
        user_practice = self.user_practice(user_practice_id)

        await callback_query.message.delete()

        capt = "تحلیل سخنرانی نشده!"
        x = "تخصیص معلم"
        if user_practice.techer_id and not user_practice.teacher_caption:
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
                        "🔙 بازگشت",
                        callback_data="admin_none_practice_paginate_list_0",
                    ),
                    InlineKeyboardButton("exit!", callback_data="back_home"),
                ],
            ]
        )
        if user_practice.teacher_caption:
            capt = (
                "تحلیل سخنرانی شده.\n" f"تحلیل سخنرانی: {user_practice.teacher_caption}"
            )
            markup = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 بازگشت",
                            callback_data="admin_none_practice_paginate_list_0",
                        ),
                        InlineKeyboardButton("exit!", callback_data="back_home"),
                    ]
                ]
            )

        await callback_query.message.reply_video(
            video=user_practice.file_link,
            caption=f"📌 عنوان سوال: {user_practice.title}\n"
            f"🔖 متن سوال: {user_practice.practice_caption}\n"
            f"👤 کاربر: {user_practice.username}\n"
            f"نوع کاربر: {user_practice.user_type.value}\n"
            f"شماره کاربر: {user_practice.phone_number}\n"
            f"کپشن کاربر:\n {user_practice.user_caption}\n"
            f"وضعیت تحلیل سخنرانی: {capt}",
            reply_markup=markup,
        )

    async def teacher_selection_list(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])

        teacher_list = (
            db.session.query(db.TeacherModel)
            .filter(db.TeacherModel.chat_id.is_not(None))
            .all()
        )
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
                    "🔙 بازگشت",
                    callback_data=f"admin_none_practice_user_practice_select_{user_practice_id}",
                ),
                InlineKeyboardButton("exit!", callback_data="back_home"),
            ]
        )

        # await callback_query.message.delete()
        await callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    @staticmethod
    def set_teacher_for_user_practice_db(pk, teacher_id):
        user_practice = db.session.query(db.UserPracticeModel).get(pk)
        if user_practice:
            user_practice.teacher_id = teacher_id
            db.session.commit()
            return True
        else:
            return False

    async def set_teacher_for_user_practice(self, client, callback_query):
        teacher_id, new_assignment_id = [
            int(i) for i in (callback_query.data.split("_")[7:9])
        ]

        if self.set_teacher_for_user_practice_db(
            pk=new_assignment_id, teacher_id=teacher_id
        ):
            await callback_query.message.reply_text("تکلیف با موفقیت تخصیص یافت.")

            await callback_query.message.delete()

            async def send_assignment_notification(
                client, teacher_id, user_practice_id
            ):
                # teacher = db.Teacher().read(pk=teacher_id)
                teacher = db.session.query(db.TeacherModel).get(teacher_id)
                await client.send_message(
                    chat_id=teacher.chat_id,
                    text="تمرین جدیدی به شما اختصاص یافت",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "مشاهده",
                                    callback_data=f"teacher_none_practice_user_practice_select_{user_practice_id}",
                                )
                            ]
                        ]
                    ),
                )

            asyncio.create_task(
                send_assignment_notification(client, teacher_id, new_assignment_id)
            )
        else:
            await callback_query.message.reply_text("error!")

            await callback_query.message.delete()


class Users:
    def __init__(self, app):
        self.app = app
        self.register_handlers()

    @staticmethod
    def is_add_user(filter, client, update):
        return (
            "Just send phone number as a reply to this message"
            in update.reply_to_message.text
        )

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
        self.app.on_message(
            filters.reply
            & filters.text
            & filters.user(ADMINS_LIST_ID)
            & filters.create(self.is_add_user)
        )(self.get_new_user_phone)
        self.app.on_callback_query(
            filters.regex(r"admin_users_set_type_(\w+)_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.set_type)

    @property
    def users(self):
        return db.session.query(db.UserModel).all()

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

    @staticmethod
    def user(pk):
        return db.session.query(db.UserModel).get(pk)

    async def select(self, client, callback_query):
        user_id = int(callback_query.data.split("_")[-1])
        user = self.user(user_id)
        await callback_query.message.delete()

        await callback_query.message.reply_text(
            f"id #{user.id}\nPhone: {user.phone_number}\nTelegram ID: {user.tell_id or 'Not set!'}"
            f"\nName: {user.name or 'Not set!'}\nUser type: {user.user_type.value or 'Not set!'}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🗑 حذف یوزر",
                            callback_data=f"admin_users_confirm_delete_{user_id}",
                        )
                    ],
                ]
                + [
                    [
                        InlineKeyboardButton(
                            "🔙 بازگشت", callback_data="admin_users_list_0"
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

    @staticmethod
    def delete_db(pk):
        user = db.session.query(db.UserModel).get(pk)
        if user:
            db.session.delete(user)
            db.session.commit()
            return True
        return False

    async def delete(self, client, callback_query):
        user_id = callback_query.data.split("_")[-1]
        # db.User().delete(pk=user_id)
        if self.delete_db(user_id):
            await callback_query.message.delete()
            await callback_query.message.reply_text("🗑 حذف شد.")
            await send_home_message_admin(callback_query.message)
        else:
            await callback_query.message.delete()
            await callback_query.message.reply_text("error!")

    async def add(self, client, message):
        await message.reply_text(
            "شماره تلفن یوزر جدید را به این پیام ریپلای کن\n"
            "فرمت صحیح:\n"
            "+989150000000",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )
        await message.reply_text(
            "<b>Just send phone number as a reply to this message</b>",
            reply_markup=ForceReply(selective=True),
        )

    @staticmethod
    def add_db(phone_num):
        new_user = db.UserModel(phone_number=phone_num)
        db.session.add(new_user)
        db.session.commit()
        return new_user.id

    async def get_new_user_phone(self, client, message):
        phone_num = message.text
        # +989154797706

        if "+" in phone_num and len(phone_num) == 13:
            user_id = self.add_db(phone_num)
            # await message.reply_text(f"کاربر {message.text} با موفقیت اضافه شد.")

            await message.reply_to_message.delete()

            # await send_home_message_admin(message)
            await message.reply_text(
                "لطفا نوع یوزر را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                i.value,
                                callback_data=f"admin_users_set_type_{i.name}_{user_id}",
                            )
                            for i in db.UserType
                        ],
                        [InlineKeyboardButton("exit!", callback_data="back_home")],
                    ]
                ),
            )
            return

        await message.reply_text(
            "No!, try again.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )

    @staticmethod
    def update_user_type(pk, user_type):
        user = db.session.query(db.UserModel).get(pk)
        if user:
            user.user_type = user_type
            db.session.commit()
            return True
        return False

    async def set_type(self, client, callback_query):
        match = re.search(r"admin_users_set_type_(\w+)_(\d+)", callback_query.data)
        if match:
            user_type = match.group(1)
            user_id = match.group(2)
            # print(user_id, user_type, db.UserType[user_type].value)
            if self.update_user_type(user_id, db.UserType[user_type]):
                await callback_query.message.delete()
                await callback_query.message.reply_text("کاربر با موفقیت اضافه شد.")
                await send_home_message_admin(callback_query.message)
            else:
                await callback_query.message.reply_text("error!")


class Teachers:
    def __init__(self, app):
        self.app = app
        self.register_handlers()

    @staticmethod
    def is_add_teacher(filter, client, update):
        return (
            "Just send tell-id as a reply to this message"
            in update.reply_to_message.text
        )

    @staticmethod
    def is_update_teacher(filter, client, update):
        return (
            "Just send teacher name as a reply to this message"
            in update.reply_to_message.text
        )

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
        self.app.on_message(
            filters.reply
            & filters.text
            & filters.user(ADMINS_LIST_ID)
            & filters.create(self.is_add_teacher)
        )(self.get_new_teacher_id)
        self.app.on_message(
            filters.reply
            & filters.text
            & filters.user(ADMINS_LIST_ID)
            & filters.create(self.is_update_teacher)
        )(self.set_teacher_name)

    @property
    def teachers(self):
        return db.session.query(db.TeacherModel).all()

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
        return db.session.query(db.TeacherModel).get(pk)

    async def select(self, client, callback_query):
        user_id = int(callback_query.data.split("_")[-1])
        user = self.user(user_id)
        await callback_query.message.delete()

        await callback_query.message.reply_text(
            f"id #{user.id}\nTelegram ID: {user.tell_id}\nName: {user.name}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🗑 حذف معلم",
                            callback_data=f"admin_teachers_confirm_delete_{user_id}",
                        )
                    ],
                ]
                + [
                    [
                        InlineKeyboardButton(
                            "🔙 بازگشت", callback_data="admin_teachers_list_0"
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

    @staticmethod
    def delete_db(pk):
        user = db.session.query(db.TeacherModel).get(pk)
        if user:
            db.session.delete(user)
            db.session.commit()
            return True
        return False

    async def delete(self, client, callback_query):
        user_id = callback_query.data.split("_")[-1]

        if self.delete_db(user_id):
            await callback_query.message.delete()
            await callback_query.message.reply_text("🗑 حذف شد.")
            await send_home_message_admin(callback_query.message)
        else:
            await callback_query.message.delete()
            await callback_query.message.reply_text("error!")
            await send_home_message_admin(callback_query.message)

    async def add(self, client, message):
        await message.reply_text(
            "شماره تلفن معلم جدید رو به این پیام ریپلای کن\n"
            "فرمت صحیح:\n"
            "<i>+989150000000</i>",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )
        await message.reply_text(
            "<b>Just send tell-id as a reply to this message</b>",
            reply_markup=ForceReply(selective=True),
        )

    @staticmethod
    def add_db(phone_num):
        new_teacher = db.TeacherModel(phone_number=phone_num)
        db.session.add(new_teacher)
        db.session.commit()
        return new_teacher.id

    async def get_new_teacher_id(self, client, message):
        phone_num = message.text

        if "+" in phone_num and len(phone_num) == 13:
            teacher_id = self.add_db(phone_num)
            await message.reply_to_message.delete()

            await message.reply_text(
                f"معلم {message.text} با موفقیت اضافه شد."
                "حال نام معلم را ارسال کنید.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("exit!", callback_data="back_home")]]
                ),
            )
            await message.reply_text(
                f"{teacher_id}\n"
                "<b>Just send teacher name as a reply to this message</b>",
                reply_markup=ForceReply(selective=True),
            )

            # await send_home_message_admin(message)
            return

        await message.reply_text(
            "No!, try again.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )

    @staticmethod
    def set_teacher_name_db(pk, name):
        teahcer = db.session.query(db.TeacherModel).get(pk)
        if teahcer:
            teahcer.name = name
            db.session.commit()
            return True
        return False

    async def set_teacher_name(self, client, message):
        teacher_id = int(message.reply_to_message.text.split("\n")[0])

        if self.set_teacher_name_db(teacher_id, message.text):
            await message.reply_text("با موفقیت ثبت شد.")
        else:
            await message.reply_text("error!")

        await message.reply_to_message.delete()
        await send_home_message_admin(message)


async def admin_my_settings(client, message):
    await message.reply(
        f"You are <b>admin</b> and your tell-id is <i>{message.from_user.id}</i>"
    )


class Notifiaction:
    base_caption = "📢  اطلاع رسانی \n"

    def __init__(self, app):
        self.app = app
        self.register_handlers()

    @staticmethod
    def is_notif_to_all(filter, client, update):
        return (
            "Just send notif as a reply to this message" in update.reply_to_message.text
        )

    @staticmethod
    def is_notif_to_users(filter, client, update):
        return (
            "Just send users-notif as a reply to this message"
            in update.reply_to_message.text
        )

    @staticmethod
    def is_notif_to_teachers(filter, client, update):
        return (
            "Just send teachers-notif as a reply to this message"
            in update.reply_to_message.text
        )

    def register_handlers(self):
        self.app.on_message(
            filters.regex("ارسال نوتیفیکیشن") & filters.user(ADMINS_LIST_ID)
        )(self.select_type)
        self.app.on_callback_query(
            filters.regex(r"admin_notif_select_(\d+)") & filters.user(ADMINS_LIST_ID)
        )(self.reply)
        self.app.on_message(
            filters.reply
            & filters.text
            & filters.user(ADMINS_LIST_ID)
            & (
                filters.create(self.is_notif_to_all)
                | filters.create(self.is_notif_to_teachers)
                | filters.create(self.is_notif_to_users)
            )
        )(self.get_notif)

    async def select_type(self, client, message):
        await message.reply_text(
            "نوع نوتیفیکیشن را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "ارسال به همه", callback_data="admin_notif_select_0"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "ارسال به کاربران", callback_data="admin_notif_select_1"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "ارسال به معلمان", callback_data="admin_notif_select_2"
                        )
                    ],
                    [InlineKeyboardButton("exit!", callback_data="back_home")],
                ]
            ),
        )

    async def reply(self, client, callback_query):
        await callback_query.message.delete()
        notif = "notif"
        if "users" in callback_query.data:
            notif = "users-notif"
        elif "teachers" in callback_query.data:
            notif = "teachers-notif"

        await callback_query.message.reply_text(
            f"<b>Just send {notif} as a reply to this message</b>",
            reply_markup=ForceReply(selective=True),
        )

    async def get_notif(self, client, message):
        data = self.base_caption + message.text

        if "users" in message.reply_to_message.text:
            asyncio.create_task(self.send_users_notification(client, data))
        elif "teachers" in message.reply_to_message.text:
            asyncio.create_task(self.send_teachers_notification(client, data))
        else:
            asyncio.create_task(self.send_alls_notification(client, data))

        await message.reply_to_message.delete()
        await message.reply_text("متن شما با موفقیت در صف تسک‌ها قرار گرفت.")
        await send_home_message_admin(message)

    @property
    def users(self):
        return (
            db.session.query(db.UserModel)
            .filter(db.UserModel.chat_id.is_not(None))
            .all()
        )

    @property
    def teachers(self):
        return (
            db.session.query(db.TeacherModel)
            .filter(db.TeacherModel.chat_id.is_not(None))
            .all()
        )

    async def send_users_notification(self, client, data):
        for user in self.users:
            await client.send_message(chat_id=user.chat_id, text=data)

    async def send_teachers_notification(self, client, data):
        for user in self.teachers:
            await client.send_message(chat_id=user.chat_id, text=data)

    async def send_alls_notification(self, client, data):
        for admin in ADMINS_LIST_ID:
            await client.send_message(chat_id=admin, text=data)
        for user in self.teachers:
            await client.send_message(chat_id=user.chat_id, text=data)
        for user in self.users:
            await client.send_message(chat_id=user.chat_id, text=data)


def register_admin_handlers(app):
    app.on_message(filters.regex("my settings") & filters.user(ADMINS_LIST_ID))(
        admin_my_settings
    )

    ActivePractice(app)
    AllPractice(app)
    NONEPractice(app)
    Users(app)
    Teachers(app)
    Practice(app)
    Notifiaction(app)
