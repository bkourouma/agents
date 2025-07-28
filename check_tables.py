#!/usr/bin/env python3
import sqlite3
import os

def check_tables():
    db_path = "insurance.db"
    
    if not os.path.exists(db_path):
        print("Database file not found!")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("Existing tables:")
    for table in tables:
        print(f"  - {table}")
    
    conn.close()

if __name__ == "__main__":
    check_tables()
