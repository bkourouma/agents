#!/usr/bin/env python3
"""
Debug the agents query to see why it's not returning agents.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database import AsyncSessionLocal
from src.models.user import User
from src.models.agent import Agent
from sqlalchemy import select, and_

async def debug_agents_query():
    """Debug the agents query."""
    print("🔍 Debugging agents query...")
    
    try:
        # Get database session
        async with AsyncSessionLocal() as db:
            # Get the test user
            result = await db.execute(select(User).where(User.username == "testuser"))
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ Test user not found")
                return
            
            print(f"✅ Found test user: {user.username} (ID: {user.id}, Tenant: {user.tenant_id})")
            
            # Check all agents in database
            print("\n📋 All agents in database:")
            result = await db.execute(select(Agent))
            all_agents = result.scalars().all()
            
            for agent in all_agents:
                print(f"  - {agent.name} (ID: {agent.id}, Owner: {agent.owner_id}, Tenant: {agent.tenant_id}, Active: {agent.is_active})")
            
            # Test the exact query from AgentService
            print(f"\n🔍 Testing AgentService query for user {user.id} and tenant {user.tenant_id}:")
            query = select(Agent).where(
                and_(
                    Agent.owner_id == user.id,
                    Agent.tenant_id == user.tenant_id,
                    Agent.is_active == True
                )
            )
            
            result = await db.execute(query)
            filtered_agents = result.scalars().all()
            
            print(f"✅ Query returned {len(filtered_agents)} agents")
            for agent in filtered_agents:
                print(f"  - {agent.name} (ID: {agent.id}, Type: {agent.agent_type}, Status: {agent.status})")
            
            # Test individual conditions
            print(f"\n🧪 Testing individual conditions:")
            
            # Test owner_id condition
            result = await db.execute(select(Agent).where(Agent.owner_id == user.id))
            owner_agents = result.scalars().all()
            print(f"  - Agents with owner_id {user.id}: {len(owner_agents)}")
            
            # Test tenant_id condition
            result = await db.execute(select(Agent).where(Agent.tenant_id == user.tenant_id))
            tenant_agents = result.scalars().all()
            print(f"  - Agents with tenant_id {user.tenant_id}: {len(tenant_agents)}")
            
            # Test is_active condition
            result = await db.execute(select(Agent).where(Agent.is_active == True))
            active_agents = result.scalars().all()
            print(f"  - Active agents: {len(active_agents)}")
            
    except Exception as e:
        print(f"❌ Error debugging agents query: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_agents_query())
