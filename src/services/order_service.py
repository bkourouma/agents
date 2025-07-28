"""
Service de gestion des commandes d'assurance.
Gère le workflow complet depuis le brouillon jusqu'à l'approbation.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc, func
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import uuid

from src.models.insurance import (
    InsuranceOrder, InsuranceOrderCreate, InsuranceOrderUpdate,
    CreateOrderRequest, UpdateOrderRequest, OrderStatusResponse,
    OrderStatus
)
from src.migrations.create_insurance_tables import (
    InsuranceOrder as OrderDB,
    InsuranceQuote as QuoteDB,
    OrderStatusHistory as StatusHistoryDB,
    OrderRider as RiderDB,
    Customer as CustomerDB,
    InsuranceProduct as ProductDB,
    SystemUser as UserDB
)


class OrderService:
    """Service pour la gestion des commandes d'assurance."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_order(self, request: CreateOrderRequest, agent_id: Optional[str] = None) -> InsuranceOrder:
        """
        Crée une nouvelle commande d'assurance.
        """
        # Générer un numéro de commande unique
        order_number = await self._generate_order_number()
        
        # Créer la commande
        db_order = OrderDB(
            id=str(uuid.uuid4()),
            order_number=order_number,
            customer_id=request.customer_id,
            product_id=request.product_id,
            order_status=OrderStatus.DRAFT,
            coverage_amount=request.coverage_amount,
            premium_amount=0,  # Sera calculé
            premium_frequency=request.premium_frequency,
            effective_date=request.effective_date,
            assigned_agent_id=agent_id,
            notes=request.notes
        )
        
        self.db.add(db_order)
        
        # Ajouter les avenants (riders) si fournis
        if request.riders:
            for rider_data in request.riders:
                db_rider = RiderDB(
                    id=str(uuid.uuid4()),
                    order_id=db_order.id,
                    rider_name=rider_data.get('rider_name'),
                    rider_type=rider_data.get('rider_type'),
                    coverage_amount=rider_data.get('coverage_amount'),
                    additional_premium=rider_data.get('additional_premium')
                )
                self.db.add(db_rider)
        
        # Enregistrer l'historique du statut
        await self._add_status_history(
            db_order.id,
            None,
            OrderStatus.DRAFT,
            agent_id,
            "Commande créée"
        )
        
        await self.db.commit()
        await self.db.refresh(db_order)
        
        return InsuranceOrder.from_orm(db_order)
    
    async def get_order_by_id(self, order_id: str) -> Optional[InsuranceOrder]:
        """Récupère une commande par son ID."""
        query = select(OrderDB).where(OrderDB.id == order_id)
        result = await self.db.execute(query)
        order = result.scalar_one_or_none()
        
        if order:
            return InsuranceOrder.from_orm(order)
        return None
    
    async def get_order_by_number(self, order_number: str) -> Optional[InsuranceOrder]:
        """Récupère une commande par son numéro."""
        query = select(OrderDB).where(OrderDB.order_number == order_number)
        result = await self.db.execute(query)
        order = result.scalar_one_or_none()
        
        if order:
            return InsuranceOrder.from_orm(order)
        return None
    
    async def update_order(self, order_id: str, request: UpdateOrderRequest, user_id: Optional[str] = None) -> Optional[InsuranceOrder]:
        """
        Met à jour une commande existante.
        """
        query = select(OrderDB).where(OrderDB.id == order_id)
        result = await self.db.execute(query)
        order = result.scalar_one_or_none()
        
        if not order:
            return None
        
        # Sauvegarder l'ancien statut pour l'historique
        old_status = order.order_status
        
        # Mettre à jour les champs fournis
        update_data = request.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(order, field, value)
        
        order.updated_at = datetime.utcnow()
        
        # Si le statut a changé, enregistrer dans l'historique
        if 'order_status' in update_data and update_data['order_status'] != old_status:
            await self._add_status_history(
                order_id,
                old_status,
                update_data['order_status'],
                user_id,
                f"Statut mis à jour de {old_status} vers {update_data['order_status']}"
            )
        
        await self.db.commit()
        await self.db.refresh(order)
        
        return InsuranceOrder.from_orm(order)
    
    async def get_order_status(self, order_number: str) -> Optional[OrderStatusResponse]:
        """
        Récupère le statut d'une commande avec son historique.
        """
        order = await self.get_order_by_number(order_number)
        if not order:
            return None
        
        # Récupérer l'historique des statuts
        history_query = select(StatusHistoryDB).where(
            StatusHistoryDB.order_id == order.id
        ).order_by(desc(StatusHistoryDB.changed_at))
        
        history_result = await self.db.execute(history_query)
        history_records = history_result.scalars().all()
        
        status_history = []
        for record in history_records:
            # Récupérer les informations de l'utilisateur qui a fait le changement
            user_info = None
            if record.changed_by:
                user_query = select(UserDB).where(UserDB.id == record.changed_by)
                user_result = await self.db.execute(user_query)
                user = user_result.scalar_one_or_none()
                if user:
                    user_info = f"{user.first_name} {user.last_name}"
            
            status_history.append({
                'previous_status': record.previous_status,
                'new_status': record.new_status,
                'changed_at': record.changed_at,
                'changed_by': user_info,
                'reason': record.reason,
                'notes': record.notes
            })
        
        return OrderStatusResponse(
            order=order,
            status_history=status_history
        )
    
    async def get_customer_orders(self, customer_id: str, status: Optional[OrderStatus] = None) -> List[InsuranceOrder]:
        """
        Récupère toutes les commandes d'un client.
        """
        query = select(OrderDB).where(OrderDB.customer_id == customer_id)
        
        if status:
            query = query.where(OrderDB.order_status == status)
        
        query = query.order_by(desc(OrderDB.application_date))
        
        result = await self.db.execute(query)
        orders = result.scalars().all()
        
        return [InsuranceOrder.from_orm(order) for order in orders]

    async def get_all_orders(self, status: Optional[str] = None, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Récupère toutes les commandes avec informations client et produit.
        """
        query = select(OrderDB)

        if status:
            query = query.where(OrderDB.order_status == status)

        query = query.order_by(desc(OrderDB.application_date)).offset(skip).limit(limit)

        result = await self.db.execute(query)
        orders = result.scalars().all()

        # Enrichir avec les informations client et produit
        enriched_orders = []
        for order in orders:
            order_dict = InsuranceOrder.from_orm(order).dict()

            # Récupérer les informations du client
            customer_query = select(CustomerDB).where(CustomerDB.id == order.customer_id)
            customer_result = await self.db.execute(customer_query)
            customer = customer_result.scalar_one_or_none()

            # Récupérer les informations du produit
            product_query = select(ProductDB).where(ProductDB.id == order.product_id)
            product_result = await self.db.execute(product_query)
            product = product_result.scalar_one_or_none()

            # Ajouter les informations enrichies
            if customer:
                order_dict['customer'] = {
                    'id': customer.id,
                    'first_name': customer.first_name,
                    'last_name': customer.last_name,
                    'email': customer.email
                }

            if product:
                order_dict['product'] = {
                    'id': product.id,
                    'name': product.name,
                    'product_type': product.product_type
                }

            enriched_orders.append(order_dict)

        return enriched_orders

    async def create_order_from_quote(self, quote_id: str, payment_method: str = "bank_transfer") -> Optional[InsuranceOrder]:
        """Crée une commande à partir d'un devis."""
        # Récupérer le devis
        quote_query = select(QuoteDB).where(QuoteDB.id == quote_id)
        quote_result = await self.db.execute(quote_query)
        quote = quote_result.scalar_one_or_none()

        if not quote:
            raise ValueError("Devis non trouvé")

        if not quote.eligible:
            raise ValueError("Le devis n'est pas éligible pour créer une commande")

        if quote.quote_status != 'active':
            raise ValueError("Le devis n'est plus actif")

        # Générer un numéro de commande
        order_number = await self._generate_order_number()

        # Créer la commande
        order = OrderDB(
            order_number=order_number,
            quote_id=quote_id,
            customer_id=quote.customer_id,
            product_id=quote.product_id,
            order_status='draft',
            coverage_amount=quote.coverage_amount,
            premium_amount=quote.final_premium,
            premium_frequency=quote.premium_frequency,
            payment_method=payment_method,
            application_date=date.today(),
            medical_exam_required=quote.medical_exam_required
        )

        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)

        # Marquer le devis comme converti
        quote.quote_status = 'converted'
        await self.db.commit()

        return InsuranceOrder.from_orm(order)
    
    async def submit_order(self, order_id: str, user_id: Optional[str] = None) -> Optional[InsuranceOrder]:
        """
        Soumet une commande pour révision.
        """
        return await self.update_order(
            order_id,
            UpdateOrderRequest(order_status=OrderStatus.SUBMITTED),
            user_id
        )
    
    async def approve_order(self, order_id: str, user_id: Optional[str] = None, notes: Optional[str] = None) -> Optional[InsuranceOrder]:
        """
        Approuve une commande.
        """
        order = await self.get_order_by_id(order_id)
        if not order:
            return None
        
        # Vérifier que la commande peut être approuvée
        if order.order_status not in [OrderStatus.SUBMITTED, OrderStatus.UNDER_REVIEW]:
            return None
        
        return await self.update_order(
            order_id,
            UpdateOrderRequest(
                order_status=OrderStatus.APPROVED,
                approval_date=date.today(),
                notes=notes
            ),
            user_id
        )
    
    async def reject_order(self, order_id: str, reason: str, user_id: Optional[str] = None) -> Optional[InsuranceOrder]:
        """
        Rejette une commande.
        """
        return await self.update_order(
            order_id,
            UpdateOrderRequest(
                order_status=OrderStatus.REJECTED,
                rejection_reason=reason
            ),
            user_id
        )
    
    async def cancel_order(self, order_id: str, user_id: Optional[str] = None) -> Optional[InsuranceOrder]:
        """
        Annule une commande.
        """
        return await self.update_order(
            order_id,
            UpdateOrderRequest(order_status=OrderStatus.CANCELLED),
            user_id
        )
    
    async def get_orders_requiring_attention(self, agent_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Récupère les commandes nécessitant une attention (documents manquants, examens médicaux, etc.).
        """
        query = select(OrderDB).where(
            OrderDB.order_status.in_([OrderStatus.SUBMITTED, OrderStatus.UNDER_REVIEW])
        )
        
        if agent_id:
            query = query.where(OrderDB.assigned_agent_id == agent_id)
        
        result = await self.db.execute(query)
        orders = result.scalars().all()
        
        attention_orders = []
        for order in orders:
            issues = []
            
            if not order.documents_received:
                issues.append("Documents manquants")
            
            if order.medical_exam_required and not order.medical_exam_completed:
                issues.append("Examen médical requis")
            
            # Vérifier si la commande est en attente depuis trop longtemps
            days_pending = (datetime.now().date() - order.application_date).days
            if days_pending > 7:
                issues.append(f"En attente depuis {days_pending} jours")
            
            if issues:
                attention_orders.append({
                    'order': InsuranceOrder.from_orm(order),
                    'issues': issues,
                    'days_pending': days_pending
                })
        
        return attention_orders
    
    async def _generate_order_number(self) -> str:
        """Génère un numéro de commande unique."""
        # Format: ORD-YYYYMMDD-NNNNNN
        today = date.today()
        date_str = today.strftime("%Y%m%d")
        
        # Compter les commandes créées aujourd'hui
        today_start = datetime.combine(today, datetime.min.time())
        today_end = datetime.combine(today, datetime.max.time())
        
        count_query = select(func.count(OrderDB.id)).where(
            and_(
                OrderDB.created_at >= today_start,
                OrderDB.created_at <= today_end
            )
        )
        result = await self.db.execute(count_query)
        count = result.scalar() or 0
        
        sequence = str(count + 1).zfill(6)
        return f"ORD-{date_str}-{sequence}"
    
    async def _add_status_history(self, order_id: str, previous_status: Optional[str], 
                                 new_status: str, changed_by: Optional[str], reason: str):
        """Ajoute une entrée dans l'historique des statuts."""
        history_record = StatusHistoryDB(
            id=str(uuid.uuid4()),
            order_id=order_id,
            previous_status=previous_status,
            new_status=new_status,
            changed_by=changed_by,
            reason=reason
        )
        
        self.db.add(history_record)
