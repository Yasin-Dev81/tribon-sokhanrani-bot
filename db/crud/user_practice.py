import datetime

from .conn import Connection


class UserPractice(Connection):
    def __init__(self) -> None:
        super().__init__()

    def add(self, user_id, file_link, practice_id, user_caption=None):
        cursor = self.conn.cursor()
        cursor.execute('INSERT INTO user_practice (user_id, file_link, practice_id, user_caption) VALUES (?, ?, ?, ?)', (user_id, file_link, practice_id, user_caption))
        self.conn.commit()
        new_id = cursor.lastrowid
        # self.conn.close()
        return new_id

    def delete(self, pk):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM user_practice WHERE id = ?', (pk,))
        self.conn.commit()
        # self.conn.close()

    def read(self, pk):
        cursor = self.conn.cursor()
        query = """
            SELECT *
            FROM user_practice up
            LEFT JOIN practice p ON p.id = up.practice_id
            WHERE up.id = ?
        """
        cursor.execute(query, (pk,))
        row = cursor.fetchone()
        # self.conn.close()
        return row

    def read_with_practice_id(self, practice_id):
        with self.conn:
            cursor = self.conn.cursor()
            query = """
                SELECT title, caption, user_caption, teacher_caption
                FROM user_practice up
                LEFT JOIN practice p ON p.id = up.practice_id
                WHERE practice_id = ?
            """
            cursor.execute(query, (practice_id,))
            row = cursor.fetchone()
            # self.conn.close()
            return row

    def set_teacher(self, pk, teacher_id):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('UPDATE user_practice SET teacher_id = ? WHERE id = ?', (teacher_id, pk))
            self.conn.commit()
            # self.conn.close()

    def set_teacher_caption(self, pk, teacher_caption):
        with self.conn:
            cursor = self.conn.cursor()
            cursor.execute('UPDATE user_practice SET teacher_caption = ? WHERE id = ?', (teacher_caption, pk))
            self.conn.commit()

    def update(self, pk, file_link, user_caption=None):
        with self.conn:
            cursor = self.conn.cursor()
            if user_caption is None:
                cursor.execute('UPDATE user_practice SET file_link = ? WHERE id = ?', (file_link, pk))
            else:
                cursor.execute('UPDATE user_practice SET file_link = ?, user_caption = ? WHERE id = ?', (file_link, user_caption, pk))
            self.conn.commit()
            # self.conn.close()
            return pk

    def read_with_teacher_tell_id(self, teacher_tell_id, practice_id=None, correction=False):
        with self.conn:
            cursor = self.conn.cursor()
            if practice_id:
                if correction:
                    query = """
                        SELECT *
                        FROM user_practice up
                        LEFT JOIN teacher t ON t.id = up.teacher_id
                        WHERE t.tell_id = ? AND up.practice_id = ? AND up.teacher_caption IS NOT NULL
                    """
                else:
                    query = """
                        SELECT *
                        FROM user_practice up
                        LEFT JOIN teacher t ON t.id = up.teacher_id
                        WHERE t.tell_id = ? AND up.teacher_caption IS NULL AND up.practice_id = ?
                    """
                cursor.execute(query, (teacher_tell_id, practice_id))
            else:
                if correction:
                    query = """
                        SELECT *
                        FROM user_practice up
                        LEFT JOIN teacher t ON t.id = up.teacher_id
                        WHERE t.tell_id = ? AND up.teacher_caption IS NOT NULL
                    """
                else:
                    query = """
                        SELECT *
                        FROM user_practice up
                        LEFT JOIN teacher t ON t.id = up.teacher_id
                        WHERE t.tell_id = ? AND up.teacher_caption IS NULL
                    """
                cursor.execute(query, (teacher_tell_id,))
            row = cursor.fetchall()
            # self.conn.close()
            return row

    def read_with_user_tell_id(self, user_tell_id):
        with self.conn:
            cursor = self.conn.cursor()
            query = """
                SELECT p.id, p.title
                FROM user_practice up
                LEFT JOIN user u ON u.id = up.user_id
                LEFT JOIN practice p ON p.id = up.practice_id
                WHERE u.tell_id = ?
            """
            cursor.execute(query, (user_tell_id,))
            row = cursor.fetchall()
            # self.conn.close()
            return row
