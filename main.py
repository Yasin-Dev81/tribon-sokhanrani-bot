from pyrogram import Client

from bot import (
    register_start_handlers,
    register_home_handlers,
    register_admin_handlers,
    register_teacher_handlers,
    register_user_handlers,
)
from config import TELL_CONFIG


BOT_TOKEN = "7243002893:AAEgy-jfsrxp4q1giFJwhtiCWkVFHkmK6co"
api_id = 22868863
api_hash = "6388e9db9f2febffe4ebf0955ccb8345"
app = Client(
    # TELL_CONFIG,
    "./var/ah-score"
    # api_id=api_id, api_hash=api_hash,
    # bot_token=BOT_TOKEN
)


# Register handlers
register_start_handlers(app)
register_home_handlers(app)
register_admin_handlers(app)
register_teacher_handlers(app)
register_user_handlers(app)


app.run()
