#!/usr/bin/env python3
"""
Script to update database schema for enhanced database connections.
Adds new columns to the database_connections table.
"""

import asyncio
import sys
from sqlalchemy import text
from src.core.database import engine

async def update_database_schema():
    """Update database schema with new columns."""
    
    # SQL commands to add new columns (SQLite compatible)
    alter_commands = [
        "ALTER TABLE database_connections ADD COLUMN last_tested TIMESTAMP;",
        "ALTER TABLE database_connections ADD COLUMN test_status VARCHAR(50);",
        "ALTER TABLE database_connections ADD COLUMN test_message TEXT;",
        "ALTER TABLE database_connections ADD COLUMN response_time_ms INTEGER;",
        "ALTER TABLE database_connections ADD COLUMN created_by VARCHAR(255);",
        "ALTER TABLE database_connections ADD COLUMN description TEXT;",
    ]
    
    # Index creation commands
    index_commands = [
        "CREATE INDEX IF NOT EXISTS idx_database_connections_test_status ON database_connections(test_status);",
        "CREATE INDEX IF NOT EXISTS idx_database_connections_last_tested ON database_connections(last_tested);",
    ]
    
    # Update existing records
    update_commands = [
        "UPDATE database_connections SET test_status = 'NotTested' WHERE test_status IS NULL;",
        "UPDATE database_connections SET created_by = 'existing_user' WHERE created_by IS NULL;",
    ]
    
    try:
        async with engine.begin() as conn:
            print("Updating database schema...")
            
            # Add columns (check if they exist first)
            for command in alter_commands:
                try:
                    await conn.execute(text(command))
                    print(f"✓ Executed: {command}")
                except Exception as e:
                    if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                        print(f"ℹ Column already exists: {command}")
                    else:
                        print(f"⚠ Warning for {command}: {e}")
            
            # Create indexes
            for command in index_commands:
                try:
                    await conn.execute(text(command))
                    print(f"✓ Executed: {command}")
                except Exception as e:
                    print(f"⚠ Warning for {command}: {e}")
            
            # Update existing records
            for command in update_commands:
                try:
                    result = await conn.execute(text(command))
                    print(f"✓ Executed: {command} (affected {result.rowcount} rows)")
                except Exception as e:
                    print(f"⚠ Warning for {command}: {e}")
            
            print("✅ Database schema update completed successfully!")
            
    except Exception as e:
        print(f"❌ Error updating database schema: {e}")
        sys.exit(1)
    
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(update_database_schema())
