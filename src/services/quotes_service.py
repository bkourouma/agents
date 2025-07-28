"""
Service de gestion des devis d'assurance.
Génère des devis personnalisés basés sur les profils clients et produits.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import uuid

from src.migrations.create_insurance_tables import (
    Customer as CustomerDB,
    InsuranceProduct as ProductDB,
    InsuranceQuote as QuoteDB,
    PricingTier as TierDB,
    PricingFactor as FactorDB,
    ProductFeature as FeatureDB
)
from src.models.insurance import (
    InsuranceQuote, InsuranceQuoteCreate, InsuranceQuoteUpdate, QuoteStatus
)


class QuotesService:
    """Service pour la génération et gestion des devis d'assurance."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def generate_quote(self, quote_request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Génère un devis personnalisé pour un client et un produit.
        """
        customer_id = quote_request['customer_id']
        product_id = quote_request['product_id']
        coverage_amount = quote_request['coverage_amount']
        premium_frequency = quote_request.get('premium_frequency', 'monthly')
        additional_features = quote_request.get('additional_features', [])
        
        # Récupérer le client
        customer_query = select(CustomerDB).where(CustomerDB.id == customer_id)
        customer_result = await self.db.execute(customer_query)
        customer = customer_result.scalar_one_or_none()
        
        if not customer:
            raise ValueError("Client non trouvé")
        
        # Récupérer le produit
        product_query = select(ProductDB).where(ProductDB.id == product_id)
        product_result = await self.db.execute(product_query)
        product = product_result.scalar_one_or_none()
        
        if not product:
            raise ValueError("Produit non trouvé")
        
        # Vérifier l'éligibilité
        eligibility = await self._check_eligibility(customer, product)
        if not eligibility['eligible']:
            return {
                'eligible': False,
                'reason': eligibility['reason'],
                'customer_name': f"{customer.first_name} {customer.last_name}",
                'product_name': product.name
            }
        
        # Calculer la prime de base
        base_premium = await self._calculate_base_premium(product_id, coverage_amount)
        
        # Appliquer les facteurs de tarification
        pricing_factors = await self._get_pricing_factors(product_id, customer)
        adjusted_premium = await self._apply_pricing_factors(base_premium, pricing_factors)
        
        # Calculer les fonctionnalités supplémentaires
        additional_premium = 0
        selected_features = []
        
        if additional_features:
            features_query = select(FeatureDB).where(
                and_(
                    FeatureDB.product_id == product_id,
                    FeatureDB.id.in_(additional_features)
                )
            )
            features_result = await self.db.execute(features_query)
            features = features_result.scalars().all()
            
            for feature in features:
                feature_premium = adjusted_premium * (feature.additional_premium_percentage / 100)
                additional_premium += feature_premium
                selected_features.append({
                    'id': feature.id,
                    'name': feature.feature_name,
                    'description': feature.description,
                    'additional_premium': feature_premium
                })
        
        # Calculer la prime finale selon la fréquence
        final_premium = adjusted_premium + additional_premium
        
        if premium_frequency == 'monthly':
            display_premium = final_premium / 12
        elif premium_frequency == 'quarterly':
            display_premium = final_premium / 4
        elif premium_frequency == 'semi-annual':
            display_premium = final_premium / 2
        else:  # annual
            display_premium = final_premium
        
        # Générer le numéro de devis
        quote_number = await self._generate_quote_number()
        
        # Calculer la date d'expiration du devis (30 jours)
        expiry_date = date.today() + timedelta(days=30)
        
        # Sauvegarder le devis en base de données
        db_quote = QuoteDB(
            quote_number=quote_number,
            customer_id=customer_id,
            product_id=product_id,
            coverage_amount=coverage_amount,
            premium_frequency=premium_frequency,
            base_premium=base_premium,
            adjusted_premium=adjusted_premium,
            additional_premium=additional_premium,
            final_premium=display_premium,
            annual_premium=final_premium,
            pricing_factors=pricing_factors,
            selected_features=selected_features,
            quote_date=date.today(),
            expiry_date=expiry_date,
            eligible=True,
            conditions=eligibility.get('conditions', []),
            medical_exam_required=eligibility.get('medical_exam_required', False)
        )

        self.db.add(db_quote)
        await self.db.commit()
        await self.db.refresh(db_quote)

        quote = {
            'id': db_quote.id,
            'quote_number': quote_number,
            'customer': {
                'id': customer.id,
                'name': f"{customer.first_name} {customer.last_name}",
                'email': customer.email,
                'phone': customer.phone,
                'age': self._calculate_age(customer.date_of_birth) if customer.date_of_birth else None,
                'risk_profile': customer.risk_profile
            },
            'product': {
                'id': product.id,
                'name': product.name,
                'product_type': product.product_type,
                'description': product.description
            },
            'coverage_amount': coverage_amount,
            'premium_frequency': premium_frequency,
            'base_premium': base_premium,
            'adjusted_premium': adjusted_premium,
            'additional_premium': additional_premium,
            'final_premium': display_premium,
            'annual_premium': final_premium,
            'pricing_factors': pricing_factors,
            'selected_features': selected_features,
            'quote_date': date.today().isoformat(),
            'expiry_date': expiry_date.isoformat(),
            'eligible': True,
            'conditions': eligibility.get('conditions', []),
            'medical_exam_required': eligibility.get('medical_exam_required', False)
        }

        return quote
    
    async def _check_eligibility(self, customer: CustomerDB, product: ProductDB) -> Dict[str, Any]:
        """
        Vérifie l'éligibilité d'un client pour un produit.
        """
        conditions = []
        
        # Vérifier l'âge
        if customer.date_of_birth and (product.min_age or product.max_age):
            age = self._calculate_age(customer.date_of_birth)
            
            if product.min_age and age < product.min_age:
                return {'eligible': False, 'reason': f'Âge minimum requis: {product.min_age} ans'}
            
            if product.max_age and age > product.max_age:
                return {'eligible': False, 'reason': f'Âge maximum autorisé: {product.max_age} ans'}
        
        # Vérifier le statut KYC
        if customer.kyc_status != 'verified':
            return {'eligible': False, 'reason': 'Vérification KYC requise'}
        
        # Conditions spéciales selon le profil de risque
        if customer.risk_profile == 'high':
            conditions.append('Surprime possible')
            if product.product_type in ['life', 'health']:
                conditions.append('Examen médical requis')
                return {
                    'eligible': True,
                    'conditions': conditions,
                    'medical_exam_required': True
                }
        
        return {'eligible': True, 'conditions': conditions}
    
    async def _calculate_base_premium(self, product_id: str, coverage_amount: float) -> float:
        """
        Calcule la prime de base pour un montant de couverture donné.
        """
        # Trouver le niveau de prix correspondant
        tier_query = select(TierDB).where(
            and_(
                TierDB.product_id == product_id,
                TierDB.coverage_amount <= coverage_amount,
                TierDB.is_active == True
            )
        ).order_by(desc(TierDB.coverage_amount)).limit(1)
        
        tier_result = await self.db.execute(tier_query)
        tier = tier_result.scalar_one_or_none()
        
        if not tier:
            # Si aucun niveau trouvé, utiliser le plus bas
            fallback_query = select(TierDB).where(
                and_(
                    TierDB.product_id == product_id,
                    TierDB.is_active == True
                )
            ).order_by(TierDB.coverage_amount).limit(1)
            
            fallback_result = await self.db.execute(fallback_query)
            tier = fallback_result.scalar_one_or_none()
        
        if not tier:
            raise ValueError("Aucun niveau de prix trouvé pour ce produit")
        
        # Calculer la prime proportionnellement
        if tier.coverage_amount > 0:
            ratio = coverage_amount / tier.coverage_amount
            return tier.base_premium * ratio
        else:
            return tier.base_premium
    
    async def _get_pricing_factors(self, product_id: str, customer: CustomerDB) -> List[Dict[str, Any]]:
        """
        Récupère les facteurs de tarification applicables.
        """
        factors_query = select(FactorDB).where(
            and_(
                FactorDB.product_id == product_id,
                FactorDB.is_active == True
            )
        )
        factors_result = await self.db.execute(factors_query)
        all_factors = factors_result.scalars().all()
        
        applicable_factors = []
        age = self._calculate_age(customer.date_of_birth) if customer.date_of_birth else None
        
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
                    'factor_type': factor.factor_type,
                    'factor_value': factor.factor_value,
                    'multiplier': multiplier
                })
        
        return applicable_factors
    
    async def _apply_pricing_factors(self, base_premium: float, factors: List[Dict[str, Any]]) -> float:
        """
        Applique les facteurs de tarification à la prime de base.
        """
        total_multiplier = 1.0
        
        for factor in factors:
            total_multiplier *= factor['multiplier']
        
        return round(base_premium * total_multiplier, 2)
    
    def _calculate_age(self, date_of_birth: date) -> int:
        """
        Calcule l'âge à partir de la date de naissance.
        """
        today = date.today()
        age = today.year - date_of_birth.year
        if today.month < date_of_birth.month or \
           (today.month == date_of_birth.month and today.day < date_of_birth.day):
            age -= 1
        return age
    
    async def _generate_quote_number(self) -> str:
        """Génère un numéro de devis unique."""
        # Format: DEV-YYYYMMDD-NNNNNN
        today = date.today()
        date_str = today.strftime("%Y%m%d")
        
        # Utiliser un compteur simple basé sur l'heure pour éviter les collisions
        timestamp = int(datetime.now().timestamp() * 1000) % 1000000
        sequence = str(timestamp).zfill(6)
        
        return f"DEV-{date_str}-{sequence}"

    # =============================================
    # CRUD OPERATIONS FOR QUOTES
    # =============================================

    async def get_quotes(self, skip: int = 0, limit: int = 50, status: Optional[str] = None) -> List[InsuranceQuote]:
        """Récupère la liste des devis avec pagination et filtrage."""
        query = select(QuoteDB).where(QuoteDB.is_active == True)

        if status:
            query = query.where(QuoteDB.quote_status == status)

        query = query.order_by(desc(QuoteDB.created_at)).offset(skip).limit(limit)

        result = await self.db.execute(query)
        quotes = result.scalars().all()

        return [InsuranceQuote.from_orm(quote) for quote in quotes]

    async def get_quote_by_id(self, quote_id: str) -> Optional[InsuranceQuote]:
        """Récupère un devis par son ID."""
        query = select(QuoteDB).where(QuoteDB.id == quote_id)
        result = await self.db.execute(query)
        quote = result.scalar_one_or_none()

        if quote:
            return InsuranceQuote.from_orm(quote)
        return None

    async def get_quote_by_number(self, quote_number: str) -> Optional[InsuranceQuote]:
        """Récupère un devis par son numéro."""
        query = select(QuoteDB).where(QuoteDB.quote_number == quote_number)
        result = await self.db.execute(query)
        quote = result.scalar_one_or_none()

        if quote:
            return InsuranceQuote.from_orm(quote)
        return None

    async def update_quote(self, quote_id: str, quote_data: InsuranceQuoteUpdate) -> Optional[InsuranceQuote]:
        """Met à jour un devis existant."""
        query = select(QuoteDB).where(QuoteDB.id == quote_id)
        result = await self.db.execute(query)
        quote = result.scalar_one_or_none()

        if not quote:
            return None

        # Mettre à jour seulement les champs fournis (non None)
        update_data = quote_data.dict(exclude_unset=True)

        # Si on modifie la couverture ou la fréquence, recalculer les primes
        if 'coverage_amount' in update_data or 'premium_frequency' in update_data:
            # Récupérer le client et le produit pour recalculer
            customer_query = select(CustomerDB).where(CustomerDB.id == quote.customer_id)
            customer_result = await self.db.execute(customer_query)
            customer = customer_result.scalar_one_or_none()

            product_query = select(ProductDB).where(ProductDB.id == quote.product_id)
            product_result = await self.db.execute(product_query)
            product = product_result.scalar_one_or_none()

            if customer and product:
                new_coverage = update_data.get('coverage_amount', quote.coverage_amount)
                new_frequency = update_data.get('premium_frequency', quote.premium_frequency)

                # Recalculer les primes
                base_premium = await self._calculate_base_premium(quote.product_id, new_coverage)
                pricing_factors = await self._get_pricing_factors(quote.product_id, customer)
                adjusted_premium = await self._apply_pricing_factors(base_premium, pricing_factors)

                final_premium = adjusted_premium + quote.additional_premium

                if new_frequency == 'monthly':
                    display_premium = final_premium / 12
                elif new_frequency == 'quarterly':
                    display_premium = final_premium / 4
                elif new_frequency == 'semi-annual':
                    display_premium = final_premium / 2
                else:  # annual
                    display_premium = final_premium

                # Mettre à jour les primes calculées
                update_data.update({
                    'base_premium': base_premium,
                    'adjusted_premium': adjusted_premium,
                    'final_premium': display_premium,
                    'annual_premium': final_premium
                })

        for field, value in update_data.items():
            if value is not None:
                setattr(quote, field, value)

        quote.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(quote)

        return InsuranceQuote.from_orm(quote)

    async def delete_quote(self, quote_id: str) -> bool:
        """Supprime un devis (suppression logique)."""
        query = select(QuoteDB).where(QuoteDB.id == quote_id)
        result = await self.db.execute(query)
        quote = result.scalar_one_or_none()

        if not quote:
            return False

        # Suppression logique - marquer comme inactif
        quote.is_active = False
        quote.updated_at = datetime.utcnow()

        await self.db.commit()

        return True

    async def get_customer_quotes(self, customer_id: str, skip: int = 0, limit: int = 20) -> List[InsuranceQuote]:
        """Récupère les devis d'un client spécifique."""
        query = select(QuoteDB).where(
            and_(
                QuoteDB.customer_id == customer_id,
                QuoteDB.is_active == True
            )
        ).order_by(desc(QuoteDB.created_at)).offset(skip).limit(limit)

        result = await self.db.execute(query)
        quotes = result.scalars().all()

        return [InsuranceQuote.from_orm(quote) for quote in quotes]

    async def expire_old_quotes(self) -> int:
        """Marque les devis expirés comme expirés."""
        today = date.today()

        query = select(QuoteDB).where(
            and_(
                QuoteDB.expiry_date < today,
                QuoteDB.quote_status == 'active',
                QuoteDB.is_active == True
            )
        )

        result = await self.db.execute(query)
        expired_quotes = result.scalars().all()

        count = 0
        for quote in expired_quotes:
            quote.quote_status = 'expired'
            quote.updated_at = datetime.utcnow()
            count += 1

        await self.db.commit()

        return count
