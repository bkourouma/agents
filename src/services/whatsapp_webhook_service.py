"""
WhatsApp Webhook Service for processing incoming messages and events.
Handles webhook verification, message parsing, and integration with orchestrator.
"""

import os
import json
import hmac
import hashlib
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.whatsapp import (
    WhatsAppContact, WhatsAppConversation, WhatsAppMessage, WhatsAppWebhookEvent,
    WhatsAppMessageType, WhatsAppMessageStatus, WhatsAppConversationStatus
)
from src.models.user import User
from src.models.tenant import Tenant
from src.core.database import get_db

logger = logging.getLogger(__name__)


class WhatsAppWebhookService:
    """Service for handling WhatsApp webhook events."""
    
    def __init__(self):
        self.verify_token = os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN")
        self.app_secret = os.getenv("WHATSAPP_APP_SECRET")  # For signature verification
        
    async def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """
        Verify WhatsApp webhook during setup.
        
        Args:
            mode: Verification mode from WhatsApp
            token: Verification token from WhatsApp
            challenge: Challenge string to echo back
            
        Returns:
            Challenge string if verification successful, None otherwise
        """
        try:
            if mode == "subscribe" and token == self.verify_token:
                logger.info("WhatsApp webhook verification successful")
                return challenge
            else:
                logger.warning(f"WhatsApp webhook verification failed: mode={mode}, token_match={token == self.verify_token}")
                return None
        except Exception as e:
            logger.error(f"Error during webhook verification: {e}")
            return None
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature for security.
        
        Args:
            payload: Raw webhook payload
            signature: X-Hub-Signature-256 header value
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.app_secret:
            logger.warning("WhatsApp app secret not configured - skipping signature verification")
            return True
            
        try:
            # Remove 'sha256=' prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.app_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    async def process_webhook_event(self, db: AsyncSession, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process incoming WhatsApp webhook event.
        
        Args:
            db: Database session
            payload: Webhook payload from WhatsApp
            
        Returns:
            Processing result with status and details
        """
        try:
            # Log the webhook event
            webhook_event = WhatsAppWebhookEvent(
                event_type="webhook_received",
                webhook_payload=payload,
                processed=False
            )
            db.add(webhook_event)
            await db.flush()  # Get the ID
            
            results = []
            
            # Process each entry in the webhook
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    if change.get("field") == "messages":
                        result = await self._process_message_change(db, change["value"], webhook_event.id)
                        results.append(result)
            
            # Mark webhook as processed
            webhook_event.processed = True
            webhook_event.processed_at = datetime.utcnow()
            await db.commit()
            
            return {
                "status": "success",
                "processed_events": len(results),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error processing webhook event: {e}")
            if 'webhook_event' in locals():
                webhook_event.processing_error = str(e)
                webhook_event.processed_at = datetime.utcnow()
                await db.commit()
            
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _process_message_change(self, db: AsyncSession, value: Dict[str, Any], webhook_event_id: str) -> Dict[str, Any]:
        """
        Process a message change from webhook.
        
        Args:
            db: Database session
            value: Message change value from webhook
            webhook_event_id: ID of the webhook event
            
        Returns:
            Processing result
        """
        try:
            # Extract phone number ID to determine tenant
            phone_number_id = value.get("metadata", {}).get("phone_number_id")
            if not phone_number_id:
                return {"status": "error", "error": "No phone number ID in webhook"}
            
            # Process messages
            messages = value.get("messages", [])
            statuses = value.get("statuses", [])
            
            results = []
            
            # Process incoming messages
            for message_data in messages:
                result = await self._process_incoming_message(db, message_data, phone_number_id, webhook_event_id)
                results.append(result)
            
            # Process message status updates
            for status_data in statuses:
                result = await self._process_message_status(db, status_data, webhook_event_id)
                results.append(result)
            
            return {
                "status": "success",
                "processed_messages": len(messages),
                "processed_statuses": len(statuses),
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error processing message change: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _process_incoming_message(
        self, 
        db: AsyncSession, 
        message_data: Dict[str, Any], 
        phone_number_id: str,
        webhook_event_id: str
    ) -> Dict[str, Any]:
        """
        Process an incoming WhatsApp message.
        
        Args:
            db: Database session
            message_data: Message data from webhook
            phone_number_id: WhatsApp phone number ID
            webhook_event_id: ID of the webhook event
            
        Returns:
            Processing result
        """
        try:
            # Extract message details
            whatsapp_message_id = message_data.get("id")
            from_number = message_data.get("from")
            timestamp = message_data.get("timestamp")
            message_type = message_data.get("type", "text")
            
            # Find or create contact
            contact = await self._find_or_create_contact(db, from_number, message_data)
            if not contact:
                return {"status": "error", "error": "Could not create/find contact"}
            
            # Find or create conversation
            conversation = await self._find_or_create_conversation(db, contact)
            
            # Extract message content based on type
            content, media_url, media_type = self._extract_message_content(message_data, message_type)
            
            # Create message record
            message = WhatsAppMessage(
                tenant_id=contact.tenant_id,
                conversation_id=conversation.id,
                contact_id=contact.id,
                whatsapp_message_id=whatsapp_message_id,
                message_type=message_type,
                direction="inbound",
                content=content,
                media_url=media_url,
                media_type=media_type,
                status=WhatsAppMessageStatus.DELIVERED.value,
                delivered_at=datetime.fromtimestamp(int(timestamp)) if timestamp else datetime.utcnow()
            )
            
            db.add(message)
            await db.flush()
            
            # Update webhook event with message ID
            webhook_event = await db.get(WhatsAppWebhookEvent, webhook_event_id)
            if webhook_event:
                webhook_event.message_id = message.id
                webhook_event.conversation_id = conversation.id
                webhook_event.tenant_id = contact.tenant_id
            
            await db.commit()
            
            # Trigger orchestrator processing (async)
            await self._trigger_orchestrator_processing(db, message, conversation, contact)
            
            return {
                "status": "success",
                "message_id": message.id,
                "conversation_id": conversation.id,
                "contact_id": contact.id
            }
            
        except Exception as e:
            logger.error(f"Error processing incoming message: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _process_message_status(
        self, 
        db: AsyncSession, 
        status_data: Dict[str, Any], 
        webhook_event_id: str
    ) -> Dict[str, Any]:
        """
        Process message status update.
        
        Args:
            db: Database session
            status_data: Status data from webhook
            webhook_event_id: ID of the webhook event
            
        Returns:
            Processing result
        """
        try:
            whatsapp_message_id = status_data.get("id")
            status = status_data.get("status")
            timestamp = status_data.get("timestamp")
            
            # Find the message
            result = await db.execute(
                select(WhatsAppMessage).where(
                    WhatsAppMessage.whatsapp_message_id == whatsapp_message_id
                )
            )
            message = result.scalar_one_or_none()
            
            if not message:
                return {"status": "warning", "error": f"Message not found: {whatsapp_message_id}"}
            
            # Update message status
            message.status = status
            status_time = datetime.fromtimestamp(int(timestamp)) if timestamp else datetime.utcnow()
            
            if status == "delivered":
                message.delivered_at = status_time
            elif status == "read":
                message.read_at = status_time
            elif status == "failed":
                message.failed_reason = status_data.get("errors", [{}])[0].get("title", "Unknown error")
            
            await db.commit()
            
            return {
                "status": "success",
                "message_id": message.id,
                "new_status": status
            }
            
        except Exception as e:
            logger.error(f"Error processing message status: {e}")
            return {"status": "error", "error": str(e)}
    
    async def _find_or_create_contact(
        self, 
        db: AsyncSession, 
        phone_number: str, 
        message_data: Dict[str, Any]
    ) -> Optional[WhatsAppContact]:
        """
        Find existing contact or create new one.
        
        Args:
            db: Database session
            phone_number: Contact's phone number
            message_data: Message data containing contact info
            
        Returns:
            WhatsApp contact or None if error
        """
        try:
            # For now, we'll use a default tenant - in production, you'd determine tenant from phone_number_id
            # This is a simplified implementation
            default_tenant_result = await db.execute(select(Tenant).limit(1))
            default_tenant = default_tenant_result.scalar_one_or_none()
            
            if not default_tenant:
                logger.error("No tenant found for WhatsApp contact creation")
                return None
            
            # Try to find existing contact
            result = await db.execute(
                select(WhatsAppContact).where(
                    WhatsAppContact.tenant_id == default_tenant.id,
                    WhatsAppContact.phone_number == phone_number
                )
            )
            contact = result.scalar_one_or_none()
            
            if contact:
                # Update last seen
                contact.last_seen = datetime.utcnow()
                return contact
            
            # Create new contact
            profile = message_data.get("profile", {})
            contact = WhatsAppContact(
                tenant_id=default_tenant.id,
                phone_number=phone_number,
                whatsapp_id=phone_number,  # Use phone number as WhatsApp ID for now
                profile_name=profile.get("name"),
                last_seen=datetime.utcnow()
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
                WhatsAppConversation.status == WhatsAppConversationStatus.ACTIVE.value
            ).order_by(WhatsAppConversation.updated_at.desc())
        )
        conversation = result.scalar_one_or_none()
        
        if conversation:
            # Update conversation timestamp
            conversation.updated_at = datetime.utcnow()
            return conversation
        
        # Create new conversation
        conversation = WhatsAppConversation(
            tenant_id=contact.tenant_id,
            contact_id=contact.id,
            status=WhatsAppConversationStatus.ACTIVE.value,
            auto_response_enabled=True
        )
        
        db.add(conversation)
        await db.flush()
        
        return conversation
    
    def _extract_message_content(self, message_data: Dict[str, Any], message_type: str) -> tuple:
        """
        Extract content from message based on type.
        
        Args:
            message_data: Message data from webhook
            message_type: Type of message
            
        Returns:
            Tuple of (content, media_url, media_type)
        """
        content = None
        media_url = None
        media_type = None
        
        if message_type == "text":
            content = message_data.get("text", {}).get("body")
        elif message_type in ["image", "audio", "video", "document"]:
            media_data = message_data.get(message_type, {})
            content = media_data.get("caption")
            media_url = media_data.get("id")  # This is the media ID, not URL
            media_type = media_data.get("mime_type")
        elif message_type == "location":
            location = message_data.get("location", {})
            content = f"Location: {location.get('latitude')}, {location.get('longitude')}"
        elif message_type == "contact":
            contacts = message_data.get("contacts", [])
            if contacts:
                contact_info = contacts[0]
                content = f"Contact: {contact_info.get('name', {}).get('formatted_name')}"
        
        return content, media_url, media_type
    
    async def _trigger_orchestrator_processing(
        self,
        db: AsyncSession,
        message: WhatsAppMessage,
        conversation: WhatsAppConversation,
        contact: WhatsAppContact
    ):
        """
        Trigger orchestrator processing for the incoming message.
        Integrates with the existing orchestrator system for intelligent agent routing.

        Args:
            db: Database session
            message: WhatsApp message
            conversation: WhatsApp conversation
            contact: WhatsApp contact
        """
        try:
            logger.info(f"Triggering orchestrator for message {message.id} from {contact.phone_number}")

            # Import here to avoid circular imports
            from src.services.whatsapp_orchestrator_service import whatsapp_orchestrator_service

            # Process message through orchestrator
            result = await whatsapp_orchestrator_service.process_whatsapp_message(db, message)

            if result.get("status") == "success":
                logger.info(f"Successfully processed WhatsApp message {message.id} through orchestrator")
                logger.info(f"Agent response: {result.get('orchestrator_response', '')[:100]}...")
            else:
                logger.error(f"Failed to process WhatsApp message through orchestrator: {result.get('error')}")

        except Exception as e:
            logger.error(f"Error triggering orchestrator processing: {e}")


# Global service instance
whatsapp_webhook_service = WhatsAppWebhookService()
