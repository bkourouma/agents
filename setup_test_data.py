#!/usr/bin/env python3
"""
Setup complete test data for insurance system
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from src.migrations.create_insurance_tables import (
    InsuranceProduct, PricingTier, PricingFactor
)

DATABASE_URL = "sqlite+aiosqlite:///./ai_agent_platform.db"

async def setup_test_data():
    """Setup complete test data"""
    
    print("🚀 Setting up test data for insurance system...")
    
    # Create async engine and session
    engine = create_async_engine(DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        # Create insurance products
        products = [
            {
                'product_code': 'VIE001',
                'name': 'Assurance Vie Essentielle',
                'description': 'Assurance vie de base pour la protection familiale',
                'product_type': 'life',
                'coverage_type': 'term_life',
                'min_coverage_amount': 10000000,  # 10M XOF
                'max_coverage_amount': 200000000,  # 200M XOF
                'min_age': 18,
                'max_age': 65,
                'policy_term_years': 20,
                'renewable': True,
                'requires_medical_exam': False
            },
            {
                'product_code': 'AUTO001',
                'name': 'Auto Tous Risques',
                'description': 'Assurance automobile complète',
                'product_type': 'auto',
                'coverage_type': 'comprehensive',
                'min_coverage_amount': 5000000,  # 5M XOF
                'max_coverage_amount': 100000000,  # 100M XOF
                'min_age': 18,
                'max_age': 75,
                'policy_term_years': 1,
                'renewable': True,
                'requires_medical_exam': False
            },
            {
                'product_code': 'SANTE001',
                'name': 'Mutuelle Famille',
                'description': 'Assurance santé familiale',
                'product_type': 'health',
                'coverage_type': 'family_health',
                'min_coverage_amount': 5000000,  # 5M XOF
                'max_coverage_amount': 150000000,  # 150M XOF
                'min_age': 0,
                'max_age': 99,
                'policy_term_years': 1,
                'renewable': True,
                'requires_medical_exam': False
            }
        ]
        
        print("📦 Creating insurance products...")
        product_ids = []
        for product_data in products:
            product = InsuranceProduct(**product_data)
            session.add(product)
            await session.flush()
            product_ids.append(product.id)
            print(f"   ✅ {product.name}")
        
        await session.commit()
        
        # Create pricing tiers for each product
        print("\n💰 Creating pricing tiers...")
        for i, product_id in enumerate(product_ids):
            product_type = products[i]['product_type']
            
            if product_type == 'life':
                tiers = [
                    {'tier_name': 'Niveau 1', 'coverage_amount': 30000000, 'base_premium': 720000},
                    {'tier_name': 'Niveau 2', 'coverage_amount': 65000000, 'base_premium': 1300000},
                    {'tier_name': 'Niveau 3', 'coverage_amount': 165000000, 'base_premium': 2700000}
                ]
            elif product_type == 'auto':
                tiers = [
                    {'tier_name': 'Essentiel', 'coverage_amount': 10000000, 'base_premium': 480000},
                    {'tier_name': 'Confort', 'coverage_amount': 32000000, 'base_premium': 720000},
                    {'tier_name': 'Premium', 'coverage_amount': 65000000, 'base_premium': 1080000}
                ]
            else:  # health
                tiers = [
                    {'tier_name': 'Base', 'coverage_amount': 16000000, 'base_premium': 360000},
                    {'tier_name': 'Confort', 'coverage_amount': 49000000, 'base_premium': 720000},
                    {'tier_name': 'Premium', 'coverage_amount': 98000000, 'base_premium': 1440000}
                ]
            
            for tier_data in tiers:
                tier = PricingTier(
                    product_id=product_id,
                    tier_name=tier_data['tier_name'],
                    coverage_amount=tier_data['coverage_amount'],
                    base_premium=tier_data['base_premium'],
                    premium_frequency='annual',
                    currency='XOF'
                )
                session.add(tier)
            
            print(f"   ✅ {len(tiers)} tiers for {products[i]['name']}")
        
        await session.commit()
        
        # Create pricing factors
        print("\n📊 Creating pricing factors...")
        for product_id in product_ids:
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
                    product_id=product_id,
                    factor_name=factor_data['factor_name'],
                    factor_type=factor_data['factor_type'],
                    factor_value=factor_data['factor_value'],
                    multiplier=factor_data['multiplier']
                )
                session.add(factor)
        
        await session.commit()
        print(f"   ✅ Pricing factors created for all products")
        
        print(f"\n🎉 Test data setup complete!")
        print(f"   📦 {len(products)} insurance products")
        print(f"   💰 Pricing tiers with XOF amounts")
        print(f"   📊 Age and risk-based pricing factors")

if __name__ == "__main__":
    asyncio.run(setup_test_data())
