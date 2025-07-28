"""
Service de gestion des produits d'assurance et moteur de tarification.
Fournit la gestion du catalogue de produits et la tarification dynamique.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import math

from src.models.insurance import (
    InsuranceProduct, InsuranceProductCreate, InsuranceProductUpdate, ProductCategory,
    ProductFeature, PricingTier, ProductSearchParams,
    ProductDetailsResponse, PricingRequest, PricingResponse
)
from src.migrations.create_insurance_tables import (
    InsuranceProduct as ProductDB,
    ProductCategory as CategoryDB,
    ProductFeature as FeatureDB,
    PricingTier as TierDB,
    PricingFactor as FactorDB,
    Customer as CustomerDB
)


class ProductService:
    """Service pour la gestion des produits d'assurance."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_products(self, params: ProductSearchParams) -> List[InsuranceProduct]:
        """
        Récupère la liste des produits d'assurance avec filtres.
        """
        query = select(ProductDB).where(ProductDB.is_active == params.is_active)
        
        if params.product_type:
            query = query.where(ProductDB.product_type == params.product_type)
        
        if params.category_id:
            query = query.where(ProductDB.category_id == params.category_id)
        
        if params.min_coverage:
            query = query.where(ProductDB.min_coverage_amount >= params.min_coverage)
        
        if params.max_coverage:
            query = query.where(ProductDB.max_coverage_amount <= params.max_coverage)
        
        query = query.order_by(ProductDB.product_type, ProductDB.name)
        
        result = await self.db.execute(query)
        products = result.scalars().all()
        
        return [InsuranceProduct.from_orm(product) for product in products]

    async def _add_default_pricing_tiers(self, product_db: ProductDB):
        """Add default pricing tiers for a product."""
        from src.migrations.create_insurance_tables import PricingTier

        # Define default tiers based on product type
        if product_db.product_type == 'life':
            tiers = [
                {'tier_name': 'Niveau 1', 'coverage_amount': 30000000, 'base_premium': 720000},
                {'tier_name': 'Niveau 2', 'coverage_amount': 65000000, 'base_premium': 1300000},
                {'tier_name': 'Niveau 3', 'coverage_amount': 165000000, 'base_premium': 2700000}
            ]
        elif product_db.product_type == 'auto':
            tiers = [
                {'tier_name': 'Essentiel', 'coverage_amount': 10000000, 'base_premium': 480000},
                {'tier_name': 'Confort', 'coverage_amount': 32000000, 'base_premium': 720000},
                {'tier_name': 'Premium', 'coverage_amount': 65000000, 'base_premium': 1080000}
            ]
        elif product_db.product_type == 'health':
            tiers = [
                {'tier_name': 'Base', 'coverage_amount': 16000000, 'base_premium': 360000},
                {'tier_name': 'Confort', 'coverage_amount': 49000000, 'base_premium': 720000},
                {'tier_name': 'Premium', 'coverage_amount': 98000000, 'base_premium': 1440000}
            ]
        elif product_db.product_type == 'home':
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
                product_id=product_db.id,
                tier_name=tier_data['tier_name'],
                coverage_amount=tier_data['coverage_amount'],
                base_premium=tier_data['base_premium'],
                premium_frequency='annual',
                currency='XOF'
            )
            self.db.add(tier)

        await self.db.commit()

    async def _add_default_pricing_factors(self, product_db: ProductDB):
        """Add default pricing factors for a product."""
        from src.migrations.create_insurance_tables import PricingFactor

        # Define default factors
        factors = [
            {'factor_name': 'Âge 18-30', 'factor_type': 'age', 'factor_value': '18-30', 'multiplier': 1.2},
            {'factor_name': 'Âge 31-45', 'factor_type': 'age', 'factor_value': '31-45', 'multiplier': 1.0},
            {'factor_name': 'Âge 46-65', 'factor_type': 'age', 'factor_value': '46-65', 'multiplier': 1.1},
            {'factor_name': 'Âge 66+', 'factor_type': 'age', 'factor_value': '66+', 'multiplier': 1.3},
            {'factor_name': 'Risque faible', 'factor_type': 'risk_profile', 'factor_value': 'low', 'multiplier': 0.9},
            {'factor_name': 'Risque moyen', 'factor_type': 'risk_profile', 'factor_value': 'medium', 'multiplier': 1.0},
            {'factor_name': 'Risque élevé', 'factor_type': 'risk_profile', 'factor_value': 'high', 'multiplier': 1.4}
        ]

        # Add specific factors based on product type
        if product_db.product_type == 'auto':
            factors.extend([
                {'factor_name': 'Conducteur expérimenté', 'factor_type': 'experience', 'factor_value': '5+', 'multiplier': 0.85},
                {'factor_name': 'Jeune conducteur', 'factor_type': 'experience', 'factor_value': '0-2', 'multiplier': 1.5}
            ])
        elif product_db.product_type == 'health':
            factors.extend([
                {'factor_name': 'Non-fumeur', 'factor_type': 'lifestyle', 'factor_value': 'non_smoker', 'multiplier': 0.9},
                {'factor_name': 'Fumeur', 'factor_type': 'lifestyle', 'factor_value': 'smoker', 'multiplier': 1.3}
            ])

        # Add pricing factors
        for factor_data in factors:
            factor = PricingFactor(
                product_id=product_db.id,
                factor_name=factor_data['factor_name'],
                factor_type=factor_data['factor_type'],
                factor_value=factor_data['factor_value'],
                multiplier=factor_data['multiplier']
            )
            self.db.add(factor)

        await self.db.commit()
    
    async def get_product_by_id(self, product_id: str) -> Optional[InsuranceProduct]:
        """Récupère un produit par son ID."""
        query = select(ProductDB).where(ProductDB.id == product_id)
        result = await self.db.execute(query)
        product = result.scalar_one_or_none()

        if product:
            return InsuranceProduct.from_orm(product)
        return None

    async def create_product(self, product_data: InsuranceProductCreate) -> InsuranceProduct:
        """Crée un nouveau produit d'assurance avec niveaux de prix par défaut."""
        import uuid

        db_product = ProductDB(
            id=str(uuid.uuid4()),
            **product_data.dict()
        )

        self.db.add(db_product)
        await self.db.commit()
        await self.db.refresh(db_product)

        # Add default pricing tiers and factors
        await self._add_default_pricing_tiers(db_product)
        await self._add_default_pricing_factors(db_product)

        return InsuranceProduct.from_orm(db_product)

    async def update_product(self, product_id: str, product_data: InsuranceProductUpdate) -> Optional[InsuranceProduct]:
        """Met à jour un produit existant."""
        query = select(ProductDB).where(ProductDB.id == product_id)
        result = await self.db.execute(query)
        product = result.scalar_one_or_none()

        if not product:
            return None

        # Mettre à jour seulement les champs fournis (non None)
        update_data = product_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(product, field, value)

        product.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(product)

        return InsuranceProduct.from_orm(product)

    async def delete_product(self, product_id: str) -> bool:
        """Supprime un produit (suppression logique)."""
        query = select(ProductDB).where(ProductDB.id == product_id)
        result = await self.db.execute(query)
        product = result.scalar_one_or_none()

        if not product:
            return False

        # Suppression logique - marquer comme inactif
        product.is_active = False
        product.updated_at = datetime.utcnow()

        await self.db.commit()

        return True
    
    async def get_product_details(self, product_id: str) -> Optional[ProductDetailsResponse]:
        """
        Récupère les détails complets d'un produit avec ses fonctionnalités et niveaux de prix.
        """
        product = await self.get_product_by_id(product_id)
        if not product:
            return None
        
        # Récupérer les fonctionnalités
        features_query = select(FeatureDB).where(FeatureDB.product_id == product_id)
        features_result = await self.db.execute(features_query)
        features = features_result.scalars().all()
        
        # Récupérer les niveaux de prix actifs
        tiers_query = select(TierDB).where(
            and_(
                TierDB.product_id == product_id,
                TierDB.is_active == True
            )
        ).order_by(TierDB.coverage_amount)
        tiers_result = await self.db.execute(tiers_query)
        tiers = tiers_result.scalars().all()
        
        return ProductDetailsResponse(
            product=product,
            features=[ProductFeature.from_orm(feature) for feature in features],
            pricing_tiers=[PricingTier.from_orm(tier) for tier in tiers]
        )
    
    async def get_categories(self) -> List[ProductCategory]:
        """Récupère toutes les catégories de produits actives."""
        query = select(CategoryDB).where(CategoryDB.is_active == True).order_by(CategoryDB.name)
        result = await self.db.execute(query)
        categories = result.scalars().all()
        
        return [ProductCategory.from_orm(category) for category in categories]
    
    async def calculate_pricing(self, request: PricingRequest) -> Optional[PricingResponse]:
        """
        Calcule la tarification dynamique pour un produit et un client.
        Applique les facteurs de risque et les multiplicateurs.
        """
        # Récupérer le produit
        product = await self.get_product_by_id(request.product_id)
        if not product:
            return None
        
        # Récupérer le client pour les facteurs de risque
        customer_query = select(CustomerDB).where(CustomerDB.id == request.customer_id)
        customer_result = await self.db.execute(customer_query)
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            return None
        
        # Récupérer le niveau de prix de base
        tier_query = select(TierDB).where(
            and_(
                TierDB.product_id == request.product_id,
                TierDB.coverage_amount == request.coverage_amount,
                TierDB.is_active == True
            )
        )
        tier_result = await self.db.execute(tier_query)
        tier = tier_result.scalar_one_or_none()
        
        if not tier:
            return None
        
        base_premium = tier.base_premium
        
        # Calculer l'âge du client
        age = None
        if customer.date_of_birth:
            today = date.today()
            age = today.year - customer.date_of_birth.year
            if today.month < customer.date_of_birth.month or \
               (today.month == customer.date_of_birth.month and today.day < customer.date_of_birth.day):
                age -= 1
        
        # Récupérer les facteurs de tarification applicables
        factors_query = select(FactorDB).where(
            and_(
                FactorDB.product_id == request.product_id,
                FactorDB.is_active == True
            )
        )
        factors_result = await self.db.execute(factors_query)
        all_factors = factors_result.scalars().all()
        
        applicable_factors = []
        total_multiplier = 1.0
        
        for factor in all_factors:
            multiplier = None
            
            # Facteur d'âge
            if factor.factor_type == 'age_group' and age is not None:
                age_range = factor.factor_value.split('-')
                if len(age_range) == 2:
                    min_age = int(age_range[0])
                    max_age = int(age_range[1])
                    if min_age <= age <= max_age:
                        multiplier = factor.multiplier
            
            # Facteur de genre
            elif factor.factor_type == 'gender' and customer.gender:
                if factor.factor_value.lower() == customer.gender.lower():
                    multiplier = factor.multiplier
            
            # Facteur de profil de risque
            elif factor.factor_type == 'risk_profile':
                if factor.factor_value == customer.risk_profile:
                    multiplier = factor.multiplier
            
            # Facteur de profession
            elif factor.factor_type == 'occupation' and customer.occupation:
                if factor.factor_value.lower() in customer.occupation.lower():
                    multiplier = factor.multiplier
            
            if multiplier is not None:
                applicable_factors.append({
                    'factor_name': factor.factor_name,
                    'factor_value': factor.factor_value,
                    'multiplier': multiplier
                })
                total_multiplier *= multiplier
        
        # Calculer la prime finale
        final_premium = round(base_premium * total_multiplier, 2)
        
        # Ajuster selon la fréquence de paiement
        if request.premium_frequency == 'monthly':
            final_premium = round(final_premium / 12, 2)
        elif request.premium_frequency == 'quarterly':
            final_premium = round(final_premium / 4, 2)
        elif request.premium_frequency == 'semi-annual':
            final_premium = round(final_premium / 2, 2)
        
        # Calculer les primes des avenants (riders)
        rider_premiums = []
        if request.additional_riders:
            for rider_id in request.additional_riders:
                # Logique pour calculer les primes des avenants
                # Pour l'instant, on applique un pourcentage fixe
                rider_premium = round(final_premium * 0.1, 2)  # 10% de la prime de base
                rider_premiums.append({
                    'rider_name': f'Avenant {rider_id}',
                    'premium': rider_premium
                })
                final_premium += rider_premium
        
        return PricingResponse(
            base_premium=base_premium,
            final_premium=final_premium,
            pricing_factors=applicable_factors,
            rider_premiums=rider_premiums
        )
    
    async def check_eligibility(self, product_id: str, customer_id: str) -> Dict[str, Any]:
        """
        Vérifie l'éligibilité d'un client pour un produit.
        """
        product = await self.get_product_by_id(product_id)
        if not product:
            return {'eligible': False, 'reason': 'Produit non trouvé'}
        
        customer_query = select(CustomerDB).where(CustomerDB.id == customer_id)
        customer_result = await self.db.execute(customer_query)
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            return {'eligible': False, 'reason': 'Client non trouvé'}
        
        # Vérifier l'âge
        if customer.date_of_birth and (product.min_age or product.max_age):
            today = date.today()
            age = today.year - customer.date_of_birth.year
            if today.month < customer.date_of_birth.month or \
               (today.month == customer.date_of_birth.month and today.day < customer.date_of_birth.day):
                age -= 1
            
            if product.min_age and age < product.min_age:
                return {'eligible': False, 'reason': f'Âge minimum requis: {product.min_age} ans'}
            
            if product.max_age and age > product.max_age:
                return {'eligible': False, 'reason': f'Âge maximum autorisé: {product.max_age} ans'}
        
        # Vérifier le statut KYC
        if customer.kyc_status != 'verified':
            return {'eligible': False, 'reason': 'Vérification KYC requise'}
        
        # Vérifier le profil de risque
        if customer.risk_profile == 'high' and product.product_type in ['life', 'health']:
            return {
                'eligible': True,
                'conditions': ['Examen médical requis', 'Surprime possible'],
                'medical_exam_required': True
            }
        
        return {'eligible': True, 'conditions': []}
    
    async def get_product_comparison(self, product_ids: List[str]) -> List[Dict[str, Any]]:
        """
        Compare plusieurs produits côte à côte.
        """
        comparison_data = []
        
        for product_id in product_ids:
            details = await self.get_product_details(product_id)
            if details:
                # Récupérer les prix minimum et maximum
                min_premium = min([tier.base_premium for tier in details.pricing_tiers]) if details.pricing_tiers else 0
                max_premium = max([tier.base_premium for tier in details.pricing_tiers]) if details.pricing_tiers else 0
                
                comparison_data.append({
                    'product': details.product,
                    'features_count': len(details.features),
                    'standard_features': [f for f in details.features if f.is_standard],
                    'optional_features': [f for f in details.features if not f.is_standard],
                    'min_premium': min_premium,
                    'max_premium': max_premium,
                    'coverage_range': {
                        'min': details.product.min_coverage_amount,
                        'max': details.product.max_coverage_amount
                    }
                })
        
        return comparison_data
