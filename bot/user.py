from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    ForceReply,
)
import datetime
import asyncio


from .pagination import get_paginated_keyboard
from .home import send_home_message_user
from config import ADMINS_LIST_ID, GROUP_CHAT_ID

import db.crud as db
from db.models import (
    Practice as PracticeModel,
    UserPractice as UserPracticeModel,
    User as UserModel,
)
from .admin import DB


def is_user(_, __, update):
    return db.User().read_with_tell_id(tell_id=update.from_user.id) is not None


class ActivePractice(DB):
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
                "user_active_practice_paginate_list",
                "user_active_practice_select",
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
                    "user_active_practice_paginate_list",
                    "user_active_practice_select",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                self.practices,
                page,
                "user_active_practices_page",
                "user_active_practice_select",
            )
        )

    def report_practice(self, pk):
        practice = self.session.query(PracticeModel).get(pk)
        return practice

    async def select(self, client, callback_query):
        practice_id = int(callback_query.data.split("_")[-1])

        # db
        practice = self.report_practice(pk=practice_id)
        user_practice = db.UserPractice().read_with_practice_id_single(
            practice_id=practice_id, tell_id=callback_query.from_user.id
        )

        await callback_query.message.delete()

        capt = "تحویل داده نشده!"
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "آپلود تمرین",
                        callback_data=f"user_active_practice_answer_{practice_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "back", callback_data="user_active_practice_paginate_list_0"
                    ),
                    InlineKeyboardButton("exit!", callback_data="back_home"),
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
                                "back",
                                callback_data="user_active_practice_paginate_list_0",
                            ),
                            InlineKeyboardButton("exit!", callback_data="back_home"),
                        ],
                    ]
                )
            else:
                capt = "در انتضار تصحیح"
                markup = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "ویرایش تمرین",
                                callback_data=f"user_active_practice_reanswer_{user_practice.id}",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "back",
                                callback_data="user_active_practice_paginate_list_0",
                            ),
                            InlineKeyboardButton("exit!", callback_data="back_home"),
                        ],
                    ]
                )

        await callback_query.message.reply_text(
            f"عنوان: {practice.title}\nمتن سوال: {practice.caption}\n----"
            f"\nوضعیت نمره: {capt}",
            reply_markup=markup,
        )

    async def answer(self, client, callback_query):
        practice_id = int(callback_query.data.split("_")[-1])

        await callback_query.message.delete()

        await callback_query.message.reply_text(
            "پیام خود را ریپلی کنید.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )
        await callback_query.message.reply_text(
            f"{practice_id}\n" "<b>Just send answer as a reply to this message</b>",
            reply_markup=ForceReply(selective=True),
        )

    @staticmethod
    async def send_admin_upload_notification(client):
        for i in ADMINS_LIST_ID:
            await client.send_message(
                chat_id=i,
                text="تکلیف جدیدی آپلود شد!",
            )

    async def upload(self, client, message):
        practice_id = int(message.reply_to_message.text.split("\n")[0])

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
        user_id = db.User().read_with_tell_id(tell_id=message.from_user.id).id

        # Store the Telegram link in the database
        db.UserPractice().add(
            user_id=user_id,
            practice_id=practice_id,
            file_link=telegram_link,
            user_caption=message.caption,
        )

        await message.reply_to_message.delete()
        await message.reply_text("تمرین با موفقیت ثبت شد.")
        await send_home_message_user(message)

        asyncio.create_task(self.send_admin_upload_notification(client))

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
        db.UserPractice().update(
            pk=user_practice_id,
            file_link=telegram_link,
            user_caption=message.caption or None,
        )

        await message.reply_to_message.delete()
        await message.reply_text("تمرین با موفقیت ثبت شد.")
        await send_home_message_user(message)

        asyncio.create_task(self.send_admin_upload_notification(client))


class AnsweredPractice(DB):
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
        query = (
            self.session.query(PracticeModel.id, PracticeModel.title)
            .join(UserPracticeModel, PracticeModel.id == UserPracticeModel.practice_id)
            .join(UserModel, UserModel.id == UserPracticeModel.user_id)
            .filter(UserModel.tell_id == user_tell_id)
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
                "user_answered_practices_page",
                "user_answered_practice_select",
            )
        )

    def report_practice(self, pk):
        practice = self.session.query(PracticeModel).get(pk)
        return practice

    async def select(self, client, callback_query):
        practice_id = int(callback_query.data.split("_")[-1])

        # db
        practice = self.report_practice(pk=practice_id)
        user_practice = db.UserPractice().read_with_practice_id_single(
            practice_id=practice_id, tell_id=callback_query.from_user.id
        )

        await callback_query.message.delete()

        capt = "تحویل داده نشده!"
        markup = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        "آپلود تمرین",
                        callback_data=f"user_answered_practice_answer_{practice_id}",
                    )
                ],
                [
                    InlineKeyboardButton(
                        "back", callback_data="user_answered_practice_paginate_list_0"
                    ),
                    InlineKeyboardButton("exit!", callback_data="back_home"),
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
                                "back",
                                callback_data="user_answered_practice_paginate_list_0",
                            ),
                            InlineKeyboardButton("exit!", callback_data="back_home"),
                        ],
                    ]
                )
            else:
                capt = "در انتضار تصحیح"
                markup = InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "ویرایش تمرین",
                                callback_data=f"user_answered_practice_reanswer_{user_practice.id}",
                            )
                        ],
                        [
                            InlineKeyboardButton(
                                "back",
                                callback_data="user_answered_practice_paginate_list_0",
                            ),
                            InlineKeyboardButton("exit!", callback_data="back_home"),
                        ],
                    ]
                )

        await callback_query.message.reply_text(
            f"عنوان: {practice.title}\nمتن سوال: {practice.caption}\n----"
            f"\nوضعیت نمره: {capt}",
            reply_markup=markup,
        )

    async def answer(self, client, callback_query):
        practice_id = int(callback_query.data.split("_")[-1])

        await callback_query.message.delete()

        await callback_query.message.reply_text(
            "پیام خود را ریپلی کنید.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]]
            ),
        )
        await callback_query.message.reply_text(
            f"{practice_id}\n" "<b>Just send answer as a reply to this message</b>",
            reply_markup=ForceReply(selective=True),
        )

    @staticmethod
    async def send_admin_upload_notification(client):
        for i in ADMINS_LIST_ID:
            await client.send_message(
                chat_id=i,
                text="تکلیف جدیدی آپلود شد!",
            )

    async def upload(self, client, message):
        practice_id = int(message.reply_to_message.text.split("\n")[0])

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
        user_id = db.User().read_with_tell_id(tell_id=message.from_user.id).id

        # Store the Telegram link in the database
        db.UserPractice().add(
            user_id=user_id,
            practice_id=practice_id,
            file_link=telegram_link,
            user_caption=message.caption,
        )

        await message.reply_to_message.delete()
        await message.reply_text("تمرین با موفقیت ثبت شد.")
        await send_home_message_user(message)

        asyncio.create_task(self.send_admin_upload_notification(client))

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
        db.UserPractice().update(
            pk=user_practice_id,
            file_link=telegram_link,
            user_caption=message.caption or None,
        )

        await message.reply_to_message.delete()
        await message.reply_text("تمرین با موفقیت ثبت شد.")
        await send_home_message_user(message)

        asyncio.create_task(self.send_admin_upload_notification(client))


async def user_settings(client, message):
    user = db.User().read_with_tell_id(tell_id=message.from_user.id)
    await message.reply(f"You are <b>user</b> and your id is <i>{user.id}</i>")


def register_user_handlers(app):
    app.on_message(filters.regex("my settings") & filters.create(is_user))(
        user_settings
    )
