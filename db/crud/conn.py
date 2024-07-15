import sqlite3
import threading


# Thread-local storage for the database connection
# thread_local = threading.local()


def get_db_connection():
    conn = sqlite3.connect('practice_db.sqlite')
    return conn

class Connection:
    thread_local = threading.local()
    # conn = sqlite3.connect('practice_db.sqlite')

    @property
    def conn(self):
        if not hasattr(self.thread_local, 'conn'):
            self.thread_local.conn = sqlite3.connect('practice_db.sqlite')
        return self.thread_local.conn
