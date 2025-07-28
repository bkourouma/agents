#!/usr/bin/env python3
"""
Migration script to add tenant_id column to conversations table.
"""

import sqlite3
import sys
import os

def migrate_conversations_table():
    """Add missing tenant_id column to conversations table."""
    print("🔄 Migrating conversations table for multi-tenant support...")
    
    try:
        # Connect to database
        conn = sqlite3.connect('ai_agent_platform.db')
        cursor = conn.cursor()
        
        # Check current table structure
        cursor.execute("PRAGMA table_info(conversations)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Current columns: {column_names}")
        
        # Add tenant_id column if missing
        if 'tenant_id' not in column_names:
            print("➕ Adding tenant_id column...")
            cursor.execute("""
                ALTER TABLE conversations 
                ADD COLUMN tenant_id TEXT NOT NULL DEFAULT '63b9ade1-0cac-44c0-8bec-dc3b2f13c0b3'
            """)
            print("✅ tenant_id column added")
        else:
            print("✅ tenant_id column already exists")
        
        # Create indexes for better performance
        print("📊 Creating indexes...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_tenant_user 
                ON conversations(tenant_id, user_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_tenant_created 
                ON conversations(tenant_id, created_at)
            """)
            print("✅ Indexes created")
        except Exception as e:
            print(f"⚠️ Index creation warning: {e}")
        
        # Commit changes
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(conversations)")
        new_columns = cursor.fetchall()
        new_column_names = [col[1] for col in new_columns]
        
        print(f"📋 Updated columns: {new_column_names}")
        
        # Check if we have any conversations
        cursor.execute("SELECT COUNT(*) FROM conversations")
        conversation_count = cursor.fetchone()[0]
        print(f"📊 Total conversations in database: {conversation_count}")
        
        conn.close()
        print("🎉 Conversations table migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = migrate_conversations_table()
    if not success:
        sys.exit(1)
