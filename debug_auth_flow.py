#!/usr/bin/env python3
"""
Debug the authentication flow to see what's happening.
"""

import asyncio
import sys
import os
import jwt
from datetime import datetime

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.database import AsyncSessionLocal
from src.models.user import User
from src.api.users import get_user_by_username, verify_token
from sqlalchemy import select

async def debug_auth_flow():
    """Debug the authentication flow."""
    print("🔍 Debugging authentication flow...")
    
    try:
        # Get database session
        async with AsyncSessionLocal() as db:
            # Test 1: Check user in database
            print("\n1. Checking user in database...")
            user = await get_user_by_username(db, "testuser")
            
            if user:
                print(f"✅ Found user: {user.username}")
                print(f"   ID: {user.id}")
                print(f"   Email: {user.email}")
                print(f"   Tenant ID: {user.tenant_id}")
                print(f"   Is Active: {user.is_active}")
                print(f"   Is Tenant Admin: {user.is_tenant_admin}")
                print(f"   Created: {user.created_at}")
                print(f"   Last Login: {user.last_login}")
            else:
                print("❌ User not found")
                return
            
            # Test 2: Create a test JWT token
            print("\n2. Testing JWT token creation and verification...")
            try:
                # Import the JWT functions
                from src.api.users import create_access_token
                
                # Create token
                token = create_access_token(data={"sub": user.username})
                print(f"✅ Created token: {token[:50]}...")
                
                # Verify token
                username = verify_token(token)
                print(f"✅ Verified token, username: {username}")
                
                if username == user.username:
                    print("✅ Token verification successful")
                else:
                    print(f"❌ Token verification mismatch: {username} != {user.username}")
                    
            except Exception as e:
                print(f"❌ JWT error: {e}")
                import traceback
                traceback.print_exc()
            
            # Test 3: Check user lookup with tenant context
            print("\n3. Testing user lookup with tenant context...")
            try:
                # Query user with tenant relationship
                result = await db.execute(
                    select(User).where(User.username == "testuser")
                )
                db_user = result.scalar_one_or_none()
                
                if db_user:
                    print(f"✅ Database user found: {db_user.username}")
                    print(f"   Tenant ID: {db_user.tenant_id}")
                    print(f"   Tenant ID type: {type(db_user.tenant_id)}")
                    
                    # Check if tenant exists
                    from src.models.tenant import Tenant
                    result = await db.execute(
                        select(Tenant).where(Tenant.id == db_user.tenant_id)
                    )
                    tenant = result.scalar_one_or_none()
                    
                    if tenant:
                        print(f"✅ Tenant found: {tenant.name}")
                        print(f"   Tenant Status: {tenant.status}")
                        print(f"   Tenant Active: {tenant.is_active}")
                    else:
                        print(f"❌ Tenant not found for ID: {db_user.tenant_id}")
                        
                else:
                    print("❌ User not found in database")
                    
            except Exception as e:
                print(f"❌ Database lookup error: {e}")
                import traceback
                traceback.print_exc()
            
            # Test 4: Test the get_current_user_from_token function simulation
            print("\n4. Simulating get_current_user_from_token...")
            try:
                # This simulates what happens in the API
                token = create_access_token(data={"sub": user.username})
                username = verify_token(token)
                api_user = await get_user_by_username(db, username)
                
                if api_user:
                    print(f"✅ API user lookup successful: {api_user.username}")
                    print(f"   API User ID: {api_user.id}")
                    print(f"   API User Tenant: {api_user.tenant_id}")
                    
                    # Compare with original user
                    if api_user.id == user.id and api_user.tenant_id == user.tenant_id:
                        print("✅ API user matches original user")
                    else:
                        print("❌ API user doesn't match original user")
                        print(f"   Original: ID={user.id}, Tenant={user.tenant_id}")
                        print(f"   API: ID={api_user.id}, Tenant={api_user.tenant_id}")
                else:
                    print("❌ API user lookup failed")
                    
            except Exception as e:
                print(f"❌ API simulation error: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_auth_flow())
