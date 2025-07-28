"""
Service de gestion des paiements d'assurance.
Gère les primes, les paiements en retard, et les transactions.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, desc, func, update
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import uuid

from src.migrations.create_insurance_tables import (
    PremiumPayment as PaymentDB,
    InsuranceContract as ContractDB,
    Customer as CustomerDB,
    InsuranceProduct as ProductDB
)


class PaymentService:
    """Service pour la gestion des paiements d'assurance."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_all_payments(self, status: Optional[str] = None, contract_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupère tous les paiements avec filtres optionnels.
        """
        query = select(PaymentDB, CustomerDB, ContractDB, ProductDB).join(
            ContractDB, PaymentDB.contract_id == ContractDB.id
        ).join(
            CustomerDB, ContractDB.customer_id == CustomerDB.id
        ).join(
            ProductDB, ContractDB.product_id == ProductDB.id
        )
        
        conditions = []
        
        if status:
            conditions.append(PaymentDB.payment_status == status)
        
        if contract_id:
            conditions.append(PaymentDB.contract_id == contract_id)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(PaymentDB.due_date))
        
        result = await self.db.execute(query)
        rows = result.all()
        
        payments = []
        for payment, customer, contract, product in rows:
            payments.append({
                'id': payment.id,
                'contract_id': payment.contract_id,
                'policy_number': contract.policy_number,
                'customer_name': f"{customer.first_name} {customer.last_name}",
                'customer_id': customer.id,
                'product_name': product.name,
                'payment_date': payment.payment_date.isoformat() if payment.payment_date else None,
                'due_date': payment.due_date.isoformat(),
                'amount': payment.amount,
                'payment_method': payment.payment_method,
                'payment_status': payment.payment_status,
                'transaction_id': payment.transaction_id,
                'late_fee': payment.late_fee or 0,
                'grace_period_used': payment.grace_period_used,
                'processed_by': payment.processed_by,
                'created_at': payment.created_at.isoformat(),
                'days_overdue': (date.today() - payment.due_date).days if payment.due_date < date.today() and payment.payment_status == 'pending' else 0
            })
        
        return payments
    
    async def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée un nouveau paiement de prime.
        """
        db_payment = PaymentDB(
            id=str(uuid.uuid4()),
            contract_id=payment_data['contract_id'],
            due_date=datetime.strptime(payment_data['due_date'], '%Y-%m-%d').date() if isinstance(payment_data['due_date'], str) else payment_data['due_date'],
            amount=payment_data['amount'],
            payment_method=payment_data.get('payment_method'),
            payment_status='pending'
        )
        
        self.db.add(db_payment)
        await self.db.commit()
        await self.db.refresh(db_payment)
        
        return {
            'id': db_payment.id,
            'contract_id': db_payment.contract_id,
            'due_date': db_payment.due_date.isoformat(),
            'amount': db_payment.amount,
            'payment_status': db_payment.payment_status,
            'created_at': db_payment.created_at.isoformat()
        }
    
    async def process_payment(self, payment_id: str, payment_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Traite un paiement (marque comme payé).
        """
        query = select(PaymentDB).where(PaymentDB.id == payment_id)
        result = await self.db.execute(query)
        payment = result.scalar_one_or_none()
        
        if not payment:
            return None
        
        # Calculer les frais de retard si applicable
        late_fee = 0
        if payment.due_date < date.today() and payment_data.get('payment_date'):
            payment_date = datetime.strptime(payment_data['payment_date'], '%Y-%m-%d').date() if isinstance(payment_data['payment_date'], str) else payment_data['payment_date']
            days_late = (payment_date - payment.due_date).days
            if days_late > 0:
                late_fee = min(days_late * 1000, payment.amount * 0.1)  # 1000 XOF par jour, max 10%
        
        payment.payment_date = datetime.strptime(payment_data['payment_date'], '%Y-%m-%d').date() if isinstance(payment_data['payment_date'], str) else payment_data['payment_date']
        payment.payment_status = 'completed'
        payment.payment_method = payment_data.get('payment_method', payment.payment_method)
        payment.transaction_id = payment_data.get('transaction_id')
        payment.late_fee = late_fee
        payment.processed_by = payment_data.get('processed_by')
        
        await self.db.commit()
        await self.db.refresh(payment)
        
        # Mettre à jour la date du dernier paiement dans le contrat
        await self._update_contract_payment_date(payment.contract_id, payment.payment_date)
        
        return {
            'id': payment.id,
            'payment_date': payment.payment_date.isoformat(),
            'payment_status': payment.payment_status,
            'transaction_id': payment.transaction_id,
            'late_fee': payment.late_fee,
            'total_amount': payment.amount + payment.late_fee
        }
    
    async def _update_contract_payment_date(self, contract_id: str, payment_date: date):
        """Met à jour la date du dernier paiement dans le contrat."""
        await self.db.execute(
            update(ContractDB)
            .where(ContractDB.id == contract_id)
            .values(last_premium_paid_date=payment_date)
        )
        await self.db.commit()
    
    async def generate_upcoming_payments(self, contract_id: str, months_ahead: int = 12) -> List[Dict[str, Any]]:
        """
        Génère les paiements à venir pour un contrat.
        """
        # Récupérer le contrat
        query = select(ContractDB).where(ContractDB.id == contract_id)
        result = await self.db.execute(query)
        contract = result.scalar_one_or_none()
        
        if not contract:
            return []
        
        payments = []
        current_date = contract.next_premium_due_date or contract.effective_date
        
        # Calculer l'intervalle selon la fréquence
        if contract.premium_frequency == 'monthly':
            interval = timedelta(days=30)
        elif contract.premium_frequency == 'quarterly':
            interval = timedelta(days=90)
        elif contract.premium_frequency == 'semi-annual':
            interval = timedelta(days=180)
        else:  # annual
            interval = timedelta(days=365)
        
        for i in range(months_ahead):
            due_date = current_date + (interval * i)
            
            # Vérifier si ce paiement n'existe pas déjà
            existing_query = select(PaymentDB).where(
                and_(
                    PaymentDB.contract_id == contract_id,
                    PaymentDB.due_date == due_date
                )
            )
            existing_result = await self.db.execute(existing_query)
            if existing_result.scalar_one_or_none():
                continue
            
            payment_data = {
                'contract_id': contract_id,
                'due_date': due_date,
                'amount': contract.premium_amount
            }
            
            payment = await self.create_payment(payment_data)
            payments.append(payment)
        
        return payments
    
    async def get_payment_statistics(self) -> Dict[str, Any]:
        """
        Récupère les statistiques des paiements.
        """
        # Total des paiements
        total_query = select(func.count(PaymentDB.id))
        total_result = await self.db.execute(total_query)
        total_payments = total_result.scalar()
        
        # Paiements par statut
        status_query = select(PaymentDB.payment_status, func.count(PaymentDB.id)).group_by(PaymentDB.payment_status)
        status_result = await self.db.execute(status_query)
        status_counts = {row[0]: row[1] for row in status_result.all()}
        
        # Montants
        amount_query = select(
            func.sum(PaymentDB.amount).label('total_amount'),
            func.sum(PaymentDB.late_fee).label('total_late_fees')
        ).where(PaymentDB.payment_status == 'completed')
        amount_result = await self.db.execute(amount_query)
        amounts = amount_result.first()
        
        # Paiements en retard
        overdue_query = select(func.count(PaymentDB.id)).where(
            and_(
                PaymentDB.payment_status == 'pending',
                PaymentDB.due_date < date.today()
            )
        )
        overdue_result = await self.db.execute(overdue_query)
        overdue_payments = overdue_result.scalar()
        
        # Paiements récents (30 derniers jours)
        thirty_days_ago = date.today() - timedelta(days=30)
        recent_query = select(func.count(PaymentDB.id)).where(
            and_(
                PaymentDB.payment_status == 'completed',
                PaymentDB.payment_date >= thirty_days_ago
            )
        )
        recent_result = await self.db.execute(recent_query)
        recent_payments = recent_result.scalar()
        
        return {
            'total_payments': total_payments or 0,
            'status_counts': status_counts,
            'total_collected': float(amounts.total_amount or 0),
            'total_late_fees': float(amounts.total_late_fees or 0),
            'overdue_payments': overdue_payments or 0,
            'recent_payments': recent_payments or 0,
            'collection_rate': (
                ((total_payments - overdue_payments) / total_payments * 100) 
                if total_payments > 0 else 0
            )
        }
