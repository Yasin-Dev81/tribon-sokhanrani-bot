from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ForceReply,
)
from sqlalchemy import and_
import datetime
import asyncio

from .pagination import get_paginated_keyboard
from .home import send_home_message_user
from config import ADMINS_LIST_ID, GROUP_CHAT_ID
import db


def is_user(_, __, update):
    with db.get_session() as session:
        return (
            session.query(db.UserModel).filter_by(tell_id=update.from_user.id).first()
            is not None
        )


class ActivePractice:
    def __init__(self, app):
        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(filters.regex("تمرین‌های فعال") & filters.create(is_user))(
            self.list
        )
        self.app.on_callback_query(
            filters.regex(r"user_active_practice_paginate_list_(\d+)")
            & filters.create(is_user)
        )(self.paginate_list)
        self.app.on_callback_query(
            filters.regex(r"user_active_practice_select_(\d+)")
            & filters.create(is_user)
        )(self.select)
        self.app.on_callback_query(
            filters.regex(r"user_active_practice_answer_(\d+)")
            & filters.create(is_user)
        )(self.answer)
        self.app.on_message(
            filters.reply
            & filters.video
            & filters.create(is_user)
            & filters.create(self.is_new_answer_msg)
        )(self.upload)
        self.app.on_callback_query(
            filters.regex(r"user_active_practice_reanswer_(\d+)")
            & filters.create(is_user)
        )(self.reanswer)
        self.app.on_message(
            filters.reply
            & filters.video
            & filters.create(is_user)
            & filters.create(self.is_reanswer_msg)
        )(self.reupload)

    @staticmethod
    def is_new_answer_msg(filter, client, update):
        return (
            "Just send answer as a reply to this message"
            in update.reply_to_message.text
        )

    @staticmethod
    def is_reanswer_msg(filter, client, update):
        return (
            "Just send x answer as a reply to this message"
            in update.reply_to_message.text
        )

    def practices(self, user_tell_id):
        current_time = datetime.datetime.now()
        with db.get_session() as session:
            practices = (
                session.query(db.PracticeModel.id, db.PracticeModel.title)
                .join(
                    db.UserModel, db.UserModel.user_type_id == db.PracticeModel.user_type_id
                )
                .filter(
                    db.UserModel.tell_id == user_tell_id,
                    db.PracticeModel.start_date <= current_time,
                    db.PracticeModel.end_date >= current_time,
                )
                .all()
            )
            return practices

    async def list(self, client, message):
        practices = self.practices(message.from_user.id)
        if not practices:
            await message.reply_text("هیچ تمرین فعالی موجود نیست!")
            return

        await message.reply_text(
            "تمارین فعال:",
            reply_markup=get_paginated_keyboard(
                practices,
                0,
                "user_active_practice_paginate_list",
                "user_active_practice_select",
            ),
        )

    async def paginate_list(self, client, callback_query):
        page = int(callback_query.data.split("_")[-1])
        practices = self.practices(callback_query.from_user.id)

        if not practices:
            await callback_query.message.reply_text("هیچ تمرین فعالی موجود نیست!")
            return

        if page == 0:
            try:
                await callback_query.message.delete()
            except Exception:
                pass

            await callback_query.message.reply_text(
                "تمارین فعال:",
                reply_markup=get_paginated_keyboard(
                    practices,
                    page,
                    "user_active_practice_paginate_list",
                    "user_active_practice_select",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                practices,
                page,
                "user_active_practice_paginate_list",
                "user_active_practice_select",
            )
        )

    @staticmethod
    def report_practice(pk):
        with db.get_session() as session:
            practice = (
                session.query(
                    db.PracticeModel.title,
                    db.PracticeModel.caption,
                    and_(
                        db.PracticeModel.start_date <= datetime.datetime.now(),
                        db.PracticeModel.end_date >= datetime.datetime.now(),
                    ).label("status"),
                )
                .filter(db.PracticeModel.id == pk)
                .first()
            )
            return practice

    @staticmethod
    def report_user_practice(practice_id, tell_id):
        with db.get_session() as session:
            query = (
                session.query(
                    db.PracticeModel.title,
                    db.PracticeModel.caption,
                    db.UserPracticeModel.user_caption,
                    db.UserPracticeModel.teacher_caption,
                    db.UserPracticeModel.id,
                    db.UserPracticeModel.teacher_voice_link,
                    db.UserPracticeModel.teacher_video_link,
                    and_(
                        db.PracticeModel.start_date <= datetime.datetime.now(),
                        db.PracticeModel.end_date >= datetime.datetime.now(),
                    ).label("status"),
                )
                .join(
                    db.PracticeModel,
                    db.PracticeModel.id == db.UserPracticeModel.practice_id,
                )
                .join(db.UserModel, db.UserModel.id == db.UserPracticeModel.user_id)
                .filter(db.UserPracticeModel.practice_id == practice_id)
                .filter(db.UserModel.tell_id == tell_id)
            )
            return query.first()

    async def select(self, client, callback_query):
        practice_id = int(callback_query.data.split("_")[-1])
        user_practice = self.report_user_practice(
            practice_id=practice_id, tell_id=callback_query.from_user.id
        )
        if not user_practice:
            practice = self.report_practice(pk=practice_id)

        try:
            await callback_query.message.delete()
        except Exception:
            pass

        capt = "تحویل داده نشده!"
        markup = [
            [
                InlineKeyboardButton(
                    "آپلود تمرین",
                    callback_data=f"user_active_practice_answer_{practice_id}",
                )
            ]
        ]
        if user_practice:
            if user_practice.teacher_caption:
                capt = (
                    "تحلیل سخنرانی شده.\n"
                    f"◾️بازخورد استاد: {user_practice.teacher_caption}"
                )
                markup = []
            else:
                capt = "در انتظار تحلیل سخنرانی"
                markup = [
                    [
                        InlineKeyboardButton(
                            "ویرایش تمرین",
                            callback_data=f"user_active_practice_reanswer_{user_practice.id}",
                        )
                    ],
                ]

            if not user_practice.status:
                markup = []

        markup.append(
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="user_active_practice_paginate_list_0",
                ),
                InlineKeyboardButton("exit!", callback_data="back_home"),
            ],
        )

        if user_practice:
            await callback_query.message.reply_text(
                f"📌 عنوان: {user_practice.title}\n🔖 متن سوال: {user_practice.caption}\n----"
                f"\n📊 وضعیت تمرین: {capt}",
                reply_markup=InlineKeyboardMarkup(markup),
            )

            if user_practice.teacher_caption:
                if user_practice.teacher_voice_link:
                    await callback_query.message.reply_voice(
                        voice=user_practice.teacher_voice_link,
                        caption="تحلیل سخنرانی",
                    )
                if user_practice.teacher_video_link:
                    await callback_query.message.reply_video(
                        video=user_practice.teacher_video_link,
                        caption="تحلیل سخنرانی",
                    )
        else:
            if not practice.status:
                markup = []

            await callback_query.message.reply_text(
                f"📌 عنوان: {practice.title}\n🔖 متن سوال: {practice.caption}\n----"
                f"\n📊 وضعیت تمرین: {capt}",
                reply_markup=InlineKeyboardMarkup(markup),
            )

    async def answer(self, client, callback_query):
        practice_id = int(callback_query.data.split("_")[-1])

        try:
            await callback_query.message.delete()
        except Exception:
            pass

        await callback_query.message.reply_text(
            "ویدیوی خود را ریپلی کنید.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )
        await callback_query.message.reply_text(
            f"{practice_id}\n" "<b>Just send answer as a reply to this message</b>",
            reply_markup=ForceReply(selective=True),
        )

    @staticmethod
    async def send_admin_upload_notification(client, user_practice_id):
        for i in ADMINS_LIST_ID:
            await client.send_message(
                chat_id=str(i),
                text="تکلیف جدیدی آپلود شد!",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "مشاهده",
                                callback_data=f"admin_all_practice_user_practice_select_{user_practice_id}",
                            )
                        ]
                    ]
                ),
            )

    @staticmethod
    def upload_db(user_id, file_link, practice_id, user_caption=None):
        with db.get_session() as session:
            new_user_practice = db.UserPracticeModel(
                user_id=user_id,
                file_link=file_link,
                practice_id=practice_id,
                user_caption=user_caption,
            )
            session.add(new_user_practice)
            session.commit()
            return new_user_practice.id

    async def upload(self, client, message):
        practice_id = int(message.reply_to_message.text.split("\n")[0])

        media_id = message.video.file_id
        media_status = (message.video.file_size / 1024) <= 50_000

        if not media_status:
            await message.reply_text("ویدیوی ارسالی باید کمتر از 50 مگابایت باشد!")
            return

        capt = (
            f"message id: <i>{message.id}</i>\n---\n"
            f"from user @{message.from_user.username}\n"
            f"user caption:\n{message.caption or 'No Caption!'}"
        )

        # Forward the video to the channel
        forwarded_message = await client.send_video(
            chat_id=GROUP_CHAT_ID, video=media_id, caption=capt
        )
        telegram_link = forwarded_message.video.file_id
        with db.get_session() as session:
            user_id = (
                session.query(db.UserModel)
                .filter_by(tell_id=message.from_user.id)
                .first()
                .id
            )

            # Store the Telegram link in the database
            user_practice_id = self.upload_db(
                user_id=user_id,
                practice_id=practice_id,
                file_link=telegram_link,
                user_caption=message.caption,
            )

        try:
            await message.reply_to_message.delete()
        except Exception:
            pass

        await message.reply_text("تمرین با موفقیت ثبت شد.")
        await send_home_message_user(message)

        asyncio.create_task(
            self.send_admin_upload_notification(client, user_practice_id)
        )

    async def reanswer(self, client, callback_query):
        practice_id = int(callback_query.data.split("_")[-1])

        await callback_query.message.delete()

        await callback_query.message.reply_text(
            "پیام خود را ریپلی کنید.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )
        await callback_query.message.reply_text(
            f"{practice_id}\n" "<b>Just send x answer as a reply to this message</b>",
            reply_markup=ForceReply(selective=True),
        )

    @staticmethod
    def update_db(pk, file_link, user_caption=None):
        with db.get_session() as session:
            user_practice = session.query(db.UserPracticeModel).get(pk)
            if user_practice:
                user_practice.file_link = file_link
                if user_caption is not None:
                    user_practice.user_caption = user_caption
                session.commit()
            return pk

    async def reupload(self, client, message):
        user_practice_id = int(message.reply_to_message.text.split("\n")[0])
        media_id = message.video.file_id

        capt = (
            f"message id: <i>{message.id}</i>\n---\n"
            f"from user @{message.from_user.username}\n"
            f"user caption:\n{message.caption or 'No Caption!'}"
        )

        # Forward the video to the channel
        forwarded_message = await client.send_video(
            chat_id=GROUP_CHAT_ID, video=media_id, caption=capt
        )
        telegram_link = forwarded_message.video.file_id

        # Store the Telegram link in the database
        self.update_db(
            pk=user_practice_id,
            file_link=telegram_link,
            user_caption=message.caption or None,
        )

        await message.reply_to_message.delete()
        await message.reply_text("تمرین با موفقیت ثبت شد.")
        await send_home_message_user(message)

        # asyncio.create_task(self.send_admin_upload_notification(client, user_practice_id))


class AnsweredPractice:
    def __init__(self, app):
        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(
            filters.regex("تحویل داده شده‌ها") & filters.create(is_user)
        )(self.list)
        self.app.on_callback_query(
            filters.regex(r"user_answered_practice_paginate_list_(\d+)")
            & filters.create(is_user)
        )(self.paginate_list)
        self.app.on_callback_query(
            filters.regex(r"user_answered_practice_select_(\d+)")
            & filters.create(is_user)
        )(self.select)
        # self.app.on_callback_query(
        #     filters.regex(r"user_answered_practice_answer_(\d+)")
        #     & filters.create(is_user)
        # )(self.answer)
        # self.app.on_message(
        #     filters.reply
        #     & filters.video
        #     & filters.create(is_user)
        #     & filters.create(self.is_new_answer_msg)
        # )(self.upload)
        self.app.on_callback_query(
            filters.regex(r"user_answered_practice_reanswer_(\d+)")
            & filters.create(is_user)
        )(self.reanswer)
        self.app.on_message(
            filters.reply
            & filters.video
            & filters.create(is_user)
            & filters.create(self.is_reanswer_msg)
        )(self.reupload)

    @staticmethod
    def is_new_answer_msg(filter, client, update):
        return (
            "Just send answer as a reply to this message"
            in update.reply_to_message.text
        )

    @staticmethod
    def is_reanswer_msg(filter, client, update):
        return (
            "Just send xx answer as a reply to this message"
            in update.reply_to_message.text
        )

    def practices(self, user_tell_id):
        with db.get_session() as session:
            query = (
                session.query(db.PracticeModel.id, db.PracticeModel.title)
                .join(
                    db.UserPracticeModel,
                    db.PracticeModel.id == db.UserPracticeModel.practice_id,
                )
                .join(db.UserModel, db.UserModel.id == db.UserPracticeModel.user_id)
                .filter(db.UserModel.tell_id == user_tell_id)
            )

            return query.all()

    async def list(self, client, message):
        practices = self.practices(message.from_user.id)
        if not practices:
            await message.reply_text("هیچ تمرین فعالی موجود نیست!")
            return

        await message.reply_text(
            "تمارین فعال:",
            reply_markup=get_paginated_keyboard(
                practices,
                0,
                "user_answered_practice_paginate_list",
                "user_answered_practice_select",
            ),
        )

    async def paginate_list(self, client, callback_query):
        page = int(callback_query.data.split("_")[-1])
        practices = self.practices(callback_query.from_user.id)

        if not practices:
            await callback_query.message.reply_text("هیچ تکلیفی موجود نیست!")
            return

        if page == 0:
            await callback_query.message.delete()
            await callback_query.message.reply_text(
                "تمارین فعال:",
                reply_markup=get_paginated_keyboard(
                    practices,
                    page,
                    "user_answered_practice_paginate_list",
                    "user_answered_practice_select",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                practices,
                page,
                "user_answered_practice_paginate_list",
                "user_answered_practice_select",
            )
        )

    @staticmethod
    def report_practice(pk):
        with db.get_session() as session:
            practice = session.query(
                db.PracticeModel,
                and_(
                    db.PracticeModel.start_date <= datetime.datetime.now(),
                    db.PracticeModel.end_date >= datetime.datetime.now(),
                ).label("status"),
            ).get(pk)
            return practice

    @staticmethod
    def report_user_practice(practice_id, tell_id):
        with db.get_session() as session:
            query = (
                session.query(
                    db.PracticeModel.title,
                    db.PracticeModel.caption,
                    db.UserPracticeModel.user_caption,
                    db.UserPracticeModel.teacher_caption,
                    db.UserPracticeModel.id,
                    db.UserPracticeModel.teacher_voice_link,
                    db.UserPracticeModel.teacher_video_link,
                    db.PracticeModel.start_date,
                    db.PracticeModel.end_date,
                    and_(
                        db.PracticeModel.start_date <= datetime.datetime.now(),
                        db.PracticeModel.end_date >= datetime.datetime.now(),
                    ).label("status"),
                )
                .join(
                    db.PracticeModel,
                    db.PracticeModel.id == db.UserPracticeModel.practice_id,
                )
                .join(db.UserModel, db.UserModel.id == db.UserPracticeModel.user_id)
                .filter(db.UserPracticeModel.practice_id == practice_id)
                .filter(db.UserModel.tell_id == tell_id)
            )
            return query.first()

    async def select(self, client, callback_query):
        practice_id = int(callback_query.data.split("_")[-1])
        user_practice = self.report_user_practice(
            practice_id=practice_id, tell_id=callback_query.from_user.id
        )
        if not user_practice:
            practice = self.report_practice(pk=practice_id)

        await callback_query.message.delete()

        capt = "تحویل داده نشده!"
        markup = [
            [
                InlineKeyboardButton(
                    "آپلود تمرین",
                    callback_data=f"user_active_practice_answer_{practice_id}",
                )
            ]
        ]
        if user_practice:
            if user_practice.teacher_caption:
                capt = (
                    "تحلیل سخنرانی شده.\n"
                    f"◾️ بازخورد استاد: {user_practice.teacher_caption}"
                )
                markup = []
            else:
                capt = "در انتظار تحلیل سخنرانی"
                markup = [
                    [
                        InlineKeyboardButton(
                            "ویرایش تمرین",
                            callback_data=f"user_active_practice_reanswer_{user_practice.id}",
                        )
                    ],
                ]

            if not user_practice.status:
                markup = []

        markup.append(
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="user_active_practice_paginate_list_0",
                ),
                InlineKeyboardButton("exit!", callback_data="back_home"),
            ],
        )

        if user_practice:
            await callback_query.message.reply_text(
                f"📌 عنوان: {user_practice.title}\n🔖 متن سوال: {user_practice.caption}\n----"
                f"\n📊 وضعیت تمرین: {capt}",
                reply_markup=InlineKeyboardMarkup(markup),
            )
            if user_practice.teacher_caption:
                if user_practice.teacher_voice_link:
                    await callback_query.message.reply_voice(
                        voice=user_practice.teacher_voice_link,
                        caption="تحلیل سخنرانی",
                    )
                if user_practice.teacher_video_link:
                    await callback_query.message.reply_video(
                        video=user_practice.teacher_video_link,
                        caption="تحلیل سخنرانی",
                    )
        else:
            if not practice.status:
                markup = []

            await callback_query.message.reply_text(
                f"📌 عنوان: {practice.title}\n🔖 متن سوال: {practice.caption}\n----"
                f"\n📊 وضعیت تمرین: {capt}",
                reply_markup=InlineKeyboardMarkup(markup),
            )

    async def answer(self, client, callback_query):
        practice_id = int(callback_query.data.split("_")[-1])

        await callback_query.message.delete()

        await callback_query.message.reply_text(
            "ویدیوی خود را ریپلی کنید.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )
        await callback_query.message.reply_text(
            f"{practice_id}\n" "<b>Just send answer as a reply to this message</b>",
            reply_markup=ForceReply(selective=True),
        )

    @staticmethod
    async def send_admin_upload_notification(client, user_practice_id):
        for i in ADMINS_LIST_ID:
            await client.send_message(
                chat_id=str(i),
                text="تکلیف جدیدی آپلود شد!",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "مشاهده",
                                callback_data=f"admin_all_practice_user_practice_select_{user_practice_id}",
                            )
                        ]
                    ]
                ),
            )

    @staticmethod
    def upload_db(user_id, file_link, practice_id, user_caption=None):
        with db.get_session() as session:
            new_user_practice = db.UserPracticeModel(
                user_id=user_id,
                file_link=file_link,
                practice_id=practice_id,
                user_caption=user_caption,
            )
            session.add(new_user_practice)
            session.commit()
            return new_user_practice.id

    async def upload(self, client, message):
        practice_id = int(message.reply_to_message.text.split("\n")[0])

        media_id = message.video.file_id
        media_status = (message.video.file_size / 1024) <= 50_000

        if not media_status:
            await message.reply_text("ویدیوی ارسالی باید کمتر از 50 مگابایت باشد!")
            return

        capt = (
            f"message id: <i>{message.id}</i>\n---\n"
            f"from user @{message.from_user.username}\n"
            f"user caption:\n{message.caption or 'No Caption!'}"
        )

        # Forward the video to the channel
        forwarded_message = await client.send_video(
            chat_id=GROUP_CHAT_ID, video=media_id, caption=capt
        )
        telegram_link = forwarded_message.video.file_id
        # user_id = db.User().read_with_tell_id(tell_id=message.from_user.id).id
        with db.get_session() as session:
            user_id = (
                session.query(db.UserModel)
                .filter_by(tell_id=message.from_user.id)
                .first()
                .id
            )

            # Store the Telegram link in the database
            user_practice_id = self.upload_db(
                user_id=user_id,
                practice_id=practice_id,
                file_link=telegram_link,
                user_caption=message.caption,
            )

        await message.reply_to_message.delete()
        await message.reply_text("تمرین با موفقیت ثبت شد.")
        await send_home_message_user(message)

        asyncio.create_task(
            self.send_admin_upload_notification(client, user_practice_id)
        )

    async def reanswer(self, client, callback_query):
        practice_id = int(callback_query.data.split("_")[-1])

        await callback_query.message.delete()

        await callback_query.message.reply_text(
            "پیام خود را ریپلی کنید.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )
        await callback_query.message.reply_text(
            f"{practice_id}\n" "<b>Just send x answer as a reply to this message</b>",
            reply_markup=ForceReply(selective=True),
        )

    @staticmethod
    def update_db(pk, file_link, user_caption=None):
        with db.get_session() as session:
            user_practice = session.query(db.UserPracticeModel).get(pk)
            if user_practice:
                user_practice.file_link = file_link
                if user_caption is not None:
                    user_practice.user_caption = user_caption
                session.commit()
            return pk

    async def reupload(self, client, message):
        user_practice_id = int(message.reply_to_message.text.split("\n")[0])
        media_id = message.video.file_id
        media_status = (message.video.file_size / 1024) <= 50_000

        if not media_status:
            await message.reply_text("ویدیوی ارسالی باید کمتر از 50 مگابایت باشد!")
            return

        capt = (
            f"message id: <i>{message.id}</i>\n---\n"
            f"from user @{message.from_user.username}\n"
            f"user caption:\n{message.caption or 'No Caption!'}"
        )

        # Forward the video to the channel
        forwarded_message = await client.send_video(
            chat_id=GROUP_CHAT_ID, video=media_id, caption=capt
        )
        telegram_link = forwarded_message.video.file_id

        # Store the Telegram link in the database
        self.update_db(
            pk=user_practice_id,
            file_link=telegram_link,
            user_caption=message.caption or None,
        )

        await message.reply_to_message.delete()
        await message.reply_text("تمرین با موفقیت ثبت شد.")
        await send_home_message_user(message)

        # asyncio.create_task(self.send_admin_upload_notification(client, user_practice_id))


async def user_settings(client, message):
    with db.get_session() as session:
        user = (
            session.query(db.UserModel).filter_by(tell_id=message.from_user.id).first()
        )
        await message.reply(
            f"You are <b>user</b> and your id is <i>{user.id}</i>\nName: {user.name}"
        )


def register_user_handlers(app):
    app.on_message(filters.regex("my settings") & filters.create(is_user))(
        user_settings
    )

    ActivePractice(app)
    AnsweredPractice(app)
