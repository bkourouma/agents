#!/usr/bin/env python3
"""
Create VannaTrainingData table migration
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.core.database import Base
from src.models.database_chat import VannaTrainingData
import os

async def create_training_data_table():
    """Create the VannaTrainingData table."""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./ai_agents.db")
    
    # Create async engine
    engine = create_async_engine(database_url, echo=True)
    
    try:
        # Create all tables
        async with engine.begin() as conn:
            # Create the VannaTrainingData table
            await conn.run_sync(Base.metadata.create_all)
            print("✅ VannaTrainingData table created successfully!")
            
    except Exception as e:
        print(f"❌ Error creating table: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_training_data_table())
