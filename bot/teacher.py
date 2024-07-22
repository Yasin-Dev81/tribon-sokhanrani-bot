from pyrogram import filters
from sqlalchemy import func
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
)
import asyncio
import datetime


from .pagination import get_paginated_keyboard
from .home import send_home_message_teacher
from config import GROUP_CHAT_ID
import db


def is_teacher(filter, client, update):
    return (
        db.session.query(db.TeacherModel).filter_by(tell_id=update.from_user.id).first()
        is not None
    )


class BasePractice:
    def __init__(self, app, type="all") -> None:
        self.app = app
        self.type = type
        self.base_register_handlers()

    def base_register_handlers(self):
        self.app.on_callback_query(
            filters.regex(rf"teacher_{self.type}_practice_select_(\d+)")
            & filters.create(is_teacher)
        )(self.select)
        self.app.on_callback_query(
            filters.regex(rf"teacher_{self.type}_practice_user_practice_list_(\d+)")
            & filters.create(is_teacher)
        )(self.user_practice_list)
        self.app.on_callback_query(
            filters.regex(rf"teacher_{self.type}_practice_user_practice_select_(\d+)")
            & filters.create(is_teacher)
        )(self.user_practice_select)
        self.app.on_callback_query(
            filters.regex(
                rf"teacher_{self.type}_practice_user_practice_correction_(\d+)"
            )
            & filters.create(is_teacher)
        )(self.correction)
        self.app.on_message(
            filters.reply
            & filters.text
            & filters.create(is_teacher)
            & filters.create(self.is_new_correction_msg)
        )(self.set_teacher_caption)
        self.app.on_message(
            filters.reply
            & filters.voice
            & filters.create(is_teacher)
            & filters.create(self.is_voice_correction_msg)
        )(self.correction_voice)

    def is_new_correction_msg(filter, client, update):
        return (
            "Just send correction as a reply to this message"
            in update.reply_to_message.text
        )

    def is_voice_correction_msg(filter, client, update):
        return (
            "Just send voice correction as a reply to this message"
            in update.reply_to_message.text
        )

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
                db.UserTypeModel.name.label("user_type_name"),
            )
            .join(db.UserTypeModel, db.PracticeModel.user_type_id == db.UserTypeModel.id)
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
            f"تایپ یوزرهای سوال: {practice.user_type_name}\n"
            f"تعداد یوزرهایی که پاسخ داده‌اند: {practice.total_count}\n"
            f"تعداد پاسخ‌هایی که تحلیل سخنرانی شده‌اند: {practice.teacher_caption_count}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "مشاهده تکالیف",
                            callback_data=f"teacher_{self.type}_practice_user_practice_list_{practice_id}_0",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔙 بازگشت",
                            callback_data=f"teacher_{self.type}_practice_paginate_list_0",
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
                db.UserTypeModel.name.label("user_type_name"),
            )
            .join(
                db.PracticeModel,
                db.UserPracticeModel.practice_id == db.PracticeModel.id,
            )
            .join(db.UserTypeModel, db.UserTypeModel.id == db.PracticeModel.user_type_id)
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
                f"تایپ یوزرهای سوال: {practice.user_type_name}\n"
                f"تعداد یوزرهایی که پاسخ داده‌اند: {practice.total_count}\n"
                f"تعداد پاسخ‌هایی که تحلیل سخنرانی شده‌اند: {practice.teacher_caption_count}",
                reply_markup=get_paginated_keyboard(
                    user_practices,
                    page,
                    f"teacher_{self.type}_practice_user_practice_list",
                    f"teacher_{self.type}_practice_user_practice_select",
                    back_query=f"teacher_{self.type}_practice_select_{practice_id}",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                user_practices,
                page,
                f"teacher_{self.type}_practice_user_practice_list",
                f"teacher_{self.type}_practice_user_practice_select",
                back_query=f"teacher_{self.type}_practice_select_{practice_id}",
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
                db.UserModel.phone_number,
                db.UserTypeModel.name.label("user_type_name")
            )
            .join(
                db.PracticeModel,
                db.PracticeModel.id == db.UserPracticeModel.practice_id,
            )
            .join(db.UserTypeModel, db.PracticeModel.user_type_id == db.UserTypeModel.id)
            .join(db.UserModel, db.UserModel.id == db.UserPracticeModel.user_id)
            .filter(db.UserPracticeModel.id == pk)
        )
        return query.first()

    async def user_practice_select(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])
        user_practice = self.user_practice(user_practice_id)

        await callback_query.message.delete()

        capt = "تحلیل سخنرانی نشده!"
        if user_practice.teacher_caption:
            capt = (
                "تحلیل سخنرانی شده.\n" f"تحلیل سخنرانی: {user_practice.teacher_caption}"
            )

        await callback_query.message.reply_video(
            video=user_practice.file_link,
            caption=f"📌 عنوان سوال: {user_practice.title}\n"
            f"🔖 متن سوال: {user_practice.practice_caption}\n"
            f"👤 کاربر: {user_practice.username}\n"
            f"نوع کاربر: {user_practice.user_type_name}\n"
            f"شماره کاربر: {user_practice.phone_number}\n"
            f"کپشن کاربر:\n {user_practice.user_caption}\n"
            f"وضعیت تحلیل سخنرانی: {capt}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "تحلیل سخنرانی مجدد"
                            if user_practice.teacher_caption
                            else "تحلیل سخنرانی",
                            callback_data=f"teacher_{self.type}_practice_user_practice_correction_{user_practice_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔙 بازگشت",
                            callback_data=f"teacher_{self.type}_practice_user_practice_list_{user_practice.practice_id}_0",
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
            f"<b>Just send correction as a reply to this message</b>",
            reply_markup=ForceReply(selective=True),
        )

    @staticmethod
    async def send_user_correction_notification(client, user_practice_id):
        user_chat_id = (
            db.session.query(db.UserModel.chat_id)
            .join(db.UserPracticeModel, db.UserModel.id == db.UserPracticeModel.user_id)
            .filter(db.UserPracticeModel.id == user_practice_id)
            .scalar()
        )

        await client.send_message(
            chat_id=user_chat_id,
            text=f"تمرین {user_practice_id} شما تحلیل سخنرانی شد.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "مشاهده",
                            callback_data=f"user_active_practice_select_{user_practice_id}",
                        )
                    ]
                ]
            ),
        )

    @staticmethod
    def set_teacher_caption_db(pk, teahcer_caption):
        user_practice = db.session.query(db.UserPracticeModel).get(pk)
        if user_practice:
            user_practice.teacher_caption = teahcer_caption
            db.session.commit()
            return True
        return False

    async def set_teacher_caption(self, client, message):
        user_practice_id = int(message.reply_to_message.text.split("\n")[0])
        if self.set_teacher_caption_db(user_practice_id, message.text):
            await message.reply_text("با موفقیت ثبت شد.")
            await message.reply_text(
                "با موفقیت ثبت شد." "در صورت نیاز ویس تحلیل سخنرانی را نیز ریپلی کنید.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("exit!", callback_data="back_home")]]
                ),
            )
            await message.reply_text(
                f"{user_practice_id}\n"
                f"<b>Just send voice correction as a reply to this message</b>",
                reply_markup=ForceReply(selective=True),
            )

            asyncio.create_task(
                self.send_user_correction_notification(client, user_practice_id)
            )
        else:
            await message.reply_text("error!")

        await message.reply_to_message.delete()
        # await send_home_message_teacher(message)

    @staticmethod
    def set_teacher_voice_db(pk, file_link):
        user_practice = db.session.query(db.UserPracticeModel).get(pk)
        if user_practice:
            user_practice.teacher_voice_link = file_link
            db.session.commit()
            return True
        return False

    async def correction_voice(self, client, message):
        practice_id = int(message.reply_to_message.text.split("\n")[0])

        media_id = message.voice.file_id

        capt = (
            f"#correction"
            f"message id: <i>{message.id}</i>\n---\n"
            f"from user @{message.from_user.username}\n"
        )

        # Forward the video to the channel
        await client.send_voice(chat_id=GROUP_CHAT_ID, voice=media_id, caption=capt)
        self.set_teacher_voice_db(practice_id, media_id)

        await message.reply_to_message.delete()
        await message.reply_text("ویس با موفقیت ثبت شد.")
        await send_home_message_teacher(message)


