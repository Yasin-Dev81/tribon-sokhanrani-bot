from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, ForceReply


async def send_home_message_admin(message):
    await message.reply_text(
        "Hi, admin!"
        "\n<b>AH-score</b> <i>v3.1</i>",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["تعریف تمرین جدید"],
                ["تمرین‌های فعال", "تکالیف بدون معلم", "تمامی تمرین‌ها"],
                ["یوزرها", "اضافه کردن یوزر جدید"],
                ["معلم‌ها", "اضافه کردن معلم جدید"],
                ["اطلاع‌رسانی به کاربران", "اطلاع‌رسانی به معلمان", "اطلاع‌رسانی به همه"],
                ["my settings"]
            ],
            resize_keyboard=True
        )
    )


async def send_home_message_teacher(message):
    await message.reply_text(
        "Hi, teacher!"
        "\n<b>AH-score</b> <i>v3.1</i>",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["تمرین‌های نیازمند به تصحیح"],
                ["تمرین‌های فعال", "تمامی تمرین‌ها", "تصحیح شده‌ها"],
                ["my settings"]
            ],
            resize_keyboard=True
        )
    )


async def send_home_message_user(message):
    await message.reply_text(
        "Hi, user!"
        "\n<b>AH-score</b> <i>v3.1</i>",
        reply_markup=ReplyKeyboardMarkup(
            [
                ["تمرین‌های فعال", "تحویل داده شده‌ها"],
                ["my settings"]
            ],
            resize_keyboard=True
        )
    )
