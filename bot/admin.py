from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from sqlalchemy import func, and_, case, select
from persiantools.jdatetime import JalaliDateTime
import asyncio
import pyrostep
import datetime
import re

from config import ADMINS_LIST_ID, TIME_ZONE, TIME_OUT, DATE_TIME_FMT
from .home import send_home_message_admin
from .pagination import (
    get_paginated_keyboard,
    users_paginated_keyboard,
    teachers_paginated_keyboard,
    user_practice_paginated_keyboard,
    select_teacher_paginated_keyboard,
)
import db


class Practice:
    user_media_acsess_list = [
        {"media_type": db.MediaType.TEXT, "user_level": db.UserLevel.USER},
        {"media_type": db.MediaType.PHOTO, "user_level": db.UserLevel.USER},
        {"media_type": db.MediaType.VIDEO, "user_level": db.UserLevel.USER},
        {"media_type": db.MediaType.VOICE, "user_level": db.UserLevel.USER},
        {"media_type": db.MediaType.DOCUMENT, "user_level": db.UserLevel.USER},
        {"media_type": db.MediaType.AUDIO, "user_level": db.UserLevel.USER},
        {"media_type": db.MediaType.VIDEO_NOTE, "user_level": db.UserLevel.USER},
    ]
    teacher_media_acsess_list = [
        {"media_type": db.MediaType.TEXT, "user_level": db.UserLevel.TEACHER},
        {"media_type": db.MediaType.PHOTO, "user_level": db.UserLevel.TEACHER},
        {"media_type": db.MediaType.VIDEO, "user_level": db.UserLevel.TEACHER},
        {"media_type": db.MediaType.VOICE, "user_level": db.UserLevel.TEACHER},
        {"media_type": db.MediaType.DOCUMENT, "user_level": db.UserLevel.TEACHER},
        {"media_type": db.MediaType.AUDIO, "user_level": db.UserLevel.TEACHER},
        {"media_type": db.MediaType.VIDEO_NOTE, "user_level": db.UserLevel.TEACHER},
    ]

    def __init__(self, app):
        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(
            filters.regex("تعریف تمرین جدید") & filters.user(ADMINS_LIST_ID)
        )(self.add)
        self.app.on_callback_query(
            filters.regex(r"admin_practice_set_type_(\d+)_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.set_type)
        self.app.on_callback_query(
            filters.regex(r"user_media_acsess_managment_(\d+)_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.user_media_acsess_managment)
        self.app.on_callback_query(
            filters.regex(r"teacher_media_acsess_managment_(\d+)_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.teacher_media_acsess_managment)
        self.app.on_callback_query(
            filters.regex(r"send_notif_(\d+)") & filters.user(ADMINS_LIST_ID)
        )(self.send_notif)
        self.app.on_callback_query(
            filters.regex(r"practice_send_teachers_notif_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.send_teachers_notif)

    # تعریف تمرین جدید
    async def add(self, client, message):
        await message.reply_text(
            "عنوان تمرین جدید را وارد کنید:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Cancel", callback_data="back_home")]]
            ),
        )

        title_msg = await pyrostep.wait_for(message.from_user.id, timeout=TIME_OUT * 60)

        await message.reply_text(
            f"عنوان سوال: {title_msg.text}\n"
            "➖➖➖➖➖➖➖➖➖\n"
            "متن تمرین جدید را وارد کنید:",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Cancel", callback_data="back_home")]]
            ),
        )

        caption_msg = await pyrostep.wait_for(
            message.from_user.id, timeout=TIME_OUT * 60
        )

        await message.reply_text(
            f"عنوان سوال: {title_msg.text}\n"
            f"متن سوال: {caption_msg.text}\n"
            "➖➖➖➖➖➖➖➖➖\n"
            "تاریخ شروع و پایان تمرین را بصورت جلالی و با فرمت زیر وارد کنید:\n"
            "تاریخ شروع - تاریخ پایان\n"
            "اگه فقط یک تاریخ وارد شود امروز بعنوان تاریخ شروع درنظر گرفته میشود!"
            "\n\n<b>فرمت تاریخ: روز/ماه/سال</b>"
            "\n\nexample:\n27/5/1403",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Cancel", callback_data="back_home")]]
            ),
        )

        date_msg = await pyrostep.wait_for(message.from_user.id, timeout=TIME_OUT * 60)
        all_date = date_msg.text.split("-")
        if len(all_date) == 2:
            new_practice_id = self.add_db(
                title=title_msg.text,
                caption=caption_msg.text,
                start_date=JalaliDateTime.strptime(all_date[0], "%d/%m/%Y")
                .to_gregorian()
                .replace(hour=23, minute=59, second=0),
                end_date=JalaliDateTime.strptime(all_date[1], "%d/%m/%Y")
                .to_gregorian()
                .replace(hour=23, minute=59, second=0),
            )
        else:
            new_practice_id = self.add_db(
                title=title_msg.text,
                caption=caption_msg.text,
                end_date=JalaliDateTime.strptime(all_date[0], "%d/%m/%Y")
                .to_gregorian()
                .replace(hour=23, minute=59, second=0),
            )

        with db.get_session() as session:
            await message.reply_text(
                f"تمرین با موفقیت ثبت شد.\nآی‌دی تمرین: {new_practice_id}\n\n"
                "لطفا نوع یوزر را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                i.name,
                                callback_data=f"admin_practice_set_type_{i.id}_{new_practice_id}",
                            )
                            for i in session.query(db.UserTypeModel).all()
                        ],
                        [InlineKeyboardButton("exit!", callback_data="back_home")],
                    ]
                ),
            )

    def add_db(
        self, title, caption, end_date, start_date=datetime.datetime.now(TIME_ZONE)
    ):
        # if isinstance(start_date, str):
        #     start_date = datetime.datetime.strptime(start_date, "%d/%m/%Y")
        # end_date = datetime.datetime.strptime(end_date, "%d/%m/%Y")

        with db.get_session() as session:
            new_practice = db.PracticeModel(
                title=title, caption=caption, start_date=start_date, end_date=end_date
            )
            session.add(new_practice)
            session.commit()
            return new_practice.id

    @staticmethod
    def users(practice_id):
        if not isinstance(practice_id, int):
            practice_id = int(practice_id)
        with db.get_session() as session:
            # return (
            #     session.query(db.UserModel)
            #     .filter(db.UserModel.chat_id.is_not(None))
            #     .filter(db.UserModel.user_type_id == user_type_id)
            #     .all()
            # )
            return (
                session.query(db.UserModel)
                .join(
                    db.PracticeModel,
                    db.PracticeModel.user_type_id == db.UserModel.user_type_id,
                )
                .filter(db.PracticeModel.id == practice_id)
                .all()
            )

    @property
    def teachers(self):
        with db.get_session() as session:
            return (
                session.query(db.TeacherModel)
                .filter(db.TeacherModel.chat_id.is_not(None))
                .all()
            )

    async def send_alls_notification(self, client, new_practice_id, data):
        for admin in ADMINS_LIST_ID:
            try:
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
            except Exception:
                pass
        for user in self.teachers:
            try:
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
            except Exception:
                pass
        for user in self.users(new_practice_id):
            try:
                await client.send_message(
                    chat_id=user.chat_id,
                    text=data,
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    "مشاهده",
                                    callback_data=f"user_active_practice_select_{new_practice_id}",
                                )
                            ]
                        ]
                    ),
                )
            except Exception:
                pass

    @staticmethod
    def update_user_type(pk, user_type_id):
        if not isinstance(user_type_id, int):
            user_type_id = int(user_type_id)

        with db.get_session() as session:
            practice = session.query(db.PracticeModel).get(pk)
            if practice:
                practice.user_type_id = user_type_id
                session.commit()
                return True
        return False

    async def set_type(self, client, callback_query):
        match = re.search(r"admin_practice_set_type_(\d+)_(\d+)", callback_query.data)
        if match:
            user_type_id = match.group(1)
            practice_id = match.group(2)
            # print(practice_id, user_type, db.UserType[user_type].value)
            if self.update_user_type(practice_id, user_type_id):
                await callback_query.answer("نوع یوزر تعیین شد.")
                # self.set_all_media_acsess(practice_id)
                media_acsess_list = list(enumerate(self.user_media_acsess_list))
                await callback_query.message.reply_text(
                    "دسترسی مدیا تایپ‌های این تمرین:",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [self.create_button("یوزرها", callback_data="namayeshi")],
                            *[
                                [
                                    self.create_button(
                                        f"🔴 {i[1]['media_type'].value}",
                                        callback_data=f"user_media_acsess_managment_{practice_id}_{i[0]}",
                                    )
                                    for i in group
                                ]
                                for group in [
                                    media_acsess_list[:4],
                                    media_acsess_list[4:7],
                                ]
                            ],
                            [
                                self.create_button(
                                    "Next",
                                    callback_data=f"teacher_media_acsess_managment_{practice_id}_7",
                                )
                            ],
                        ]
                    ),
                )
                await callback_query.message.delete()
            else:
                await callback_query.message.reply_text("error!")

    @staticmethod
    def create_button(text, callback_data="back_home"):
        return InlineKeyboardButton(text, callback_data=callback_data)

    @staticmethod
    def set_all_media_acsess(practice_id):
        with db.get_session() as session:
            media_access_entries = []

            for media_type in db.MediaType:
                media_access_entries.append(
                    db.MediaAcsessModel(
                        practice_id=practice_id,
                        media_type=media_type,
                        user_level=db.UserLevel.USER,
                    )
                )
                media_access_entries.append(
                    db.MediaAcsessModel(
                        practice_id=practice_id,
                        media_type=media_type,
                        user_level=db.UserLevel.TEACHER,
                    )
                )

            session.bulk_save_objects(media_access_entries)
            session.commit()

    async def user_media_acsess_managment(self, client, callback_query):
        match = re.search(
            r"user_media_acsess_managment_(\d+)_(\d+)", callback_query.data
        )

        if not match:
            await callback_query.message.delete()
            return

        practice_id = int(match.group(1))
        row_id = int(match.group(2))

        with db.get_session() as session:
            if row_id == 7:
                pass
            else:
                kwargs = self.user_media_acsess_list[row_id]
                kwargs["practice_id"] = practice_id
                ma = session.query(db.MediaAcsessModel).filter_by(**kwargs).first()
                if ma:
                    session.delete(ma)
                    session.commit()
                    await callback_query.answer(
                        "removed %s - %s"
                        % (kwargs["media_type"].value, kwargs["user_level"].value)
                    )
                else:
                    ma = db.MediaAcsessModel(**kwargs)
                    session.add(ma)
                    session.commit()
                    await callback_query.answer(
                        "added %s - %s"
                        % (kwargs["media_type"].value, kwargs["user_level"].value)
                    )

            all_data = (
                session.query(db.MediaAcsessModel)
                .filter_by(practice_id=practice_id, user_level=db.UserLevel.USER)
                .all()
            )
            all_data_list = [
                "%s_%s" % (i.media_type.value, i.user_level.value) for i in all_data
            ]

            media_acsess_list = list(enumerate(self.user_media_acsess_list))
            await callback_query.message.edit_reply_markup(
                reply_markup=InlineKeyboardMarkup(
                    [
                        [self.create_button("یوزرها", callback_data="namayeshi")],
                        *[
                            [
                                self.create_button(
                                    f"{'🟢' if ('%s_%s'%(i[1]['media_type'].value, i[1]['user_level'].value)) in all_data_list else '🔴'} {i[1]['media_type'].value}",
                                    callback_data=f"user_media_acsess_managment_{practice_id}_{i[0]}",
                                )
                                for i in group
                            ]
                            for group in [
                                media_acsess_list[:4],
                                media_acsess_list[4:7],
                            ]
                        ],
                        [
                            self.create_button(
                                "Done",
                                callback_data=f"teacher_media_acsess_managment_{practice_id}_7",
                            )
                        ],
                    ]
                ),
            )

    async def teacher_media_acsess_managment(self, client, callback_query):
        match = re.search(
            r"teacher_media_acsess_managment_(\d+)_(\d+)", callback_query.data
        )

        if not match:
            await callback_query.message.delete()
            return

        practice_id = int(match.group(1))
        row_id = int(match.group(2))

        with db.get_session() as session:
            if row_id == 7:
                pass
            else:
                kwargs = self.teacher_media_acsess_list[row_id]
                kwargs["practice_id"] = practice_id
                ma = session.query(db.MediaAcsessModel).filter_by(**kwargs).first()
                if ma:
                    session.delete(ma)
                    session.commit()
                    await callback_query.answer(
                        "removed %s - %s"
                        % (kwargs["media_type"].value, kwargs["user_level"].value)
                    )
                else:
                    ma = db.MediaAcsessModel(**kwargs)
                    session.add(ma)
                    session.commit()
                    await callback_query.answer(
                        "added %s - %s"
                        % (kwargs["media_type"].value, kwargs["user_level"].value)
                    )

            all_data = (
                session.query(db.MediaAcsessModel)
                .filter_by(practice_id=practice_id, user_level=db.UserLevel.TEACHER)
                .all()
            )
            all_data_list = [
                "%s_%s" % (i.media_type.value, i.user_level.value) for i in all_data
            ]

            media_acsess_list = list(enumerate(self.teacher_media_acsess_list))
            await callback_query.message.edit_reply_markup(
                reply_markup=InlineKeyboardMarkup(
                    [
                        [self.create_button("منتورها", callback_data="namayeshi")],
                        *[
                            [
                                self.create_button(
                                    f"{'🟢' if ('%s_%s'%(i[1]['media_type'].value, i[1]['user_level'].value)) in all_data_list else '🔴'} {i[1]['media_type'].value}",
                                    callback_data=f"teacher_media_acsess_managment_{practice_id}_{i[0]}",
                                )
                                for i in group
                            ]
                            for group in [
                                media_acsess_list[:4],
                                media_acsess_list[4:7],
                            ]
                        ],
                        [
                            self.create_button(
                                "Perivios",
                                callback_data=f"user_media_acsess_managment_{practice_id}_7",
                            ),
                            self.create_button(
                                "Done", callback_data=f"send_notif_{practice_id}"
                            ),
                        ],
                    ]
                ),
            )

    async def send_notif(self, client, callback_query):
        practice_id = int(callback_query.data.split("_")[-1])
        await callback_query.message.delete()
        asyncio.create_task(
            self.send_alls_notification(client, practice_id, "تمرین جدید بارگذاری شد!")
        )
        await callback_query.answer("تمرین با موفقیت اضافه شد.", show_alert=True)

    @staticmethod
    async def teachers_not_corrected(client, practic_id, data):
        with db.get_session() as session:
            subquery = select(
                (
                    session.query(db.CorrectionModel.teacher_id)
                    .join(
                        db.UserPracticeModel,
                        db.UserPracticeModel.id == db.CorrectionModel.user_practice_id,
                    )
                    .filter(db.UserPracticeModel.practice_id == practic_id)
                ).subquery()
            )

            teachers = (
                session.query(db.TeacherModel)
                .filter(db.TeacherModel.id.notin_(subquery))
                .all()
            )

            for teacher in teachers:
                try:
                    await client.send_message(chat_id=teacher.chat_id, text=data)
                except Exception:
                    pass

    async def send_teachers_notif(self, client, callback_query):
        practic_id = int(callback_query.data.split("_")[-1])
        await callback_query.answer("لطفا پیام خود را ارسال کنید", show_alert=True)
        await callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Cancel", callback_data="back_home")],
                ]
            )
        )

        try:
            answer = await pyrostep.wait_for(
                callback_query.from_user.id, timeout=TIME_OUT * 60
            )

            msg = "📢  اطلاع رسانی \n" + answer.text
            asyncio.create_task(self.teachers_not_corrected(client, practic_id, msg))
            await callback_query.message.reply_text("پیام در صف ارسال قرار گرفت")
        except TimeoutError:
            await callback_query.message.reply_text("مهلت زمانی پاسخ تمام شد!")
        except asyncio.CancelledError:
            await callback_query.message.reply_text("کنسل شد!")
        except Exception:
            await callback_query.message.reply_text("error!")


