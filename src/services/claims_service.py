"""
Service de gestion des réclamations d'assurance.
Gère le workflow complet depuis la soumission jusqu'au règlement.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, date, timedelta
import uuid

from src.models.insurance import ClaimStatus
from src.migrations.create_insurance_tables import (
    InsuranceClaim as ClaimDB,
    InsuranceContract as ContractDB,
    Customer as CustomerDB,
    InsuranceProduct as ProductDB,
    CustomerDocument as DocumentDB
)


class ClaimsService:
    """Service pour la gestion des réclamations d'assurance."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_claim(self, claim_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Crée une nouvelle réclamation.
        """
        # Générer un numéro de réclamation unique
        claim_number = await self._generate_claim_number()

        # Convertir la date d'incident en objet date si c'est une chaîne
        incident_date = claim_data['incident_date']
        if isinstance(incident_date, str):
            incident_date = datetime.strptime(incident_date, '%Y-%m-%d').date()

        db_claim = ClaimDB(
            id=str(uuid.uuid4()),
            claim_number=claim_number,
            contract_id=claim_data['contract_id'],
            customer_id=claim_data['customer_id'],
            claim_type=claim_data['claim_type'],
            claim_amount=claim_data['claim_amount'],
            incident_date=incident_date,
            description=claim_data['description'],
            claim_status=ClaimStatus.SUBMITTED
        )
        
        self.db.add(db_claim)
        await self.db.commit()
        await self.db.refresh(db_claim)
        
        return {
            'id': db_claim.id,
            'claim_number': db_claim.claim_number,
            'claim_status': db_claim.claim_status,
            'claim_amount': db_claim.claim_amount,
            'incident_date': db_claim.incident_date.isoformat(),
            'report_date': db_claim.report_date.isoformat(),
            'description': db_claim.description
        }
    
    async def get_claims(self, customer_id: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupère les réclamations avec filtres optionnels.
        """
        query = select(ClaimDB, CustomerDB, ContractDB).join(
            CustomerDB, ClaimDB.customer_id == CustomerDB.id
        ).join(
            ContractDB, ClaimDB.contract_id == ContractDB.id
        )
        
        conditions = []
        
        if customer_id:
            conditions.append(ClaimDB.customer_id == customer_id)
        
        if status:
            conditions.append(ClaimDB.claim_status == status)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        query = query.order_by(desc(ClaimDB.report_date))
        
        result = await self.db.execute(query)
        rows = result.all()
        
        claims = []
        for claim, customer, contract in rows:
            claims.append({
                'id': claim.id,
                'claim_number': claim.claim_number,
                'customer_id': claim.customer_id,
                'customer_name': f"{customer.first_name} {customer.last_name}",
                'contract_id': claim.contract_id,
                'policy_number': contract.policy_number,
                'claim_type': claim.claim_type,
                'claim_status': claim.claim_status,
                'claim_amount': claim.claim_amount,
                'incident_date': claim.incident_date.isoformat(),
                'report_date': claim.report_date.isoformat(),
                'description': claim.description,
                'approval_amount': claim.approval_amount,
                'rejection_reason': claim.rejection_reason,
                'payment_date': claim.payment_date.isoformat() if claim.payment_date else None,
                'assigned_adjuster_id': claim.assigned_adjuster_id,
                'investigation_notes': claim.investigation_notes
            })
        
        return claims
    
    async def get_claim_by_number(self, claim_number: str) -> Optional[Dict[str, Any]]:
        """
        Récupère une réclamation par son numéro.
        """
        query = select(ClaimDB, CustomerDB, ContractDB, ProductDB).join(
            CustomerDB, ClaimDB.customer_id == CustomerDB.id
        ).join(
            ContractDB, ClaimDB.contract_id == ContractDB.id
        ).join(
            ProductDB, ContractDB.product_id == ProductDB.id
        ).where(ClaimDB.claim_number == claim_number)
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        claim, customer, contract, product = row
        
        # Récupérer les documents associés
        docs_query = select(DocumentDB).where(
            DocumentDB.customer_id == claim.customer_id
        )
        docs_result = await self.db.execute(docs_query)
        documents = docs_result.scalars().all()
        
        return {
            'id': claim.id,
            'claim_number': claim.claim_number,
            'customer': {
                'id': customer.id,
                'name': f"{customer.first_name} {customer.last_name}",
                'email': customer.email,
                'phone': customer.phone
            },
            'contract': {
                'id': contract.id,
                'policy_number': contract.policy_number,
                'coverage_amount': contract.coverage_amount
            },
            'product': {
                'id': product.id,
                'name': product.name,
                'product_type': product.product_type
            },
            'claim_type': claim.claim_type,
            'claim_status': claim.claim_status,
            'claim_amount': claim.claim_amount,
            'incident_date': claim.incident_date.isoformat(),
            'report_date': claim.report_date.isoformat(),
            'description': claim.description,
            'approval_amount': claim.approval_amount,
            'rejection_reason': claim.rejection_reason,
            'payment_date': claim.payment_date.isoformat() if claim.payment_date else None,
            'assigned_adjuster_id': claim.assigned_adjuster_id,
            'investigation_notes': claim.investigation_notes,
            'documents': [{
                'id': doc.id,
                'document_type': doc.document_type,
                'document_name': doc.document_name,
                'upload_date': doc.upload_date.isoformat(),
                'is_verified': doc.is_verified
            } for doc in documents]
        }
    
    async def update_claim_status(self, claim_id: str, new_status: str, notes: Optional[str] = None, 
                                 approval_amount: Optional[float] = None, 
                                 rejection_reason: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Met à jour le statut d'une réclamation.
        """
        query = select(ClaimDB).where(ClaimDB.id == claim_id)
        result = await self.db.execute(query)
        claim = result.scalar_one_or_none()
        
        if not claim:
            return None
        
        claim.claim_status = new_status
        claim.updated_at = datetime.utcnow()
        
        if notes:
            claim.investigation_notes = notes
        
        if approval_amount is not None:
            claim.approval_amount = approval_amount
        
        if rejection_reason:
            claim.rejection_reason = rejection_reason
        
        if new_status == ClaimStatus.PAID:
            claim.payment_date = date.today()
        
        await self.db.commit()
        await self.db.refresh(claim)
        
        return {
            'id': claim.id,
            'claim_number': claim.claim_number,
            'claim_status': claim.claim_status,
            'approval_amount': claim.approval_amount,
            'payment_date': claim.payment_date.isoformat() if claim.payment_date else None
        }
    
    async def assign_adjuster(self, claim_id: str, adjuster_id: str) -> bool:
        """
        Assigne un expert à une réclamation.
        """
        query = select(ClaimDB).where(ClaimDB.id == claim_id)
        result = await self.db.execute(query)
        claim = result.scalar_one_or_none()
        
        if not claim:
            return False
        
        claim.assigned_adjuster_id = adjuster_id
        claim.claim_status = ClaimStatus.INVESTIGATING
        claim.updated_at = datetime.utcnow()
        
        await self.db.commit()
        return True
    
    async def get_claims_statistics(self) -> Dict[str, Any]:
        """
        Récupère les statistiques des réclamations.
        """
        # Nombre total de réclamations
        total_query = select(func.count(ClaimDB.id))
        total_result = await self.db.execute(total_query)
        total_claims = total_result.scalar()
        
        # Réclamations par statut
        status_query = select(
            ClaimDB.claim_status,
            func.count(ClaimDB.id).label('count')
        ).group_by(ClaimDB.claim_status)
        status_result = await self.db.execute(status_query)
        status_counts = {row.claim_status: row.count for row in status_result}
        
        # Montant total des réclamations
        amount_query = select(
            func.coalesce(func.sum(ClaimDB.claim_amount), 0).label('total_claimed'),
            func.coalesce(func.sum(ClaimDB.approval_amount), 0).label('total_approved')
        )
        amount_result = await self.db.execute(amount_query)
        amounts = amount_result.first()
        
        # Réclamations récentes (30 derniers jours)
        thirty_days_ago = date.today() - timedelta(days=30)
        recent_query = select(func.count(ClaimDB.id)).where(
            ClaimDB.report_date >= thirty_days_ago
        )
        recent_result = await self.db.execute(recent_query)
        recent_claims = recent_result.scalar()
        
        return {
            'total_claims': total_claims or 0,
            'status_counts': status_counts,
            'total_claimed_amount': float(amounts.total_claimed or 0),
            'total_approved_amount': float(amounts.total_approved or 0),
            'recent_claims': recent_claims or 0,
            'approval_rate': (
                (amounts.total_approved / amounts.total_claimed * 100) 
                if amounts.total_claimed > 0 else 0
            )
        }
    
    async def _generate_claim_number(self) -> str:
        """Génère un numéro de réclamation unique."""
        # Format: REC-YYYYMMDD-NNNNNN
        today = date.today()
        date_str = today.strftime("%Y%m%d")
        
        # Compter les réclamations créées aujourd'hui
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        count_query = select(func.count(ClaimDB.id)).where(
            and_(
                ClaimDB.created_at >= today_start,
                ClaimDB.created_at <= today_end
            )
        )
        result = await self.db.execute(count_query)
        count = result.scalar() or 0
        
        sequence = str(count + 1).zfill(6)
        return f"REC-{date_str}-{sequence}"
