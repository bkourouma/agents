"""
WhatsApp API Service for sending messages and managing WhatsApp Business API.
Handles message sending, templates, media uploads, and rate limiting.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.models.whatsapp import (
    WhatsAppMessage, WhatsAppContact, WhatsAppConversation,
    WhatsAppMessageType, WhatsAppMessageStatus
)

logger = logging.getLogger(__name__)


class WhatsAppAPIService:
    """Service for interacting with WhatsApp Business API."""
    
    def __init__(self):
        self.access_token = os.getenv("WHATSAPP_ACCESS_TOKEN")
        self.phone_number_id = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
        self.api_version = os.getenv("WHATSAPP_API_VERSION", "v18.0")
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        
        # Rate limiting
        self.rate_limit_per_second = 80  # WhatsApp allows 80 messages per second
        self.rate_limit_per_minute = 1000  # 1000 messages per minute
        self.last_request_time = datetime.utcnow()
        self.requests_this_second = 0
        self.requests_this_minute = 0
        
        # HTTP client
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()
    
    async def send_text_message(
        self, 
        db: AsyncSession,
        phone_number: str, 
        message: str,
        conversation_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a text message via WhatsApp.
        
        Args:
            db: Database session
            phone_number: Recipient phone number
            message: Text message content
            conversation_id: Optional conversation ID
            tenant_id: Optional tenant ID
            
        Returns:
            API response with message details
        """
        try:
            # Rate limiting check
            await self._check_rate_limit()
            
            # Prepare message payload
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "text",
                "text": {
                    "body": message
                }
            }
            
            # Send message
            response = await self._make_api_request(
                method="POST",
                endpoint=f"/{self.phone_number_id}/messages",
                data=payload
            )
            
            if response.get("messages"):
                whatsapp_message_id = response["messages"][0]["id"]
                
                # Save message to database
                await self._save_outbound_message(
                    db=db,
                    phone_number=phone_number,
                    whatsapp_message_id=whatsapp_message_id,
                    message_type=WhatsAppMessageType.TEXT,
                    content=message,
                    conversation_id=conversation_id,
                    tenant_id=tenant_id
                )
                
                return {
                    "status": "success",
                    "whatsapp_message_id": whatsapp_message_id,
                    "phone_number": phone_number
                }
            else:
                return {
                    "status": "error",
                    "error": "No message ID returned from WhatsApp API"
                }
                
        except Exception as e:
            logger.error(f"Error sending text message to {phone_number}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def send_template_message(
        self,
        db: AsyncSession,
        phone_number: str,
        template_name: str,
        language_code: str = "fr",
        parameters: Optional[List[str]] = None,
        conversation_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a template message via WhatsApp.
        
        Args:
            db: Database session
            phone_number: Recipient phone number
            template_name: Name of the approved template
            language_code: Template language code
            parameters: Template parameters
            conversation_id: Optional conversation ID
            tenant_id: Optional tenant ID
            
        Returns:
            API response with message details
        """
        try:
            # Rate limiting check
            await self._check_rate_limit()
            
            # Prepare template payload
            template_payload = {
                "name": template_name,
                "language": {
                    "code": language_code
                }
            }
            
            # Add parameters if provided
            if parameters:
                template_payload["components"] = [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": param} for param in parameters
                        ]
                    }
                ]
            
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": "template",
                "template": template_payload
            }
            
            # Send message
            response = await self._make_api_request(
                method="POST",
                endpoint=f"/{self.phone_number_id}/messages",
                data=payload
            )
            
            if response.get("messages"):
                whatsapp_message_id = response["messages"][0]["id"]
                
                # Save message to database
                await self._save_outbound_message(
                    db=db,
                    phone_number=phone_number,
                    whatsapp_message_id=whatsapp_message_id,
                    message_type=WhatsAppMessageType.TEMPLATE,
                    content=f"Template: {template_name}",
                    conversation_id=conversation_id,
                    tenant_id=tenant_id,
                    template_name=template_name,
                    template_language=language_code
                )
                
                return {
                    "status": "success",
                    "whatsapp_message_id": whatsapp_message_id,
                    "phone_number": phone_number,
                    "template_name": template_name
                }
            else:
                return {
                    "status": "error",
                    "error": "No message ID returned from WhatsApp API"
                }
                
        except Exception as e:
            logger.error(f"Error sending template message to {phone_number}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def send_media_message(
        self,
        db: AsyncSession,
        phone_number: str,
        media_type: WhatsAppMessageType,
        media_url: str,
        caption: Optional[str] = None,
        conversation_id: Optional[str] = None,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send a media message via WhatsApp.
        
        Args:
            db: Database session
            phone_number: Recipient phone number
            media_type: Type of media (image, audio, video, document)
            media_url: URL of the media file
            caption: Optional caption for the media
            conversation_id: Optional conversation ID
            tenant_id: Optional tenant ID
            
        Returns:
            API response with message details
        """
        try:
            # Rate limiting check
            await self._check_rate_limit()
            
            # Prepare media payload
            media_payload = {
                "link": media_url
            }
            
            if caption and media_type in [WhatsAppMessageType.IMAGE, WhatsAppMessageType.VIDEO, WhatsAppMessageType.DOCUMENT]:
                media_payload["caption"] = caption
            
            payload = {
                "messaging_product": "whatsapp",
                "to": phone_number,
                "type": media_type.value,
                media_type.value: media_payload
            }
            
            # Send message
            response = await self._make_api_request(
                method="POST",
                endpoint=f"/{self.phone_number_id}/messages",
                data=payload
            )
            
            if response.get("messages"):
                whatsapp_message_id = response["messages"][0]["id"]
                
                # Save message to database
                await self._save_outbound_message(
                    db=db,
                    phone_number=phone_number,
                    whatsapp_message_id=whatsapp_message_id,
                    message_type=media_type,
                    content=caption,
                    media_url=media_url,
                    conversation_id=conversation_id,
                    tenant_id=tenant_id
                )
                
                return {
                    "status": "success",
                    "whatsapp_message_id": whatsapp_message_id,
                    "phone_number": phone_number,
                    "media_type": media_type.value
                }
            else:
                return {
                    "status": "error",
                    "error": "No message ID returned from WhatsApp API"
                }
                
        except Exception as e:
            logger.error(f"Error sending media message to {phone_number}: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def get_media_url(self, media_id: str) -> Optional[str]:
        """
        Get the download URL for a media file.
        
        Args:
            media_id: WhatsApp media ID
            
        Returns:
            Media download URL or None if error
        """
        try:
            response = await self._make_api_request(
                method="GET",
                endpoint=f"/{media_id}"
            )
            
            return response.get("url")
            
        except Exception as e:
            logger.error(f"Error getting media URL for {media_id}: {e}")
            return None
    
    async def download_media(self, media_url: str) -> Optional[bytes]:
        """
        Download media content from WhatsApp.
        
        Args:
            media_url: Media download URL
            
        Returns:
            Media content as bytes or None if error
        """
        try:
            response = await self.client.get(media_url)
            response.raise_for_status()
            return response.content
            
        except Exception as e:
            logger.error(f"Error downloading media from {media_url}: {e}")
            return None
    
    async def mark_message_as_read(self, whatsapp_message_id: str) -> bool:
        """
        Mark a message as read.
        
        Args:
            whatsapp_message_id: WhatsApp message ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": whatsapp_message_id
            }
            
            response = await self._make_api_request(
                method="POST",
                endpoint=f"/{self.phone_number_id}/messages",
                data=payload
            )
            
            return response.get("success", False)
            
        except Exception as e:
            logger.error(f"Error marking message as read {whatsapp_message_id}: {e}")
            return False
    
    async def _check_rate_limit(self):
        """Check and enforce rate limiting."""
        now = datetime.utcnow()
        
        # Reset counters if needed
        if (now - self.last_request_time).total_seconds() >= 1:
            self.requests_this_second = 0
        
        if (now - self.last_request_time).total_seconds() >= 60:
            self.requests_this_minute = 0
        
        # Check rate limits
        if self.requests_this_second >= self.rate_limit_per_second:
            sleep_time = 1 - (now - self.last_request_time).total_seconds()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                self.requests_this_second = 0
        
        if self.requests_this_minute >= self.rate_limit_per_minute:
            sleep_time = 60 - (now - self.last_request_time).total_seconds()
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
                self.requests_this_minute = 0
        
        # Update counters
        self.requests_this_second += 1
        self.requests_this_minute += 1
        self.last_request_time = now
    
    async def _make_api_request(
        self, 
        method: str, 
        endpoint: str, 
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Make an API request to WhatsApp Business API.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request data
            
        Returns:
            API response
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            if method == "GET":
                response = await self.client.get(url)
            elif method == "POST":
                response = await self.client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json()
            
        except httpx.HTTPStatusError as e:
            logger.error(f"WhatsApp API error {e.response.status_code}: {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Error making API request to {url}: {e}")
            raise
    
    async def _save_outbound_message(
        self,
        db: AsyncSession,
        phone_number: str,
        whatsapp_message_id: str,
        message_type: WhatsAppMessageType,
        content: Optional[str] = None,
        media_url: Optional[str] = None,
        conversation_id: Optional[str] = None,
        tenant_id: Optional[str] = None,
        template_name: Optional[str] = None,
        template_language: Optional[str] = None
    ):
        """
        Save outbound message to database.
        
        Args:
            db: Database session
            phone_number: Recipient phone number
            whatsapp_message_id: WhatsApp message ID
            message_type: Type of message
            content: Message content
            media_url: Media URL if applicable
            conversation_id: Conversation ID
            tenant_id: Tenant ID
            template_name: Template name if applicable
            template_language: Template language if applicable
        """
        try:
            # Find contact
            contact_result = await db.execute(
                select(WhatsAppContact).where(
                    WhatsAppContact.phone_number == phone_number
                )
            )
            contact = contact_result.scalar_one_or_none()
            
            if not contact:
                logger.warning(f"Contact not found for phone number {phone_number}")
                return
            
            # Find conversation
            if conversation_id:
                conversation_result = await db.execute(
                    select(WhatsAppConversation).where(
                        WhatsAppConversation.id == conversation_id
                    )
                )
                conversation = conversation_result.scalar_one_or_none()
            else:
                # Find active conversation
                conversation_result = await db.execute(
                    select(WhatsAppConversation).where(
                        WhatsAppConversation.contact_id == contact.id,
                        WhatsAppConversation.status == "active"
                    ).order_by(WhatsAppConversation.updated_at.desc())
                )
                conversation = conversation_result.scalar_one_or_none()
            
            if not conversation:
                logger.warning(f"No conversation found for contact {contact.id}")
                return
            
            # Create message record
            message = WhatsAppMessage(
                tenant_id=tenant_id or contact.tenant_id,
                conversation_id=conversation.id,
                contact_id=contact.id,
                whatsapp_message_id=whatsapp_message_id,
                message_type=message_type.value,
                direction="outbound",
                content=content,
                media_url=media_url,
                status=WhatsAppMessageStatus.SENT.value,
                template_name=template_name,
                template_language=template_language,
                auto_generated=True
            )
            
            db.add(message)
            await db.commit()
            
        except Exception as e:
            logger.error(f"Error saving outbound message: {e}")


# Global service instance
whatsapp_api_service = WhatsAppAPIService()
