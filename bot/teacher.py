from pyrogram import filters
from persiantools.jdatetime import JalaliDate
from sqlalchemy import func
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
)
import asyncio
import datetime
import re

from .pagination import get_paginated_keyboard, user_practice_paginated_keyboard
from .home import send_home_message_teacher
from config import GROUP_CHAT_ID, TIME_ZONE
import db


def is_teacher(filter, client, update):
    with db.get_session() as session:
        return (
            session.query(db.TeacherModel)
            .filter_by(tell_id=update.from_user.id)
            .first()
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
            filters.regex(
                rf"teacher_{self.type}_practice_user_practice_list_(\d+)_(\d+)"
            )
            & filters.create(is_teacher)
        )(self.user_practice_list)
        self.app.on_callback_query(
            filters.regex(rf"teacher_{self.type}_practice_user_practice_select_(\d+)")
            & filters.create(is_teacher)
        )(self.user_practice_select)
        self.app.on_callback_query(
            filters.regex(
                rf"teacher_{self.type}_practice_user_practice_correction_type_(\d+)_(\d+)"
            )
            & filters.create(is_teacher)
        )(self.correction_type)
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
        )(self.correction_text)
        self.app.on_message(
            filters.reply
            & filters.voice
            & filters.create(is_teacher)
            & filters.create(self.is_voice_correction_msg)
        )(self.correction_voice)
        self.app.on_message(
            filters.reply
            & filters.video
            & filters.create(is_teacher)
            & filters.create(self.is_video_correction_msg)
        )(self.correction_video)
        self.app.on_callback_query(
            filters.regex(
                rf"teacher_{self.type}_practice_user_practice_confirm_(\d+)_(\d+)"
            )
            & filters.create(is_teacher)
        )(self.confirm)

    def is_new_correction_msg(filter, client, update):
        return (
            "ابتدا به این پیام ریپلای (پاسخ) بزنید سپس تحلیل متنی خود را ارسال کنید."
            in update.reply_to_message.text
        )

    def is_voice_correction_msg(filter, client, update):
        return (
            "ابتدا به این پیام ریپلای (پاسخ) بزنید سپس تحلیل صوتی خود را ارسال کنید."
            in update.reply_to_message.text
        )

    def is_video_correction_msg(filter, client, update):
        return (
            "ابتدا به این پیام ریپلای (پاسخ) بزنید سپس تحلیل ویدیویی خود را ارسال کنید."
            in update.reply_to_message.text
        )

    @staticmethod
    def report_practice(pk):
        with db.get_session() as session:
            total_count_subquery = (
                session.query(func.count(db.UserPracticeModel.id))
                .filter(db.UserPracticeModel.practice_id == pk)
                .scalar_subquery()
            )
            teacher_caption_count_subquery = (
                session.query(func.count(db.UserPracticeModel.id))
                .filter(
                    db.UserPracticeModel.practice_id == pk,
                    db.UserPracticeModel.teacher_caption.isnot(None),
                )
                .scalar_subquery()
            )
            practice = (
                session.query(
                    db.PracticeModel.title,
                    db.PracticeModel.caption,
                    db.PracticeModel.end_date,
                    total_count_subquery.label("total_count"),
                    teacher_caption_count_subquery.label("teacher_caption_count"),
                    db.UserTypeModel.name.label("user_type_name"),
                )
                .join(
                    db.UserTypeModel,
                    db.PracticeModel.user_type_id == db.UserTypeModel.id,
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
            f"◾️ ددلاین تمرین: {JalaliDate(practice.end_date).strftime('%c | ساعت %H:%M:%S', locale='fa')}\n"
            f"◾️ تایپ یوزرهای سوال: {practice.user_type_name}\n",
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
    def user_practices(pk, teacher_tell_id):
        with db.get_session() as session:
            query = (
                session.query(
                    db.UserPracticeModel.id.label("id"),
                    db.UserModel.name.label("title"),
                    db.UserPracticeModel.teacher_caption,
                    db.UserTypeModel.name.label("user_type_name"),
                )
                .join(
                    db.PracticeModel,
                    db.UserPracticeModel.practice_id == db.PracticeModel.id,
                )
                .join(
                    db.UserTypeModel,
                    db.UserTypeModel.id == db.PracticeModel.user_type_id,
                )
                .join(db.UserModel, db.UserPracticeModel.user_id == db.UserModel.id)
                .join(
                    db.TeacherModel,
                    db.TeacherModel.id == db.UserPracticeModel.teacher_id,
                )
                .filter(db.UserPracticeModel.practice_id == pk)
                .filter(db.TeacherModel.tell_id == teacher_tell_id)
            )
            return query.all()

    async def user_practice_list(self, client, callback_query):
        match = re.search(
            rf"teacher_{self.type}_practice_user_practice_list_(\d+)_(\d+)",
            callback_query.data,
        )
        if not match:
            return

        practice_id = int(match.group(1))
        page = int(match.group(2))

        # practice_id, page = [int(i) for i in (callback_query.data.split("_")[6:8])]
        user_practices = self.user_practices(practice_id, callback_query.from_user.id)

        if not user_practices:
            await callback_query.message.reply_text("هیچ تکلیفی ارسال نشده!")
            return

        if page == 0:
            practice = self.report_practice(pk=practice_id)
            await callback_query.message.delete()
            await callback_query.message.reply_text(
                f"📌 عنوان: {practice.title}\n🔖 متن سوال: {practice.caption}\n"
                f"◾️ ددلاین تمرین: {JalaliDate(practice.end_date).strftime('%c | ساعت %H:%M:%S', locale='fa')}\n"
                f"◾️ تایپ یوزرهای سوال: {practice.user_type_name}",
                reply_markup=user_practice_paginated_keyboard(
                    user_practices,
                    0,
                    practice_id,
                    f"teacher_{self.type}_practice_user_practice_list",
                    f"teacher_{self.type}_practice_user_practice_select",
                    back_query=f"teacher_{self.type}_practice_select_{practice_id}",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=user_practice_paginated_keyboard(
                user_practices,
                page,
                practice_id,
                f"teacher_{self.type}_practice_user_practice_list",
                f"teacher_{self.type}_practice_user_practice_select",
                back_query=f"teacher_{self.type}_practice_select_{practice_id}",
            )
        )

    @staticmethod
    def user_practice(pk):
        with db.get_session() as session:
            query = (
                session.query(
                    db.UserPracticeModel.id.label("id"),
                    db.UserModel.name.label("username"),
                    db.UserPracticeModel.file_link.label("file_link"),
                    db.UserPracticeModel.user_caption.label("user_caption"),
                    db.UserPracticeModel.teacher_caption.label("teacher_caption"),
                    db.PracticeModel.title.label("title"),
                    db.PracticeModel.caption.label("practice_caption"),
                    db.UserPracticeModel.practice_id.label("practice_id"),
                    db.UserPracticeModel.teacher_video_link,
                    db.UserPracticeModel.teacher_voice_link,
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

        capt = "تحلیل سخنرانی شده.\n" f"تحلیل سخنرانی: {user_practice.teacher_caption}"
        markup = []
        if not user_practice.teacher_caption:
            capt = "تحلیل سخنرانی نشده!"
            markup.append(
                [
                    InlineKeyboardButton(
                        "تحلیل سخنرانی",
                        callback_data=f"teacher_{self.type}_practice_user_practice_correction_{user_practice_id}",
                    )
                ]
            )

        markup.append(
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data=f"teacher_{self.type}_practice_user_practice_list_{user_practice.practice_id}_0",
                ),
                InlineKeyboardButton("exit!", callback_data="back_home"),
            ]
        )

        await callback_query.message.reply_video(
            video=user_practice.file_link,
            caption=f"📌 عنوان سوال: {user_practice.title}\n"
            f"🔖 متن سوال: {user_practice.practice_caption}\n"
            f"👤 نام کاربر: {user_practice.username}\n"
            f"◾️ کپشن کاربر:\n {user_practice.user_caption}\n"
            f"◾️ وضعیت تحلیل سخنرانی: {capt}",
            reply_markup=InlineKeyboardMarkup(markup),
        )

        if user_practice.teacher_caption:
            if user_practice.teacher_voice_link:
                await callback_query.message.reply_voice(
                    voice=user_practice.teacher_voice_link, caption="تحلیل سخنرانی"
                )
            if user_practice.teacher_video_link:
                await callback_query.message.reply_video(
                    video=user_practice.teacher_video_link, caption="تحلیل سخنرانی"
                )

    async def correction(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])

        # await callback_query.message.delete()
        await callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 بازگشت",
                            callback_data=f"teacher_{self.type}_practice_user_practice_select_{user_practice_id}",
                        ),
                        InlineKeyboardButton(
                            "exit!",
                            callback_data="back_home",
                        ),
                    ]
                ]
            ),
        )

        await callback_query.message.reply_text(
            "نوع تحلیل را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "💬 متنی",
                            callback_data=f"teacher_{self.type}_practice_user_practice_correction_type_0_{user_practice_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔈 صوتی",
                            callback_data=f"teacher_{self.type}_practice_user_practice_correction_type_1_{user_practice_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "📹 ویدیوئی",
                            callback_data=f"teacher_{self.type}_practice_user_practice_correction_type_2_{user_practice_id}",
                        )
                    ],
                    [InlineKeyboardButton("exit!", callback_data="back_home")],
                ]
            ),
        )

    async def correction_type(self, client, callback_query):
        match = re.search(
            rf"teacher_{self.type}_practice_user_practice_correction_type_(\d+)_(\d+)",
            callback_query.data,
        )
        # types_list = ["متنی", "صوتی", "ویدیوئی"]
        if match:
            await callback_query.message.delete()

            type = int(match.group(1))
            user_practice_id = int(match.group(2))

            # await callback_query.message.reply_text(
            #     f"لطفا تحیلی <b>{types_list[type]}</b> را ریپلی کنید.",
            #     reply_markup=InlineKeyboardMarkup(
            #         [
            #             [
            #                 InlineKeyboardButton(
            #                     "exit!",
            #                     callback_data="back_home",
            #                 )
            #             ]
            #         ]
            #     ),
            # )

            if type == 0:
                await callback_query.message.reply_text(
                    f"{user_practice_id}\n"
                    "👈 <b>ابتدا به این پیام ریپلای (پاسخ) بزنید سپس تحلیل متنی خود را ارسال کنید.</b>\n\n"
                    "⚠️ توجه: در صورتی که به این پیام ریپلای نزنید، ارسال تحلیل شما ناموفق خواهد بود!",
                    reply_markup=ForceReply(selective=True),
                )
            elif type == 1:
                await callback_query.message.reply_text(
                    f"{user_practice_id}\n"
                    "👈 <b>ابتدا به این پیام ریپلای (پاسخ) بزنید سپس تحلیل صوتی خود را ارسال کنید.</b>\n\n"
                    "⚠️ توجه: در صورتی که به این پیام ریپلای نزنید، ارسال تحلیل شما ناموفق خواهد بود!",
                    reply_markup=ForceReply(selective=True),
                )
            else:
                await callback_query.message.reply_text(
                    f"{user_practice_id}\n"
                    f"👈 <b>ابتدا به این پیام ریپلای (پاسخ) بزنید سپس تحلیل ویدیویی خود را ارسال کنید.</b>\n\n"
                    "⚠️ توجه: در صورتی که به این پیام ریپلای نزنید، ارسال تحلیل شما ناموفق خواهد بود!\n"
                    "همچنین ویدیوی ارسالی باید کمتر از 50 مگابایت باشد!",
                    reply_markup=ForceReply(selective=True),
                )
        else:
            await callback_query.message.reply_text("error!")

    @staticmethod
    async def send_user_correction_notification(client, user_practice_id):
        with db.get_session() as session:
            user_info = (
                session.query(db.UserModel.chat_id, db.UserPracticeModel.practice_id)
                .join(
                    db.UserPracticeModel,
                    db.UserModel.id == db.UserPracticeModel.user_id,
                )
                .filter(db.UserPracticeModel.id == user_practice_id)
                .first()
            )

            await client.send_message(
                chat_id=user_info.chat_id,
                text=f"تمرین {user_practice_id} شما تحلیل سخنرانی شد.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "مشاهده",
                                callback_data=f"user_answered_practice_select_{user_info.practice_id}",
                            )
                        ]
                    ]
                ),
            )

    @staticmethod
    def set_teacher_caption_db(pk, teahcer_caption):
        with db.get_session() as session:
            user_practice = session.query(db.UserPracticeModel).get(pk)
            if user_practice:
                user_practice.teacher_caption = teahcer_caption
                session.commit()
                return True
        return False

    @staticmethod
    def set_teacher_voice_db(pk, file_link):
        with db.get_session() as session:
            user_practice = session.query(db.UserPracticeModel).get(pk)
            if user_practice:
                user_practice.teacher_voice_link = file_link
                user_practice.teacher_caption = "تحلیل صوتی است!"
                session.commit()
                return True
        return False

    @staticmethod
    def set_teacher_video_db(pk, file_link):
        with db.get_session() as session:
            user_practice = session.query(db.UserPracticeModel).get(pk)
            if user_practice:
                user_practice.teacher_video_link = file_link
                user_practice.teacher_caption = "تحلیل ویدیوئی است!"
                session.commit()
                return True
        return False

    async def correction_text(self, client, message):
        user_practice_id = int(message.reply_to_message.text.split("\n")[0])

        if self.set_teacher_caption_db(user_practice_id, message.text):
            await message.reply_to_message.delete()
            # await message.reply_text("ویس با موفقیت ثبت شد.")
            await message.reply_text(
                "آیا از ثبت این تحلیل سخنرانی اطمینان دارید؟",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "بلی",
                                callback_data=f"teacher_{self.type}_practice_user_practice_confirm_{user_practice_id}_1",
                            ),
                            InlineKeyboardButton(
                                "خیر",
                                callback_data=f"teacher_{self.type}_practice_user_practice_confirm_{user_practice_id}_0",
                            ),
                        ]
                    ]
                ),
            )

    async def correction_voice(self, client, message):
        user_practice_id = int(message.reply_to_message.text.split("\n")[0])

        media_id = message.voice.file_id

        capt = (
            f"#correction"
            f"message id: <i>{message.id}</i>\n---\n"
            f"from user @{message.from_user.username}\n"
        )

        # Forward the video to the channel
        await client.send_voice(chat_id=GROUP_CHAT_ID, voice=media_id, caption=capt)
        if self.set_teacher_voice_db(user_practice_id, media_id):
            await message.reply_to_message.delete()
            # await message.reply_text("ویس با موفقیت ثبت شد.")
            await message.reply_text(
                "آیا از ثبت این تحلیل سخنرانی اطمینان دارید؟",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "بلی",
                                callback_data=f"teacher_{self.type}_practice_user_practice_confirm_{user_practice_id}_1",
                            ),
                            InlineKeyboardButton(
                                "خیر",
                                callback_data=f"teacher_{self.type}_practice_user_practice_confirm_{user_practice_id}_0",
                            ),
                        ]
                    ]
                ),
            )

    async def correction_video(self, client, message):
        user_practice_id = int(message.reply_to_message.text.split("\n")[0])

        media_id = message.video.file_id
        media_status = (message.video.file_size / 1024) <= 50_000

        if not media_status:
            await message.reply_text("ویدیوی ارسالی باید کمتر از 50 مگابایت باشد!")
            return

        capt = (
            f"#correction"
            f"message id: <i>{message.id}</i>\n---\n"
            f"from user @{message.from_user.username}\n"
        )

        # Forward the video to the channel
        await client.send_video(chat_id=GROUP_CHAT_ID, video=media_id, caption=capt)
        if self.set_teacher_video_db(user_practice_id, media_id):
            await message.reply_to_message.delete()
            # await message.reply_text("ویدئو با موفقیت ثبت شد.")

            await message.reply_text(
                "آیا از ثبت این تحلیل سخنرانی اطمینان دارید؟",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "بلی",
                                callback_data=f"teacher_none_practice_user_practice_confirm_{user_practice_id}_1",
                            ),
                            InlineKeyboardButton(
                                "خیر",
                                callback_data=f"teacher_none_practice_user_practice_confirm_{user_practice_id}_0",
                            ),
                        ]
                    ]
                ),
            )

    @staticmethod
    def clear_correction_db(pk):
        with db.get_session() as session:
            user_practice = session.query(db.UserPracticeModel).get(pk)
            if user_practice:
                user_practice.teacher_caption = None
                user_practice.teacher_voice_link = None
                user_practice.teacher_video_link = None
                session.commit()
                return True
        return False

    async def confirm(self, client, callback_query):
        match = re.search(
            rf"teacher_{self.type}_practice_user_practice_confirm_(\d+)_(\d+)",
            callback_query.data,
        )
        if match:
            user_practice_id = match.group(1)
            status = int(match.group(2))

            if status == 0:
                if self.clear_correction_db(user_practice_id):
                    await callback_query.message.delete()
                    await callback_query.message.reply_text("تحلیل پاک شد.")
                    await send_home_message_teacher(callback_query.message)
                    return
            else:
                await callback_query.answer("تحلیل با موفقیت ثبت شد.", show_alert=True)
                await callback_query.message.delete()
                await callback_query.message.reply_text("تحلیل با موفقیت ثبت شد.")
                await send_home_message_teacher(callback_query.message)
                asyncio.create_task(
                    self.send_user_correction_notification(client, user_practice_id)
                )
                return

        await callback_query.message.delete()
        await callback_query.message.reply_text("error!")


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
        current_time = datetime.datetime.now(TIME_ZONE)
        with db.get_session() as session:
            practices = (
                session.query(db.PracticeModel.id, db.PracticeModel.title)
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
        with db.get_session() as session:
            practices = session.query(db.PracticeModel.id, db.PracticeModel.title).all()
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
            filters.regex(
                r"teacher_none_practice_user_practice_correction_type_(\d+)_(\d+)"
            )
            & filters.create(is_teacher)
        )(self.correction_type)
        self.app.on_callback_query(
            filters.regex(r"teacher_none_practice_user_practice_correction_(\d+)")
            & filters.create(is_teacher)
        )(self.correction)
        # self.app.on_message(
        #     filters.reply
        #     & filters.text
        #     & filters.create(is_teacher)
        #     & filters.create(self.is_new_correction_msg)
        # )(self.correction_text)
        # self.app.on_message(
        #     filters.reply
        #     & filters.voice
        #     & filters.create(is_teacher)
        #     & filters.create(self.is_voice_correction_msg)
        # )(self.correction_voice)
        # self.app.on_message(
        #     filters.reply
        #     & filters.video
        #     & filters.create(is_teacher)
        #     & filters.create(self.is_video_correction_msg)
        # )(self.correction_video)
        self.app.on_callback_query(
            filters.regex(r"teacher_none_practice_user_practice_confirm_(\d+)_(\d+)")
            & filters.create(is_teacher)
        )(self.confirm)

    def is_new_correction_msg(filter, client, update):
        return (
            "Just send n correction as a reply to this message"
            in update.reply_to_message.text
        )

    def is_voice_correction_msg(filter, client, update):
        return (
            "Just send n voice correction as a reply to this message"
            in update.reply_to_message.text
        )

    def is_video_correction_msg(filter, client, update):
        return (
            "Just send n video correction as a reply to this message"
            in update.reply_to_message.text
        )

    @staticmethod
    def user_practices(tell_id):
        with db.get_session() as session:
            query = (
                session.query(
                    db.UserPracticeModel.id,
                    (db.UserModel.name + " | " + db.PracticeModel.title).label("title"),
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
                    db.TeacherModel,
                    db.UserPracticeModel.teacher_id == db.TeacherModel.id,
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
        with db.get_session() as session:
            query = (
                session.query(
                    db.UserPracticeModel.id.label("id"),
                    db.UserModel.name.label("username"),
                    db.UserPracticeModel.file_link.label("file_link"),
                    db.UserPracticeModel.user_caption.label("user_caption"),
                    db.UserPracticeModel.teacher_caption.label("teacher_caption"),
                    db.PracticeModel.title.label("title"),
                    db.PracticeModel.caption.label("practice_caption"),
                    db.UserPracticeModel.practice_id.label("practice_id"),
                    db.UserPracticeModel.teacher_id.label("techer_id"),
                    db.UserPracticeModel.teacher_video_link,
                    db.UserPracticeModel.teacher_video_link,
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

        capt = "تحلیل سخنرانی شده.\n" f"تحلیل سخنرانی: {user_practice.teacher_caption}"
        markup = []
        if not user_practice.teacher_caption:
            capt = "تحلیل سخنرانی نشده!"
            markup = [
                [
                    InlineKeyboardButton(
                        "تحلیل سخنرانی",
                        callback_data=f"teacher_none_practice_user_practice_correction_{user_practice_id}",
                    )
                ]
            ]

        markup.append(
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data=f"teacher_none_practice_user_practice_list_{user_practice.practice_id}_0",
                ),
                InlineKeyboardButton("exit!", callback_data="back_home"),
            ]
        )

        await callback_query.message.reply_video(
            video=user_practice.file_link,
            caption=f"📌 عنوان سوال: {user_practice.title}\n"
            f"🔖 متن سوال: {user_practice.practice_caption}\n"
            f"👤 نام کاربر: {user_practice.username}\n"
            f"◾️ کپشن کاربر:\n {user_practice.user_caption}\n"
            f"◾️ وضعیت تحلیل سخنرانی: {capt}",
            reply_markup=InlineKeyboardMarkup(markup),
        )

        if user_practice.teacher_caption:
            if user_practice.teacher_voice_link:
                await callback_query.message.reply_voice(
                    voice=user_practice.teacher_voice_link, caption="تحلیل سخنرانی"
                )
            if user_practice.teacher_video_link:
                await callback_query.message.reply_video(
                    video=user_practice.teacher_video_link, caption="تحلیل سخنرانی"
                )

    async def correction(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])

        # await callback_query.message.delete()
        await callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔙 بازگشت",
                            callback_data=f"teacher_none_practice_user_practice_select_{user_practice_id}",
                        ),
                        InlineKeyboardButton(
                            "exit!",
                            callback_data="back_home",
                        ),
                    ]
                ]
            ),
        )

        await callback_query.message.reply_text(
            "نوع تحلیل را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "💬 متنی",
                            callback_data=f"teacher_none_practice_user_practice_correction_type_0_{user_practice_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🔈 صوتی",
                            callback_data=f"teacher_none_practice_user_practice_correction_type_1_{user_practice_id}",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "📹 ویدیوئی",
                            callback_data=f"teacher_none_practice_user_practice_correction_type_2_{user_practice_id}",
                        )
                    ],
                    [InlineKeyboardButton("exit!", callback_data="back_home")],
                ]
            ),
        )

    async def correction_type(self, client, callback_query):
        match = re.search(
            r"teacher_none_practice_user_practice_correction_type_(\d+)_(\d+)",
            callback_query.data,
        )
        # types_list = ["متنی", "صوتی", "ویدیوئی"]
        if match:
            await callback_query.message.delete()

            type = int(match.group(1))
            user_practice_id = int(match.group(2))

            # await callback_query.message.reply_text(
            #     f"لطفا تحلیل <b>{types_list[type]}</b> را ریپلی کنید.",
            #     reply_markup=InlineKeyboardMarkup(
            #         [
            #             [
            #                 InlineKeyboardButton(
            #                     "exit!",
            #                     callback_data="back_home",
            #                 )
            #             ]
            #         ]
            #     ),
            # )

            if type == 0:
                await callback_query.message.reply_text(
                    f"{user_practice_id}\n"
                    "👈 <b>ابتدا به این پیام ریپلای (پاسخ) بزنید سپس تحلیل متنی خود را ارسال کنید.</b>\n\n"
                    "⚠️ توجه: در صورتی که به این پیام ریپلای نزنید، ارسال تحلیل شما ناموفق خواهد بود!",
                    reply_markup=ForceReply(selective=True),
                )
            elif type == 1:
                await callback_query.message.reply_text(
                    f"{user_practice_id}\n"
                    "👈 <b>ابتدا به این پیام ریپلای (پاسخ) بزنید سپس تحلیل صوتی خود را ارسال کنید.</b>\n\n"
                    "⚠️ توجه: در صورتی که به این پیام ریپلای نزنید، ارسال تحلیل شما ناموفق خواهد بود!",
                    reply_markup=ForceReply(selective=True),
                )
            else:
                await callback_query.message.reply_text(
                    f"{user_practice_id}\n"
                    f"👈 <b>ابتدا به این پیام ریپلای (پاسخ) بزنید سپس تحلیل ویدیویی خود را ارسال کنید.</b>\n\n"
                    "⚠️ توجه: در صورتی که به این پیام ریپلای نزنید، ارسال تحلیل شما ناموفق خواهد بود!\n"
                    "همچنین ویدیوی ارسالی باید کمتر از 50 مگابایت باشد!",
                    reply_markup=ForceReply(selective=True),
                )
        else:
            await callback_query.message.reply_text("error!")

    @staticmethod
    async def send_user_correction_notification(client, user_practice_id):
        with db.get_session() as session:
            user_info = (
                session.query(db.UserModel.chat_id, db.UserPracticeModel.practice_id)
                .join(
                    db.UserPracticeModel,
                    db.UserModel.id == db.UserPracticeModel.user_id,
                )
                .filter(db.UserPracticeModel.id == user_practice_id)
                .first()
            )

            await client.send_message(
                chat_id=str(user_info.chat_id),
                text=f"تمرین {user_practice_id} شما تحلیل سخنرانی شد.",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "مشاهده",
                                callback_data=f"user_answered_practice_select_{user_info.practice_id}",
                            )
                        ]
                    ]
                ),
            )

    @staticmethod
    def set_teacher_caption_db(pk, teahcer_caption):
        with db.get_session() as session:
            user_practice = session.query(db.UserPracticeModel).get(pk)
            if user_practice:
                user_practice.teacher_caption = teahcer_caption
                session.commit()
                return True
        return False

    @staticmethod
    def set_teacher_voice_db(pk, file_link):
        with db.get_session() as session:
            user_practice = session.query(db.UserPracticeModel).get(pk)
            if user_practice:
                user_practice.teacher_voice_link = file_link
                user_practice.teacher_caption = "تحلیل صوتی است!"
                session.commit()
                return True
        return False

    @staticmethod
    def set_teacher_video_db(pk, file_link):
        with db.get_session() as session:
            user_practice = session.query(db.UserPracticeModel).get(pk)
            if user_practice:
                user_practice.teacher_video_link = file_link
                user_practice.teacher_caption = "تحلیل ویدیوئی است!"
                session.commit()
                return True
        return False

    async def correction_text(self, client, message):
        user_practice_id = int(message.reply_to_message.text.split("\n")[0])

        if self.set_teacher_caption_db(user_practice_id, message.text):
            await message.reply_to_message.delete()
            # await message.reply_text("ویس با موفقیت ثبت شد.")
            await message.reply_text(
                "آیا از ثبت این تحلیل سخنرانی اطمینان دارید؟",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "بلی",
                                callback_data=f"teacher_none_practice_user_practice_confirm_{user_practice_id}_1",
                            ),
                            InlineKeyboardButton(
                                "خیر",
                                callback_data=f"teacher_none_practice_user_practice_confirm_{user_practice_id}_0",
                            ),
                        ]
                    ]
                ),
            )

    async def correction_voice(self, client, message):
        user_practice_id = int(message.reply_to_message.text.split("\n")[0])

        media_id = message.voice.file_id

        capt = (
            f"#correction"
            f"message id: <i>{message.id}</i>\n---\n"
            f"from user @{message.from_user.username}\n"
        )

        # Forward the video to the channel
        await client.send_voice(chat_id=GROUP_CHAT_ID, voice=media_id, caption=capt)
        if self.set_teacher_voice_db(user_practice_id, media_id):
            await message.reply_to_message.delete()
            # await message.reply_text("ویس با موفقیت ثبت شد.")
            await message.reply_text(
                "آیا از ثبت این تحلیل سخنرانی اطمینان دارید؟",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "بلی",
                                callback_data=f"teacher_none_practice_user_practice_confirm_{user_practice_id}_1",
                            ),
                            InlineKeyboardButton(
                                "خیر",
                                callback_data=f"teacher_none_practice_user_practice_confirm_{user_practice_id}_0",
                            ),
                        ]
                    ]
                ),
            )

    async def correction_video(self, client, message):
        user_practice_id = int(message.reply_to_message.text.split("\n")[0])

        media_id = message.video.file_id
        media_status = (message.video.file_size / 1024) <= 50_000

        if not media_status:
            await message.reply_text("ویدیوی ارسالی باید کمتر از 50 مگابایت باشد!")
            return

        capt = (
            f"#correction"
            f"message id: <i>{message.id}</i>\n---\n"
            f"from user @{message.from_user.username}\n"
        )

        # Forward the video to the channel
        await client.send_video(chat_id=GROUP_CHAT_ID, video=media_id, caption=capt)
        if self.set_teacher_video_db(user_practice_id, media_id):
            await message.reply_to_message.delete()
            # await message.reply_text("ویدئو با موفقیت ثبت شد.")

            await message.reply_text(
                "آیا از ثبت این تحلیل سخنرانی اطمینان دارید؟",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "بلی",
                                callback_data=f"teacher_none_practice_user_practice_confirm_{user_practice_id}_1",
                            ),
                            InlineKeyboardButton(
                                "خیر",
                                callback_data=f"teacher_none_practice_user_practice_confirm_{user_practice_id}_0",
                            ),
                        ]
                    ]
                ),
            )

    @staticmethod
    def clear_correction_db(pk):
        with db.get_session() as session:
            user_practice = session.query(db.UserPracticeModel).get(pk)
            if user_practice:
                user_practice.teacher_caption = None
                user_practice.teacher_voice_link = None
                user_practice.teacher_video_link = None
                session.commit()
                return True
            return False

    async def confirm(self, client, callback_query):
        match = re.search(
            r"teacher_none_practice_user_practice_confirm_(\d+)_(\d+)",
            callback_query.data,
        )
        if match:
            user_practice_id = match.group(1)
            status = int(match.group(2))

            if status == 0:
                if self.clear_correction_db(user_practice_id):
                    await callback_query.message.delete()
                    await callback_query.message.reply_text("تحلیل پاک شد.")
                    await send_home_message_teacher(callback_query.message)
                    return
            else:
                await callback_query.answer("تحلیل با موفقیت ثبت شد.", show_alert=True)
                await callback_query.message.delete()
                await callback_query.message.reply_text("تحلیل با موفقیت ثبت شد.")
                await send_home_message_teacher(callback_query.message)
                asyncio.create_task(
                    self.send_user_correction_notification(client, user_practice_id)
                )
                return

        await callback_query.message.delete()
        await callback_query.message.reply_text("error!")


