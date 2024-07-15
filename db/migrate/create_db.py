import sqlite3

DB_FILE = "practice_db.sqlite"


def create_database():
    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create the user table
    cursor.execute('''
        CREATE TABLE user (
            id INTEGER PRIMARY KEY,
            tell_id INTEGER,
            phone_number CHAR,
            chat_id INTEGER,
            name CHAR
        )
    ''')

    # Create the teacher table
    cursor.execute('''
        CREATE TABLE teacher (
            id INTEGER PRIMARY KEY,
            tell_id INTEGER,
            chat_id INTEGER,
            name CHAR
        )
    ''')

    # Create the practice table
    cursor.execute('''
        CREATE TABLE practice (
            id INTEGER PRIMARY KEY,
            title CHAR,
            caption TEXT,
            end_date DATETIME,
            start_date DATETIME
        )
    ''')

    # Create the user_practice table
    cursor.execute('''
        CREATE TABLE user_practice (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            user_caption TEXT,
            file_link TEXT,
            teacher_id INTEGER,
            practice_id INTEGER,
            teacher_caption TEXT,
            FOREIGN KEY(user_id) REFERENCES user(id),
            FOREIGN KEY(teacher_id) REFERENCES teacher(id),
            FOREIGN KEY(practice_id) REFERENCES practice(id)
        )
    ''')

    # Commit the changes and close the connection
    conn.commit()
    conn.close()

    print("Database and tables created successfully.")


if __name__ == "__main__":
    create_database()
