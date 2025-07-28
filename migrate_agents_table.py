#!/usr/bin/env python3
"""
Migration script to add tenant_id and is_active columns to agents table.
"""

import sqlite3
import sys
import os

def migrate_agents_table():
    """Add missing columns to agents table."""
    print("🔄 Migrating agents table for multi-tenant support...")
    
    try:
        # Connect to database
        conn = sqlite3.connect('ai_agent_platform.db')
        cursor = conn.cursor()
        
        # Check current table structure
        cursor.execute("PRAGMA table_info(agents)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Current columns: {column_names}")
        
        # Add tenant_id column if missing
        if 'tenant_id' not in column_names:
            print("➕ Adding tenant_id column...")
            cursor.execute("""
                ALTER TABLE agents 
                ADD COLUMN tenant_id TEXT NOT NULL DEFAULT '63b9ade1-0cac-44c0-8bec-dc3b2f13c0b3'
            """)
            print("✅ tenant_id column added")
        else:
            print("✅ tenant_id column already exists")
        
        # Add is_active column if missing
        if 'is_active' not in column_names:
            print("➕ Adding is_active column...")
            cursor.execute("""
                ALTER TABLE agents 
                ADD COLUMN is_active BOOLEAN NOT NULL DEFAULT 1
            """)
            print("✅ is_active column added")
        else:
            print("✅ is_active column already exists")
        
        # Create indexes for better performance
        print("📊 Creating indexes...")
        try:
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_agents_tenant_owner 
                ON agents(tenant_id, owner_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_agents_tenant_active 
                ON agents(tenant_id, is_active)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_agents_tenant_type 
                ON agents(tenant_id, agent_type)
            """)
            print("✅ Indexes created")
        except Exception as e:
            print(f"⚠️ Index creation warning: {e}")
        
        # Commit changes
        conn.commit()
        
        # Verify the changes
        cursor.execute("PRAGMA table_info(agents)")
        new_columns = cursor.fetchall()
        new_column_names = [col[1] for col in new_columns]
        
        print(f"📋 Updated columns: {new_column_names}")
        
        # Check if we have any agents
        cursor.execute("SELECT COUNT(*) FROM agents")
        agent_count = cursor.fetchone()[0]
        print(f"📊 Total agents in database: {agent_count}")
        
        conn.close()
        print("🎉 Agents table migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = migrate_agents_table()
    if not success:
        sys.exit(1)
