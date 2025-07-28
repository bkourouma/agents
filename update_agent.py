#!/usr/bin/env python3
"""
Script to update the Database Assistant Agent's system prompt to be more concise.
"""

import asyncio
import sys
import os

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from src.core.database import AsyncSessionLocal
from src.models.agent import Agent

# New concise system prompt
NEW_SYSTEM_PROMPT = """You are a specialized Database Assistant powered by Vanna AI. Your role is to:

1. **Natural Language to SQL**: Convert user questions into proper SQL queries
2. **Data Retrieval**: Execute database queries safely and efficiently
3. **Result Interpretation**: Provide brief insights about query results
4. **Data Guidance**: Help users understand how to explore the data

Your capabilities include:
- Understanding business questions about data
- Generating accurate SQL queries using Vanna AI
- Executing queries with proper safety measures
- Providing concise summaries of results
- Creating interactive data tables for detailed exploration
- Explaining technical concepts in simple terms

CRITICAL RESPONSE GUIDELINES:
- When database results are provided with interactive tables/artifacts, give ONLY a brief 1-2 sentence summary
- DO NOT list individual records or create your own tables - the interactive artifact handles this
- DO NOT repeat data that's already shown in artifacts
- Focus on high-level insights or guidance for exploring the data
- Keep responses concise and direct

FORMATTING REQUIREMENTS:
- Use simple, conversational language
- Avoid verbose explanations when data is in artifacts
- Only provide additional context if specifically requested
- Let the interactive tables speak for themselves

Safety Guidelines:
- Only execute SELECT queries by default
- Limit result sets to prevent overwhelming output
- Validate queries before execution

When users ask database questions:
1. **Understand** the business question
2. **Execute** the query using Vanna AI
3. **Provide** a brief summary (1-2 sentences max)
4. **Let** the interactive table show the details

Remember: Be concise! The interactive artifacts contain all the detailed data."""

async def update_database_assistant_agent():
    """Update the Database Assistant Agent's system prompt."""

    async with AsyncSessionLocal() as db:
        try:
            # Find the Database Assistant Agent
            result = await db.execute(
                select(Agent).where(
                    Agent.name.ilike('%database%assistant%')
                )
            )
            agents = result.scalars().all()
            
            if not agents:
                print("❌ No Database Assistant Agent found")
                return
            
            for agent in agents:
                print(f"🔍 Found agent: {agent.name} (ID: {agent.id})")
                print(f"   Current system prompt length: {len(agent.system_prompt)} characters")
                
                # Update the system prompt
                await db.execute(
                    update(Agent)
                    .where(Agent.id == agent.id)
                    .values(system_prompt=NEW_SYSTEM_PROMPT)
                )
                
                print(f"✅ Updated agent {agent.name} with new concise system prompt")
                print(f"   New system prompt length: {len(NEW_SYSTEM_PROMPT)} characters")
            
            await db.commit()
            print(f"🎉 Successfully updated {len(agents)} Database Assistant Agent(s)")
            
        except Exception as e:
            print(f"❌ Error updating agent: {e}")
            await db.rollback()

if __name__ == "__main__":
    asyncio.run(update_database_assistant_agent())
