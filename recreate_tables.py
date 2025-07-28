#!/usr/bin/env python3
"""
Script to recreate database tables with the latest schema
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine
from src.migrations.create_insurance_tables import Base

DATABASE_URL = "sqlite+aiosqlite:///./ai_agent_platform.db"

async def recreate_tables():
    """Recreate all tables with the latest schema"""
    
    print("🔄 Recreating database tables...")
    
    # Create async engine
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        # Drop all tables
        print("🗑️ Dropping existing tables...")
        await conn.run_sync(Base.metadata.drop_all)
        
        # Create all tables
        print("🏗️ Creating tables with latest schema...")
        await conn.run_sync(Base.metadata.create_all)
    
    await engine.dispose()
    print("✅ Tables recreated successfully!")

if __name__ == "__main__":
    asyncio.run(recreate_tables())
