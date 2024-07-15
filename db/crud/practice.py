import datetime

from .conn import Connection


class Practice(Connection):
    def __init__(self) -> None:
        super().__init__()

    def add(self, title, caption, end_date, start_date=datetime.datetime.now()):
        # d - m - y
        if type(start_date) == str:
            start_date = datetime.datetime.strptime(start_date, "%d/%m/%Y")
        end_date = datetime.datetime.strptime(end_date, "%d/%m/%Y")

        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('INSERT INTO practice (title, caption, start_date, end_date) VALUES (?, ?, ?, ?)', (title, caption, start_date, end_date))

    def delete(self, pk):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('DELETE FROM practice WHERE id = ?', (pk,))

    def read(self, pk):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM practice WHERE id = ?', (pk,))
        return cursor.fetchone()

    def available(self):
        with self.conn:
            cursor = self.conn.cursor()
            current_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute('SELECT id, title FROM practice WHERE start_date <= ? AND end_date >= ?', (current_time, current_time))
            return cursor.fetchall()

    def all(self):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('SELECT id, title FROM practice')
            return cursor.fetchall()

    def report(self, pk):
        query = """
            SELECT p.title, p.caption, count(up.id) AS total_count, count(up.teacher_caption) AS teacher_caption_count
            FROM user_practice up
            LEFT JOIN practice p ON p.id = up.practice_id
            WHERE up.practice_id = ?
        """
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute(query, (pk, ))
            return cursor.fetchone()
