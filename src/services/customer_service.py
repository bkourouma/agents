"""
Service de gestion des clients pour le système d'assurance.
Fournit toutes les fonctionnalités de recherche, gestion et aperçu à 360° des clients.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, desc
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import uuid

from src.models.insurance import (
    Customer, CustomerCreate, CustomerUpdate, CustomerSearchParams,
    CustomerDetailsResponse, CustomerSummaryResponse, ApiResponse
)
from src.migrations.create_insurance_tables import (
    Customer as CustomerDB,
    InsuranceContract as ContractDB,
    InsuranceOrder as OrderDB,
    InsuranceClaim as ClaimDB,
    CustomerInteraction as InteractionDB,
    PremiumPayment as PaymentDB
)


class CustomerService:
    """Service pour la gestion des clients d'assurance."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def search_customers(self, params: CustomerSearchParams) -> List[Customer]:
        """
        Recherche de clients par téléphone, email, nom ou numéro client.
        """
        query = select(CustomerDB).where(CustomerDB.is_active == True)
        
        # Recherche par requête générale
        if params.query:
            search_term = f"%{params.query}%"
            query = query.where(
                or_(
                    CustomerDB.phone.ilike(search_term),
                    CustomerDB.email.ilike(search_term),
                    func.concat(CustomerDB.first_name, ' ', CustomerDB.last_name).ilike(search_term),
                    CustomerDB.customer_number == params.query
                )
            )
        
        # Filtres additionnels
        if params.customer_type:
            query = query.where(CustomerDB.customer_type == params.customer_type)
        
        if params.risk_profile:
            query = query.where(CustomerDB.risk_profile == params.risk_profile)
        
        if params.kyc_status:
            query = query.where(CustomerDB.kyc_status == params.kyc_status)
        
        query = query.limit(params.limit)
        
        result = await self.db.execute(query)
        customers = result.scalars().all()
        
        return [Customer.from_orm(customer) for customer in customers]

    async def get_customers(self, skip: int = 0, limit: int = 100) -> List[Customer]:
        """Récupère la liste des clients avec pagination."""
        query = select(CustomerDB).where(CustomerDB.is_active == True).order_by(desc(CustomerDB.created_at)).offset(skip).limit(limit)

        result = await self.db.execute(query)
        customers = result.scalars().all()

        return [Customer.from_orm(customer) for customer in customers]

    async def get_customer_by_id(self, customer_id: str) -> Optional[Customer]:
        """Récupère un client par son ID."""
        query = select(CustomerDB).where(CustomerDB.id == customer_id)
        result = await self.db.execute(query)
        customer = result.scalar_one_or_none()
        
        if customer:
            return Customer.from_orm(customer)
        return None
    
    async def get_customer_by_number(self, customer_number: str) -> Optional[Customer]:
        """Récupère un client par son numéro."""
        query = select(CustomerDB).where(CustomerDB.customer_number == customer_number)
        result = await self.db.execute(query)
        customer = result.scalar_one_or_none()
        
        if customer:
            return Customer.from_orm(customer)
        return None
    
    async def create_customer(self, customer_data: CustomerCreate) -> Customer:
        """Crée un nouveau client."""
        # Convertir les données en dictionnaire
        data_dict = customer_data.dict()

        # Générer un numéro client unique si pas fourni ou vide
        if not data_dict.get('customer_number'):
            data_dict['customer_number'] = await self._generate_customer_number()

        db_customer = CustomerDB(
            id=str(uuid.uuid4()),
            **data_dict
        )

        self.db.add(db_customer)
        await self.db.commit()
        await self.db.refresh(db_customer)

        return Customer.from_orm(db_customer)
    
    async def update_customer(self, customer_id: str, customer_data: CustomerUpdate) -> Optional[Customer]:
        """Met à jour un client existant."""
        query = select(CustomerDB).where(CustomerDB.id == customer_id)
        result = await self.db.execute(query)
        customer = result.scalar_one_or_none()

        if not customer:
            return None

        # Mettre à jour les champs fournis
        update_data = customer_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(customer, field, value)

        customer.updated_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(customer)

        return Customer.from_orm(customer)

    async def delete_customer(self, customer_id: str) -> bool:
        """Supprime un client (suppression logique)."""
        query = select(CustomerDB).where(CustomerDB.id == customer_id)
        result = await self.db.execute(query)
        customer = result.scalar_one_or_none()

        if not customer:
            return False

        # Suppression logique - marquer comme inactif
        customer.is_active = False
        customer.updated_at = datetime.utcnow()

        await self.db.commit()

        return True
    
    async def get_customer_details(self, customer_id: str) -> Optional[CustomerDetailsResponse]:
        """
        Récupère l'aperçu complet à 360° d'un client.
        Inclut les contrats actifs, commandes récentes et interactions.
        """
        # Récupérer le client
        customer = await self.get_customer_by_id(customer_id)
        if not customer:
            return None
        
        # Récupérer les contrats actifs
        contracts_query = select(ContractDB).where(
            and_(
                ContractDB.customer_id == customer_id,
                ContractDB.contract_status == 'active'
            )
        )
        contracts_result = await self.db.execute(contracts_query)
        active_contracts = contracts_result.scalars().all()
        
        # Récupérer les commandes récentes (30 derniers jours)
        thirty_days_ago = date.today() - timedelta(days=30)
        orders_query = select(OrderDB).where(
            and_(
                OrderDB.customer_id == customer_id,
                OrderDB.application_date >= thirty_days_ago
            )
        ).order_by(desc(OrderDB.application_date)).limit(10)
        orders_result = await self.db.execute(orders_query)
        recent_orders = orders_result.scalars().all()
        
        # Récupérer les interactions récentes (30 derniers jours)
        interactions_query = select(InteractionDB).where(
            and_(
                InteractionDB.customer_id == customer_id,
                InteractionDB.interaction_date >= datetime.now() - timedelta(days=30)
            )
        ).order_by(desc(InteractionDB.interaction_date)).limit(10)
        interactions_result = await self.db.execute(interactions_query)
        recent_interactions = interactions_result.scalars().all()
        
        return CustomerDetailsResponse(
            customer=customer,
            active_contracts=[contract for contract in active_contracts],
            recent_orders=[order for order in recent_orders],
            recent_interactions=[interaction for interaction in recent_interactions]
        )
    
    async def get_customer_summary(self, customer_id: str) -> Optional[CustomerSummaryResponse]:
        """
        Récupère un résumé des métriques clés du client.
        """
        customer = await self.get_customer_by_id(customer_id)
        if not customer:
            return None
        
        # Calculer les métriques
        # Contrats actifs et montant total de couverture
        contracts_query = select(
            func.count(ContractDB.id).label('active_contracts'),
            func.coalesce(func.sum(ContractDB.coverage_amount), 0).label('total_coverage'),
            func.coalesce(func.sum(
                func.case(
                    (ContractDB.premium_frequency == 'monthly', ContractDB.premium_amount * 12),
                    (ContractDB.premium_frequency == 'quarterly', ContractDB.premium_amount * 4),
                    (ContractDB.premium_frequency == 'semi-annual', ContractDB.premium_amount * 2),
                    else_=ContractDB.premium_amount
                )
            ), 0).label('annual_premium')
        ).where(
            and_(
                ContractDB.customer_id == customer_id,
                ContractDB.contract_status == 'active'
            )
        )
        
        contracts_result = await self.db.execute(contracts_query)
        contracts_metrics = contracts_result.first()
        
        # Commandes en attente
        pending_orders_query = select(func.count(OrderDB.id)).where(
            and_(
                OrderDB.customer_id == customer_id,
                OrderDB.order_status.in_(['submitted', 'under_review'])
            )
        )
        pending_orders_result = await self.db.execute(pending_orders_query)
        pending_orders = pending_orders_result.scalar()
        
        # Réclamations ouvertes
        open_claims_query = select(func.count(ClaimDB.id)).where(
            and_(
                ClaimDB.customer_id == customer_id,
                ClaimDB.claim_status.in_(['submitted', 'investigating', 'approved'])
            )
        )
        open_claims_result = await self.db.execute(open_claims_query)
        open_claims = open_claims_result.scalar()
        
        # Interactions récentes (30 derniers jours)
        recent_interactions_query = select(func.count(InteractionDB.id)).where(
            and_(
                InteractionDB.customer_id == customer_id,
                InteractionDB.interaction_date >= datetime.now() - timedelta(days=30)
            )
        )
        recent_interactions_result = await self.db.execute(recent_interactions_query)
        recent_interactions = recent_interactions_result.scalar()
        
        # Statut de paiement (vérifier les paiements en retard)
        overdue_payments_query = select(func.count(ContractDB.id)).where(
            and_(
                ContractDB.customer_id == customer_id,
                ContractDB.contract_status == 'active',
                ContractDB.next_premium_due_date < date.today()
            )
        )
        overdue_payments_result = await self.db.execute(overdue_payments_query)
        overdue_payments = overdue_payments_result.scalar()
        
        payment_status = "En retard" if overdue_payments > 0 else "À jour"
        
        return CustomerSummaryResponse(
            customer=customer,
            total_coverage_amount=float(contracts_metrics.total_coverage or 0),
            total_premium_amount=float(contracts_metrics.annual_premium or 0),
            active_contracts=int(contracts_metrics.active_contracts or 0),
            pending_orders=int(pending_orders or 0),
            open_claims=int(open_claims or 0),
            recent_interactions=int(recent_interactions or 0),
            payment_status=payment_status
        )
    
    async def _generate_customer_number(self) -> str:
        """Génère un numéro client unique."""
        # Format: CUST-YYYYMMDD-NNNN
        today = date.today()
        date_str = today.strftime("%Y%m%d")
        
        # Compter les clients créés aujourd'hui
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        count_query = select(func.count(CustomerDB.id)).where(
            and_(
                CustomerDB.created_at >= today_start,
                CustomerDB.created_at <= today_end
            )
        )
        result = await self.db.execute(count_query)
        count = result.scalar() or 0
        
        sequence = str(count + 1).zfill(4)
        return f"CUST-{date_str}-{sequence}"
    
    async def deactivate_customer(self, customer_id: str) -> bool:
        """Désactive un client (soft delete)."""
        query = select(CustomerDB).where(CustomerDB.id == customer_id)
        result = await self.db.execute(query)
        customer = result.scalar_one_or_none()
        
        if not customer:
            return False
        
        customer.is_active = False
        customer.updated_at = datetime.utcnow()
        
        await self.db.commit()
        return True
