"""
Service de gestion des contrats d'assurance.
Gère les polices actives, renouvellements et bénéficiaires.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import uuid

from src.models.insurance import (
    InsuranceContract, InsuranceContractCreate, ContractSearchParams,
    ContractDetailsResponse, ContractStatus
)
from src.migrations.create_insurance_tables import (
    InsuranceContract as ContractDB,
    ContractBeneficiary as BeneficiaryDB,
    PremiumPayment as PaymentDB,
    Customer as CustomerDB,
    InsuranceProduct as ProductDB,
    RenewalNotification as NotificationDB
)


class ContractService:
    """Service pour la gestion des contrats d'assurance."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_contract_from_order(self, order_id: str) -> Optional[InsuranceContract]:
        """
        Crée un contrat à partir d'une commande approuvée.
        """
        # Récupérer les informations de la commande
        from src.migrations.create_insurance_tables import InsuranceOrder as OrderDB
        
        order_query = select(OrderDB).where(OrderDB.id == order_id)
        order_result = await self.db.execute(order_query)
        order = order_result.scalar_one_or_none()
        
        if not order or order.order_status != 'approved':
            return None
        
        # Générer un numéro de police unique
        policy_number = await self._generate_policy_number()
        
        # Calculer les dates
        issue_date = date.today()
        effective_date = order.effective_date or issue_date
        
        # Calculer la date d'expiration (par défaut 1 an)
        expiry_date = effective_date.replace(year=effective_date.year + 1)
        next_renewal_date = expiry_date - timedelta(days=30)  # Rappel 30 jours avant
        
        # Calculer la prochaine échéance de prime
        if order.premium_frequency == 'monthly':
            next_due = effective_date + timedelta(days=30)
        elif order.premium_frequency == 'quarterly':
            next_due = effective_date + timedelta(days=90)
        elif order.premium_frequency == 'semi-annual':
            next_due = effective_date + timedelta(days=180)
        else:  # annual
            next_due = effective_date + timedelta(days=365)
        
        # Créer le contrat
        db_contract = ContractDB(
            id=str(uuid.uuid4()),
            policy_number=policy_number,
            order_id=order_id,
            customer_id=order.customer_id,
            product_id=order.product_id,
            contract_status=ContractStatus.ACTIVE,
            coverage_amount=order.coverage_amount,
            premium_amount=order.premium_amount,
            premium_frequency=order.premium_frequency,
            issue_date=issue_date,
            effective_date=effective_date,
            expiry_date=expiry_date,
            next_renewal_date=next_renewal_date,
            next_premium_due_date=next_due
        )
        
        self.db.add(db_contract)
        await self.db.commit()
        await self.db.refresh(db_contract)
        
        return InsuranceContract.from_orm(db_contract)
    
    async def get_contract_by_policy_number(self, policy_number: str) -> Optional[InsuranceContract]:
        """Récupère un contrat par son numéro de police."""
        query = select(ContractDB).where(ContractDB.policy_number == policy_number)
        result = await self.db.execute(query)
        contract = result.scalar_one_or_none()
        
        if contract:
            return InsuranceContract.from_orm(contract)
        return None
    
    async def search_contracts(self, params: ContractSearchParams) -> List[InsuranceContract]:
        """
        Recherche de contrats avec filtres.
        """
        query = select(ContractDB)
        
        conditions = []
        
        if params.customer_id:
            conditions.append(ContractDB.customer_id == params.customer_id)
        
        if params.policy_number:
            conditions.append(ContractDB.policy_number.ilike(f"%{params.policy_number}%"))
        
        if params.contract_status:
            conditions.append(ContractDB.contract_status == params.contract_status)
        
        if params.expiry_date_from:
            conditions.append(ContractDB.expiry_date >= params.expiry_date_from)
        
        if params.expiry_date_to:
            conditions.append(ContractDB.expiry_date <= params.expiry_date_to)
        
        if params.next_renewal_date_from:
            conditions.append(ContractDB.next_renewal_date >= params.next_renewal_date_from)
        
        if params.next_renewal_date_to:
            conditions.append(ContractDB.next_renewal_date <= params.next_renewal_date_to)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Filtrer par type de produit si spécifié
        if params.product_type:
            query = query.join(ProductDB).where(ProductDB.product_type == params.product_type)
        
        query = query.order_by(desc(ContractDB.issue_date))
        
        # Pagination
        offset = (params.page - 1) * params.page_size
        query = query.offset(offset).limit(params.page_size)
        
        result = await self.db.execute(query)
        contracts = result.scalars().all()
        
        return [InsuranceContract.from_orm(contract) for contract in contracts]
    
    async def get_contract_details(self, policy_number: str) -> Optional[ContractDetailsResponse]:
        """
        Récupère les détails complets d'un contrat.
        """
        contract = await self.get_contract_by_policy_number(policy_number)
        if not contract:
            return None
        
        # Récupérer le client
        customer_query = select(CustomerDB).where(CustomerDB.id == contract.customer_id)
        customer_result = await self.db.execute(customer_query)
        customer = customer_result.scalar_one_or_none()
        
        # Récupérer le produit
        product_query = select(ProductDB).where(ProductDB.id == contract.product_id)
        product_result = await self.db.execute(product_query)
        product = product_result.scalar_one_or_none()
        
        # Récupérer les bénéficiaires
        beneficiaries_query = select(BeneficiaryDB).where(
            and_(
                BeneficiaryDB.contract_id == contract.id,
                BeneficiaryDB.is_active == True
            )
        ).order_by(BeneficiaryDB.beneficiary_type, desc(BeneficiaryDB.percentage))
        
        beneficiaries_result = await self.db.execute(beneficiaries_query)
        beneficiaries = beneficiaries_result.scalars().all()
        
        # Récupérer l'historique des paiements (derniers 12 mois)
        twelve_months_ago = date.today() - timedelta(days=365)
        payments_query = select(PaymentDB).where(
            and_(
                PaymentDB.contract_id == contract.id,
                PaymentDB.payment_date >= twelve_months_ago
            )
        ).order_by(desc(PaymentDB.payment_date))
        
        payments_result = await self.db.execute(payments_query)
        payments = payments_result.scalars().all()
        
        return ContractDetailsResponse(
            contract=contract,
            customer=customer,
            product=product,
            beneficiaries=[{
                'first_name': b.first_name,
                'last_name': b.last_name,
                'relationship': b.relationship,
                'percentage': b.percentage,
                'beneficiary_type': b.beneficiary_type
            } for b in beneficiaries],
            payment_history=[{
                'payment_date': p.payment_date,
                'amount': p.amount,
                'status': p.payment_status,
                'payment_method': p.payment_method,
                'late_fee': p.late_fee
            } for p in payments]
        )
    
    async def get_contracts_expiring_soon(self, days_ahead: int = 30, customer_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupère les contrats qui expirent bientôt.
        """
        cutoff_date = date.today() + timedelta(days=days_ahead)
        
        query = select(ContractDB).where(
            and_(
                ContractDB.contract_status == ContractStatus.ACTIVE,
                ContractDB.expiry_date <= cutoff_date,
                ContractDB.expiry_date >= date.today()
            )
        )
        
        if customer_id:
            query = query.where(ContractDB.customer_id == customer_id)
        
        query = query.order_by(ContractDB.expiry_date)
        
        result = await self.db.execute(query)
        contracts = result.scalars().all()
        
        expiring_contracts = []
        for contract in contracts:
            # Calculer les jours jusqu'à expiration
            days_until_expiry = (contract.expiry_date - date.today()).days
            
            # Récupérer les informations du client et du produit
            customer_query = select(CustomerDB).where(CustomerDB.id == contract.customer_id)
            customer_result = await self.db.execute(customer_query)
            customer = customer_result.scalar_one_or_none()
            
            product_query = select(ProductDB).where(ProductDB.id == contract.product_id)
            product_result = await self.db.execute(product_query)
            product = product_result.scalar_one_or_none()
            
            expiring_contracts.append({
                'contract': InsuranceContract.from_orm(contract),
                'customer': customer,
                'product': product,
                'days_until_expiry': days_until_expiry
            })
        
        return expiring_contracts
    
    async def get_renewal_status(self, policy_number: str) -> Optional[Dict[str, Any]]:
        """
        Récupère le statut de renouvellement d'un contrat.
        """
        contract = await self.get_contract_by_policy_number(policy_number)
        if not contract:
            return None
        
        # Vérifier l'éligibilité au renouvellement
        renewal_eligible = (
            contract.contract_status == ContractStatus.ACTIVE and
            contract.next_renewal_date and
            contract.next_renewal_date <= date.today() + timedelta(days=60)
        )
        
        # Calculer la nouvelle prime (pour l'instant, on garde la même)
        new_premium = contract.premium_amount
        
        # Documents requis pour le renouvellement
        required_documents = []
        if contract.next_renewal_date and contract.next_renewal_date <= date.today() + timedelta(days=30):
            required_documents.append("Formulaire de renouvellement")
            
            # Vérifier si un examen médical est requis (par exemple, pour les clients âgés)
            customer_query = select(CustomerDB).where(CustomerDB.id == contract.customer_id)
            customer_result = await self.db.execute(customer_query)
            customer = customer_result.scalar_one_or_none()
            
            if customer and customer.date_of_birth:
                age = date.today().year - customer.date_of_birth.year
                if age >= 65:
                    required_documents.append("Examen médical")
        
        return {
            'contract': contract,
            'renewal_eligible': renewal_eligible,
            'renewal_date': contract.next_renewal_date,
            'new_premium': new_premium,
            'required_documents': required_documents,
            'auto_renewal': contract.auto_renewal
        }
    
    async def add_beneficiary(self, contract_id: str, beneficiary_data: Dict[str, Any]) -> bool:
        """
        Ajoute un bénéficiaire à un contrat.
        """
        db_beneficiary = BeneficiaryDB(
            id=str(uuid.uuid4()),
            contract_id=contract_id,
            **beneficiary_data
        )
        
        self.db.add(db_beneficiary)
        await self.db.commit()
        return True
    
    async def update_contract_status(self, policy_number: str, new_status: ContractStatus, reason: Optional[str] = None) -> Optional[InsuranceContract]:
        """
        Met à jour le statut d'un contrat.
        """
        query = select(ContractDB).where(ContractDB.policy_number == policy_number)
        result = await self.db.execute(query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            return None
        
        contract.contract_status = new_status
        contract.updated_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(contract)
        
        return InsuranceContract.from_orm(contract)
    
    async def _generate_policy_number(self) -> str:
        """Génère un numéro de police unique."""
        # Format: POL-YYYYMMDD-NNNNNN
        today = date.today()
        date_str = today.strftime("%Y%m%d")
        
        # Compter les contrats créés aujourd'hui
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        count_query = select(func.count(ContractDB.id)).where(
            and_(
                ContractDB.created_at >= today_start,
                ContractDB.created_at <= today_end
            )
        )
        result = await self.db.execute(count_query)
        count = result.scalar() or 0
        
        sequence = str(count + 1).zfill(6)
        return f"POL-{date_str}-{sequence}"
