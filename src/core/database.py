"""
Database configuration and session management for the AI Agent Platform.
Enhanced for PostgreSQL with multi-tenant support.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy.pool import QueuePool
from typing import AsyncGenerator, Generator, Optional
import os
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Database URL - PostgreSQL for production, SQLite for fallback
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_agent_platform")

# Fallback to SQLite if PostgreSQL is not available
FALLBACK_DATABASE_URL = "sqlite+aiosqlite:///./ai_agent_platform.db"

# Database configuration
DATABASE_POOL_SIZE = int(os.getenv("DATABASE_POOL_SIZE", "20"))
DATABASE_MAX_OVERFLOW = int(os.getenv("DATABASE_MAX_OVERFLOW", "30"))
DATABASE_POOL_TIMEOUT = int(os.getenv("DATABASE_POOL_TIMEOUT", "30"))
DATABASE_POOL_RECYCLE = int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))

def create_database_engine(database_url: str = None):
    """Create database engine with appropriate configuration."""
    url = database_url or DATABASE_URL

    # PostgreSQL configuration
    if url.startswith("postgresql"):
        return create_async_engine(
            url,
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            future=True,
            poolclass=QueuePool,
            pool_size=DATABASE_POOL_SIZE,
            max_overflow=DATABASE_MAX_OVERFLOW,
            pool_timeout=DATABASE_POOL_TIMEOUT,
            pool_recycle=DATABASE_POOL_RECYCLE,
            pool_pre_ping=True,
            connect_args={
                "server_settings": {
                    "application_name": "ai_agent_platform",
                    "jit": "off",  # Disable JIT for faster startup
                }
            }
        )

    # SQLite fallback configuration
    else:
        return create_async_engine(
            url,
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            future=True,
            pool_pre_ping=True,
            pool_recycle=300,
            connect_args={"check_same_thread": False}
        )

# Create async engine
try:
    engine = create_database_engine(DATABASE_URL)
    logger.info(f"Database engine created for: {DATABASE_URL.split('@')[0]}@***")
except Exception as e:
    logger.warning(f"Failed to create PostgreSQL engine, falling back to SQLite: {e}")
    engine = create_database_engine(FALLBACK_DATABASE_URL)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Tenant context for multi-tenant support
_tenant_context: Optional[str] = None

class Base(DeclarativeBase):
    """Base class for all database models with multi-tenant support."""
    pass


def set_tenant_context(tenant_id: str):
    """Set the current tenant context for database operations."""
    global _tenant_context
    _tenant_context = tenant_id


def get_tenant_context() -> Optional[str]:
    """Get the current tenant context."""
    return _tenant_context


def clear_tenant_context():
    """Clear the current tenant context."""
    global _tenant_context
    _tenant_context = None


@contextmanager
def tenant_context(tenant_id: str):
    """Context manager for tenant-aware database operations."""
    old_context = get_tenant_context()
    set_tenant_context(tenant_id)
    try:
        yield
    finally:
        if old_context:
            set_tenant_context(old_context)
        else:
            clear_tenant_context()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session with tenant context.
    """
    async with AsyncSessionLocal() as session:
        try:
            # Set tenant context in PostgreSQL session if available
            tenant_id = get_tenant_context()
            if tenant_id and DATABASE_URL.startswith("postgresql"):
                await session.execute(
                    f"SET LOCAL app.current_tenant_id = '{tenant_id}'"
                )
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def get_db_without_tenant() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session without tenant context.
    Used for system operations like tenant management.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def create_tables():
    """Create all database tables with PostgreSQL extensions."""
    async with engine.begin() as conn:
        # Enable PostgreSQL extensions if using PostgreSQL
        if DATABASE_URL.startswith("postgresql"):
            await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            await conn.execute('CREATE EXTENSION IF NOT EXISTS "pg_trgm"')
            logger.info("PostgreSQL extensions enabled")

        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created")


async def drop_tables():
    """Drop all database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        logger.info("Database tables dropped")


async def create_tenant_policies():
    """Create Row-Level Security policies for multi-tenant isolation."""
    if not DATABASE_URL.startswith("postgresql"):
        logger.info("RLS policies skipped - not using PostgreSQL")
        return

    async with engine.begin() as conn:
        # Enable RLS on tenant-aware tables
        tables_with_rls = [
            "users", "agents", "conversations", "conversation_messages",
            "database_tables", "database_columns", "query_history",
            "vanna_training_sessions", "vanna_training_data"
        ]

        for table in tables_with_rls:
            try:
                await conn.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
                await conn.execute(f"""
                    CREATE POLICY IF NOT EXISTS tenant_isolation_{table} ON {table}
                    USING (tenant_id = current_setting('app.current_tenant_id', true)::uuid)
                """)
                logger.info(f"RLS policy created for table: {table}")
            except Exception as e:
                logger.warning(f"Failed to create RLS policy for {table}: {e}")


async def test_connection():
    """Test database connection."""
    try:
        async with engine.begin() as conn:
            result = await conn.execute("SELECT 1")
            logger.info("Database connection successful")
            return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False
