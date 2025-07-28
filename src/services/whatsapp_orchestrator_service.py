"""
WhatsApp Orchestrator Integration Service.
Bridges WhatsApp messages with the existing orchestrator system for intelligent agent routing.
"""

import logging
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.whatsapp import (
    WhatsAppMessage, WhatsAppConversation, WhatsAppContact
)
from src.models.orchestrator import Conversation, ConversationMessage, OrchestratorRequest
from src.models.user import User
from src.models.tenant import Tenant
from src.services.whatsapp_api_service import whatsapp_api_service
from src.orchestrator.llm_service import llm_orchestrator_service

logger = logging.getLogger(__name__)


class WhatsAppOrchestratorService:
    """Service for integrating WhatsApp messages with the orchestrator system."""
    
    async def process_whatsapp_message(
        self, 
        db: AsyncSession, 
        whatsapp_message: WhatsAppMessage
    ) -> Dict[str, Any]:
        """
        Process an incoming WhatsApp message through the orchestrator.
        
        Args:
            db: Database session
            whatsapp_message: WhatsApp message to process
            
        Returns:
            Processing result with orchestrator response
        """
        try:
            # Get the WhatsApp conversation and contact
            conversation = await db.get(WhatsAppConversation, whatsapp_message.conversation_id)
            contact = await db.get(WhatsAppContact, whatsapp_message.contact_id)
            
            if not conversation or not contact:
                return {
                    "status": "error",
                    "error": "Conversation or contact not found"
                }
            
            # Get or create a system user for WhatsApp integration
            system_user = await self._get_whatsapp_system_user(db, contact.tenant_id)
            if not system_user:
                return {
                    "status": "error",
                    "error": "Could not create system user for WhatsApp"
                }
            
            # Create or get orchestrator conversation
            orchestrator_conversation_id = await self._get_or_create_orchestrator_conversation(
                db, conversation, contact, system_user
            )
            
            # Prepare orchestrator request
            orchestrator_request = OrchestratorRequest(
                message=whatsapp_message.content or "Media message",
                conversation_id=orchestrator_conversation_id,
                context={
                    "source": "whatsapp",
                    "phone_number": contact.phone_number,
                    "contact_name": contact.profile_name or contact.first_name,
                    "message_type": whatsapp_message.message_type,
                    "media_url": whatsapp_message.media_url,
                    "whatsapp_conversation_id": conversation.id,
                    "whatsapp_message_id": whatsapp_message.id
                }
            )
            
            # Process through orchestrator
            orchestrator_response = await llm_orchestrator_service.process_message(
                db, system_user, orchestrator_request
            )
            
            # Update WhatsApp message with orchestrator details
            whatsapp_message.orchestrator_message_id = orchestrator_response.conversation_id
            if orchestrator_response.routing_result and orchestrator_response.routing_result.selected_agent:
                whatsapp_message.processed_by_agent_id = orchestrator_response.routing_result.selected_agent.agent_id
            
            # Update WhatsApp conversation with orchestrator link
            conversation.orchestrator_conversation_id = orchestrator_response.conversation_id
            conversation.last_agent_response = whatsapp_message.created_at
            
            await db.commit()
            
            # Send response back to WhatsApp if auto-response is enabled
            if conversation.auto_response_enabled and orchestrator_response.agent_response:
                await self._send_whatsapp_response(
                    db, conversation, contact, orchestrator_response.agent_response
                )
            
            return {
                "status": "success",
                "orchestrator_response": orchestrator_response.agent_response,
                "agent_name": orchestrator_response.routing_result.selected_agent.agent_name if orchestrator_response.routing_result.selected_agent else None,
                "conversation_id": orchestrator_response.conversation_id
            }
            
        except Exception as e:
            logger.error(f"Error processing WhatsApp message through orchestrator: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def send_proactive_message(
        self,
        db: AsyncSession,
        phone_number: str,
        message: str,
        tenant_id: str,
        template_name: Optional[str] = None,
        template_parameters: Optional[list] = None
    ) -> Dict[str, Any]:
        """
        Send a proactive message to a WhatsApp contact.
        
        Args:
            db: Database session
            phone_number: Recipient phone number
            message: Message content
            tenant_id: Tenant ID
            template_name: Optional template name for template messages
            template_parameters: Optional template parameters
            
        Returns:
            Sending result
        """
        try:
            # Find or create contact
            contact = await self._find_or_create_contact(db, phone_number, tenant_id)
            if not contact:
                return {
                    "status": "error",
                    "error": "Could not find or create contact"
                }
            
            # Find or create conversation
            conversation = await self._find_or_create_conversation(db, contact)
            
            # Send message
            if template_name:
                # Send template message
                result = await whatsapp_api_service.send_template_message(
                    db=db,
                    phone_number=phone_number,
                    template_name=template_name,
                    parameters=template_parameters,
                    conversation_id=conversation.id,
                    tenant_id=tenant_id
                )
            else:
                # Send text message
                result = await whatsapp_api_service.send_text_message(
                    db=db,
                    phone_number=phone_number,
                    message=message,
                    conversation_id=conversation.id,
                    tenant_id=tenant_id
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error sending proactive WhatsApp message: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _get_whatsapp_system_user(self, db: AsyncSession, tenant_id: str) -> Optional[User]:
        """
        Get or create a system user for WhatsApp integration.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            
        Returns:
            System user for WhatsApp or None if error
        """
        try:
            # Try to find existing WhatsApp system user
            result = await db.execute(
                select(User).where(
                    User.tenant_id == tenant_id,
                    User.username == "whatsapp_system"
                )
            )
            user = result.scalar_one_or_none()
            
            if user:
                return user
            
            # Create WhatsApp system user
            from src.core.auth import get_password_hash
            
            user = User(
                tenant_id=tenant_id,
                username="whatsapp_system",
                email="whatsapp@system.local",
                full_name="WhatsApp System User",
                hashed_password=get_password_hash("system_password_not_used"),
                is_active=True,
                is_superuser=False
            )
            
            db.add(user)
            await db.flush()
            
            return user
            
        except Exception as e:
            logger.error(f"Error getting WhatsApp system user: {e}")
            return None
    
    async def _get_or_create_orchestrator_conversation(
        self,
        db: AsyncSession,
        whatsapp_conversation: WhatsAppConversation,
        contact: WhatsAppContact,
        user: User
    ) -> str:
        """
        Get or create orchestrator conversation for WhatsApp conversation.
        
        Args:
            db: Database session
            whatsapp_conversation: WhatsApp conversation
            contact: WhatsApp contact
            user: System user
            
        Returns:
            Orchestrator conversation ID
        """
        try:
            # Check if orchestrator conversation already exists
            if whatsapp_conversation.orchestrator_conversation_id:
                return whatsapp_conversation.orchestrator_conversation_id
            
            # Create new orchestrator conversation
            orchestrator_conversation = Conversation(
                user_id=user.id,
                tenant_id=user.tenant_id,
                title=f"WhatsApp: {contact.profile_name or contact.phone_number}",
                context={
                    "source": "whatsapp",
                    "phone_number": contact.phone_number,
                    "contact_name": contact.profile_name,
                    "whatsapp_conversation_id": whatsapp_conversation.id
                }
            )
            
            db.add(orchestrator_conversation)
            await db.flush()
            
            # Update WhatsApp conversation with orchestrator ID
            whatsapp_conversation.orchestrator_conversation_id = orchestrator_conversation.id
            
            return orchestrator_conversation.id
            
        except Exception as e:
            logger.error(f"Error creating orchestrator conversation: {e}")
            raise
    
    async def _send_whatsapp_response(
        self,
        db: AsyncSession,
        conversation: WhatsAppConversation,
        contact: WhatsAppContact,
        response_message: str
    ):
        """
        Send orchestrator response back to WhatsApp.
        
        Args:
            db: Database session
            conversation: WhatsApp conversation
            contact: WhatsApp contact
            response_message: Response message from orchestrator
        """
        try:
            # Check if we should send response (business hours, rate limiting, etc.)
            if not self._should_send_auto_response(conversation, contact):
                logger.info(f"Skipping auto-response for conversation {conversation.id}")
                return
            
            # Send text message
            result = await whatsapp_api_service.send_text_message(
                db=db,
                phone_number=contact.phone_number,
                message=response_message,
                conversation_id=conversation.id,
                tenant_id=contact.tenant_id
            )
            
            if result.get("status") == "success":
                logger.info(f"Sent WhatsApp response to {contact.phone_number}")
            else:
                logger.error(f"Failed to send WhatsApp response: {result.get('error')}")
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp response: {e}")
    
    def _should_send_auto_response(
        self, 
        conversation: WhatsAppConversation, 
        contact: WhatsAppContact
    ) -> bool:
        """
        Determine if we should send an automatic response.
        
        Args:
            conversation: WhatsApp conversation
            contact: WhatsApp contact
            
        Returns:
            True if should send auto-response, False otherwise
        """
        # Check if auto-response is enabled
        if not conversation.auto_response_enabled:
            return False
        
        # Check if contact is opted in
        if not contact.opt_in_status or contact.blocked:
            return False
        
        # Check business hours if required
        if conversation.business_hours_only:
            # TODO: Implement business hours check based on contact timezone
            pass
        
        # TODO: Add rate limiting per contact
        # TODO: Add escalation rules check
        
        return True
    
    async def _find_or_create_contact(
        self, 
        db: AsyncSession, 
        phone_number: str, 
        tenant_id: str
    ) -> Optional[WhatsAppContact]:
        """
        Find existing contact or create new one.
        
        Args:
            db: Database session
            phone_number: Contact's phone number
            tenant_id: Tenant ID
            
        Returns:
            WhatsApp contact or None if error
        """
        try:
            # Try to find existing contact
            result = await db.execute(
                select(WhatsAppContact).where(
                    WhatsAppContact.tenant_id == tenant_id,
                    WhatsAppContact.phone_number == phone_number
                )
            )
            contact = result.scalar_one_or_none()
            
            if contact:
                return contact
            
            # Create new contact
            contact = WhatsAppContact(
                tenant_id=tenant_id,
                phone_number=phone_number,
                whatsapp_id=phone_number,  # Use phone number as WhatsApp ID for now
                opt_in_status=True
            )
            
            db.add(contact)
            await db.flush()
            
            return contact
            
        except Exception as e:
            logger.error(f"Error finding/creating contact: {e}")
            return None
    
    async def _find_or_create_conversation(
        self, 
        db: AsyncSession, 
        contact: WhatsAppContact
    ) -> WhatsAppConversation:
        """
        Find active conversation or create new one.
        
        Args:
            db: Database session
            contact: WhatsApp contact
            
        Returns:
            WhatsApp conversation
        """
        # Try to find active conversation
        result = await db.execute(
            select(WhatsAppConversation).where(
                WhatsAppConversation.tenant_id == contact.tenant_id,
                WhatsAppConversation.contact_id == contact.id,
                WhatsAppConversation.status == "active"
            ).order_by(WhatsAppConversation.updated_at.desc())
        )
        conversation = result.scalar_one_or_none()
        
        if conversation:
            return conversation
        
        # Create new conversation
        conversation = WhatsAppConversation(
            tenant_id=contact.tenant_id,
            contact_id=contact.id,
            status="active",
            auto_response_enabled=True
        )
        
        db.add(conversation)
        await db.flush()
        
        return conversation


# Global service instance
whatsapp_orchestrator_service = WhatsAppOrchestratorService()
