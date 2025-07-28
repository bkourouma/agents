#!/usr/bin/env python3
"""
Check existing users in the database.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from sqlalchemy import text
from src.core.database import AsyncSessionLocal

async def check_users():
    """Check existing users in the database."""
    async with AsyncSessionLocal() as session:
        try:
            # Get all users
            result = await session.execute(text("""
                SELECT id, username, email, tenant_id, is_tenant_admin, is_active
                FROM users
            """))
            
            users = result.fetchall()
            
            print("👥 Existing users in database:")
            print("-" * 80)
            
            if not users:
                print("No users found in database.")
                return
            
            for user in users:
                print(f"ID: {user[0]}")
                print(f"Username: {user[1]}")
                print(f"Email: {user[2]}")
                print(f"Tenant ID: {user[3]}")
                print(f"Is Tenant Admin: {user[4]}")
                print(f"Is Active: {user[5]}")
                print("-" * 40)
            
            # Check tenants
            print("\n🏢 Existing tenants:")
            print("-" * 80)
            
            tenant_result = await session.execute(text("""
                SELECT id, name, slug, status, plan
                FROM tenants
            """))
            
            tenants = tenant_result.fetchall()
            
            for tenant in tenants:
                print(f"ID: {tenant[0]}")
                print(f"Name: {tenant[1]}")
                print(f"Slug: {tenant[2]}")
                print(f"Status: {tenant[3]}")
                print(f"Plan: {tenant[4]}")
                print("-" * 40)
                
        except Exception as e:
            print(f"Error checking users: {e}")

async def create_test_user():
    """Create a test user for testing."""
    async with AsyncSessionLocal() as session:
        try:
            # Get the default tenant ID
            tenant_result = await session.execute(text("""
                SELECT id FROM tenants WHERE slug = 'default' LIMIT 1
            """))
            tenant_row = tenant_result.fetchone()
            
            if not tenant_row:
                print("❌ No default tenant found. Please run the migration first.")
                return
            
            tenant_id = tenant_row[0]
            
            # Check if test user already exists
            user_result = await session.execute(text("""
                SELECT id FROM users WHERE username = 'testuser'
            """))
            
            if user_result.fetchone():
                print("✅ Test user 'testuser' already exists.")
                return
            
            # Create test user with hashed password
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            hashed_password = pwd_context.hash("testpass123")
            
            await session.execute(text("""
                INSERT INTO users (
                    tenant_id, email, username, full_name, hashed_password,
                    is_active, is_superuser, is_tenant_admin
                ) VALUES (
                    :tenant_id, :email, :username, :full_name, :hashed_password,
                    :is_active, :is_superuser, :is_tenant_admin
                )
            """), {
                "tenant_id": tenant_id,
                "email": "testuser@example.com",
                "username": "testuser",
                "full_name": "Test User",
                "hashed_password": hashed_password,
                "is_active": True,
                "is_superuser": False,
                "is_tenant_admin": True
            })
            
            await session.commit()
            print("✅ Created test user:")
            print("   Username: testuser")
            print("   Password: testpass123")
            print("   Email: testuser@example.com")
            print("   Tenant Admin: Yes")
            
        except Exception as e:
            print(f"Error creating test user: {e}")
            await session.rollback()

async def main():
    """Main function."""
    print("🔍 Checking database users and tenants...\n")
    
    await check_users()
    
    print("\n" + "="*80)
    print("🆕 Creating test user for multi-tenant testing...")
    await create_test_user()

if __name__ == "__main__":
    asyncio.run(main())
