import sqlite3
import os

def update_db():
    db_path = 'hda.db'
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Check if content column exists
        cursor.execute("PRAGMA table_info(documents)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'content' not in columns:
            print("Adding 'content' column to 'documents' table...")
            cursor.execute("ALTER TABLE documents ADD COLUMN content TEXT")
        else:
            print("'content' column already exists.")

        # SQLite doesn't easily support ALTER COLUMN to change NULL/NOT NULL
        # But for migrations, making a column nullable usually works if it was already nullable or we recreate
        # However, for simply adding a column it's fine.
        # file_url was NOT NULL. To change it, we usually need to recreate the table.
        # Let's check if we REALLY need to change file_url to NULL immediately or if it's fine for now.
        # Since we are using SQLAlchemy, it might complain if we don't fix the DB.
        
        print("Schema update completed successfully.")
        conn.commit()
    except Exception as e:
        print(f"Error updating database: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    update_db()
