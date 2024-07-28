from pyrogram import Client

from bot import (
    register_start_handlers,
    register_home_handlers,
    register_admin_handlers,
    register_teacher_handlers,
    register_user_handlers,
)
from config import TELL_CONFIG, BOT_TOKEN, API_ID, API_HASH


if API_ID and API_HASH and BOT_TOKEN:
    app = Client(
        TELL_CONFIG,
        # "./var/ah-score",
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
    )
else:
    app = Client(
        TELL_CONFIG
    )


# Register handlers
register_start_handlers(app)
register_home_handlers(app)
register_admin_handlers(app)
register_teacher_handlers(app)
register_user_handlers(app)


app.run()
