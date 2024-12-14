from pyrogram import filters
from persiantools.jdatetime import JalaliDateTime
from sqlalchemy import func, case, and_
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from pyrogram.enums import MessageMediaType
import asyncio
import datetime
import re
import pyrostep

from .pagination import get_paginated_keyboard, user_practice_paginated_keyboard
from .home import send_home_message_teacher
from config import GROUP_CHAT_ID, TIME_ZONE, TIME_OUT, WARN_MSG, DATE_TIME_FMT
import db


def is_teacher(filter, client, update):
    with db.get_session() as session:
        return (
            session.query(db.TeacherModel)
            .filter_by(tell_id=update.from_user.id)
            .first()
            is not None
        )


class BaseUserPractice:
    correction_msg_dict = {
        db.MediaType.PHOTO: "تحلیل بصورت عکس است.",
        db.MediaType.DOCUMENT: "تحلیل بصورت فایل است.",
        db.MediaType.VIDEO: "تحلیل بصورت ویدیو است.",
        db.MediaType.VOICE: "تحلیل بصورت ویس است.",
        db.MediaType.AUDIO: "تحلیل بصورت فایل صوتی است.",
        db.MediaType.VIDEO_NOTE: "تحلیل بصورت ویدیو نوت است.",
    }

    def __init__(self, app, type="all") -> None:
        self.app = app
        self.type = type
        self.xbase_register_handlers()

    def xbase_register_handlers(self):
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
        self.app.on_callback_query(
            filters.regex(
                rf"teacher_{self.type}_practice_user_practice_confirm_(\d+)_(\d+)"
            )
            & filters.create(is_teacher)
        )(self.confirm)

    @staticmethod
    def report_user_practice(pk):
        with db.get_session() as session:
            query = (
                session.query(
                    db.PracticeModel.title,
                    db.PracticeModel.caption,
                    db.UserPracticeModel.file_link.label("user_file_link"),
                    db.UserPracticeModel.media_type.label("user_media_type"),
                    db.UserPracticeModel.caption.label("user_caption"),
                    db.CorrectionModel.caption.label("teacher_caption"),
                    db.CorrectionModel.file_link.label("teacher_file_link"),
                    db.CorrectionModel.media_type.label("teacher_media_type"),
                    db.UserPracticeModel.id,
                    db.CorrectionModel.id.label("correction_id"),
                    case(
                        (func.count(db.CorrectionModel.id) > 0, False),
                        else_=and_(
                            db.PracticeModel.start_date
                            <= datetime.datetime.now(TIME_ZONE),
                            db.PracticeModel.end_date
                            >= datetime.datetime.now(TIME_ZONE),
                        ),
                    ).label("status"),
                    db.PracticeModel.end_date.label("dd_line"),
                    db.UserModel.name.label("user_name"),
                )
                .join(
                    db.PracticeModel,
                    db.PracticeModel.id == db.UserPracticeModel.practice_id,
                )
                .outerjoin(
                    db.UserModel,
                    db.UserModel.id == db.UserPracticeModel.user_id,
                )
                .outerjoin(
                    db.CorrectionModel,
                    db.CorrectionModel.user_practice_id == db.UserPracticeModel.id,
                )
                .filter(db.UserPracticeModel.id == pk)
                .group_by(
                    db.UserPracticeModel.id,
                    db.PracticeModel.title,
                    db.PracticeModel.caption,
                    db.UserPracticeModel.file_link,
                    db.UserPracticeModel.media_type,
                    db.UserPracticeModel.caption,
                    db.CorrectionModel.caption,
                    db.CorrectionModel.file_link,
                    db.CorrectionModel.media_type,
                    db.PracticeModel.end_date,
                    db.CorrectionModel.id,
                    db.UserModel.name,
                )
            ).first()
            return query

    async def user_practice_select(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])
        await callback_query.answer(f"تکلیف {user_practice_id}")

        try:
            await callback_query.message.delete()
        except Exception:
            pass

        user_practice = self.report_user_practice(user_practice_id)

        markup = [
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data=f"teacher_{self.type}_practice_paginate_list_0",
                ),
                InlineKeyboardButton("exit!", callback_data="back_home"),
            ]
        ]

        if user_practice:
            correction = "در انتظار تحلیل سخنرانی"

            if user_practice.teacher_caption:
                correction = f"تحلیل سخنرانی شده.\n◾️ کپشن منتور: {user_practice.teacher_caption}"
            else:
                markup.insert(
                    0,
                    [
                        InlineKeyboardButton(
                            "تحلیل سخنرانی",
                            callback_data=f"teacher_{self.type}_practice_user_practice_correction_{user_practice_id}",
                        )
                    ],
                )

            caption = (
                f"📌 عنوان: {user_practice.title}\n🔖 متن سوال: {user_practice.caption}\n"
                f"◾️ ددلاین تمرین: {JalaliDateTime(user_practice.dd_line).strftime(DATE_TIME_FMT, locale='fa')}\n"
                f"◾️ کپشن کاربر: {user_practice.user_caption or 'بدون کپشن!'}\n"
                f"◾️ نام کاربر: {user_practice.user_name}\n"
                "➖➖➖➖➖➖➖➖➖\n"
                f"<blockquote expandable>📊 وضعیت تمرین: {correction}</blockquote>"
            )

            media_reply_methods = {
                db.MediaType.TEXT: callback_query.message.reply_text,
                db.MediaType.PHOTO: callback_query.message.reply_photo,
                db.MediaType.DOCUMENT: callback_query.message.reply_document,
                db.MediaType.VIDEO: callback_query.message.reply_video,
                db.MediaType.VOICE: callback_query.message.reply_voice,
                db.MediaType.AUDIO: callback_query.message.reply_audio,
                db.MediaType.VIDEO_NOTE: callback_query.message.reply_video_note,
            }

            reply_method = media_reply_methods.get(user_practice.user_media_type)

            if reply_method:
                if user_practice.user_media_type == db.MediaType.TEXT:
                    await callback_query.message.reply_text(
                        caption,
                        reply_markup=InlineKeyboardMarkup(markup),
                    )
                elif user_practice.user_media_type == db.MediaType.VIDEO_NOTE:
                    await reply_method(video_note=user_practice.user_file_link)
                    await callback_query.message.reply_text(
                        caption,
                        reply_markup=InlineKeyboardMarkup(markup),
                    )
                else:
                    kwargs = {
                        "caption": caption,
                        "reply_markup": InlineKeyboardMarkup(markup),
                    }
                    if user_practice.user_media_type != db.MediaType.TEXT:
                        kwargs[reply_method.__name__.split("_")[-1]] = (
                            user_practice.user_file_link
                        )
                    await reply_method(**kwargs)

            if (
                user_practice.correction_id
                and user_practice.teacher_media_type != db.MediaType.TEXT
            ):
                correction_reply_method = media_reply_methods.get(
                    user_practice.teacher_media_type
                )
                if correction_reply_method:
                    if user_practice.teacher_media_type == db.MediaType.VIDEO_NOTE:
                        await correction_reply_method(
                            video_note=user_practice.teacher_file_link
                        )
                        await callback_query.message.reply_text(
                            "تحلیل سخنرانی",
                        )
                    else:
                        kwargs = {
                            "caption": "تحلیل سخنرانی",
                        }
                        if user_practice.teacher_media_type != db.MediaType.TEXT:
                            kwargs[correction_reply_method.__name__.split("_")[-1]] = (
                                user_practice.teacher_file_link
                            )
                        await correction_reply_method(**kwargs)

        else:
            await callback_query.message.reply_text("این تکلیف موجود نیست!")

    @staticmethod
    def media_acsess(user_practice_id):
        with db.get_session() as session:
            return (
                session.query(db.MediaAcsessModel)
                .join(
                    db.UserPracticeModel,
                    db.UserPracticeModel.practice_id == db.MediaAcsessModel.practice_id,
                )
                .filter(db.UserPracticeModel.id == user_practice_id)
                .filter(db.MediaAcsessModel.user_level == db.UserLevel.TEACHER)
                .all()
            )

    @staticmethod
    def upload_db(pk, media_type, file_id, caption):
        with db.get_session() as session:
            correction = (
                session.query(db.CorrectionModel).filter_by(user_practice_id=pk).first()
            )
            if correction:
                correction.media_type = media_type
                correction.file_link = file_id
                correction.caption = caption
                session.commit()
                return True
        return False

    async def correction(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])

        with db.get_session() as session:
            if (
                not session.query(db.CorrectionModel)
                .filter_by(user_practice_id=user_practice_id)
                .join(
                    db.TeacherModel, db.TeacherModel.id == db.CorrectionModel.teacher_id
                )
                .filter(db.TeacherModel.tell_id == callback_query.from_user.id)
                .first()
            ):
                await callback_query.answer("شما امکان تصحیح این تکلیف را ندارید!")

        media_acsess = self.media_acsess(user_practice_id)
        # print(media_acsess)

        try:
            # await callback_query.message.delete()
            await callback_query.message.edit_reply_markup(
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Cancel", callback_data="back_home")]]
                ),
            )
        except Exception:
            pass

        media_types = [i.media_type.value for i in media_acsess]
        str_media_types = "\n✔️ ".join(media_types)
        await callback_query.message.reply_text(
            f"📌 تایپ‌های مدیای قابل قبول:\n✔️ {str_media_types}\n{WARN_MSG}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Cancel", callback_data="back_home")]]
            ),
        )

        media_methods = {
            MessageMediaType.VIDEO: (client.send_video, db.MediaType.VIDEO),
            MessageMediaType.PHOTO: (client.send_photo, db.MediaType.PHOTO),
            MessageMediaType.DOCUMENT: (client.send_document, db.MediaType.DOCUMENT),
            MessageMediaType.VOICE: (client.send_voice, db.MediaType.VOICE),
            MessageMediaType.AUDIO: (client.send_audio, db.MediaType.AUDIO),
            MessageMediaType.VIDEO_NOTE: (
                client.send_video_note,
                db.MediaType.VIDEO_NOTE,
            ),
        }

        try:
            answer = await pyrostep.wait_for(
                callback_query.from_user.id, timeout=TIME_OUT * 60
            )

            # Handle media messages
            if answer.media and answer.media in media_methods:
                send_method, media_type = media_methods[answer.media]

                if media_type.value not in media_types:
                    await answer.reply_text("این تایپ مدیا مجاز نیست!\nلطفا دوباره اقدام به ارسال کنید!")
                    return

                media_id = getattr(answer, answer.media.value.lower()).file_id
                caption = answer.caption or self.correction_msg_dict.get(media_type)
                file_size = getattr(answer, answer.media.value.lower()).file_size

                # Check file size limit
                if (file_size / 1024) > 50_000:
                    await answer.reply_text(
                        "فایل ارسالی باید کمتر از <b>50 مگابایت</b> باشد!\nلطفا دوباره اقدام به ارسال کنید!"
                    )
                    return

                capt = (
                    f"message id: <i>{answer.id}</i>\n---\n"
                    f"from user @{answer.from_user.username}\n"
                    f"user caption:\n{caption}\n"
                    f"user_practice_id: {user_practice_id}"
                )

                # Forward the media to the channel
                forwarded_message = await send_method(
                    chat_id=GROUP_CHAT_ID,
                    **{answer.media.value.lower(): media_id},
                    caption=capt,
                )
                telegram_link = getattr(
                    forwarded_message, answer.media.value.lower()
                ).file_id

                self.upload_db(
                    pk=user_practice_id,
                    media_type=media_type,
                    file_id=telegram_link,
                    caption=caption,
                )

                # await answer.reply_text("تکلیف با موفقیت ثبت شد.")
                await answer.reply_text(
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
                # asyncio.create_task(
                #     self.send_user_correction_notification(client, user_practice_id)
                # )
                if not media_type == db.MediaType.VIDEO_NOTE:
                    asyncio.create_task(
                        self.update_group_msg_caption(
                            forwarded_message, user_practice_id
                        )
                    )
                try:
                    await callback_query.message.delete()
                except Exception:
                    pass
                return

            # Handle text messages
            elif db.MediaType.TEXT.value in media_types and answer.text:
                self.upload_db(
                    pk=user_practice_id,
                    media_type=db.MediaType.TEXT,
                    file_id=None,
                    caption=answer.text,
                )

                # await answer.reply_text("تکلیف با موفقیت ثبت شد.")
                await answer.reply_text(
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
                # asyncio.create_task(
                #     self.send_user_correction_notification(client, user_practice_id)
                # )
                try:
                    await callback_query.message.delete()
                except Exception:
                    pass
                return

            else:
                await answer.reply_text(
                    "فقط امکان ثبت تایپ مدیاهای ذکر شده برقرار است!"
                )

        except TimeoutError:
            await callback_query.message.reply_text("مهلت زمانی آپلود تمام شد!")
        except asyncio.CancelledError:
            await callback_query.message.reply_text("آپلود کنسل شد!")

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
    def clear_correction_db(pk):
        with db.get_session() as session:
            correction = (
                session.query(db.CorrectionModel)
                .join(
                    db.UserPracticeModel,
                    db.UserPracticeModel.id == db.CorrectionModel.user_practice_id,
                )
                .filter(db.UserPracticeModel.id == pk)
                .first()
            )
            if correction:
                correction.file_link = None
                correction.caption = None
                correction.media_type = None
                session.commit()
                return True
            return False

    async def confirm(self, client, callback_query):
        match = re.search(
            rf"teacher_{self.type}_practice_user_practice_confirm_(\d+)_(\d+)",
            callback_query.data,
        )
        if match:
            user_practice_id = int(match.group(1))
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

    @staticmethod
    async def update_group_msg_caption(msg, user_practice_id):
        with db.get_session() as session:
            correction = (
                session.query(
                    db.UserPracticeModel.id,
                    db.CorrectionModel.id,
                    db.TeacherModel.name,
                    db.UserPracticeModel.practice_id,
                )
                .filter(db.UserPracticeModel.id == user_practice_id)
                .join(
                    db.CorrectionModel,
                    db.UserPracticeModel.id == db.CorrectionModel.user_practice_id,
                )
                .join(
                    db.TeacherModel, db.TeacherModel.id == db.CorrectionModel.teacher_id
                )
                .first()
            )
            if correction:
                await msg.edit_text(
                    f"practice-id: {correction.practice_id}\n"
                    f"user-practice: {user_practice_id}\n"
                    f"correction-id: {correction.id}\n"
                    f"teacher-name: {correction.name}\n"
                )


class BasePractice(BaseUserPractice):
    def __init__(self, app, type="all") -> None:
        super().__init__(app, type)

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

    @staticmethod
    def report_practice(pk):
        with db.get_session() as session:
            practice = (
                session.query(
                    db.PracticeModel.title,
                    db.PracticeModel.caption,
                    db.PracticeModel.end_date,
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
            f"◾️ ددلاین تمرین: {JalaliDateTime(practice.end_date).strftime(DATE_TIME_FMT, locale='fa')}\n"
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
                    db.CorrectionModel.user_practice_id.label("id"),
                    db.UserModel.name.label("title"),
                )
                .join(
                    db.TeacherModel, db.TeacherModel.id == db.CorrectionModel.teacher_id
                )
                .filter(db.TeacherModel.tell_id == teacher_tell_id)
                .join(
                    db.UserPracticeModel,
                    db.UserPracticeModel.id == db.CorrectionModel.user_practice_id,
                )
                .filter(db.UserPracticeModel.practice_id == pk)
                .join(
                    db.PracticeModel,
                    db.PracticeModel.id == db.UserPracticeModel.practice_id,
                )
                .join(db.UserModel, db.UserModel.id == db.UserPracticeModel.user_id)
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
                f"◾️ ددلاین تمرین: {JalaliDateTime(practice.end_date).strftime(DATE_TIME_FMT, locale='fa')}\n"
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
        self.type = type
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


class NONEPractice(BaseUserPractice):
    def __init__(self, app, type="none"):
        super().__init__(app, type)

        self.app = app
        self.type = type
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

    @staticmethod
    def user_practices(tell_id):
        with db.get_session() as session:
            query = (
                session.query(
                    db.CorrectionModel.id.label("correction_id"),
                    db.UserPracticeModel.id,
                    (db.UserModel.name + " | " + db.PracticeModel.title).label("title"),
                )
                .filter(db.CorrectionModel.caption.is_(None))
                .join(
                    db.TeacherModel, db.TeacherModel.id == db.CorrectionModel.teacher_id
                )
                .filter(db.TeacherModel.tell_id == tell_id)
                .join(
                    db.UserPracticeModel,
                    db.UserPracticeModel.id == db.CorrectionModel.user_practice_id,
                )
                .join(db.UserModel, db.UserModel.id == db.UserPracticeModel.user_id)
                .join(
                    db.PracticeModel,
                    db.PracticeModel.id == db.UserPracticeModel.practice_id,
                )
                .all()
            )
            return query

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


async def teacher_my_settings(client, message):
    with db.get_session() as session:
        teacher = (
            session.query(
                db.TeacherModel.id,
                db.TeacherModel.name,
                db.TeacherModel.tell_id,
                db.TeacherModel.phone_number,
                func.count(db.CorrectionModel.id).label("user_practice_count"),
                func.count(func.nullif(db.CorrectionModel.caption, None)).label(
                    "corrected_user_practice_count"
                ),
            )
            .outerjoin(
                db.CorrectionModel,
                db.CorrectionModel.teacher_id == db.TeacherModel.id,
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
