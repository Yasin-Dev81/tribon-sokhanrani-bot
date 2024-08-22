from pyrogram import filters
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)
from pyrogram.enums import MessageMediaType
from pyrogram.errors.exceptions.bad_request_400 import UserIsBlocked
from sqlalchemy import and_, func, case
from persiantools.jdatetime import JalaliDateTime
import datetime
import asyncio
import pyrostep


from .pagination import get_paginated_keyboard
from config import (
    ADMINS_LIST_ID,
    GROUP_CHAT_ID,
    TIME_ZONE,
    TIME_OUT,
    WARN_MSG,
    DATE_TIME_FMT,
)
import db


def is_user(_, __, update):
    with db.get_session() as session:
        return (
            session.query(db.UserModel).filter_by(tell_id=update.from_user.id).first()
            is not None
        )


class BasePractice:
    def __init__(self, app, type="active"):
        self.app = app
        self.type = type
        self.base_register_handlers()

    def base_register_handlers(self):
        self.app.on_callback_query(
            filters.regex(rf"user_{self.type}_practice_select_(\d+)")
            & filters.create(is_user)
        )(self.select)
        self.app.on_callback_query(
            filters.regex(rf"user_{self.type}_practice_answer_(\d+)")
            & filters.create(is_user)
        )(self.answer)
        self.app.on_callback_query(
            filters.regex(rf"user_{self.type}_practice_reanswer_(\d+)")
            & filters.create(is_user)
        )(self.reanswer)

    @staticmethod
    def report_practice(pk):
        with db.get_session() as session:
            practice = (
                session.query(
                    db.PracticeModel.title,
                    db.PracticeModel.caption,
                    and_(
                        db.PracticeModel.start_date <= datetime.datetime.now(TIME_ZONE),
                        db.PracticeModel.end_date >= datetime.datetime.now(TIME_ZONE),
                    ).label("status"),
                    db.PracticeModel.end_date.label("dd_line"),
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
                    db.UserPracticeModel.datetime_created,
                    db.UserPracticeModel.datetime_modified,
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
                .filter(db.UserPracticeModel.practice_id == practice_id)
                .filter(db.UserModel.tell_id == tell_id)
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
                    db.UserPracticeModel.datetime_created,
                    db.UserPracticeModel.datetime_modified,
                )
            ).first()
            return query  # .first()

    async def select(self, client, callback_query):
        practice_id = int(callback_query.data.split("_")[-1])
        await callback_query.answer(f"تمرین {practice_id}")

        try:
            await callback_query.message.delete()
        except Exception:
            pass

        user_practice = self.report_user_practice(
            practice_id=practice_id, tell_id=callback_query.from_user.id
        )

        markup = [
            [
                InlineKeyboardButton(
                    "🔙 بازگشت", callback_data="user_active_practice_paginate_list_0"
                ),
                InlineKeyboardButton("exit!", callback_data="back_home"),
            ]
        ]

        if user_practice:
            correction = "در انتظار تحلیل سخنرانی"

            if user_practice.status:
                markup.insert(
                    0,
                    [
                        InlineKeyboardButton(
                            "ویرایش تمرین",
                            callback_data=f"user_active_practice_reanswer_{user_practice.id}",
                        )
                    ],
                )

            if user_practice.teacher_caption:
                correction = f"تحلیل سخنرانی شده.\n◾️ کپشن منتور: {user_practice.teacher_caption}"

            update_user_practice = ""
            if not user_practice.datetime_created==user_practice.datetime_modified:
                update_user_practice = '◾️ تاریخ ویرایش: %s \n'%JalaliDateTime(user_practice.datetime_modified).strftime(DATE_TIME_FMT, locale='fa')

            caption = (
                f"📌 عنوان: {user_practice.title}\n🔖 متن سوال: {user_practice.caption}\n"
                f"◾️ ددلاین تمرین: {JalaliDateTime(user_practice.dd_line).strftime(DATE_TIME_FMT, locale='fa')}\n"
                "➖➖➖➖➖➖➖➖➖\n"
                f"◾️ کپشن کاربر: {user_practice.user_caption or 'بدون کپشن!'}\n"
                f"◾️ تاریخ آپلود: {JalaliDateTime(user_practice.datetime_created).strftime(DATE_TIME_FMT, locale='fa')} \n"
                f"{update_user_practice}"
                "➖➖➖➖➖➖➖➖➖\n"
                "<blockquote expandable>\n"
                f"📊 وضعیت تمرین: {correction}"
                "</blockquote>"
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
            practice = self.report_practice(pk=practice_id)
            markup.insert(
                0,
                [
                    InlineKeyboardButton(
                        "آپلود تمرین",
                        callback_data=f"user_active_practice_answer_{practice_id}",
                    )
                ],
            )

            await callback_query.message.reply_text(
                f"📌 عنوان: {practice.title}\n🔖 متن سوال: {practice.caption}\n"
                f"◾️ ددلاین تمرین: {JalaliDateTime(practice.dd_line).strftime(DATE_TIME_FMT, locale='fa')}\n"
                "➖➖➖➖➖➖➖➖➖\n"
                "📊 وضعیت تمرین: تحویل داده نشده!",
                reply_markup=InlineKeyboardMarkup(markup),
            )

    @staticmethod
    def media_acsess(practice_id):
        with db.get_session() as session:
            return (
                session.query(db.MediaAcsessModel)
                .filter_by(practice_id=practice_id)
                .filter(db.MediaAcsessModel.user_level == db.UserLevel.USER)
                .all()
            )

    async def answer(self, client, callback_query):
        practice_id = int(callback_query.data.split("_")[-1])

        media_acsess = self.media_acsess(practice_id)
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
            f"📌 تایپ‌های قابل قبول:\n✔️ {str_media_types}\n{WARN_MSG}",
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

        while True:
            try:
                answer = await pyrostep.wait_for(
                    callback_query.from_user.id, timeout=TIME_OUT * 60
                )

                if not self.practice_status(practice_id):
                    await answer.reply_text(
                        "دیگر امکان آپلود تمرین نمی‌باشد!\n"
                        "<spoiler>لطفا قوانین را مطالعه فرمایید.</spoiler>"
                    )
                    break

                # Handle media messages
                if answer.media and answer.media in media_methods:
                    send_method, media_type = media_methods[answer.media]

                    if media_type.value not in media_types:
                        await answer.reply_text("این تایپ مدیا مجاز نیست!")
                        continue

                    media_id = getattr(answer, answer.media.value.lower()).file_id
                    caption = answer.caption or None
                    file_size = getattr(answer, answer.media.value.lower()).file_size

                    # Check file size limit
                    if (file_size / 1024) > 50_000:
                        await answer.reply_text(
                            "فایل ارسالی باید کمتر از <b>50 مگابایت</b> باشد!"
                        )
                        continue

                    if not self.practice_status(practice_id):
                        await answer.reply_to_message.delete()
                        await answer.reply_text(
                            "دیگر امکان آپلود تمرین نمی‌باشد!\n"
                            "<spoiler>لطفا قوانین را مطالعه فرمایید.</spoiler>"
                        )
                        break

                    capt = (
                        f"message id: <i>{answer.id}</i>\n---\n"
                        f"from user @{answer.from_user.username}\n"
                        f"user caption:\n{caption}\n"
                        f"practice_id: {practice_id}"
                    )

                    # Forward the media to the channel
                    if media_type == db.MediaType.VIDEO_NOTE:
                        forwarded_message = await send_method(
                            chat_id=GROUP_CHAT_ID,
                            **{answer.media.value.lower(): media_id},
                        )
                    else:
                        forwarded_message = await send_method(
                            chat_id=GROUP_CHAT_ID,
                            **{answer.media.value.lower(): media_id},
                            caption=capt,
                        )
                    telegram_link = getattr(
                        forwarded_message, answer.media.value.lower()
                    ).file_id

                    with db.get_session() as session:
                        user_id = (
                            session.query(db.UserModel)
                            .filter_by(tell_id=answer.from_user.id)
                            .first()
                            .id
                        )

                        # Store the Telegram link in the database
                        user_practice_id = self.upload_db(
                            user_id=user_id,
                            practice_id=practice_id,
                            media_type=media_type,
                            file_link=telegram_link,
                            user_caption=caption,
                        )

                    await answer.reply_text("تکلیف با موفقیت ثبت شد.")
                    asyncio.create_task(
                        self.send_admin_upload_notification(client, user_practice_id)
                    )
                    try:
                        await callback_query.message.delete()
                    except Exception:
                        pass
                    break

                # Handle text messages
                elif db.MediaType.TEXT.value in media_types and answer.text:
                    caption = answer.text

                    with db.get_session() as session:
                        user_id = (
                            session.query(db.UserModel)
                            .filter_by(tell_id=answer.from_user.id)
                            .first()
                            .id
                        )

                        user_practice_id = self.upload_db(
                            user_id=user_id,
                            practice_id=practice_id,
                            media_type=db.MediaType.TEXT,
                            file_link=None,
                            user_caption=caption,
                        )

                    await answer.reply_text("تکلیف با موفقیت ثبت شد.")
                    asyncio.create_task(
                        self.send_admin_upload_notification(client, user_practice_id)
                    )
                    try:
                        await callback_query.message.delete()
                    except Exception:
                        pass
                    break

                else:
                    await answer.reply_text(
                        "فقط امکان ثبت تایپ مدیاهای ذکر شده برقرار است!"
                    )

            except TimeoutError:
                await callback_query.message.reply_text("مهلت زمانی آپلود تمام شد!")
                break
            except asyncio.CancelledError:
                await callback_query.message.reply_text("آپلود کنسل شد!")
                break

    @staticmethod
    async def send_admin_upload_notification(client, user_practice_id):
        for i in ADMINS_LIST_ID:
            try:
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
            except UserIsBlocked:
                print("bro bache poroo, bro bache poroo!")

    @staticmethod
    def upload_db(user_id, media_type, file_link, practice_id, user_caption=None):
        with db.get_session() as session:
            new_user_practice = db.UserPracticeModel(
                user_id=user_id,
                file_link=file_link,
                media_type=media_type,
                practice_id=practice_id,
                caption=user_caption,
            )
            session.add(new_user_practice)
            session.commit()
            return new_user_practice.id

    @staticmethod
    def practice_status(practice_id):
        with db.get_session() as session:
            query = session.query(
                and_(
                    db.PracticeModel.start_date <= datetime.datetime.now(TIME_ZONE),
                    db.PracticeModel.end_date >= datetime.datetime.now(TIME_ZONE),
                ).label("status"),
            ).filter_by(id=practice_id)
            return query.first().status

    @staticmethod
    def user_media_acsess(user_practice_id):
        with db.get_session() as session:
            return (
                session.query(db.UserPracticeModel.id, db.MediaAcsessModel.media_type)
                .join(
                    db.MediaAcsessModel,
                    db.MediaAcsessModel.practice_id == db.UserPracticeModel.practice_id,
                )
                .filter(
                    and_(
                        db.UserPracticeModel.id == user_practice_id,
                        db.MediaAcsessModel.user_level == db.UserLevel.USER,
                    )
                )
                .all()
            )

    async def reanswer(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])

        media_acsess = self.user_media_acsess(user_practice_id)

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
            f"📌 تایپ‌های قابل قبول:\n✔️ {str_media_types}\n{WARN_MSG}",
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

        while True:
            try:
                answer = await pyrostep.wait_for(
                    callback_query.from_user.id, timeout=TIME_OUT * 60
                )

                if not self.user_practice_status(user_practice_id):
                    await answer.reply_text(
                        "دیگر امکان آپلود تمرین نمی‌باشد!\n"
                        "<spoiler>لطفا قوانین را مطالعه فرمایید.</spoiler>"
                    )
                    break

                # Handle media messages
                if answer.media and answer.media in media_methods:
                    send_method, media_type = media_methods[answer.media]

                    if media_type.value not in media_types:
                        await answer.reply_text("این تایپ مدیا مجاز نیست!")
                        continue

                    media_id = getattr(answer, answer.media.value.lower()).file_id
                    caption = answer.caption or None
                    file_size = getattr(answer, answer.media.value.lower()).file_size

                    # Check file size limit
                    if (file_size / 1024) > 50_000:
                        await answer.reply_text(
                            "فایل ارسالی باید کمتر از <b>50 مگابایت</b> باشد!"
                        )
                        continue

                    if not self.user_practice_status(user_practice_id):
                        await answer.reply_to_message.delete()
                        await answer.reply_text(
                            "دیگر امکان آپلود تمرین نمی‌باشد!\n"
                            "<spoiler>لطفا قوانین را مطالعه فرمایید.</spoiler>"
                        )
                        break

                    capt = (
                        f"message id: <i>{answer.id}</i>\n---\n"
                        f"from user @{answer.from_user.username}\n"
                        f"user caption:\n{caption}\n"
                        f"user_practice_id: {user_practice_id}"
                    )

                    # Forward the media to the channel
                    if media_type == db.MediaType.VIDEO_NOTE:
                        forwarded_message = await send_method(
                            chat_id=GROUP_CHAT_ID,
                            **{answer.media.value.lower(): media_id},
                        )
                    else:
                        forwarded_message = await send_method(
                            chat_id=GROUP_CHAT_ID,
                            **{answer.media.value.lower(): media_id},
                            caption=capt,
                        )
                    telegram_link = getattr(
                        forwarded_message, answer.media.value.lower()
                    ).file_id

                    self.update_db(
                        pk=user_practice_id,
                        file_link=telegram_link,
                        media_type=media_type,
                        user_caption=caption,
                    )

                    await answer.reply_text("تکلیف با موفقیت ثبت شد.")
                    try:
                        await callback_query.message.delete()
                    except Exception:
                        pass
                    break

                # Handle text messages
                elif db.MediaType.TEXT.value in media_types and answer.text:
                    self.update_db(
                        pk=user_practice_id,
                        file_link=None,
                        media_type=db.MediaType.TEXT,
                        user_caption=answer.text,
                    )

                    await answer.reply_text("تکلیف با موفقیت ثبت شد.")
                    try:
                        await callback_query.message.delete()
                    except Exception:
                        pass
                    break

                else:
                    await answer.reply_text(
                        "فقط امکان ثبت تایپ مدیاهای ذکر شده برقرار است!"
                    )

            except TimeoutError:
                await callback_query.message.reply_text("مهلت زمانی آپلود تمام شد!")
                break
            except asyncio.CancelledError:
                await callback_query.message.reply_text("آپلود کنسل شد!")
                break

    @staticmethod
    def update_db(pk, file_link, media_type, user_caption=None):
        with db.get_session() as session:
            user_practice = session.query(db.UserPracticeModel).get(pk)
            if user_practice:
                user_practice.file_link = file_link
                user_practice.media_type = media_type
                if user_caption is not None:
                    user_practice.caption = user_caption
                session.commit()
            return pk

    @staticmethod
    def user_practice_status(user_practice_id):
        with db.get_session() as session:
            query = (
                session.query(
                    db.UserPracticeModel.id,
                    case(
                        # Provide the conditions as positional arguments
                        (func.count(db.CorrectionModel.id) > 0, False),
                        else_=and_(
                            db.PracticeModel.start_date
                            <= datetime.datetime.now(TIME_ZONE),
                            db.PracticeModel.end_date
                            >= datetime.datetime.now(TIME_ZONE),
                        ),
                    ).label("status"),
                )
                .join(
                    db.PracticeModel,
                    db.PracticeModel.id == db.UserPracticeModel.practice_id,
                )
                .outerjoin(
                    db.CorrectionModel,
                    db.CorrectionModel.user_practice_id == db.UserPracticeModel.id,
                )
                .filter(db.UserPracticeModel.id == user_practice_id)
                .group_by(
                    db.UserPracticeModel.id,
                    db.PracticeModel.start_date,
                    db.PracticeModel.end_date,
                )
            ).first()
            return query.status


