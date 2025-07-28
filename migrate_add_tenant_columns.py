#!/usr/bin/env python3
"""
Migration script to add tenant_id and is_tenant_admin columns to existing database.
This script handles the migration from non-multi-tenant to multi-tenant schema.
"""

import asyncio
import sys
import logging
import uuid
from pathlib import Path
from datetime import datetime

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from sqlalchemy import text
from src.core.database import AsyncSessionLocal, engine
from src.models.tenant import Tenant, TenantStatus, TenantPlan

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_column_exists(session, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table."""
    try:
        # Try PostgreSQL first
        try:
            result = await session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = :table_name AND column_name = :column_name
            """), {"table_name": table_name, "column_name": column_name})
            return result.fetchone() is not None
        except:
            # Fallback to SQLite
            result = await session.execute(text(f"PRAGMA table_info({table_name})"))
            columns = result.fetchall()
            return any(col[1] == column_name for col in columns)
    except Exception as e:
        logger.error(f"Error checking column existence: {e}")
        return False

async def add_tenant_columns():
    """Add tenant_id and is_tenant_admin columns to users table."""
    async with AsyncSessionLocal() as session:
        try:
            # Check if tenant_id column exists
            tenant_id_exists = await check_column_exists(session, "users", "tenant_id")
            is_tenant_admin_exists = await check_column_exists(session, "users", "is_tenant_admin")
            
            if tenant_id_exists and is_tenant_admin_exists:
                logger.info("Tenant columns already exist. No migration needed.")
                return True
            
            logger.info("Adding tenant columns to users table...")
            
            # Add tenant_id column if it doesn't exist
            if not tenant_id_exists:
                logger.info("Adding tenant_id column...")
                try:
                    # Try PostgreSQL syntax first
                    await session.execute(text("""
                        ALTER TABLE users
                        ADD COLUMN tenant_id UUID
                    """))

                    # Add foreign key constraint (PostgreSQL)
                    await session.execute(text("""
                        ALTER TABLE users
                        ADD CONSTRAINT fk_users_tenant_id
                        FOREIGN KEY (tenant_id) REFERENCES tenants(id)
                    """))
                except:
                    # Fallback to SQLite syntax
                    await session.execute(text("""
                        ALTER TABLE users
                        ADD COLUMN tenant_id TEXT
                    """))

                # Add index (works for both PostgreSQL and SQLite)
                try:
                    await session.execute(text("""
                        CREATE INDEX idx_users_tenant_id ON users(tenant_id)
                    """))
                except:
                    logger.warning("Index creation failed (may already exist)")
            
            # Add is_tenant_admin column if it doesn't exist
            if not is_tenant_admin_exists:
                logger.info("Adding is_tenant_admin column...")
                await session.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN is_tenant_admin BOOLEAN DEFAULT FALSE NOT NULL
                """))
            
            await session.commit()
            logger.info("Successfully added tenant columns to users table.")
            return True
            
        except Exception as e:
            logger.error(f"Error adding tenant columns: {e}")
            await session.rollback()
            return False

async def create_default_tenant():
    """Create a default tenant for existing users."""
    async with AsyncSessionLocal() as session:
        try:
            # Check if default tenant already exists
            result = await session.execute(text("""
                SELECT id FROM tenants WHERE slug = 'default'
            """))
            existing_tenant = result.fetchone()
            
            if existing_tenant:
                default_tenant_id = existing_tenant[0]
                logger.info(f"Default tenant already exists with ID: {default_tenant_id}")
            else:
                # Create default tenant
                default_tenant_id = str(uuid.uuid4())
                logger.info("Creating default tenant...")
                
                await session.execute(text("""
                    INSERT INTO tenants (
                        id, name, slug, contact_email, status, plan, 
                        settings, features, tenant_metadata,
                        max_users, max_agents, max_storage_mb,
                        created_at, is_active
                    ) VALUES (
                        :id, :name, :slug, :contact_email, :status, :plan,
                        :settings, :features, :tenant_metadata,
                        :max_users, :max_agents, :max_storage_mb,
                        :created_at, :is_active
                    )
                """), {
                    "id": default_tenant_id,
                    "name": "Default Tenant",
                    "slug": "default",
                    "contact_email": "admin@example.com",
                    "status": TenantStatus.ACTIVE.value,
                    "plan": TenantPlan.FREE.value,
                    "settings": "{}",
                    "features": "[]",
                    "tenant_metadata": "{}",
                    "max_users": 10,
                    "max_agents": 5,
                    "max_storage_mb": 1024,
                    "created_at": datetime.utcnow(),
                    "is_active": True
                })
                
                logger.info(f"Created default tenant with ID: {default_tenant_id}")
            
            # Update existing users to use default tenant
            result = await session.execute(text("""
                UPDATE users 
                SET tenant_id = :tenant_id 
                WHERE tenant_id IS NULL
            """), {"tenant_id": default_tenant_id})
            
            updated_count = result.rowcount
            logger.info(f"Updated {updated_count} users to use default tenant.")
            
            # Make the first user a tenant admin
            await session.execute(text("""
                UPDATE users 
                SET is_tenant_admin = TRUE 
                WHERE id = (SELECT MIN(id) FROM users WHERE tenant_id = :tenant_id)
            """), {"tenant_id": default_tenant_id})
            
            await session.commit()
            logger.info("Successfully created default tenant and updated users.")
            return True
            
        except Exception as e:
            logger.error(f"Error creating default tenant: {e}")
            await session.rollback()
            return False

async def add_tenant_indexes():
    """Add tenant-aware indexes to improve performance."""
    async with AsyncSessionLocal() as session:
        try:
            logger.info("Adding tenant-aware indexes...")
            
            # Add unique constraints for email and username within tenant
            indexes_to_create = [
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_tenant_email ON users(tenant_id, email)",
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_tenant_username ON users(tenant_id, username)",
                "CREATE INDEX IF NOT EXISTS idx_users_tenant_active ON users(tenant_id, is_active)",
                "CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)"
            ]
            
            for index_sql in indexes_to_create:
                try:
                    await session.execute(text(index_sql))
                    logger.info(f"Created index: {index_sql.split()[-1]}")
                except Exception as e:
                    logger.warning(f"Index creation failed (may already exist): {e}")
            
            await session.commit()
            logger.info("Successfully added tenant-aware indexes.")
            return True
            
        except Exception as e:
            logger.error(f"Error adding indexes: {e}")
            await session.rollback()
            return False

async def main():
    """Run the complete migration process."""
    logger.info("🚀 Starting multi-tenant migration...")
    
    try:
        # Step 1: Add tenant columns to users table
        logger.info("Step 1: Adding tenant columns...")
        if not await add_tenant_columns():
            logger.error("Failed to add tenant columns. Aborting migration.")
            return False
        
        # Step 2: Create default tenant and assign users
        logger.info("Step 2: Creating default tenant...")
        if not await create_default_tenant():
            logger.error("Failed to create default tenant. Aborting migration.")
            return False
        
        # Step 3: Add tenant-aware indexes
        logger.info("Step 3: Adding tenant-aware indexes...")
        if not await add_tenant_indexes():
            logger.error("Failed to add indexes. Migration partially complete.")
            return False
        
        logger.info("✅ Multi-tenant migration completed successfully!")
        logger.info("🎉 Your database is now multi-tenant ready!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎉 Migration completed successfully!")
        print("You can now restart your application with multi-tenant support.")
    else:
        print("\n❌ Migration failed!")
        print("Please check the logs and fix any issues before retrying.")
        sys.exit(1)
