#!/usr/bin/env python3
"""Check the database for training sessions"""

import sqlite3
import json
from datetime import datetime

# Connect to the database
db_path = "ai_agent_platform.db"

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔍 Checking Vanna Training Sessions in Database...")
    print("=" * 60)
    
    # Check if the table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='vanna_training_sessions';")
    table_exists = cursor.fetchone()
    
    if not table_exists:
        print("❌ Table 'vanna_training_sessions' does not exist!")
        
        # List all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print("\n📋 Available tables:")
        for table in tables:
            print(f"  - {table[0]}")
    else:
        print("✅ Table 'vanna_training_sessions' exists")
        
        # Get table schema
        cursor.execute("PRAGMA table_info(vanna_training_sessions);")
        columns = cursor.fetchall()
        print("\n📋 Table Schema:")
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        # Count total records
        cursor.execute("SELECT COUNT(*) FROM vanna_training_sessions;")
        total_count = cursor.fetchone()[0]
        print(f"\n📊 Total training sessions: {total_count}")
        
        if total_count > 0:
            # Get recent sessions
            cursor.execute("""
                SELECT id, model_name, training_status, created_at, training_started_at, training_completed_at
                FROM vanna_training_sessions 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            sessions = cursor.fetchall()
            
            print("\n🕒 Recent Training Sessions:")
            print("-" * 80)
            for session in sessions:
                id_val, model_name, status, created_at, started_at, completed_at = session
                print(f"ID: {id_val}")
                print(f"  Model: {model_name}")
                print(f"  Status: {status}")
                print(f"  Created: {created_at}")
                print(f"  Started: {started_at}")
                print(f"  Completed: {completed_at}")
                print("-" * 40)
            
            # Check for today's sessions
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute("""
                SELECT COUNT(*) FROM vanna_training_sessions 
                WHERE DATE(created_at) = ?
            """, (today,))
            today_count = cursor.fetchone()[0]
            print(f"\n📅 Training sessions created today ({today}): {today_count}")
            
            if today_count > 0:
                cursor.execute("""
                    SELECT id, model_name, training_status, created_at
                    FROM vanna_training_sessions 
                    WHERE DATE(created_at) = ?
                    ORDER BY created_at DESC
                """, (today,))
                today_sessions = cursor.fetchall()
                
                print("\n🆕 Today's Sessions:")
                for session in today_sessions:
                    print(f"  ID {session[0]}: {session[1]} - {session[2]} ({session[3]})")
        
    conn.close()
    print("\n✅ Database check completed!")
    
except Exception as e:
    print(f"❌ Error checking database: {e}")
