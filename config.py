from decouple import config
from dotenv import load_dotenv

load_dotenv()


SQLALCHEMY_DATABASE_URL = config("SQLALCHEMY_DATABASE_URL", default="sqlite:///db.sqlite3")

ADMINS_LIST_ID = [713775832, 1024669168] # config("ADMINS_LIST_ID", default="sqlite:///db.sqlite3")
CHANEL_CHAT_ID = "-1002218177926"
GROUP_CHAT_ID = "-1002218303002"


PRACTICES_PER_PAGE = 5
