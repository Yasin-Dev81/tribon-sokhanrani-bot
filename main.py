# -*- coding:utf8 -*-

from pyrogram import Client, filters, idle
import logging
import uvloop
import pyrostep

from bot import (
    register_start_handlers,
    register_home_handlers,
    register_admin_handlers,
    register_teacher_handlers,
    register_user_handlers,
    register_report_handlers,
    register_utils_handlers,
    register_system_handlers,
)
from config import TELL_CONFIG, BOT_TOKEN, API_ID, API_HASH

# Set up logging
logging.basicConfig(level=logging.INFO)

# Install UVLoop for faster event loops
uvloop.install()

# Install pyrostep for enhanced performance
pyrostep.install()

# Initialize the Pyrogram Client
app = (
    Client(
        TELL_CONFIG,
        api_id=API_ID,
        api_hash=API_HASH,
        bot_token=BOT_TOKEN,
    )
    if API_ID and API_HASH and BOT_TOKEN
    else Client(TELL_CONFIG)
)

# Listen for non-command messages excluding "back_home"
app.listen(filters=~filters.command("back_home"))

# Register handlers
register_start_handlers(app)
register_home_handlers(app)
register_admin_handlers(app)
register_teacher_handlers(app)
register_user_handlers(app)
register_report_handlers(app)
register_utils_handlers(app)
register_system_handlers(app)


async def main():
    await app.start()
    await idle()
    await app.stop()


# Run the Pyrogram Client and AioClock concurrently
if __name__ == "__main__":
    app.run(main())
