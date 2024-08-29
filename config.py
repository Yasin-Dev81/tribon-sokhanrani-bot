from decouple import config
from dotenv import load_dotenv
import pytz

load_dotenv()


# version
BOT_VERSION = config("BOT_VERSION", default="dev")

# bot
TELL_CONFIG = config("TELL_CONFIG", default="/var/lib/tribon/tribon")
BOT_TOKEN = config("BOT_TOKEN", default=None)
API_ID = config("API_ID", default=None)
API_HASH = config("API_HASH", default=None)

# db
SQLALCHEMY_DATABASE_URL = config(
    "SQLALCHEMY_DATABASE_URL",
    default="mysql+pymysql://root:jojo9900@127.0.0.1:3306/tribon",
)
DB_ADDRESS = config("DB_ADDRESS", default="127.0.0.1")

# users
ADMINS_LIST_ID = config(
    "ADMINS_LIST_ID",
    default="",
    cast=lambda v: [
        int(i) for i in filter(str.isdigit, (s.strip() for s in v.split(",")))
    ],
)

GROUP_CHAT_ID = config("GROUP_CHAT_ID", default=None)

# pagination
PRACTICES_PER_PAGE = config("PRACTICES_PER_PAGE", cast=int, default=5)

TIME_ZONE = pytz.timezone(config("TIME_ZONE", cast=str, default="Asia/Tehran"))
DATE_TIME_FMT = config("DATE_TIME_FMT", cast=str, default="%c")

TIME_OUT = config("TIME_OUT", cast=int, default=15)


# msg
LEARN_URL = config("LEARN_URL", cast=str, default="https://t.me/sokhanrani/1389")

default_info_msg = f"""
📝 قوانین

▫️ مدیای آپلود شده باید کمتر از <b>50 مگابایت</b> باشد.
▫️ کپشن مدیاهای ارسال شده ذخیره خواهند شد.
▫️ امکان ویرایش تکلیف تحویل داده شده فقط تا زمان ددلاین تمرین فراهم است، مگر آنکه تکلیف درحال تصحیح توسط منتور باشد.
▫️ درصورت مشاهده‌ی هرگونه مشکل به ادمین مراجعه کنید.


<a href='{LEARN_URL}'>ℹ️ ویدیو آموزشی نحوه ارسال تمرینات</a>
"""
INFO_MSG = config("INFO_MSG", cast=str, default=default_info_msg)

default_warn_msg = f"""
<blockquote expandable>
⚠️ توجه:
🌵 درصورت منصرف شدن از ارسال پاسخ، حتما دکمه‌ی کنسل را کلیک کنید!
⭕️ بات {TIME_OUT} دقیقه منتظر پاسخ شما خواهد ماند، درصورت ارسال نکردن پاسخ باید دوباره روی دکمه‌ی تحویل کلیک کنید!
⛔️ حجم هر نوع مدیای ارسالی باید کمتر از 50 مگابایت باشد.
</blockquote>
"""
WARN_MSG = config("WARN_MSG", cast=str, default=default_warn_msg)
