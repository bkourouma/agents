#!/usr/bin/env python3
"""
Script to add pricing factors for insurance products
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from src.migrations.create_insurance_tables import (
    InsuranceProduct, PricingFactor
)

DATABASE_URL = "sqlite+aiosqlite:///./ai_agent_platform.db"

async def add_pricing_factors():
    """Add pricing factors for all products"""
    
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
            
            # Check if pricing factors already exist
            existing_factors = await session.execute(
                select(PricingFactor).where(PricingFactor.product_id == product.id)
            )
            existing_count = len(existing_factors.scalars().all())
            
            if existing_count > 0:
                print(f"  - {existing_count} pricing factors already exist for {product.name}")
                continue
            
            # Add pricing factors
            factors = [
                {
                    'factor_name': 'Âge 18-30',
                    'factor_type': 'age',
                    'factor_value': '18-30',
                    'multiplier': 1.2
                },
                {
                    'factor_name': 'Âge 31-45',
                    'factor_type': 'age',
                    'factor_value': '31-45',
                    'multiplier': 1.0
                },
                {
                    'factor_name': 'Âge 46-65',
                    'factor_type': 'age',
                    'factor_value': '46-65',
                    'multiplier': 1.1
                },
                {
                    'factor_name': 'Âge 66+',
                    'factor_type': 'age',
                    'factor_value': '66+',
                    'multiplier': 1.3
                },
                {
                    'factor_name': 'Risque faible',
                    'factor_type': 'risk_profile',
                    'factor_value': 'low',
                    'multiplier': 0.9
                },
                {
                    'factor_name': 'Risque moyen',
                    'factor_type': 'risk_profile',
                    'factor_value': 'medium',
                    'multiplier': 1.0
                },
                {
                    'factor_name': 'Risque élevé',
                    'factor_type': 'risk_profile',
                    'factor_value': 'high',
                    'multiplier': 1.4
                }
            ]
            
            # Add specific factors based on product type
            if product.product_type == 'auto':
                factors.extend([
                    {
                        'factor_name': 'Conducteur expérimenté',
                        'factor_type': 'experience',
                        'factor_value': '5+',
                        'multiplier': 0.85
                    },
                    {
                        'factor_name': 'Jeune conducteur',
                        'factor_type': 'experience',
                        'factor_value': '0-2',
                        'multiplier': 1.5
                    }
                ])
            elif product.product_type == 'health':
                factors.extend([
                    {
                        'factor_name': 'Non-fumeur',
                        'factor_type': 'lifestyle',
                        'factor_value': 'non_smoker',
                        'multiplier': 0.9
                    },
                    {
                        'factor_name': 'Fumeur',
                        'factor_type': 'lifestyle',
                        'factor_value': 'smoker',
                        'multiplier': 1.3
                    }
                ])
            
            for factor_data in factors:
                factor = PricingFactor(
                    product_id=product.id,
                    factor_name=factor_data['factor_name'],
                    factor_type=factor_data['factor_type'],
                    factor_value=factor_data['factor_value'],
                    multiplier=factor_data['multiplier']
                )
                session.add(factor)
                print(f"  - Added factor: {factor_data['factor_name']} (×{factor_data['multiplier']})")
        
        # Commit all changes
        await session.commit()
        print(f"\n✅ Successfully added pricing factors for all products!")

if __name__ == "__main__":
    asyncio.run(add_pricing_factors())
