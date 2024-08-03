from decouple import config
from dotenv import load_dotenv

load_dotenv()


# version
BOT_VERSION = config("BOT_VERSION", default="dev")

# bot
TELL_CONFIG = config(
    "TELL_CONFIG", default="/var/lib/tribon/tribon"
)

BOT_TOKEN = config("BOT_TOKEN", default=None)

API_ID = config("API_ID", default=None)

API_HASH = config("API_HASH", default=None)

# db
SQLALCHEMY_DATABASE_URL = config(
    "SQLALCHEMY_DATABASE_URL", default="mysql+pymysql://root:jojo9900@127.0.0.1:3306/tribon"
)

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

LEARN_URL = config("LEARN_URL", cast=str, default="https://t.me/sokhanrani/1389")
