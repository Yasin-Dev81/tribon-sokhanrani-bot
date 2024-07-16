from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
)
import asyncio
import datetime

from sqlalchemy import func

from .pagination import get_paginated_keyboard, none_teacher_paginated_keyboard_t
from .home import send_home_message_teacher
from .admin import DB
import db.crud as db
from db.models import (
    Practice as PracticeModel,
    UserPractice as UserPracticeModel,
    User as UserModel,
    Teacher as TeacherModel,
)


def is_teacher(filter, client, update):
    return db.Teacher().read_with_tell_id(tell_id=update.from_user.id) is not None


class ActivePractice(DB):
    def __init__(self, app):
        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(
            filters.regex("تمرین‌های فعال") & filters.create(is_teacher)
        )(self.list)
        self.app.on_callback_query(
            filters.regex(r"teacher_active_practice_paginate_list_(\d+)")
            & filters.create(is_teacher)
        )(self.paginate_list)
        self.app.on_callback_query(
            filters.regex(r"teacher_active_practice_select_(\d+)")
            & filters.create(is_teacher)
        )(self.select)
        self.app.on_callback_query(
            filters.regex(r"teacher_active_practice_user_practice_list_(\d+)")
            & filters.create(is_teacher)
        )(self.user_practice_list)
        self.app.on_callback_query(
            filters.regex(r"teacher_active_practice_user_practice_select_(\d+)")
            & filters.create(is_teacher)
        )(self.user_practice_select)
        self.app.on_callback_query(
            filters.regex(r"teacher_active_practice_user_practice_correction_(\d+)")
            & filters.create(is_teacher)
        )(self.correction)
        self.app.on_message(
            filters.reply
            & filters.text
            & filters.create(is_teacher)
            & filters.create(self.is_new_correction_msg)
        )(self.set_teacher_caption)

    @staticmethod
    def is_new_correction_msg(filter, client, update):
        return (
            "Just send correction as a reply to this message"
            in update.reply_to_message.text
        )

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
                "teacher_active_practice_paginate_list",
                "teacher_active_practice_select",
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
                    "teacher_active_practice_paginate_list",
                    "teacher_active_practice_select",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                self.practices,
                page,
                "teacher_active_practices_page",
                "teacher_active_practice_select",
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
                            "مشاهده تکالیف",
                            callback_data=f"teacher_active_practice_user_practice_list_{practice_id}_0",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "back",
                            callback_data="teacher_active_practice_paginate_list_0",
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
                    "teacher_active_practice_user_practice_list",
                    "teacher_active_practice_user_practice_select",
                    back_query=f"teacher_active_practice_select_{practice_id}",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                user_practices,
                page,
                "teacher_active_practice_user_practice_list",
                "teacher_active_practice_user_practice_select",
                back_query=f"teacher_active_practice_select_{practice_id}",
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
                            callback_data=f"teacher_active_practice_user_practice_correction_{user_practice_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "back",
                            callback_data=f"teacher_active_practice_user_practice_list_{user_practice.practice_id}_0",
                        ),
                        InlineKeyboardButton("exit!", callback_data="back_home"),
                    ],
                ]
            ),
        )

    async def correction(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])

        await callback_query.message.delete()

        await callback_query.message.reply_text(
            "پیام خود را ریپلی کنید.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )
        await callback_query.message.reply_text(
            f"{user_practice_id}\n"
            "<b>Just send correction as a reply to this message</b>",
            reply_markup=ForceReply(selective=True),
        )

    @staticmethod
    async def send_user_correction_notification(client, user_practice_id):
        await client.send_message(
            chat_id=db.User().read_chat_id_user_with_user_practice_id(user_practice_id),
            text=f"تمرین {user_practice_id} شما تصحیح شد.",
        )

    async def set_teacher_caption(self, client, message):
        user_practice_id = int(message.reply_to_message.text.split("\n")[0])
        db.UserPractice().set_teacher_caption(
            pk=user_practice_id, teacher_caption=message.text
        )
        await message.reply_text("با موفقیت ثبت شد.")

        await message.reply_to_message.delete()

        asyncio.create_task(
            self.send_user_correction_notification(client, user_practice_id)
        )

        await send_home_message_teacher(message)


class AllPractice(DB):
    def __init__(self, app):
        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(
            filters.regex("تمامی تمرین‌ها") & filters.create(is_teacher)
        )(self.list)
        self.app.on_callback_query(
            filters.regex(r"teacher_all_practice_paginate_list_(\d+)")
            & filters.create(is_teacher)
        )(self.paginate_list)
        self.app.on_callback_query(
            filters.regex(r"teacher_all_practice_select_(\d+)")
            & filters.create(is_teacher)
        )(self.select)
        self.app.on_callback_query(
            filters.regex(r"teacher_all_practice_user_practice_list_(\d+)")
            & filters.create(is_teacher)
        )(self.user_practice_list)
        self.app.on_callback_query(
            filters.regex(r"teacher_all_practice_user_practice_select_(\d+)")
            & filters.create(is_teacher)
        )(self.user_practice_select)
        self.app.on_callback_query(
            filters.regex(r"teacher_all_practice_user_practice_correction_(\d+)")
            & filters.create(is_teacher)
        )(self.correction)
        self.app.on_message(
            filters.reply
            & filters.text
            & filters.create(is_teacher)
            & filters.create(self.is_new_correction_msg)
        )(self.set_teacher_caption)

    @staticmethod
    def is_new_correction_msg(filter, client, update):
        return (
            "Just send correction as a reply to this message"
            in update.reply_to_message.text
        )

    @property
    def practices(self):
        practices = self.session.query(PracticeModel.id, PracticeModel.title).all()
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
                "teacher_all_practice_paginate_list",
                "teacher_all_practice_select",
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
                    "teacher_all_practice_paginate_list",
                    "teacher_all_practice_select",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                self.practices,
                page,
                "teacher_all_practices_page",
                "teacher_all_practice_select",
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
                            "مشاهده تکالیف",
                            callback_data=f"teacher_all_practice_user_practice_list_{practice_id}_0",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "back",
                            callback_data="teacher_all_practice_paginate_list_0",
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
                    "teacher_all_practice_user_practice_list",
                    "teacher_all_practice_user_practice_select",
                    back_query=f"teacher_all_practice_select_{practice_id}",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                user_practices,
                page,
                "teacher_all_practice_user_practice_list",
                "teacher_all_practice_user_practice_select",
                back_query=f"teacher_all_practice_select_{practice_id}",
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
                            callback_data=f"teacher_all_practice_user_practice_correction_{user_practice_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "back",
                            callback_data=f"teacher_all_practice_user_practice_list_{user_practice.practice_id}_0",
                        ),
                        InlineKeyboardButton("exit!", callback_data="back_home"),
                    ],
                ]
            ),
        )

    async def correction(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])

        await callback_query.message.delete()

        await callback_query.message.reply_text(
            "پیام خود را ریپلی کنید.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )
        await callback_query.message.reply_text(
            f"{user_practice_id}\n"
            "<b>Just send correction as a reply to this message</b>",
            reply_markup=ForceReply(selective=True),
        )

    @staticmethod
    async def send_user_correction_notification(client, user_practice_id):
        await client.send_message(
            chat_id=db.User().read_chat_id_user_with_user_practice_id(user_practice_id),
            text=f"تمرین {user_practice_id} شما تصحیح شد.",
        )

    async def set_teacher_caption(self, client, message):
        user_practice_id = int(message.reply_to_message.text.split("\n")[0])
        db.UserPractice().set_teacher_caption(
            pk=user_practice_id, teacher_caption=message.text
        )
        await message.reply_text("با موفقیت ثبت شد.")

        await message.reply_to_message.delete()

        asyncio.create_task(
            self.send_user_correction_notification(client, user_practice_id)
        )

        await send_home_message_teacher(message)


class NONEPractice(DB):
    def __init__(self, app):
        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(
            filters.regex("تکالیف نیازمند به تصحیح") & filters.create(is_teacher)
        )(self.list)
        self.app.on_callback_query(
            filters.regex(r"teacher_none_practice_paginate_list_(\d+)")
            & filters.create(is_teacher)
        )(self.paginate_list)
        self.app.on_callback_query(
            filters.regex(r"teacher_none_practice_user_practice_select_(\d+)")
            & filters.create(is_teacher)
        )(self.user_practice_select)
        self.app.on_callback_query(
            filters.regex(r"teacher_none_practice_user_practice_correction_(\d+)")
            & filters.create(is_teacher)
        )(self.correction)
        self.app.on_message(
            filters.reply
            & filters.text
            & filters.create(is_teacher)
            & filters.create(self.is_new_correction_msg)
        )(self.set_teacher_caption)

    @staticmethod
    def is_new_correction_msg(filter, client, update):
        return (
            "Just send x correction as a reply to this message"
            in update.reply_to_message.text
        )

    def user_practices(self, tell_id):
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
            .join(TeacherModel, UserPracticeModel.teacher_id == TeacherModel.id)
            .filter(TeacherModel.tell_id == tell_id)
            .filter(UserPracticeModel.teacher_caption.is_(None))
        )

        return query.all()

    async def list(self, client, message):
        # user_practices = self.user_practice(int(message.from_user.id))
        user_practices = db.UserPractice().read_with_teacher_tell_id(
            teacher_tell_id=message.from_user.id
        )
        if not user_practices:
            await message.reply_text("هیچ تکلیفی موجود نیست!")
            return

        await message.reply_text(
            "تمامی تکالیف:",
            reply_markup=none_teacher_paginated_keyboard_t(
                user_practices,
                0,
                "teacher_none_practice_paginate_list",
                "teacher_none_practice_user_practice_select",
            ),
        )

    async def paginate_list(self, client, callback_query):
        page = int(callback_query.data.split("_")[-1])
        # user_practices = self.user_practice(callback_query.from_user.id)
        user_practices = db.UserPractice().read_with_teacher_tell_id(
            teacher_tell_id=callback_query.from_user.id
        )

        if not user_practices:
            await callback_query.message.reply_text(
                "هیچ تکلیف تصحیح نشده‌ای موجود نیست!"
            )
            return

        if page == 0:
            await callback_query.message.delete()
            await callback_query.message.reply_text(
                "تمارین فعال:",
                reply_markup=none_teacher_paginated_keyboard_t(
                    user_practices,
                    page,
                    "teacher_none_practice_paginate_list",
                    "teacher_none_practice_user_practice_select",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=none_teacher_paginated_keyboard_t(
                user_practices,
                page,
                "teacher_none_practice_paginate_list",
                "teacher_none_practice_user_practice_select",
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
                UserPracticeModel.teacher_id.label("techer_id"),
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
                            callback_data=f"teacher_all_practice_user_practice_correction_{user_practice_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "back",
                            callback_data=f"teacher_all_practice_user_practice_list_{user_practice.practice_id}_0",
                        ),
                        InlineKeyboardButton("exit!", callback_data="back_home"),
                    ],
                ]
            ),
        )

    async def correction(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])

        await callback_query.message.delete()

        await callback_query.message.reply_text(
            "پیام خود را ریپلی کنید.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )
        await callback_query.message.reply_text(
            f"{user_practice_id}\n"
            "<b>Just send x correction as a reply to this message</b>",
            reply_markup=ForceReply(selective=True),
        )

    @staticmethod
    async def send_user_correction_notification(client, user_practice_id):
        await client.send_message(
            chat_id=db.User().read_chat_id_user_with_user_practice_id(user_practice_id),
            text=f"تمرین {user_practice_id} شما تصحیح شد.",
        )

    async def set_teacher_caption(self, client, message):
        user_practice_id = int(message.reply_to_message.text.split("\n")[0])
        db.UserPractice().set_teacher_caption(
            pk=user_practice_id, teacher_caption=message.text
        )
        await message.reply_text("با موفقیت ثبت شد.")

        await message.reply_to_message.delete()

        asyncio.create_task(
            self.send_user_correction_notification(client, user_practice_id)
        )

        await send_home_message_teacher(message)


async def teacher_my_settings(client, message):
    teacher = db.Teacher().read_with_tell_id(tell_id=message.from_user.id)
    await message.reply(f"You are <b>teacher</b> and your id is <i>{teacher.id}</i>")


def register_teacher_handlers(app):
    app.on_message(filters.regex("my settings") & filters.create(is_teacher))(
        teacher_my_settings
    )
