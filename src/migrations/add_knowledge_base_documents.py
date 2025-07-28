"""
Database migration to add knowledge base documents table.
Run this after updating the models.
"""

import asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
import os


async def create_knowledge_base_documents_table():
    """Create the knowledge_base_documents table."""

    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "postgresql+asyncpg://user:password@localhost/ai_agents")
    engine = create_async_engine(database_url)

    create_table_sql = """
    CREATE TABLE IF NOT EXISTS knowledge_base_documents (
        id SERIAL PRIMARY KEY,
        agent_id INTEGER NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
        title VARCHAR(500) NOT NULL,
        content TEXT NOT NULL,
        content_type VARCHAR(50) NOT NULL DEFAULT 'text',
        file_path VARCHAR(1000),
        content_hash VARCHAR(64) NOT NULL,
        doc_metadata TEXT,
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE
    );
    """

    create_indexes_sql = """
    CREATE INDEX IF NOT EXISTS idx_knowledge_base_documents_agent_id
    ON knowledge_base_documents(agent_id);

    CREATE INDEX IF NOT EXISTS idx_knowledge_base_documents_content_hash
    ON knowledge_base_documents(content_hash);

    CREATE INDEX IF NOT EXISTS idx_knowledge_base_documents_is_active
    ON knowledge_base_documents(is_active);

    CREATE INDEX IF NOT EXISTS idx_knowledge_base_documents_created_at
    ON knowledge_base_documents(created_at);
    """

    try:
        async with engine.begin() as conn:
            # Create table
            await conn.execute(text(create_table_sql))
            print("✓ Created knowledge_base_documents table")

            # Create indexes
            await conn.execute(text(create_indexes_sql))
            print("✓ Created indexes for knowledge_base_documents table")
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(create_knowledge_base_documents_table())
    print("Knowledge base documents table migration completed!")
