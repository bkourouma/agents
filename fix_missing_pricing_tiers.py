#!/usr/bin/env python3
"""
Script to add missing pricing tiers for all products
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from src.migrations.create_insurance_tables import (
    InsuranceProduct, PricingTier, PricingFactor
)

DATABASE_URL = "sqlite+aiosqlite:///./ai_agent_platform.db"

async def fix_missing_pricing_tiers():
    """Add pricing tiers for products that don't have any"""
    
    print("🔧 Fixing missing pricing tiers...")
    
    # Create async engine and session
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Get all products
        result = await session.execute(select(InsuranceProduct))
        products = result.scalars().all()
        
        print(f"Found {len(products)} products")
        
        for product in products:
            print(f"\nChecking product: {product.name} ({product.product_type})")
            
            # Check if pricing tiers exist
            existing_tiers = await session.execute(
                select(PricingTier).where(PricingTier.product_id == product.id)
            )
            existing_count = len(existing_tiers.scalars().all())
            
            if existing_count > 0:
                print(f"  ✅ {existing_count} pricing tiers already exist")
                continue
            
            print(f"  ⚠️ No pricing tiers found, adding default tiers...")
            
            # Add default pricing tiers based on product type
            if product.product_type == 'life':
                tiers = [
                    {'tier_name': 'Niveau 1', 'coverage_amount': 30000000, 'base_premium': 720000},
                    {'tier_name': 'Niveau 2', 'coverage_amount': 65000000, 'base_premium': 1300000},
                    {'tier_name': 'Niveau 3', 'coverage_amount': 165000000, 'base_premium': 2700000}
                ]
            elif product.product_type == 'auto':
                tiers = [
                    {'tier_name': 'Essentiel', 'coverage_amount': 10000000, 'base_premium': 480000},
                    {'tier_name': 'Confort', 'coverage_amount': 32000000, 'base_premium': 720000},
                    {'tier_name': 'Premium', 'coverage_amount': 65000000, 'base_premium': 1080000}
                ]
            elif product.product_type == 'health':
                tiers = [
                    {'tier_name': 'Base', 'coverage_amount': 16000000, 'base_premium': 360000},
                    {'tier_name': 'Confort', 'coverage_amount': 49000000, 'base_premium': 720000},
                    {'tier_name': 'Premium', 'coverage_amount': 98000000, 'base_premium': 1440000}
                ]
            elif product.product_type == 'home':
                tiers = [
                    {'tier_name': 'Standard', 'coverage_amount': 65000000, 'base_premium': 240000},
                    {'tier_name': 'Confort', 'coverage_amount': 195000000, 'base_premium': 480000},
                    {'tier_name': 'Premium', 'coverage_amount': 390000000, 'base_premium': 840000}
                ]
            else:
                # Default tiers for other types
                tiers = [
                    {'tier_name': 'Standard', 'coverage_amount': 32000000, 'base_premium': 600000},
                    {'tier_name': 'Premium', 'coverage_amount': 65000000, 'base_premium': 1080000}
                ]
            
            # Add pricing tiers
            for tier_data in tiers:
                tier = PricingTier(
                    product_id=product.id,
                    tier_name=tier_data['tier_name'],
                    coverage_amount=tier_data['coverage_amount'],
                    base_premium=tier_data['base_premium'],
                    premium_frequency='annual',
                    currency='XOF'
                )
                session.add(tier)
                print(f"    + {tier_data['tier_name']}: {tier_data['coverage_amount']:,} XOF -> {tier_data['base_premium']:,} XOF/an")
            
            # Check if pricing factors exist
            existing_factors = await session.execute(
                select(PricingFactor).where(PricingFactor.product_id == product.id)
            )
            existing_factors_count = len(existing_factors.scalars().all())
            
            if existing_factors_count == 0:
                print(f"  ⚠️ No pricing factors found, adding default factors...")
                
                # Add default pricing factors
                factors = [
                    {'factor_name': 'Âge 18-30', 'factor_type': 'age', 'factor_value': '18-30', 'multiplier': 1.2},
                    {'factor_name': 'Âge 31-45', 'factor_type': 'age', 'factor_value': '31-45', 'multiplier': 1.0},
                    {'factor_name': 'Âge 46-65', 'factor_type': 'age', 'factor_value': '46-65', 'multiplier': 1.1},
                    {'factor_name': 'Âge 66+', 'factor_type': 'age', 'factor_value': '66+', 'multiplier': 1.3},
                    {'factor_name': 'Risque faible', 'factor_type': 'risk_profile', 'factor_value': 'low', 'multiplier': 0.9},
                    {'factor_name': 'Risque moyen', 'factor_type': 'risk_profile', 'factor_value': 'medium', 'multiplier': 1.0},
                    {'factor_name': 'Risque élevé', 'factor_type': 'risk_profile', 'factor_value': 'high', 'multiplier': 1.4}
                ]
                
                for factor_data in factors:
                    factor = PricingFactor(
                        product_id=product.id,
                        factor_name=factor_data['factor_name'],
                        factor_type=factor_data['factor_type'],
                        factor_value=factor_data['factor_value'],
                        multiplier=factor_data['multiplier']
                    )
                    session.add(factor)
                
                print(f"    + Added {len(factors)} pricing factors")
            else:
                print(f"  ✅ {existing_factors_count} pricing factors already exist")
        
        # Commit all changes
        await session.commit()
        print(f"\n✅ All products now have pricing tiers and factors!")

if __name__ == "__main__":
    asyncio.run(fix_missing_pricing_tiers())
