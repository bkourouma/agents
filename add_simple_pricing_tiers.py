#!/usr/bin/env python3
"""
Script to add simple pricing tiers for insurance products
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from src.migrations.create_insurance_tables import (
    InsuranceProduct, PricingTier
)

DATABASE_URL = "sqlite+aiosqlite:///./ai_agent_platform.db"

async def add_simple_pricing_tiers():
    """Add simple pricing tiers for all products"""
    
    # Create async engine and session
    engine = create_async_engine(DATABASE_URL, echo=True)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get all products
        result = await session.execute(select(InsuranceProduct))
        products = result.scalars().all()
        
        print(f"Found {len(products)} products")
        
        for product in products:
            print(f"\nProcessing product: {product.name} ({product.product_type})")
            
            # Check if pricing tiers already exist
            existing_tiers = await session.execute(
                select(PricingTier).where(PricingTier.product_id == product.id)
            )
            existing_count = len(existing_tiers.scalars().all())
            
            if existing_count > 0:
                print(f"  - {existing_count} pricing tiers already exist for {product.name}")
                continue
            
            # Add simple pricing tiers based on product type
            if product.product_type == 'life':
                # Life insurance tiers (amounts in XOF)
                tiers = [
                    {
                        'tier_name': 'Niveau 1',
                        'coverage_amount': 30000000,  # 30M XOF (~45k EUR)
                        'base_premium': 720000,  # 720k XOF annual premium
                    },
                    {
                        'tier_name': 'Niveau 2',
                        'coverage_amount': 65000000,  # 65M XOF (~100k EUR)
                        'base_premium': 1300000,  # 1.3M XOF annual premium
                    },
                    {
                        'tier_name': 'Niveau 3',
                        'coverage_amount': 165000000,  # 165M XOF (~250k EUR)
                        'base_premium': 2700000,  # 2.7M XOF annual premium
                    }
                ]
            elif product.product_type == 'auto':
                # Auto insurance tiers (amounts in XOF)
                tiers = [
                    {
                        'tier_name': 'Essentiel',
                        'coverage_amount': 10000000,  # 10M XOF
                        'base_premium': 480000,  # 480k XOF annual premium
                    },
                    {
                        'tier_name': 'Confort',
                        'coverage_amount': 32000000,  # 32M XOF
                        'base_premium': 720000,  # 720k XOF annual premium
                    },
                    {
                        'tier_name': 'Premium',
                        'coverage_amount': 65000000,  # 65M XOF
                        'base_premium': 1080000,  # 1.08M XOF annual premium
                    }
                ]
            elif product.product_type == 'health':
                # Health insurance tiers (amounts in XOF)
                tiers = [
                    {
                        'tier_name': 'Base',
                        'coverage_amount': 16000000,  # 16M XOF
                        'base_premium': 360000,  # 360k XOF annual premium
                    },
                    {
                        'tier_name': 'Confort',
                        'coverage_amount': 49000000,  # 49M XOF
                        'base_premium': 720000,  # 720k XOF annual premium
                    },
                    {
                        'tier_name': 'Premium',
                        'coverage_amount': 98000000,  # 98M XOF
                        'base_premium': 1440000,  # 1.44M XOF annual premium
                    }
                ]
            elif product.product_type == 'home':
                # Home insurance tiers (amounts in XOF)
                tiers = [
                    {
                        'tier_name': 'Standard',
                        'coverage_amount': 65000000,  # 65M XOF
                        'base_premium': 240000,  # 240k XOF annual premium
                    },
                    {
                        'tier_name': 'Confort',
                        'coverage_amount': 195000000,  # 195M XOF
                        'base_premium': 480000,  # 480k XOF annual premium
                    },
                    {
                        'tier_name': 'Premium',
                        'coverage_amount': 390000000,  # 390M XOF
                        'base_premium': 840000,  # 840k XOF annual premium
                    }
                ]
            else:
                # Default tiers for other types (amounts in XOF)
                tiers = [
                    {
                        'tier_name': 'Standard',
                        'coverage_amount': 32000000,  # 32M XOF
                        'base_premium': 600000,  # 600k XOF annual premium
                    },
                    {
                        'tier_name': 'Premium',
                        'coverage_amount': 65000000,  # 65M XOF
                        'base_premium': 1080000,  # 1.08M XOF annual premium
                    }
                ]
            
            # Add pricing tiers
            for tier_data in tiers:
                tier = PricingTier(
                    product_id=product.id,
                    tier_name=tier_data['tier_name'],
                    coverage_amount=tier_data['coverage_amount'],
                    base_premium=tier_data['base_premium'],
                    premium_frequency='annual'
                )
                session.add(tier)
                print(f"  - Added tier: {tier_data['tier_name']} ({tier_data['coverage_amount']:,} XOF coverage, {tier_data['base_premium']:,} XOF premium)")
        
        # Commit all changes
        await session.commit()
        print(f"\n✅ Successfully added pricing tiers for all products!")

if __name__ == "__main__":
    asyncio.run(add_simple_pricing_tiers())
