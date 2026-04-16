import sqlite3

def upgrade_database():
    print("🔧 Connecting to agent.db...")
    conn = sqlite3.connect('agent.db')
    cursor = conn.cursor()

    try:
        print("⚡ Adding 'is_pinned' column...")
        cursor.execute("ALTER TABLE chat_sessions ADD COLUMN is_pinned BOOLEAN DEFAULT 0;")
    except sqlite3.OperationalError:
        print("⚠️ 'is_pinned' already exists, skipping.")

    try:
        print("⚡ Adding 'is_archived' column...")
        cursor.execute("ALTER TABLE chat_sessions ADD COLUMN is_archived BOOLEAN DEFAULT 0;")
    except sqlite3.OperationalError:
        print("⚠️ 'is_archived' already exists, skipping.")

    conn.commit()
    conn.close()
    print("✅ Database upgrade complete! You can start your server now.")

if __name__ == "__main__":
    upgrade_database()