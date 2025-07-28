#!/usr/bin/env python3
"""
Migration script to add tenant_id columns to database chat tables.
"""

import sqlite3
import sys
import os

def migrate_database_chat_tables():
    """Add missing tenant_id columns to database chat tables."""
    print("🔄 Migrating database chat tables for multi-tenant support...")
    
    tables_to_migrate = [
        'database_tables',
        'database_columns', 
        'query_history',
        'vanna_training_sessions',
        'vanna_training_data',
        'data_import_sessions'
    ]
    
    try:
        # Connect to database
        conn = sqlite3.connect('ai_agent_platform.db')
        cursor = conn.cursor()
        
        for table_name in tables_to_migrate:
            print(f"\n📋 Checking table: {table_name}")
            
            # Check if table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                print(f"   ⚠️ Table {table_name} does not exist, skipping...")
                continue
            
            # Check current table structure
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            print(f"   Current columns: {len(column_names)} columns")
            
            # Add tenant_id column if missing
            if 'tenant_id' not in column_names:
                print(f"   ➕ Adding tenant_id column to {table_name}...")
                cursor.execute(f"""
                    ALTER TABLE {table_name} 
                    ADD COLUMN tenant_id TEXT NOT NULL DEFAULT '63b9ade1-0cac-44c0-8bec-dc3b2f13c0b3'
                """)
                print(f"   ✅ tenant_id column added to {table_name}")
            else:
                print(f"   ✅ tenant_id column already exists in {table_name}")
            
            # Create indexes for better performance
            try:
                cursor.execute(f"""
                    CREATE INDEX IF NOT EXISTS idx_{table_name}_tenant 
                    ON {table_name}(tenant_id)
                """)
                print(f"   📊 Index created for {table_name}")
            except Exception as e:
                print(f"   ⚠️ Index creation warning for {table_name}: {e}")
        
        # Commit changes
        conn.commit()
        
        # Verify the changes
        print(f"\n🔍 Verification:")
        for table_name in tables_to_migrate:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if cursor.fetchone():
                cursor.execute(f"PRAGMA table_info({table_name})")
                columns = cursor.fetchall()
                column_names = [col[1] for col in columns]
                has_tenant_id = 'tenant_id' in column_names
                print(f"   {table_name}: {'✅' if has_tenant_id else '❌'} tenant_id column")
                
                # Check record count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f"     Records: {count}")
        
        conn.close()
        print("\n🎉 Database chat tables migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = migrate_database_chat_tables()
    if not success:
        sys.exit(1)
