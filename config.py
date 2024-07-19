from decouple import config
from dotenv import load_dotenv

load_dotenv()

TELL_CONFIG = config("TELL_CONFIG", default="/var/lib/tribon_sokhanrani/tribon_sokhanrani")

SQLALCHEMY_DATABASE_URL = config("SQLALCHEMY_DATABASE_URL", default="sqlite:///db.sqlite3")

ADMINS_LIST_ID = [713775832, 1024669168]
# ADMINS_LIST_ID = config(
#     'ADMINS_LIST_ID',
#     default="",
#     cast=lambda v: [int(i) for i in filter(str.isdigit, (s.strip() for s in v.split(',')))]
# )

CHANEL_CHAT_ID = config("CHANEL_CHAT_ID", default="-1002218177926")
GROUP_CHAT_ID = config("GROUP_CHAT_ID", default="-1002218303002")


PRACTICES_PER_PAGE = config("PRACTICES_PER_PAGE", cast=int, default=5)
