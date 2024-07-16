from pyrogram import Client

from bot import (
    register_start_handlers,
    register_home_handlers,
    register_admin_handlers,
    register_teacher_handlers,
    register_user_handlers,
)
import bot


# BOT_TOKEN = "7005827895:AAEd4wtyF-oOftIoNG0PSV0dK4yGZR7fhek"
# api_id = 22868863
# api_hash = "6388e9db9f2febffe4ebf0955ccb8345"
app = Client(
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

bot.admin.ActivePractice(app)
bot.admin.AllPractice(app)
bot.admin.NONEPractice(app)
bot.admin.Users(app)
bot.admin.Teachers(app)
bot.admin.Practice(app)
bot.admin.Notifiaction(app)

bot.teacher.ActivePractice(app)
bot.teacher.AllPractice(app)
bot.teacher.NONEPractice(app)

bot.user.ActivePractice(app)
bot.user.AnsweredPractice(app)


app.run()
