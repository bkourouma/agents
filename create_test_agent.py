#!/usr/bin/env python3
"""
Create a test agent for the frontend to display.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database import AsyncSessionLocal
from src.models.user import User
from src.models.agent import Agent
from sqlalchemy import select

async def create_test_agent():
    """Create a test agent."""
    print("🤖 Creating test agent...")
    
    try:
        # Get database session
        async with AsyncSessionLocal() as db:
            # Get the test user
            result = await db.execute(select(User).where(User.username == "testuser"))
            user = result.scalar_one_or_none()
            
            if not user:
                print("❌ Test user not found")
                return
            
            print(f"✅ Found test user: {user.username}")
            
            # Check if test agent already exists
            result = await db.execute(
                select(Agent).where(
                    Agent.name == "Test Assistant",
                    Agent.owner_id == user.id
                )
            )
            existing_agent = result.scalar_one_or_none()
            
            if existing_agent:
                print("✅ Test agent already exists")
                return
            
            # Create test agent
            test_agent = Agent(
                name="Test Assistant",
                description="A helpful test assistant for demonstration purposes",
                agent_type="general",
                status="active",
                owner_id=user.id,
                tenant_id=user.tenant_id,
                system_prompt="You are a helpful assistant. Respond to user questions in a friendly and informative manner.",
                personality="Friendly and professional",
                instructions="Always be helpful and provide clear, concise answers.",
                llm_provider="openai",
                llm_model="gpt-3.5-turbo",
                temperature="0.7",
                max_tokens=1000,
                tools_config={},
                capabilities=["general_chat", "question_answering"],
                is_active=True,
                is_public=False,
                is_template=False,
                usage_count=0
            )
            
            db.add(test_agent)
            await db.commit()
            await db.refresh(test_agent)
            
            print(f"✅ Created test agent: {test_agent.name} (ID: {test_agent.id})")
            
    except Exception as e:
        print(f"❌ Error creating test agent: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(create_test_agent())