class UserPracticeUtils:
    def __init__(self, app) -> None:
        self.app = app

        self.register_handlers()

    def register_handlers(self):
        self.app.on_callback_query(
            filters.regex(r"admin_utils_user_practice_confirm_rm_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.confirm_rm_user_practice)
        self.app.on_callback_query(
            filters.regex(r"admin_utils_user_practice_done_rm_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.rm_user_practice)
        self.app.on_callback_query(
            filters.regex(r"admin_utils_correction_confirm_rm_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.confirm_rm_correction)
        self.app.on_callback_query(
            filters.regex(r"admin_utils_correction_done_rm_(\d+)_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.rm_correction)

    # rm user-practice
    async def confirm_rm_user_practice(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])
        await callback_query.message.delete()

        await callback_query.message.reply_text(
            "مطمئنی مرد؟",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "بله",
                            callback_data=f"admin_utils_user_practice_done_rm_{user_practice_id}",
                        ),
                        InlineKeyboardButton(
                            "نه!",
                            callback_data="back_home",
                        ),
                    ]
                ]
            ),
        )

    @staticmethod
    def delete_user_practice(pk):
        with db.get_session() as session:
            user_practice = session.query(db.UserPracticeModel).get(pk)
            if user_practice:
                session.delete(user_practice)
                session.commit()
                return True
        return False

    async def rm_user_practice(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])

        if self.delete_user_practice(user_practice_id):
            await callback_query.message.reply_text("تکلیف با موفقیت حذف شد.")

            await callback_query.message.delete()

    # rm correction
    async def confirm_rm_correction(self, client, callback_query):
        user_practice_id = int(callback_query.data.split("_")[-1])
        await callback_query.message.delete()

        with db.get_session() as session:
            correction_id = (
                session.query(db.CorrectionModel)
                .filter_by(user_practice_id=user_practice_id)
                .first()
                .id
            )

            await callback_query.message.reply_text(
                "مطمئنی مرد؟",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                "بله، حذف تحلیل و تخصیص",
                                callback_data=f"admin_utils_correction_done_rm_{correction_id}_1",
                            ),
                        ],
                        [
                            InlineKeyboardButton(
                                "بله، فقط حذف تحلیل",
                                callback_data=f"admin_utils_correction_done_rm_{correction_id}_0",
                            ),
                        ],
                        [
                            InlineKeyboardButton(
                                "نه!",
                                callback_data="back_home",
                            ),
                        ],
                    ]
                ),
            )

    @staticmethod
    def clear_correction_db(pk):
        with db.get_session() as session:
            correction = session.query(db.CorrectionModel).get(pk)
            if correction:
                correction.caption = None
                correction.file_link = None
                correction.media_type = None
                session.commit()
                return True
            return False

    @staticmethod
    def rm_correction_db(pk):
        with db.get_session() as session:
            correction = session.query(db.CorrectionModel).get(pk)
            if correction:
                session.delete(correction)
                session.commit()
                return True
            return False

    async def rm_correction(self, client, callback_query):
        match = re.search(
            r"admin_utils_correction_done_rm_(\d+)_(\d+)",
            callback_query.data,
        )
        if not match:
            print("nnnnnnnn")
            return

        correction_id = int(match.group(1))
        status = int(match.group(2))
        if status == 0:
            self.clear_correction_db(correction_id)
            await callback_query.answer("تحلیل با موفقیت حذف شد.", show_alert=True)
        elif status == 1:
            self.rm_correction_db(correction_id)
            await callback_query.answer(
                "تحلیل و تخصیص با موفقیت حذف شد.", show_alert=True
            )
        else:
            await callback_query.message.reply_text("error!")

        await callback_query.message.delete()


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
            filters.regex(rf"admin_{self.type}_practice_user_practice_select_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.user_practice_select)
        self.app.on_callback_query(
            filters.regex(rf"admin_{self.type}_user_practice_teahcer_list_(\d+)_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.teacher_selection_list)
        self.app.on_callback_query(
            filters.regex(rf"admin_{self.type}_user_practice_set_teahcer_(\d+)_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.create_correction)
        self.app.on_callback_query(
            filters.regex(
                rf"admin_{self.type}_user_practice_update_teahcer_list_(\d+)_(\d+)"
            )
            & filters.user(ADMINS_LIST_ID)
        )(self.update_teacher_selection_list)
        self.app.on_callback_query(
            filters.regex(
                rf"admin_{self.type}_user_practice_update_teahcer_(\d+)_(\d+)"
            )
            & filters.user(ADMINS_LIST_ID)
        )(self.update_correction)

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
                    db.UserModel.id.label("user_id"),
                    db.UserPracticeModel.datetime_created,
                    db.UserPracticeModel.datetime_modified,
                    db.CorrectionModel.datetime_created.label("takhsis_date"),
                    db.CorrectionModel.datetime_modified.label("tashih_date"),
                    db.TeacherModel.name.label("teacher_name"),
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
                .join(
                    db.TeacherModel, db.TeacherModel.id == db.CorrectionModel.teacher_id
                )
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
                    db.CorrectionModel.id,
                    db.UserModel.id,
                    db.UserPracticeModel.datetime_created,
                    db.UserPracticeModel.datetime_modified,
                    db.CorrectionModel.datetime_created,
                    db.CorrectionModel.datetime_modified,
                    db.TeacherModel.name,
                )
            ).first()
            return query

    @staticmethod
    def old_teachers(user_id):
        with db.get_session() as session:
            return (
                session.query(db.TeacherModel.name)
                .join(
                    db.CorrectionModel,
                    db.CorrectionModel.teacher_id == db.TeacherModel.id,
                )
                .join(
                    db.UserPracticeModel,
                    db.UserPracticeModel.id == db.CorrectionModel.user_practice_id,
                )
                .filter(db.UserPracticeModel.user_id == user_id)
                .distinct()
                .limit(5)
                .all()
            )

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
                    callback_data=f"admin_{self.type}_practice_paginate_list_0",
                ),
                InlineKeyboardButton("exit!", callback_data="back_home"),
            ]
        ]

        if user_practice:
            correction = "در انتظار تحلیل سخنرانی"

            if user_practice.teacher_caption:
                correction = (
                    f"تحلیل سخنرانی شده.\n◾️ کپشن منتور: {user_practice.teacher_caption}"
                    f"\n◾️ منتور: {user_practice.teacher_name}"
                    f"\n◾️ تاریخ تخصیص: {JalaliDateTime(user_practice.takhsis_date).strftime(DATE_TIME_FMT, locale='fa',)}"
                    f"\n◾️ تاریخ تحلیل: {JalaliDateTime(user_practice.tashih_date).strftime(DATE_TIME_FMT, locale='fa')}"
                )
                markup.insert(
                    0,
                    [
                        InlineKeyboardButton(
                            "🗑 حذف تکلیف",
                            callback_data=f"admin_utils_user_practice_confirm_rm_{user_practice_id}",
                        ),
                        InlineKeyboardButton(
                            "🗑 حذف تحلیل",
                            callback_data=f"admin_utils_correction_confirm_rm_{user_practice_id}",
                        ),
                    ],
                )
            elif user_practice.correction_id:
                correction = (
                    correction
                    + f"\n◾️ منتور: {user_practice.teacher_name}"
                    + f"\n◾️ تاریخ تخصیص: {JalaliDateTime(user_practice.takhsis_date).strftime(DATE_TIME_FMT, locale='fa')}"
                )
                markup.insert(
                    0,
                    [
                        InlineKeyboardButton(
                            "تعویض منتور",
                            callback_data=f"admin_{self.type}_user_practice_update_teahcer_list_{user_practice_id}_0",
                        )
                    ],
                )
                markup.insert(
                    1,
                    [
                        InlineKeyboardButton(
                            "🗑 حذف تکلیف",
                            callback_data=f"admin_utils_user_practice_confirm_rm_{user_practice_id}",
                        ),
                    ],
                )
            else:
                markup.insert(
                    0,
                    [
                        InlineKeyboardButton(
                            "تخصیص",
                            callback_data=f"admin_{self.type}_user_practice_teahcer_list_{user_practice_id}_0",
                        )
                    ],
                )
                markup.insert(
                    1,
                    [
                        InlineKeyboardButton(
                            "🗑 حذف تکلیف",
                            callback_data=f"admin_utils_user_practice_confirm_rm_{user_practice_id}",
                        ),
                    ],
                )

            old_teacher = list(
                map(lambda i: i.name, self.old_teachers(user_id=user_practice.user_id))
            )
            old_teacher = "\n▫️ ".join(old_teacher)
            update_user_practice = ""
            if not user_practice.datetime_created==user_practice.datetime_modified:
                update_user_practice = '◾️ تاریخ ویرایش: %s \n'%JalaliDateTime(user_practice.datetime_modified).strftime(DATE_TIME_FMT, locale='fa')
            caption = (
                f"📌 عنوان: {user_practice.title}\n🔖 متن سوال: {user_practice.caption}\n"
                f"◾️ کپشن کاربر: {user_practice.user_caption or 'بدون کپشن!'}\n"
                f"◾️ تاریخ پاسخ: {JalaliDateTime(user_practice.datetime_created).strftime(DATE_TIME_FMT, locale='fa')} \n"
                f"{update_user_practice}"
                "➖➖➖➖➖➖➖➖➖\n"
                "<blockquote expandable>\n"
                "منتورهای سابق:\n"
                f"▫️ {old_teacher}\n"
                "</blockquote>"
                "<blockquote expandable>\n"
                f"📊 وضعیت تمرین: {correction}!"
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
            await callback_query.message.reply_text("این تکلیف موجود نیست!")

    @staticmethod
    def teachers():
        with db.get_session() as session:
            return (
                session.query(
                    db.TeacherModel.id.label("id"),
                    db.TeacherModel.name.label("title"),
                )
                .filter(db.TeacherModel.chat_id.is_not(None))
                .all()
            )

    async def teacher_selection_list(self, client, callback_query):
        match = re.search(
            rf"admin_{self.type}_user_practice_teahcer_list_(\d+)_(\d+)",
            callback_query.data,
        )
        if not match:
            return

        user_practice_id = int(match.group(1))
        page = int(match.group(2))

        teachers = self.teachers()

        if not teachers:
            await callback_query.answer("هیچ منتور فعالی موجود نیست!")
            return

        await callback_query.answer("لطفا یک منتور انتخاب کنید", show_alert=True)

        # if page == 0:
        #     await callback_query.message.reply_text(
        #         "لطفا یک منتور انتخاب کنید:",
        #         reply_markup=select_teacher_paginated_keyboard(
        #             teachers,
        #             0,
        #             f"admin_{self.type}_practice_user_practice_list",
        #             f"admin_{self.type}_user_practice_set_teahcer",
        #             user_practice_id=user_practice_id,
        #             back_query="delete_this_msg",
        #         ),
        #     )
        #     return

        await callback_query.message.edit_reply_markup(
            reply_markup=select_teacher_paginated_keyboard(
                teachers,
                page,
                f"admin_{self.type}_practice_user_practice_list",
                f"admin_{self.type}_user_practice_set_teahcer",
                user_practice_id=user_practice_id,
                back_query="delete_this_msg",
            )
        )

    async def create_correction(self, client, callback_query):
        match = re.search(
            rf"admin_{self.type}_user_practice_set_teahcer_(\d+)_(\d+)",
            callback_query.data,
        )
        if not match:
            await callback_query.message.delete()
            return

        user_practice_id = int(match.group(1))
        teacher_id = int(match.group(2))

        with db.get_session() as session:
            new_correction = db.CorrectionModel(
                teacher_id=teacher_id, user_practice_id=user_practice_id
            )
            session.add(new_correction)
            session.commit()
            await callback_query.answer("تکلیف با موفقیت تخصیص یافت.", show_alert=True)
            await callback_query.message.delete()
            asyncio.create_task(
                self.send_teacher_notification(
                    client,
                    new_correction.user_practice_id,
                    teacher_id,
                )
            )
            return  # new_correction.id

    async def update_teacher_selection_list(self, client, callback_query):
        match = re.search(
            rf"admin_{self.type}_user_practice_update_teahcer_list_(\d+)_(\d+)",
            callback_query.data,
        )
        if not match:
            return

        correction_id = int(match.group(1))
        page = int(match.group(2))

        teachers = self.teachers()

        if not teachers:
            await callback_query.answer("هیچ منتور فعالی موجود نیست!")
            return

        await callback_query.answer("لطفا یک منتور انتخاب کنید", show_alert=True)

        # if page == 0:
        #     await callback_query.message.reply_text(
        #         "لطفا یک منتور انتخاب کنید:",
        #         reply_markup=select_teacher_paginated_keyboard(
        #             teachers,
        #             0,
        #             f"admin_{self.type}_practice_user_practice_list",
        #             f"admin_{self.type}_user_practice_set_teahcer",
        #             user_practice_id=correction_id,
        #             back_query="delete_this_msg",
        #         ),
        #     )
        #     return

        await callback_query.message.edit_reply_markup(
            reply_markup=select_teacher_paginated_keyboard(
                teachers,
                page,
                f"admin_{self.type}_practice_user_practice_list",
                f"admin_{self.type}_user_practice_set_teahcer",
                user_practice_id=correction_id,
                back_query="delete_this_msg",
            )
        )

    async def update_correction(self, client, callback_query):
        match = re.search(
            rf"admin_{self.type}_user_practice_update_teahcer_(\d+)_(\d+)",
            callback_query.data,
        )
        if not match:
            await callback_query.message.delete()
            return

        correction_id = int(match.group(1))
        teacher_id = int(match.group(2))

        with db.get_session() as session:
            correction = session.query(db.CorrectionModel).get(correction_id)
            if correction:
                session.teacher_id = teacher_id
                session.commit()
                await callback_query.answer(
                    "تکلیف با موفقیت تخصیص یافت.", show_alert=True
                )
                asyncio.create_task(
                    self.send_teacher_notification(
                        client,
                        correction.user_practice_id,
                        teacher_id,
                    )
                )
            else:
                await callback_query.answer("error!")

            await callback_query.message.delete()

    async def send_teacher_notification(self, client, user_practice_id, teacher_id):
        try:
            with db.get_session() as session:
                teacher = session.query(db.TeacherModel.tell_id).get(teacher_id)
                await client.send_message(
                    chat_id=teacher.tell_id,
                    text="تکلیف جدیدی به شما تخصیص یافت.",
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
        except Exception:
            pass


class BasePractice(BaseUserPractice):
    def __init__(self, app, type="all") -> None:
        super().__init__(app, type)

        self.app = app
        self.type = type
        self.base_register_handlers()

    def base_register_handlers(self):
        self.app.on_callback_query(
            filters.regex(rf"admin_{self.type}_practice_select_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.select)
        self.app.on_callback_query(
            filters.regex(rf"admin_{self.type}_practice_user_practice_list_(\d+)_(\d+)")
            & filters.user(ADMINS_LIST_ID)
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
                            callback_data=f"admin_{self.type}_practice_user_practice_list_{practice_id}_0",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "ارسال نوتیف به معلمان تمام نکرده",
                            callback_data=f"practice_send_teachers_notif_{practice_id}",
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
    def user_practices(pk, teacher_tell_id):
        with db.get_session() as session:
            return (
                session.query(
                    db.UserPracticeModel.id.label("id"),
                    db.UserModel.name.label("title"),
                )
                .filter_by(practice_id=pk)
                .join(db.UserModel, db.UserModel.id == db.UserPracticeModel.user_id)
                .all()
            )

    async def user_practice_list(self, client, callback_query):
        match = re.search(
            rf"admin_{self.type}_practice_user_practice_list_(\d+)_(\d+)",
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
                    f"admin_{self.type}_practice_user_practice_list",
                    f"admin_{self.type}_practice_user_practice_select",
                    back_query=f"admin_{self.type}_practice_select_{practice_id}",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=user_practice_paginated_keyboard(
                user_practices,
                page,
                practice_id,
                f"admin_{self.type}_practice_user_practice_list",
                f"admin_{self.type}_practice_user_practice_select",
                back_query=f"admin_{self.type}_practice_select_{practice_id}",
            )
        )


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
        practices = self.practices
        if not practices:
            await message.reply_text("هیچ تمرین فعالی موجود نیست!")
            return

        await message.reply_text(
            "تمارین فعال:",
            reply_markup=get_paginated_keyboard(
                practices,
                0,
                "admin_active_practice_paginate_list",
                "admin_active_practice_select",
            ),
        )

    async def paginate_list(self, client, callback_query):
        page = int(callback_query.data.split("_")[-1])
        practices = self.practices

        if not practices:
            await callback_query.message.reply_text("هیچ تمرین فعالی موجود نیست!")
            return

        if page == 0:
            await callback_query.message.delete()
            await callback_query.message.reply_text(
                "تمارین فعال:",
                reply_markup=get_paginated_keyboard(
                    practices,
                    page,
                    "admin_active_practice_paginate_list",
                    "admin_active_practice_select",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                practices,
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
        with db.get_session() as session:
            practices = session.query(db.PracticeModel.id, db.PracticeModel.title).all()
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


class NONEPractice(BaseUserPractice):
    def __init__(self, app, type="none"):
        super().__init__(app, type)

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

    @property
    def user_practices(self):
        with db.get_session() as session:
            subquery = select(
                session.query(db.CorrectionModel.user_practice_id).subquery()
            )

            query = (
                session.query(
                    db.UserPracticeModel.id,
                    (db.UserModel.name + " | " + db.PracticeModel.title).label("title"),
                )
                .filter(db.UserPracticeModel.id.notin_(subquery))
                .join(db.UserModel, db.UserModel.id == db.UserPracticeModel.user_id)
                .join(
                    db.PracticeModel,
                    db.PracticeModel.id == db.UserPracticeModel.practice_id,
                )
            )

            return query.all()

    async def list(self, client, message):
        if not self.user_practices:
            await message.reply_text("هیچ تکلیفی موجود نیست!")
            return

        await message.reply_text(
            "تکالیف تخصیص داده نشده:",
            reply_markup=get_paginated_keyboard(
                self.user_practices,
                0,
                "admin_none_practice_paginate_list",
                f"admin_{self.type}_practice_user_practice_select",
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
                "تکالیف تخصیص داده نشده:",
                reply_markup=get_paginated_keyboard(
                    self.user_practices,
                    page,
                    "admin_none_practice_paginate_list",
                    f"admin_{self.type}_practice_user_practice_select",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                self.user_practices,
                page,
                "admin_none_practice_paginate_list",
                f"admin_{self.type}_practice_user_practice_select",
            )
        )


class DonePractice(BaseUserPractice):
    def __init__(self, app, type="done"):
        super().__init__(app, type)

        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(
            filters.regex("تکالیف تحلیل شده") & filters.user(ADMINS_LIST_ID)
        )(self.list)
        self.app.on_callback_query(
            filters.regex(r"admin_done_practice_paginate_list_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.paginate_list)
        self.app.on_callback_query(
            filters.regex(r"admin_done_practice_user_practice_select_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.user_practice_select)

    @property
    def user_practices(self):
        with db.get_session() as session:
            query = (
                session.query(
                    db.CorrectionModel.id.label("correction_id"),
                    db.UserPracticeModel.id,
                    (db.UserModel.name + " | " + db.PracticeModel.title).label("title"),
                )
                .filter(db.CorrectionModel.caption.is_not(None))
                .join(
                    db.UserPracticeModel,
                    db.UserPracticeModel.id == db.CorrectionModel.user_practice_id,
                )
                .join(
                    db.PracticeModel,
                    db.PracticeModel.id == db.UserPracticeModel.practice_id,
                )
                .join(db.UserModel, db.UserModel.id == db.UserPracticeModel.user_id)
            )

            return query.all()

    async def list(self, client, message):
        if not self.user_practices:
            await message.reply_text("هیچ تکلیفی موجود نیست!")
            return

        await message.reply_text(
            "تکالیف تحلیل شده:",
            reply_markup=get_paginated_keyboard(
                self.user_practices,
                0,
                "admin_done_practice_paginate_list",
                f"admin_{self.type}_practice_user_practice_select",
            ),
        )

    async def paginate_list(self, client, callback_query):
        page = int(callback_query.data.split("_")[-1])

        if not self.user_practices:
            await callback_query.message.delete()
            await callback_query.message.reply_text("هیچ تکلیف موجود نیست!")
            return

        if page == 0:
            await callback_query.message.delete()
            await callback_query.message.reply_text(
                "تکالیف تحلیل شده:",
                reply_markup=get_paginated_keyboard(
                    self.user_practices,
                    page,
                    "admin_done_practice_paginate_list",
                    f"admin_{self.type}_practice_user_practice_select",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                self.user_practices,
                page,
                "admin_done_practice_paginate_list",
                f"admin_{self.type}_practice_user_practice_select",
            )
        )


class NotDonePractice(BaseUserPractice):
    def __init__(self, app, type="notdone"):
        super().__init__(app, type)

        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(
            filters.regex("تکالیف تحلیل نشده") & filters.user(ADMINS_LIST_ID)
        )(self.list)
        self.app.on_callback_query(
            filters.regex(r"admin_ndone_practice_paginate_list_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.paginate_list)

    @property
    def user_practices(self):
        with db.get_session() as session:
            query = (
                session.query(
                    db.CorrectionModel.id.label("correction_id"),
                    db.UserPracticeModel.id,
                    (db.UserModel.name + " | " + db.PracticeModel.title).label("title"),
                )
                .filter(db.CorrectionModel.caption.is_(None))
                .join(
                    db.UserPracticeModel,
                    db.UserPracticeModel.id == db.CorrectionModel.user_practice_id,
                )
                .join(
                    db.PracticeModel,
                    db.PracticeModel.id == db.UserPracticeModel.practice_id,
                )
                .join(db.UserModel, db.UserModel.id == db.UserPracticeModel.user_id)
            )

            return query.all()

    async def list(self, client, message):
        if not self.user_practices:
            await message.reply_text("هیچ تکلیفی موجود نیست!")
            return

        await message.reply_text(
            "تکالیف تخصیص یافته ولی تحلیل نشده:",
            reply_markup=get_paginated_keyboard(
                self.user_practices,
                0,
                "admin_ndone_practice_paginate_list",
                f"admin_{self.type}_practice_user_practice_select",
            ),
        )

    async def paginate_list(self, client, callback_query):
        page = int(callback_query.data.split("_")[-1])

        if not self.user_practices:
            await callback_query.message.delete()
            await callback_query.message.reply_text("هیچ تکلیفی موجود نیست!")
            return

        if page == 0:
            await callback_query.message.delete()
            await callback_query.message.reply_text(
                "تکالیف تخصیص یافته ولی تحلیل نشده:",
                reply_markup=get_paginated_keyboard(
                    self.user_practices,
                    page,
                    "admin_ndone_practice_paginate_list",
                    f"admin_{self.type}_practice_user_practice_select",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                self.user_practices,
                page,
                "admin_ndone_practice_paginate_list",
                f"admin_{self.type}_practice_user_practice_select",
            )
        )


class AllUserPractice(BaseUserPractice):
    def __init__(self, app, type="aa"):
        super().__init__(app, type)

        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(
            filters.regex("تمامی تکالیف") & filters.user(ADMINS_LIST_ID)
        )(self.list)
        self.app.on_callback_query(
            filters.regex(r"admin_aa_practice_paginate_list_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.paginate_list)
        self.app.on_callback_query(
            filters.regex(r"admin_aa_practice_user_practice_select_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.user_practice_select)

    @property
    def user_practices(self):
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
            )

            return query.all()

    async def list(self, client, message):
        if not self.user_practices:
            await message.reply_text("هیچ تکلیفی موجود نیست!")
            return

        await message.reply_text(
            "تمامی تکالیف:",
            reply_markup=get_paginated_keyboard(
                self.user_practices,
                0,
                "admin_aa_practice_paginate_list",
                "admin_aa_practice_user_practice_select",
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
                    "admin_aa_practice_paginate_list",
                    "admin_aa_practice_user_practice_select",
                ),
            )
            return

        await callback_query.message.edit_reply_markup(
            reply_markup=get_paginated_keyboard(
                self.user_practices,
                page,
                "admin_aa_practice_paginate_list",
                "admin_aa_practice_user_practice_select",
            )
        )


class Users:
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
            filters.regex(r"admin_users_notif_(\d+)") & filters.user(ADMINS_LIST_ID)
        )(self.notif)
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
        self.app.on_callback_query(
            filters.regex(r"admin_users_set_type_(\d+)_(\d+)")
            & filters.user(ADMINS_LIST_ID)
        )(self.set_type)

    @property
    def users(self):
        with db.get_session() as session:
            return session.query(db.UserModel).all()

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
        with db.get_session() as session:
            # total_count_subquery = (
            #     session.query(func.count(db.PracticeModel.id))
            #     .join(
            #         db.UserModel,
            #         db.UserModel.user_type_id == db.PracticeModel.user_type_id,
            #     )
            #     .filter(db.UserModel.id == pk)
            #     .scalar_subquery()
            # )

            # user_practice_count_subquery = (
            #     session.query(func.count(db.UserPracticeModel.id))
            #     .filter(db.UserPracticeModel.user_id == pk)
            #     .scalar_subquery()
            # )

            # correction_count_subquery = (
            #     session.query(func.count(db.UserPracticeModel.id))
            #     .filter(
            #         db.UserPracticeModel.user_id == pk,
            #         db.UserPracticeModel.teacher_caption.is_not(None),
            #     )
            #     .scalar_subquery()
            # )

            # not_correction_count_subquery = (
            #     session.query(func.count(db.UserPracticeModel.id))
            #     .filter(
            #         db.UserPracticeModel.user_id == pk,
            #         db.UserPracticeModel.teacher_caption.is_(None),
            #     )
            #     .scalar_subquery()
            # )
            user_type_subquery = (
                session.query(db.UserTypeModel.name)
                .filter(db.UserModel.user_type_id == db.UserTypeModel.id)
                .scalar_subquery()
            )

            result = (
                session.query(
                    db.UserModel.name,
                    db.UserModel.phone_number,
                    user_type_subquery.label("user_type_name"),
                    # total_count_subquery.label("total_count_practice"),
                    # user_practice_count_subquery.label("total_count_user_practice"),
                    # correction_count_subquery.label("total_count_correction"),
                    # not_correction_count_subquery.label("total_count_not_correction"),
                )
                .filter(db.UserModel.id == pk)
                .first()
            )
            return result

    async def select(self, client, callback_query):
        user_id = int(callback_query.data.split("_")[-1])
        user = self.user(user_id)
        await callback_query.message.delete()

        await callback_query.message.reply_text(
            f"🆔 #{user_id}\n📞 شماره: \n{user.phone_number}"
            f"\n👤 نام: {user.name or 'Not set!'}\n"
            f"◾️ نوع یوزر: {user.user_type_name}\n",
            # "➖➖➖➖➖➖➖➖➖\n"
            # f"◾️ تعداد کل تمارین: {user.total_count_practice}\n"
            # f"◾️ تعداد تکالیف تحویل داده شده: {user.total_count_user_practice}\n"
            # f"◾️ تعداد تکالیف تحویل داده نشده: {user.total_count_practice - user.total_count_user_practice}\n"
            # f"◾️ تعداد تکالیف تصحیح شده: {user.total_count_correction}\n"
            # f"◾️ تعداد تکالیف تصحیح نشده: {user.total_count_not_correction}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🗑 حذف یوزر",
                            callback_data=f"admin_users_confirm_delete_{user_id}",
                        ),
                        InlineKeyboardButton(
                            "ارسال نوتیف",
                            callback_data=f"admin_users_notif_{user_id}",
                        ),
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

    async def notif(self, client, callback_query):
        teacher_id = int(callback_query.data.split("_")[-1])
        await callback_query.answer("لطفا پیام خود را ارسال کنید", show_alert=True)
        await callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Cancel", callback_data="back_home")],
                ]
            )
        )

        try:
            answer = await pyrostep.wait_for(
                callback_query.from_user.id, timeout=TIME_OUT * 60
            )

            msg = "📢  اطلاع رسانی \n" + answer.text
            asyncio.create_task(self.send_notif(client, msg, teacher_id))
            await callback_query.message.reply_text("پیام در صف ارسال قرار گرفت")
        except TimeoutError:
            await callback_query.message.reply_text("مهلت زمانی پاسخ تمام شد!")
        except asyncio.CancelledError:
            await callback_query.message.reply_text("کنسل شد!")
        except Exception:
            await callback_query.message.reply_text("error!")

    async def send_notif(self, client, data, pk):
        with db.get_session() as session:
            user = session.query(db.UserModel).get(pk)
            if user and user.chat_id:
                try:
                    await client.send_message(chat_id=user.chat_id, text=data)
                except Exception:
                    pass

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
        with db.get_session() as session:
            user = session.query(db.UserModel).get(pk)
            if user:
                session.delete(user)
                session.commit()
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
            "شماره تلفن یوزر جدید را ارسال کنید:\n" "فرمت صحیح:\n" "+989150000000",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Cancel", callback_data="back_home")]]
            ),
        )

        while True:
            try:
                phone_number = await pyrostep.wait_for(
                    message.from_user.id, timeout=TIME_OUT * 60
                )

                if (
                    self.not_in_db(phone_number.text)
                    and "+98" in phone_number.text
                    and len(phone_number.text) == 13
                ):
                    await message.reply_text(
                        "نام کاربر را ارسال کنید:\n"
                        f"شماره تلفن کاربر: {phone_number.text}",
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(
                                        "Cancel", callback_data="back_home"
                                    )
                                ]
                            ]
                        ),
                    )

                    name = await pyrostep.wait_for(
                        message.from_user.id, timeout=TIME_OUT * 60
                    )
                    user_id = self.add_db(phone_number.text, name.text)

                    if user_id:
                        with db.get_session() as session:
                            await message.reply_text(
                                f"👤 نام کاربر: {name.text}\n📞 شماره تلفن: {phone_number.text}\n"
                                "لطفا نوع یوزر را انتخاب کنید:",
                                reply_markup=InlineKeyboardMarkup(
                                    [
                                        [
                                            InlineKeyboardButton(
                                                i.name,
                                                callback_data=f"admin_users_set_type_{i.id}_{user_id}",
                                            )
                                            for i in session.query(
                                                db.UserTypeModel
                                            ).all()
                                        ],
                                        [
                                            InlineKeyboardButton(
                                                "exit!", callback_data="back_home"
                                            )
                                        ],
                                    ]
                                ),
                            )
                        break

                await message.reply_text(
                    "شماره ارسال شده معتبر نیست!\nلطفا دوبار ارسال کنید یا روی دکمه‌ی کنسل بزنید.",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Cancel", callback_data="back_home")]]
                    ),
                )
            except TimeoutError:
                await message.reply_text("مهلت زمانی پاسخ تمام شد!")
                break
            except asyncio.CancelledError:
                await message.reply_text("کنسل شد!")
                break

    @staticmethod
    def not_in_db(phone_num):
        with db.get_session() as session:
            return (
                session.query(db.UserModel).filter_by(phone_number=phone_num).first()
                is None
            )

    @staticmethod
    def add_db(phone_num, name):
        with db.get_session() as session:
            new_user = db.UserModel(phone_number=phone_num, name=name)
            session.add(new_user)
            session.commit()
            return new_user.id

    @staticmethod
    def update_user_type(pk, user_type_id):
        if not isinstance(user_type_id, int):
            user_type_id = int(user_type_id)
        with db.get_session() as session:
            user = session.query(db.UserModel).get(pk)
            if user:
                user.user_type_id = user_type_id
                session.commit()
                return True
        return False

    async def set_type(self, client, callback_query):
        match = re.search(r"admin_users_set_type_(\d+)_(\d+)", callback_query.data)
        if match:
            user_type_id = match.group(1)
            user_id = match.group(2)
            # print(user_id, user_type, db.UserType[user_type].value)
            if self.update_user_type(user_id, user_type_id):
                await callback_query.answer(
                    "کاربر با موفقیت اضافه شد.", show_alert=True
                )
                await callback_query.message.delete()
                # await callback_query.message.reply_text("کاربر با موفقیت اضافه شد.")
                await send_home_message_admin(callback_query.message)
            else:
                await callback_query.message.reply_text("error!")


class Teachers:
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
            filters.regex(r"admin_teachers_notif_(\d+)") & filters.user(ADMINS_LIST_ID)
        )(self.notif)
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
        with db.get_session() as session:
            return session.query(db.TeacherModel).all()

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

    @staticmethod
    def user(pk):
        with db.get_session() as session:
            # total_count_subquery = (
            #     session.query(func.count(db.UserPracticeModel.id))
            #     .filter(db.UserPracticeModel.teacher_id == pk)
            #     .scalar_subquery()
            # )

            # teacher_caption_count_subquery = (
            #     session.query(func.count(db.UserPracticeModel.id))
            #     .filter(
            #         db.UserPracticeModel.teacher_id == pk,
            #         db.UserPracticeModel.teacher_caption.isnot(None),
            #     )
            #     .scalar_subquery()
            # )

            # teacher_caption_none_count_subquery = (
            #     session.query(func.count(db.UserPracticeModel.id))
            #     .filter(
            #         db.UserPracticeModel.teacher_id == pk,
            #         db.UserPracticeModel.teacher_caption.is_(None),
            #     )
            #     .scalar_subquery()
            # )

            result = (
                session.query(
                    db.TeacherModel.name,
                    db.TeacherModel.phone_number,
                    # total_count_subquery.label("total_count_user_practice"),
                    # teacher_caption_count_subquery.label(
                    #     "count_correction_user_practice"
                    # ),
                    # teacher_caption_none_count_subquery.label(
                    #     "count_not_correction_user_practice"
                    # ),
                )
                .filter(db.TeacherModel.id == pk)
                .first()
            )
            return result

    async def select(self, client, callback_query):
        user_id = int(callback_query.data.split("_")[-1])
        user = self.user(user_id)
        await callback_query.message.delete()

        await callback_query.message.reply_text(
            f"🆔 #{user_id}\n👤 نام معلم: {user.name}\n"
            f"📞 شماره معلم: \n{user.phone_number}\n",
            # "➖➖➖➖➖➖➖➖➖\n"
            # f"◾️ تعداد تمارین تخصیص داده شده: {user.total_count_user_practice}\n"
            # f"◾️ تعداد تمارین تحیل شده: {user.count_correction_user_practice}\n"
            # f"◾️ تعداد تمارین تحلیل نشده: {user.count_not_correction_user_practice}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🗑 حذف معلم",
                            callback_data=f"admin_teachers_confirm_delete_{user_id}",
                        ),
                        InlineKeyboardButton(
                            "ارسال نوتیف",
                            callback_data=f"admin_teachers_notif_{user_id}",
                        ),
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

    async def notif(self, client, callback_query):
        teacher_id = int(callback_query.data.split("_")[-1])
        await callback_query.answer("لطفا پیام خود را ارسال کنید", show_alert=True)
        await callback_query.message.edit_reply_markup(
            reply_markup=InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton("Cancel", callback_data="back_home")],
                ]
            )
        )

        try:
            answer = await pyrostep.wait_for(
                callback_query.from_user.id, timeout=TIME_OUT * 60
            )

            msg = "📢  اطلاع رسانی \n" + answer.text
            asyncio.create_task(self.send_notif(client, msg, teacher_id))
            await callback_query.message.reply_text("پیام در صف ارسال قرار گرفت")
        except TimeoutError:
            await callback_query.message.reply_text("مهلت زمانی پاسخ تمام شد!")
        except asyncio.CancelledError:
            await callback_query.message.reply_text("کنسل شد!")
        except Exception:
            await callback_query.message.reply_text("error!")

    async def send_notif(self, client, data, pk):
        with db.get_session() as session:
            teacher = session.query(db.TeacherModel).get(pk)
            if teacher and teacher.chat_id:
                try:
                    await client.send_message(chat_id=teacher.chat_id, text=data)
                except Exception:
                    pass

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
        with db.get_session() as session:
            user = session.query(db.TeacherModel).get(pk)
            if user:
                session.delete(user)
                session.commit()
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
            "شماره تلفن معلم جدید را ارسال کنید:\n" "فرمت صحیح:\n" "+989150000000",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Cancel", callback_data="back_home")]]
            ),
        )

        while True:
            try:
                phone_number = await pyrostep.wait_for(
                    message.from_user.id, timeout=TIME_OUT * 60
                )

                if (
                    self.not_in_db(phone_number.text)
                    and "+98" in phone_number.text
                    and len(phone_number.text) == 13
                ):
                    await message.reply_text(
                        "نام معلم را ارسال کنید:\n"
                        f"شماره تلفن معلم: {phone_number.text}",
                        reply_markup=InlineKeyboardMarkup(
                            [
                                [
                                    InlineKeyboardButton(
                                        "Cancel", callback_data="back_home"
                                    )
                                ]
                            ]
                        ),
                    )

                    name = await pyrostep.wait_for(
                        message.from_user.id, timeout=TIME_OUT * 60
                    )

                    if self.add_db(phone_number.text, name.text):
                        await message.reply_text("معلم با موفقیت افزوده شد!")
                        break

                await message.reply_text(
                    "شماره ارسال شده معتبر نیست!\nلطفا دوبار ارسال کنید یا روی دکمه‌ی کنسل بزنید.",
                    reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Cancel", callback_data="back_home")]]
                    ),
                )
            except TimeoutError:
                await message.reply_text("مهلت زمانی پاسخ تمام شد!")
                break
            except asyncio.CancelledError:
                await message.reply_text("کنسل شد!")
                break

    @staticmethod
    def not_in_db(phone_num):
        with db.get_session() as session:
            return (
                session.query(db.TeacherModel).filter_by(phone_number=phone_num).first()
                is None
            )

    @staticmethod
    def add_db(phone_num, name):
        with db.get_session() as session:
            new_teacher = db.TeacherModel(phone_number=phone_num, name=name)
            session.add(new_teacher)
            session.commit()
            return new_teacher.id


