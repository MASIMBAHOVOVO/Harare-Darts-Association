import sqlite3
import os

def check_schema():
    db_path = 'hda.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(documents)")
    cols = cursor.fetchall()
    for col in cols:
        print(f"ID: {col[0]}, Name: {col[1]}, Type: {col[2]}, NotNull: {col[3]}, Default: {col[4]}, PK: {col[5]}")
    conn.close()

if __name__ == "__main__":
    check_schema()
