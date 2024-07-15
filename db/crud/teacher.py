from .conn import Connection

class Teacher(Connection):
    def __init__(self) -> None:
        super().__init__()

    def add(self, tell_id, chat_id=None):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('INSERT INTO teacher (tell_id, chat_id) VALUES (?, ?)', (tell_id, chat_id))

    def delete(self, pk):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM teacher WHERE id = ?', (pk,))

    def read(self, pk):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT * FROM teacher WHERE id = ?', (pk,))
            return cursor.fetchone()

    def all(self):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM teacher')
        return cursor.fetchall()

    def read_with_tell_id(self, tell_id):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM teacher WHERE tell_id = ?', (tell_id,))
        return cursor.fetchone()

    def update_with_tell_id(self, tell_id, chat_id, name):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('UPDATE teacher SET chat_id = ?, name = ? WHERE tell_id = ?', (chat_id, name, tell_id))