class ActivePractice(BasePractice):
    def __init__(self, app, type="active"):
        super().__init__(app, type)

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

    def practices(self, user_tell_id):
        current_time = datetime.datetime.now(TIME_ZONE)
        with db.get_session() as session:
            practices = (
                session.query(db.PracticeModel.id, db.PracticeModel.title)
                .join(
                    db.UserModel,
                    db.UserModel.user_type_id == db.PracticeModel.user_type_id,
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


class AnsweredPractice(BasePractice):
    def __init__(self, app, type="answered"):
        super().__init__(app, type)

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

    def practices(self, user_tell_id):
        with db.get_session() as session:
            query = (
                session.query(
                    db.UserPracticeModel.id.label("user_practice_id"),
                    db.PracticeModel.id,
                    db.PracticeModel.title,
                )
                .join(
                    db.PracticeModel,
                    db.PracticeModel.id == db.UserPracticeModel.practice_id,
                )
                .join(db.UserModel, db.UserModel.id == db.UserPracticeModel.user_id)
                .filter(db.UserModel.tell_id == user_tell_id)
            )

            return query.all()

    async def list(self, client, message):
        practices = self.practices(message.from_user.id)
        if not practices:
            await message.reply_text("هیچ تمرین تحویل داده شده‌ای موجود نیست!")
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


class CorrectedPractice(BasePractice):
    def __init__(self, app, type="corrected"):
        super().__init__(app, type)

        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(filters.regex("تصحیح شده‌ها") & filters.create(is_user))(
            self.list
        )
        self.app.on_callback_query(
            filters.regex(r"user_corrected_practice_paginate_list_(\d+)")
            & filters.create(is_user)
        )(self.paginate_list)

    def practices(self, user_tell_id):
        with db.get_session() as session:
            query = (
                session.query(
                    db.CorrectionModel.id.label("correction_id"),
                    db.PracticeModel.id,
                    db.PracticeModel.title,
                )
                .join(
                    db.UserPracticeModel,
                    db.UserPracticeModel.id == db.CorrectionModel.user_practice_id,
                )
                .join(
                    db.PracticeModel,
                    db.PracticeModel.id == db.UserPracticeModel.practice_id,
                )
                .filter(db.UserModel.tell_id == user_tell_id)
            ).all()

            return query

    async def list(self, client, message):
        practices = self.practices(message.from_user.id)
        if not practices:
            await message.reply_text("هیچ تمرین تصحیح شده‌ای موجود نیست!")
            return

        await message.reply_text(
            "تمارین فعال:",
            reply_markup=get_paginated_keyboard(
                practices,
                0,
                "user_corrected_practice_paginate_list",
                "user_corrected_practice_select",
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
                    "user_corrected_practice_paginate_list",
                    "user_corrected_practice_select",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                practices,
                page,
                "user_corrected_practice_paginate_list",
                "user_corrected_practice_select",
            )
        )


async def user_settings(client, message):
    with db.get_session() as session:
        user = (
            session.query(
                db.UserModel.id,
                db.UserModel.name,
                db.UserModel.tell_id,
                db.UserModel.phone_number,
                func.count(db.UserPracticeModel.id).label("user_practice_count"),
                func.count(func.nullif(db.CorrectionModel.id, None)).label(
                    "corrected_user_practice_count"
                ),
            )
            .outerjoin(
                db.UserPracticeModel, db.UserModel.id == db.UserPracticeModel.user_id
            )
            .filter(db.UserModel.tell_id == message.from_user.id)
            .outerjoin(
                db.CorrectionModel,
                db.CorrectionModel.user_practice_id == db.UserPracticeModel.id,
            )
            .group_by(db.UserModel.id)
            .first()
        )
        await message.reply(
            "ℹ️ user-level: <b>user</b>\n"
            f"🆔 user-id: <i>{user.id}</i>\n"
            f"👤 user-name: <code>{user.name}</code>\n"
            f"◾️ user-tell-id: <i>{user.tell_id}</i>\n"
            f"📞 user-phone-number: {user.phone_number}\n"
            "➖➖➖➖➖➖➖➖➖\n"
            f"▫️ تعداد تکلیف تحویل داده شده: {user.user_practice_count}\n"
            f"▫️ تعداد تکلیف تصحیح شده: {user.corrected_user_practice_count}"
        )


def register_user_handlers(app):
    app.on_message(filters.regex("اطلاعات من") & filters.create(is_user))(user_settings)

    ActivePractice(app)
    AnsweredPractice(app)
    CorrectedPractice(app)
