#!/usr/bin/env python3
"""
Check tenant status in database.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from sqlalchemy import text
from src.core.database import AsyncSessionLocal

async def check_tenant_status():
    """Check tenant status."""
    async with AsyncSessionLocal() as session:
        try:
            # Get all tenant data
            result = await session.execute(text("""
                SELECT id, name, slug, status, is_active FROM tenants
            """))
            
            tenants = result.fetchall()
            
            print("🏢 All tenants in database:")
            print("-" * 80)
            
            for tenant in tenants:
                print(f"ID: {tenant[0]}")
                print(f"Name: {tenant[1]}")
                print(f"Slug: {tenant[2]}")
                print(f"Status: {tenant[3]}")
                print(f"Is Active: {tenant[4]}")
                print("-" * 40)
                
                # Test the specific query that's failing
                tenant_id = str(tenant[0])
                print(f"Testing query for tenant {tenant_id}...")
                
                result2 = await session.execute(text("""
                    SELECT id, name FROM tenants 
                    WHERE id = :tenant_id AND is_active = true
                """), {"tenant_id": tenant_id})
                
                tenant2 = result2.fetchone()
                if tenant2:
                    print("✅ Found with is_active = true")
                else:
                    print("❌ NOT found with is_active = true")
                    
                    # Check without is_active filter
                    result3 = await session.execute(text("""
                        SELECT id, name, is_active FROM tenants 
                        WHERE id = :tenant_id
                    """), {"tenant_id": tenant_id})
                    
                    tenant3 = result3.fetchone()
                    if tenant3:
                        print(f"Found without is_active filter: is_active = {tenant3[2]}")
                    else:
                        print("Not found even without is_active filter")
                
                print()
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(check_tenant_status())
