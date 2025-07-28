#!/usr/bin/env python3
"""
Debug the orchestrator error step by step.
"""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database import AsyncSessionLocal
from src.models.user import User
from src.models.orchestrator import OrchestratorRequest
from src.orchestrator.llm_service import LLMOrchestratorService
from src.api.users import get_user_by_username
from sqlalchemy import select

async def debug_orchestrator_error():
    """Debug the orchestrator error step by step."""
    print("🔍 Debugging orchestrator error...")
    
    try:
        # Get database session
        async with AsyncSessionLocal() as db:
            # Get the test user
            user = await get_user_by_username(db, "testuser")
            
            if not user:
                print("❌ User not found")
                return
            
            print(f"✅ Found user: {user.username}")
            
            # Create orchestrator request
            request = OrchestratorRequest(
                message="la liste des transactions momoney?",
                context={}
            )
            
            print(f"✅ Created request: {request.message}")
            
            # Test the orchestrator service
            print("\n📋 Testing LLMOrchestratorService...")
            try:
                orchestrator = LLMOrchestratorService()
                print("✅ Orchestrator service created")
                
                # Call the process_message method
                print("📤 Calling process_message...")
                response = await orchestrator.process_message(db, user, request)
                
                print(f"✅ Response received!")
                print(f"   Type: {type(response)}")
                print(f"   Conversation ID: {response.conversation_id}")
                print(f"   Agent response: {response.agent_response[:100]}...")
                print(f"   Routing result: {response.routing_result}")
                
            except Exception as e:
                print(f"❌ Orchestrator error: {type(e).__name__}: {str(e)}")
                import traceback
                traceback.print_exc()
                
                # Try to identify where the error occurs
                print(f"\n🔍 Error details:")
                print(f"   Error type: {type(e)}")
                print(f"   Error message: {str(e)}")
                
                # Check if it's the specific NoneType error
                if "'NoneType' object has no attribute 'get'" in str(e):
                    print("   🎯 This is the NoneType.get() error we're looking for!")
                    
                    # Print the full traceback to identify the exact line
                    print("\n📋 Full traceback:")
                    traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_orchestrator_error())
