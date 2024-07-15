import datetime

from .conn import Connection


class User(Connection):
    def __init__(self) -> None:
        super().__init__()

    def add(self, phone_number, tell_id=None, chat_id=None):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO user (phone_number, tell_id, chat_id) VALUES (?, ?, ?)', (phone_number, tell_id, chat_id))
        self.conn.commit()
        # self.conn.close()

    def delete(self, pk):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM user WHERE id = ?', (pk,))
        self.conn.commit()
        # self.conn.close()

    def read(self, pk):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM user WHERE id = ?', (pk,))
        row = cursor.fetchone()
        # self.conn.close()
        return row

    def read_with_phone_number(self, phone_number):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM user WHERE phone_number = ?', (phone_number,))
        row = cursor.fetchone()
        # self.conn.close()
        return row

    def read_with_tell_id(self, tell_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT id FROM user WHERE tell_id = ?', (tell_id,))
        row = cursor.fetchone()
        # self.conn.close()
        return row

    def update(self, pk, tell_id, chat_id, name):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE user SET chat_id = ?, tell_id = ?, name = ? WHERE id = ?', (chat_id, tell_id, name, pk))
        self.conn.commit()
        # self.conn.close()

    def available_practice(self, pk):
        with self.conn:
            cursor = self.conn.cursor()
            now = datetime.datetime.now()
            query = """
            SELECT p.id, p.title, p.end_date
            FROM practice p
            JOIN user_practice up ON p.id = up.practice_id
            WHERE up.user_id = ?
            AND NOT EXISTS (
                SELECT 1
                FROM user_practice up2
                WHERE up2.practice_id = p.id
                AND up2.user_id = ?
                AND up2.file_link IS NOT NULL
            )
            ORDER BY p.end_date
            """
            cursor.execute(query, (pk, pk))
            return cursor.fetchall()

    def all(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM user')
        row = cursor.fetchall()
        # self.conn.close()
        return row

    def read_chat_id_user_with_user_practice_id(self, user_practice_id):
        with self.conn:
            cursor = self.conn.cursor()
            now = datetime.datetime.now()
            query = """
                SELECT chat_id
                FROM user_practice up
                JOIN user u ON u.id = up.user_id
                WHERE up.id = ?
            """
            cursor.execute(query, (user_practice_id, ))
            return cursor.fetchone()[0]
