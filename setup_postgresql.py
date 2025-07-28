#!/usr/bin/env python3
"""
PostgreSQL setup and migration script for AI Agent Platform.
This script handles:
1. PostgreSQL database creation
2. Data migration from SQLite to PostgreSQL
3. Multi-tenant setup with default tenant
4. Row-Level Security configuration
"""

import asyncio
import os
import sys
import logging
import uuid
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

import asyncpg
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
import pandas as pd

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from src.core.database import (
    create_tables, 
    create_tenant_policies, 
    test_connection,
    DATABASE_URL,
    FALLBACK_DATABASE_URL
)
from src.models.tenant import Tenant, TenantStatus, TenantPlan

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PostgreSQLSetup:
    """PostgreSQL setup and migration manager."""
    
    def __init__(self):
        self.pg_url = DATABASE_URL
        self.sqlite_url = FALLBACK_DATABASE_URL
        self.default_tenant_id = uuid.uuid4()
        
    async def create_database_if_not_exists(self):
        """Create PostgreSQL database if it doesn't exist."""
        try:
            # Parse database URL to get connection details
            if not self.pg_url.startswith("postgresql"):
                logger.error("DATABASE_URL must be a PostgreSQL URL")
                return False
                
            # Extract database name and connection details
            url_parts = self.pg_url.replace("postgresql+asyncpg://", "").split("/")
            db_name = url_parts[-1]
            connection_base = "/".join(url_parts[:-1])
            
            # Connect to postgres database to create our database
            postgres_url = f"postgresql://{connection_base}/postgres"
            
            conn = await asyncpg.connect(postgres_url)
            
            # Check if database exists
            exists = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", db_name
            )
            
            if not exists:
                await conn.execute(f'CREATE DATABASE "{db_name}"')
                logger.info(f"Created database: {db_name}")
            else:
                logger.info(f"Database already exists: {db_name}")
                
            await conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to create database: {e}")
            return False
    
    async def setup_postgresql(self):
        """Set up PostgreSQL with tables and extensions."""
        try:
            logger.info("Setting up PostgreSQL...")
            
            # Test connection
            if not await test_connection():
                logger.error("Failed to connect to PostgreSQL")
                return False
            
            # Create tables
            await create_tables()
            logger.info("Database tables created")
            
            # Create RLS policies
            await create_tenant_policies()
            logger.info("Row-Level Security policies created")
            
            return True
            
        except Exception as e:
            logger.error(f"PostgreSQL setup failed: {e}")
            return False
    
    async def create_default_tenant(self):
        """Create a default tenant for existing data."""
        try:
            from src.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as session:
                # Check if default tenant already exists
                existing = await session.get(Tenant, self.default_tenant_id)
                if existing:
                    logger.info("Default tenant already exists")
                    return self.default_tenant_id
                
                # Create default tenant
                default_tenant = Tenant(
                    id=self.default_tenant_id,
                    name="Default Organization",
                    slug="default",
                    contact_email="admin@example.com",
                    status=TenantStatus.ACTIVE,
                    plan=TenantPlan.ENTERPRISE,
                    settings={
                        "theme": "light",
                        "language": "en",
                        "timezone": "UTC"
                    },
                    features=[
                        "database_chat",
                        "knowledge_base", 
                        "file_upload",
                        "custom_agents"
                    ],
                    max_users=100,
                    max_agents=50,
                    max_storage_mb=10000,
                    created_at=datetime.utcnow()
                )
                
                session.add(default_tenant)
                await session.commit()
                
                logger.info(f"Created default tenant: {self.default_tenant_id}")
                return self.default_tenant_id
                
        except Exception as e:
            logger.error(f"Failed to create default tenant: {e}")
            return None
    
    async def migrate_sqlite_data(self):
        """Migrate data from SQLite to PostgreSQL."""
        try:
            sqlite_path = "./ai_agent_platform.db"
            if not Path(sqlite_path).exists():
                logger.info("No SQLite database found, skipping migration")
                return True
            
            logger.info("Starting SQLite to PostgreSQL migration...")
            
            # Create sync engines for data migration
            sqlite_engine = create_engine(f"sqlite:///{sqlite_path}")
            pg_engine = create_async_engine(self.pg_url)
            
            # Tables to migrate (in dependency order)
            tables_to_migrate = [
                "users",
                "agents", 
                "conversations",
                "conversation_messages",
                "database_tables",
                "database_columns",
                "query_history"
            ]
            
            migrated_count = 0
            
            for table_name in tables_to_migrate:
                try:
                    # Read from SQLite
                    df = pd.read_sql_table(table_name, sqlite_engine)
                    
                    if df.empty:
                        logger.info(f"Table {table_name} is empty, skipping")
                        continue
                    
                    # Add tenant_id to all records (will be added to models later)
                    if 'tenant_id' not in df.columns:
                        df['tenant_id'] = str(self.default_tenant_id)
                    
                    # Convert datetime columns
                    datetime_columns = [col for col in df.columns if 'at' in col.lower()]
                    for col in datetime_columns:
                        if col in df.columns:
                            df[col] = pd.to_datetime(df[col], errors='coerce')
                    
                    # Write to PostgreSQL
                    async with pg_engine.begin() as conn:
                        # Use pandas to_sql with asyncpg
                        await conn.run_sync(
                            lambda sync_conn: df.to_sql(
                                table_name, 
                                sync_conn, 
                                if_exists='append', 
                                index=False,
                                method='multi'
                            )
                        )
                    
                    migrated_count += len(df)
                    logger.info(f"Migrated {len(df)} records from {table_name}")
                    
                except Exception as e:
                    logger.warning(f"Failed to migrate table {table_name}: {e}")
                    continue
            
            logger.info(f"Migration completed. Total records migrated: {migrated_count}")
            return True
            
        except Exception as e:
            logger.error(f"Data migration failed: {e}")
            return False
    
    async def verify_setup(self):
        """Verify PostgreSQL setup and data integrity."""
        try:
            from src.core.database import AsyncSessionLocal
            
            async with AsyncSessionLocal() as session:
                # Test basic queries
                result = await session.execute(text("SELECT version()"))
                pg_version = result.scalar()
                logger.info(f"PostgreSQL version: {pg_version}")
                
                # Check tenant table
                result = await session.execute(text("SELECT COUNT(*) FROM tenants"))
                tenant_count = result.scalar()
                logger.info(f"Tenants in database: {tenant_count}")
                
                # Check extensions
                result = await session.execute(text(
                    "SELECT extname FROM pg_extension WHERE extname IN ('uuid-ossp', 'pg_trgm')"
                ))
                extensions = [row[0] for row in result.fetchall()]
                logger.info(f"PostgreSQL extensions: {extensions}")
                
                return True
                
        except Exception as e:
            logger.error(f"Setup verification failed: {e}")
            return False


async def main():
    """Main setup function."""
    logger.info("Starting PostgreSQL setup for AI Agent Platform...")
    
    setup = PostgreSQLSetup()
    
    # Step 1: Create database
    if not await setup.create_database_if_not_exists():
        logger.error("Failed to create database")
        return False
    
    # Step 2: Setup PostgreSQL
    if not await setup.setup_postgresql():
        logger.error("Failed to setup PostgreSQL")
        return False
    
    # Step 3: Create default tenant
    tenant_id = await setup.create_default_tenant()
    if not tenant_id:
        logger.error("Failed to create default tenant")
        return False
    
    # Step 4: Migrate existing data
    if not await setup.migrate_sqlite_data():
        logger.error("Failed to migrate data")
        return False
    
    # Step 5: Verify setup
    if not await setup.verify_setup():
        logger.error("Setup verification failed")
        return False
    
    logger.info("✅ PostgreSQL setup completed successfully!")
    logger.info(f"Default tenant ID: {tenant_id}")
    logger.info("You can now start the application with PostgreSQL")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