class ActivePractice(BasePractice):
    def __init__(self, app, type="active") -> None:
        super().__init__(app, type)
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
                "teacher_active_practice_paginate_list",
                "teacher_active_practice_select",
            )
        )


class AllPractice(BasePractice):
    def __init__(self, app, type="all") -> None:
        super().__init__(app, type)
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

    @property
    def practices(self):
        practices = db.session.query(db.PracticeModel.id, db.PracticeModel.title).all()
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
                "teacher_all_practice_paginate_list",
                "teacher_all_practice_select",
            )
        )


class NONEPractice:
    def __init__(self, app):
        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(
            filters.regex("تکالیف نیازمند به تحلیل سخنرانی")
            & filters.create(is_teacher)
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
        self.app.on_message(
            filters.reply
            & filters.voice
            & filters.create(is_teacher)
            & filters.create(self.is_voice_correction_msg)
        )(self.correction_voice)

    @staticmethod
    def is_new_correction_msg(filter, client, update):
        return (
            "Just send n correction as a reply to this message"
            in update.reply_to_message.text
        )

    @staticmethod
    def is_voice_correction_msg(filter, client, update):
        return (
            "Just send n voice correction as a reply to this message"
            in update.reply_to_message.text
        )

    @staticmethod
    def user_practices(tell_id):
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
            .join(
                db.TeacherModel, db.UserPracticeModel.teacher_id == db.TeacherModel.id
            )
            .filter(db.TeacherModel.tell_id == tell_id)
            .filter(db.UserPracticeModel.teacher_caption.is_(None))
        )

        return query.all()

    async def list(self, client, message):
        user_practices = self.user_practices(message.from_user.id)

        if not user_practices:
            await message.reply_text("هیچ تکلیفی موجود نیست!")
            return

        await message.reply_text(
            "تمامی تکالیف:",
            reply_markup=get_paginated_keyboard(
                user_practices,
                0,
                "teacher_none_practice_paginate_list",
                "teacher_none_practice_user_practice_select",
            ),
        )

    async def paginate_list(self, client, callback_query):
        page = int(callback_query.data.split("_")[-1])
        user_practices = self.user_practices(callback_query.from_user.id)

        if not user_practices:
            await callback_query.message.reply_text(
                "هیچ تکلیف تحلیل سخنرانی نشده‌ای موجود نیست!"
            )
            return

        if page == 0:
            await callback_query.message.delete()
            await callback_query.message.reply_text(
                "تمارین فعال:",
                reply_markup=get_paginated_keyboard(
                    user_practices,
                    page,
                    "teacher_none_practice_paginate_list",
                    "teacher_none_practice_user_practice_select",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                user_practices,
                page,
                "teacher_none_practice_paginate_list",
                "teacher_none_practice_user_practice_select",
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
                db.UserTypeModel.name.label("user_type_name"),
                db.UserModel.phone_number,
            )
            .join(
                db.PracticeModel,
                db.PracticeModel.id == db.UserPracticeModel.practice_id,
            )
            .join(db.UserModel, db.UserModel.id == db.UserPracticeModel.user_id)
            .join(db.UserTypeModel, db.PracticeModel.user_type_id == db.UserTypeModel.id)
            .filter(db.UserPracticeModel.id == pk)
        )
        return query.first()

    async def user_practice_select(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])
        user_practice = self.user_practice(user_practice_id)

        await callback_query.message.delete()

        capt = "تحلیل سخنرانی نشده!"
        if user_practice.teacher_caption:
            capt = (
                "تحلیل سخنرانی شده.\n" f"تحلیل سخنرانی: {user_practice.teacher_caption}"
            )

        await callback_query.message.reply_video(
            video=user_practice.file_link,
            caption=f"📌 عنوان سوال: {user_practice.title}\n"
            f"🔖 متن سوال: {user_practice.practice_caption}\n"
            f"👤 کاربر: {user_practice.username}\n"
            f"نوع کاربر: {user_practice.user_type_name}\n"
            f"شماره کاربر: {user_practice.phone_number}\n"
            f"کپشن کاربر:\n {user_practice.user_caption}\n"
            f"وضعیت تحلیل سخنرانی: {capt}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "تحلیل سخنرانی مجدد"
                            if user_practice.teacher_caption
                            else "تحلیل سخنرانی",
                            callback_data=f"teacher_all_practice_user_practice_correction_{user_practice_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔙 بازگشت",
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
            "<b>Just send n correction as a reply to this message</b>",
            reply_markup=ForceReply(selective=True),
        )

    @staticmethod
    async def send_user_correction_notification(client, user_practice_id):
        user_chat_id = (
            db.session.query(db.UserModel.chat_id)
            .join(db.UserPracticeModel, db.UserModel.id == db.UserPracticeModel.user_id)
            .filter(db.UserPracticeModel.id == user_practice_id)
            .scalar()
        )

        await client.send_message(
            chat_id=user_chat_id,
            text=f"تمرین {user_practice_id} شما تحلیل سخنرانی شد.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "مشاهده",
                            callback_data=f"user_active_practice_select_{user_practice_id}",
                        )
                    ]
                ]
            ),
        )

    @staticmethod
    def set_teacher_caption_db(pk, teahcer_caption):
        user_practice = db.session.query(db.UserPracticeModel).get(pk)
        if user_practice:
            user_practice.teacher_caption = teahcer_caption
            db.session.commit()
            return True
        return False

    async def set_teacher_caption(self, client, message):
        user_practice_id = int(message.reply_to_message.text.split("\n")[0])
        if self.set_teacher_caption_db(user_practice_id, message.text):
            await message.reply_text("با موفقیت ثبت شد.")
            await message.reply_text(
                "با موفقیت ثبت شد." "در صورت نیاز ویس تحلیل سخنرانی را نیز ریپلی کنید.",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("exit!", callback_data="back_home")]]
                ),
            )
            await message.reply_text(
                f"{user_practice_id}\n"
                "<b>Just send n voice correction as a reply to this message</b>",
                reply_markup=ForceReply(selective=True),
            )

            asyncio.create_task(
                self.send_user_correction_notification(client, user_practice_id)
            )
        else:
            await message.reply_text("error!")

        await message.reply_to_message.delete()
        await send_home_message_teacher(message)

    @staticmethod
    def set_teacher_voice_db(pk, file_link):
        user_practice = db.session.query(db.UserPracticeModel).get(pk)
        if user_practice:
            user_practice.teacher_voice_link = file_link
            db.session.commit()
            return True
        return False

    async def correction_voice(self, client, message):
        practice_id = int(message.reply_to_message.text.split("\n")[0])

        media_id = message.voice.file_id

        capt = (
            f"#correction"
            f"message id: <i>{message.id}</i>\n---\n"
            f"from user @{message.from_user.username}\n"
        )

        # Forward the video to the channel
        await client.send_voice(chat_id=GROUP_CHAT_ID, voice=media_id, caption=capt)
        self.set_teacher_voice_db(practice_id, media_id)

        await message.reply_to_message.delete()
        await message.reply_text("ویس با موفقیت ثبت شد.")
        await send_home_message_teacher(message)


async def teacher_my_settings(client, message):
    teacher = (
        db.session.query(db.TeacherModel)
        .filter_by(tell_id=message.from_user.id)
        .first()
    )
    await message.reply(
        f"You are <b>teacher</b> and your id is <i>{teacher.id}</i>\nName: {teacher.name}"
    )


def register_teacher_handlers(app):
    app.on_message(filters.regex("my settings") & filters.create(is_teacher))(
        teacher_my_settings
    )

    ActivePractice(app)
    AllPractice(app)
    NONEPractice(app)
