#!/usr/bin/env python3
"""
Debug tenant ID type and format.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from sqlalchemy import text
from src.core.database import AsyncSessionLocal

async def debug_tenant_id():
    """Debug tenant ID format."""
    async with AsyncSessionLocal() as session:
        try:
            # Get tenant data directly
            result = await session.execute(text("""
                SELECT id, name, slug FROM tenants LIMIT 1
            """))
            
            tenant = result.fetchone()
            
            if tenant:
                print(f"Tenant ID: {tenant[0]}")
                print(f"Tenant ID type: {type(tenant[0])}")
                print(f"Tenant Name: {tenant[1]}")
                print(f"Tenant Slug: {tenant[2]}")
                
                # Try to query by ID
                tenant_id = str(tenant[0])
                print(f"\nTrying to query with ID: {tenant_id}")
                
                result2 = await session.execute(text("""
                    SELECT id, name FROM tenants WHERE id = :tenant_id
                """), {"tenant_id": tenant_id})
                
                tenant2 = result2.fetchone()
                if tenant2:
                    print("✅ Found tenant by string ID")
                else:
                    print("❌ Could not find tenant by string ID")
                
                # Try with UUID cast
                result3 = await session.execute(text("""
                    SELECT id, name FROM tenants WHERE id = CAST(:tenant_id AS UUID)
                """), {"tenant_id": tenant_id})
                
                tenant3 = result3.fetchone()
                if tenant3:
                    print("✅ Found tenant by UUID cast")
                else:
                    print("❌ Could not find tenant by UUID cast")
                    
            else:
                print("No tenants found")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_tenant_id())
