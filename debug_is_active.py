#!/usr/bin/env python3
"""
Debug is_active field.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

from sqlalchemy import select
from src.core.database import AsyncSessionLocal
from src.models.tenant import Tenant

async def debug_is_active():
    """Debug is_active field."""
    async with AsyncSessionLocal() as session:
        try:
            tenant_id_str = "63b9ade1-0cac-44c0-8bec-dc3b2f13c0b3"
            
            # Get tenant and check is_active value
            result = await session.execute(
                select(Tenant).where(Tenant.id == tenant_id_str)
            )
            tenant = result.scalar_one_or_none()
            
            if tenant:
                print(f"Tenant found: {tenant.name}")
                print(f"is_active value: {tenant.is_active}")
                print(f"is_active type: {type(tenant.is_active)}")
                print(f"is_active == True: {tenant.is_active == True}")
                print(f"is_active is True: {tenant.is_active is True}")
                print(f"bool(is_active): {bool(tenant.is_active)}")
                
                # Test different comparisons
                print("\nTesting different is_active comparisons:")
                
                # Test 1: == True
                result1 = await session.execute(
                    select(Tenant).where(
                        Tenant.id == tenant_id_str,
                        Tenant.is_active == True
                    )
                )
                tenant1 = result1.scalar_one_or_none()
                print(f"is_active == True: {'Found' if tenant1 else 'Not found'}")
                
                # Test 2: is True
                result2 = await session.execute(
                    select(Tenant).where(
                        Tenant.id == tenant_id_str,
                        Tenant.is_active.is_(True)
                    )
                )
                tenant2 = result2.scalar_one_or_none()
                print(f"is_active.is_(True): {'Found' if tenant2 else 'Not found'}")
                
                # Test 3: == 1 (for SQLite boolean)
                result3 = await session.execute(
                    select(Tenant).where(
                        Tenant.id == tenant_id_str,
                        Tenant.is_active == 1
                    )
                )
                tenant3 = result3.scalar_one_or_none()
                print(f"is_active == 1: {'Found' if tenant3 else 'Not found'}")
                
                # Test 4: No filter
                result4 = await session.execute(
                    select(Tenant).where(Tenant.id == tenant_id_str)
                )
                tenant4 = result4.scalar_one_or_none()
                print(f"No is_active filter: {'Found' if tenant4 else 'Not found'}")
                
            else:
                print("Tenant not found")
                
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(debug_is_active())