class Notifiaction:
    base_caption = "📢  اطلاع رسانی \n"

    def __init__(self, app):
        self.app = app
        self.register_handlers()

    def register_handlers(self):
        self.app.on_message(
            filters.regex("ارسال نوتیفیکیشن") & filters.user(ADMINS_LIST_ID)
        )(self.select_type)
        self.app.on_callback_query(
            filters.regex(r"admin_notif_select_(\d+)") & filters.user(ADMINS_LIST_ID)
        )(self.reply)
        self.app.on_callback_query(
            filters.regex(r"admin_notif_user_type_(\d+)") & filters.user(ADMINS_LIST_ID)
        )(self.reply_user_type)

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
                            "ارسال به معلمان", callback_data="admin_notif_select_1"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "ارسال به همه کاربران", callback_data="admin_notif_select_3"
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "ارسال به کاربران یک تایپ خاص",
                            callback_data="admin_notif_select_4",
                        )
                    ],
                    [InlineKeyboardButton("exit!", callback_data="back_home")],
                ]
            ),
        )

    async def reply(self, client, callback_query):
        # await callback_query.message.delete()
        type = int(callback_query.data.split("_")[-1])
        await callback_query.message.delete()

        if type == 4:
            with db.get_session() as session:
                await callback_query.message.reply_text(
                    "لطفا نوع یوزر را انتخاب کنید:",
                    reply_markup=InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton(
                                    i.name,
                                    callback_data=f"admin_notif_user_type_{i.id}",
                                )
                                for i in session.query(db.UserTypeModel).all()
                            ],
                            [InlineKeyboardButton("exit!", callback_data="back_home")],
                        ]
                    ),
                )
            return

        await callback_query.message.reply_text(
            "پیام موردنظر را ارسال کنید.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]],
            ),
        )

        try:
            answer = await pyrostep.wait_for(
                callback_query.from_user.id, timeout=TIME_OUT * 60
            )
            msg = self.base_caption + answer.text

            if type == 0:
                asyncio.create_task(self.send_alls_notification(client, msg))
            elif type == 1:
                asyncio.create_task(self.send_teachers_notification(client, msg))
            else:
                asyncio.create_task(self.send_users_notification(client, msg))

            await answer.reply_text("پیام در صف ارسال قرار گرفت.")
        except TimeoutError:
            await callback_query.message.reply_text("مهلت زمانی پاسخ تمام شد!")
        except asyncio.CancelledError:
            await callback_query.message.reply_text("کنسل شد!")
        except Exception:
            await callback_query.message.reply_text("error!")

    async def reply_user_type(self, client, callback_query):
        user_type = int(callback_query.data.split("_")[-1])
        await callback_query.message.delete()

        await callback_query.message.reply_text(
            "پیام موردنظر را ارسال کنید.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("exit!", callback_data="back_home")]],
            ),
        )

        try:
            answer = await pyrostep.wait_for(
                callback_query.from_user.id, timeout=TIME_OUT * 60
            )
            msg = self.base_caption + answer.text

            asyncio.create_task(
                self.send_users_type_notification(client, msg, user_type)
            )

            await answer.reply_text("پیام در صف ارسال قرار گرفت.")
        except TimeoutError:
            await callback_query.message.reply_text("مهلت زمانی پاسخ تمام شد!")
        except asyncio.CancelledError:
            await callback_query.message.reply_text("کنسل شد!")
        except Exception:
            await callback_query.message.reply_text("error!")

    @property
    def users(self):
        with db.get_session() as session:
            return (
                session.query(db.UserModel)
                .filter(db.UserModel.chat_id.is_not(None))
                .all()
            )

    @staticmethod
    def users_with_type(user_type):
        with db.get_session() as session:
            return (
                session.query(db.UserModel)
                .filter(
                    and_(
                        db.UserModel.chat_id.is_not(None),
                        db.UserModel.user_type_id == user_type,
                    )
                )
                .all()
            )

    @property
    def teachers(self):
        with db.get_session() as session:
            return (
                session.query(db.TeacherModel)
                .filter(db.TeacherModel.chat_id.is_not(None))
                .all()
            )

    async def send_users_notification(self, client, data):
        for user in self.users:
            try:
                await client.send_message(chat_id=user.chat_id, text=data)
            except Exception:
                pass

    async def send_users_type_notification(self, client, data, user_type):
        for user in self.users_with_type(user_type):
            try:
                await client.send_message(chat_id=user.chat_id, text=data)
            except Exception:
                pass

    async def send_teachers_notification(self, client, data):
        for user in self.teachers:
            try:
                await client.send_message(chat_id=user.chat_id, text=data)
            except Exception:
                pass

    async def send_alls_notification(self, client, data):
        for admin in ADMINS_LIST_ID:
            try:
                await client.send_message(chat_id=admin, text=data)
            except Exception:
                pass
        for user in self.teachers:
            try:
                await client.send_message(chat_id=user.chat_id, text=data)
            except Exception:
                pass
        for user in self.users:
            try:
                await client.send_message(chat_id=user.chat_id, text=data)
            except Exception:
                pass


def register_admin_handlers(app):
    UserPracticeUtils(app)

    ActivePractice(app)
    AllPractice(app)
    NONEPractice(app)
    DonePractice(app)
    NotDonePractice(app)
    AllUserPractice(app)
    Users(app)
    Teachers(app)
    Practice(app)
    Notifiaction(app)
