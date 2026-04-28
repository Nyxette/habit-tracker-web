import sqlite3

DB_PATH="habits.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn=get_connection()
    cursor=conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   name TEXT NOT NULL,
                   created_at TEXT NOT NULL)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_logs(
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   logged_at TEXT NOT NULL,
                   habit_id INTEGER NOT NULL,
                   FOREIGN KEY (habit_id) REFERENCES habits(id))
    """)

    conn.commit()
    conn.close()
