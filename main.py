from pyrogram import Client
import uvloop
import logging

from bot import (
    register_start_handlers,
    register_home_handlers,
    register_admin_handlers,
    register_teacher_handlers,
    register_user_handlers,
    register_report_handlers,
    register_utils_handlers,
)
from config import TELL_CONFIG, BOT_TOKEN, API_ID, API_HASH


logging.basicConfig(level=logging.WARN)

# speed up
uvloop.install()


if API_ID and API_HASH and BOT_TOKEN:
    app = Client(
        TELL_CONFIG,
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
    )
else:
    app = Client(TELL_CONFIG)


# Register handlers
register_start_handlers(app)
register_home_handlers(app)
register_admin_handlers(app)
register_teacher_handlers(app)
register_user_handlers(app)
register_report_handlers(app)
register_utils_handlers(app)


app.run()