async def teacher_my_settings(client, message):
    with db.get_session() as session:
        teacher = (
            session.query(
                db.TeacherModel.id,
                db.TeacherModel.name,
                db.TeacherModel.tell_id,
                db.TeacherModel.phone_number,
                func.count(db.UserPracticeModel.id).label("user_practice_count"),
                func.count(
                    func.nullif(db.UserPracticeModel.teacher_caption, None)
                ).label("corrected_user_practice_count"),
            )
            .join(
                db.UserPracticeModel,
                db.UserPracticeModel.teacher_id == db.TeacherModel.id,
            )
            .filter(db.TeacherModel.tell_id == message.from_user.id)
            .group_by(db.TeacherModel.id)
            .first()
        )
        await message.reply(
            "ℹ️ user-level: <b>teacher</b>\n"
            f"🆔 teacher-id: <i>{teacher.id}</i>\n"
            f"👤 teacher-name: <code>{teacher.name}</code>\n"
            f"◾️ teacher-tell-id: <i>{teacher.tell_id}</i>\n"
            f"📞 teacher-phone-number: {teacher.phone_number}\n"
            "➖➖➖➖➖➖➖➖➖\n"
            f"▫️ تعداد تکلیف تخصیص داده شده: {teacher.user_practice_count}\n"
            f"▫️ تعداد تکلیف تصحیح شده: {teacher.corrected_user_practice_count}"
        )


def register_teacher_handlers(app):
    app.on_message(filters.regex("اطلاعات من") & filters.create(is_teacher))(
        teacher_my_settings
    )

    ActivePractice(app)
    AllPractice(app)
    NONEPractice(app)
