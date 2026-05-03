import sqlite3

DB_PATH = "habits.db"

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habits(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL,
            type TEXT DEFAULT 'good',
            icon TEXT DEFAULT '⭐',
            log_type TEXT DEFAULT 'boolean')
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS habit_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            logged_at TEXT NOT NULL,
            habit_id INTEGER NOT NULL,
            value REAL DEFAULT 1,
            FOREIGN KEY (habit_id) REFERENCES habits(id)
            )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS profile(
            id INTEGER PRIMARY KEY,
            name TEXT DEFAULT 'Habit Hero',
            pic TEXT DEFAULT '')
    """)

    cursor.execute("INSERT OR IGNORE INTO profile (id, name, pic) VALUES (1, 'Habit Hero', '')")

    # Safe migrations for existing databases
    try:
        cursor.execute("ALTER TABLE habits ADD COLUMN type TEXT DEFAULT 'good'")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE habits ADD COLUMN icon TEXT DEFAULT '⭐'")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE habits ADD COLUMN log_type TEXT DEFAULT 'boolean'")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE habit_logs ADD COLUMN value REAL DEFAULT 1")
    except Exception:
        pass    

    conn.commit()
    conn.close()