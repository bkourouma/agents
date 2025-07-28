#!/usr/bin/env python3
"""
Script to add missing pricing tiers and factors for insurance products
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

async def add_pricing_data():
    """Add pricing tiers and factors for all products"""
    
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
            if existing_tiers.scalars().first():
                print(f"  - Pricing tiers already exist for {product.name}")
                continue
            
            # Add pricing tiers based on product type
            if product.product_type == 'life':
                # Life insurance tiers
                tiers = [
                    {
                        'tier_name': 'Standard',
                        'min_coverage': 10000,
                        'max_coverage': 100000,
                        'base_premium_rate': 0.002,  # 0.2% of coverage
                        'description': 'Couverture standard pour assurance vie'
                    },
                    {
                        'tier_name': 'Premium',
                        'min_coverage': 100001,
                        'max_coverage': 500000,
                        'base_premium_rate': 0.0015,  # 0.15% of coverage
                        'description': 'Couverture premium pour assurance vie'
                    }
                ]
            elif product.product_type == 'auto':
                # Auto insurance tiers
                tiers = [
                    {
                        'tier_name': 'Essentiel',
                        'min_coverage': 5000,
                        'max_coverage': 25000,
                        'base_premium_rate': 0.08,  # 8% of coverage
                        'description': 'Couverture essentielle automobile'
                    },
                    {
                        'tier_name': 'Confort',
                        'min_coverage': 25001,
                        'max_coverage': 100000,
                        'base_premium_rate': 0.06,  # 6% of coverage
                        'description': 'Couverture confort automobile'
                    }
                ]
            elif product.product_type == 'health':
                # Health insurance tiers
                tiers = [
                    {
                        'tier_name': 'Base',
                        'min_coverage': 0,
                        'max_coverage': 50000,
                        'base_premium_rate': 0.05,  # 5% of coverage or fixed amount
                        'description': 'Couverture santé de base'
                    },
                    {
                        'tier_name': 'Confort',
                        'min_coverage': 50001,
                        'max_coverage': 200000,
                        'base_premium_rate': 0.04,  # 4% of coverage
                        'description': 'Couverture santé confort'
                    }
                ]
            elif product.product_type == 'home':
                # Home insurance tiers
                tiers = [
                    {
                        'tier_name': 'Standard',
                        'min_coverage': 10000,
                        'max_coverage': 300000,
                        'base_premium_rate': 0.003,  # 0.3% of coverage
                        'description': 'Couverture habitation standard'
                    },
                    {
                        'tier_name': 'Premium',
                        'min_coverage': 300001,
                        'max_coverage': 1000000,
                        'base_premium_rate': 0.0025,  # 0.25% of coverage
                        'description': 'Couverture habitation premium'
                    }
                ]
            else:
                # Default tiers for other types
                tiers = [
                    {
                        'tier_name': 'Standard',
                        'min_coverage': 1000,
                        'max_coverage': 100000,
                        'base_premium_rate': 0.01,  # 1% of coverage
                        'description': 'Couverture standard'
                    }
                ]
            
            # Add pricing tiers
            for tier_data in tiers:
                tier = PricingTier(
                    product_id=product.id,
                    tier_name=tier_data['tier_name'],
                    min_coverage_amount=tier_data['min_coverage'],
                    max_coverage_amount=tier_data['max_coverage'],
                    base_premium_rate=tier_data['base_premium_rate'],
                    description=tier_data['description']
                )
                session.add(tier)
                print(f"  - Added tier: {tier_data['tier_name']}")
            
            # Check if pricing factors already exist
            existing_factors = await session.execute(
                select(PricingFactor).where(PricingFactor.product_id == product.id)
            )
            if existing_factors.scalars().first():
                print(f"  - Pricing factors already exist for {product.name}")
                continue
            
            # Add pricing factors
            factors = [
                {
                    'factor_name': 'Âge 18-30',
                    'factor_type': 'age',
                    'min_value': 18,
                    'max_value': 30,
                    'multiplier': 1.2,
                    'description': 'Jeune conducteur/assuré'
                },
                {
                    'factor_name': 'Âge 31-45',
                    'factor_type': 'age',
                    'min_value': 31,
                    'max_value': 45,
                    'multiplier': 1.0,
                    'description': 'Âge standard'
                },
                {
                    'factor_name': 'Âge 46-65',
                    'factor_type': 'age',
                    'min_value': 46,
                    'max_value': 65,
                    'multiplier': 1.1,
                    'description': 'Âge mature'
                },
                {
                    'factor_name': 'Âge 66+',
                    'factor_type': 'age',
                    'min_value': 66,
                    'max_value': 99,
                    'multiplier': 1.3,
                    'description': 'Senior'
                },
                {
                    'factor_name': 'Risque faible',
                    'factor_type': 'risk_profile',
                    'string_value': 'low',
                    'multiplier': 0.9,
                    'description': 'Profil de risque faible'
                },
                {
                    'factor_name': 'Risque moyen',
                    'factor_type': 'risk_profile',
                    'string_value': 'medium',
                    'multiplier': 1.0,
                    'description': 'Profil de risque moyen'
                },
                {
                    'factor_name': 'Risque élevé',
                    'factor_type': 'risk_profile',
                    'string_value': 'high',
                    'multiplier': 1.4,
                    'description': 'Profil de risque élevé'
                }
            ]
            
            for factor_data in factors:
                factor = PricingFactor(
                    product_id=product.id,
                    factor_name=factor_data['factor_name'],
                    factor_type=factor_data['factor_type'],
                    min_value=factor_data.get('min_value'),
                    max_value=factor_data.get('max_value'),
                    string_value=factor_data.get('string_value'),
                    multiplier=factor_data['multiplier'],
                    description=factor_data['description']
                )
                session.add(factor)
                print(f"  - Added factor: {factor_data['factor_name']}")
        
        # Commit all changes
        await session.commit()
        print(f"\n✅ Successfully added pricing data for all products!")

if __name__ == "__main__":
    asyncio.run(add_pricing_data())
