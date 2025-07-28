"""
WhatsApp API endpoints for webhook handling, message management, and conversation history.
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, func
from sqlalchemy.orm import selectinload

from src.core.database import get_db
from src.api.users import get_current_user_from_token
from src.models.user import User
from src.models.whatsapp import (
    WhatsAppContact, WhatsAppConversation, WhatsAppMessage, WhatsAppWebhookEvent,
    WhatsAppContactResponse, WhatsAppConversationResponse, WhatsAppMessageResponse,
    WhatsAppSendMessageRequest, WhatsAppWebhookPayload
)
from src.services.whatsapp_webhook_service import whatsapp_webhook_service
from src.services.whatsapp_api_service import whatsapp_api_service
from src.services.whatsapp_orchestrator_service import whatsapp_orchestrator_service

logger = logging.getLogger(__name__)

router = APIRouter()


# Webhook endpoints (no authentication required)
@router.get("/webhook")
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode"),
    hub_verify_token: str = Query(alias="hub.verify_token"),
    hub_challenge: str = Query(alias="hub.challenge")
):
    """
    Verify WhatsApp webhook during setup.
    This endpoint is called by WhatsApp to verify the webhook URL.
    """
    try:
        challenge = await whatsapp_webhook_service.verify_webhook(
            mode=hub_mode,
            token=hub_verify_token,
            challenge=hub_challenge
        )
        
        if challenge:
            return PlainTextResponse(challenge)
        else:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Webhook verification failed"
            )
    except Exception as e:
        logger.error(f"Webhook verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Webhook verification error"
        )


@router.post("/webhook")
async def handle_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle incoming WhatsApp webhook events.
    This endpoint receives messages, status updates, and other events from WhatsApp.
    """
    try:
        # Get raw body for signature verification
        body = await request.body()
        
        # Verify webhook signature if configured
        signature = request.headers.get("X-Hub-Signature-256", "")
        if not whatsapp_webhook_service.verify_signature(body, signature):
            logger.warning("Invalid webhook signature")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid signature"
            )
        
        # Parse JSON payload
        payload = await request.json()
        
        # Process webhook event
        result = await whatsapp_webhook_service.process_webhook_event(db, payload)
        
        if result.get("status") == "success":
            return {"status": "ok"}
        else:
            logger.error(f"Webhook processing failed: {result.get('error')}")
            return {"status": "error", "message": result.get("error")}
            
    except Exception as e:
        logger.error(f"Webhook handling error: {e}")
        return {"status": "error", "message": str(e)}


# Authenticated endpoints
@router.get("/contacts", response_model=List[WhatsAppContactResponse])
async def get_contacts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    search: Optional[str] = Query(None)
):
    """Get WhatsApp contacts for the current tenant."""
    try:
        query = select(WhatsAppContact).where(
            WhatsAppContact.tenant_id == current_user.tenant_id
        )
        
        # Add search filter
        if search:
            search_filter = f"%{search}%"
            query = query.where(
                (WhatsAppContact.phone_number.ilike(search_filter)) |
                (WhatsAppContact.profile_name.ilike(search_filter)) |
                (WhatsAppContact.first_name.ilike(search_filter)) |
                (WhatsAppContact.last_name.ilike(search_filter))
            )
        
        query = query.order_by(desc(WhatsAppContact.last_seen)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        contacts = result.scalars().all()
        
        return [WhatsAppContactResponse.from_orm(contact) for contact in contacts]
        
    except Exception as e:
        logger.error(f"Error getting contacts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve contacts"
        )


@router.get("/conversations", response_model=List[WhatsAppConversationResponse])
async def get_conversations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0),
    status_filter: Optional[str] = Query(None, alias="status")
):
    """Get WhatsApp conversations for the current tenant."""
    try:
        query = select(WhatsAppConversation).options(
            selectinload(WhatsAppConversation.contact)
        ).where(
            WhatsAppConversation.tenant_id == current_user.tenant_id
        )
        
        # Add status filter
        if status_filter:
            query = query.where(WhatsAppConversation.status == status_filter)
        
        query = query.order_by(desc(WhatsAppConversation.updated_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        conversations = result.scalars().all()
        
        # Get message counts and last messages
        conversation_responses = []
        for conversation in conversations:
            # Get message count
            count_result = await db.execute(
                select(func.count(WhatsAppMessage.id)).where(
                    WhatsAppMessage.conversation_id == conversation.id
                )
            )
            message_count = count_result.scalar()
            
            # Get last message
            last_message_result = await db.execute(
                select(WhatsAppMessage).where(
                    WhatsAppMessage.conversation_id == conversation.id
                ).order_by(desc(WhatsAppMessage.created_at)).limit(1)
            )
            last_message = last_message_result.scalar_one_or_none()
            
            conversation_response = WhatsAppConversationResponse.from_orm(conversation)
            conversation_response.message_count = message_count
            if last_message:
                conversation_response.last_message = WhatsAppMessageResponse.from_orm(last_message)
            
            conversation_responses.append(conversation_response)
        
        return conversation_responses
        
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations"
        )


@router.get("/conversations/{conversation_id}/messages", response_model=List[WhatsAppMessageResponse])
async def get_conversation_messages(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    """Get messages for a specific WhatsApp conversation."""
    try:
        # Verify conversation belongs to user's tenant
        conversation_result = await db.execute(
            select(WhatsAppConversation).where(
                WhatsAppConversation.id == conversation_id,
                WhatsAppConversation.tenant_id == current_user.tenant_id
            )
        )
        conversation = conversation_result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Get messages
        query = select(WhatsAppMessage).where(
            WhatsAppMessage.conversation_id == conversation_id
        ).order_by(desc(WhatsAppMessage.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        messages = result.scalars().all()
        
        return [WhatsAppMessageResponse.from_orm(message) for message in messages]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation messages: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages"
        )


@router.post("/send-message")
async def send_message(
    request: WhatsAppSendMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Send a WhatsApp message."""
    try:
        result = None
        
        if request.template_name:
            # Send template message
            result = await whatsapp_api_service.send_template_message(
                db=db,
                phone_number=request.phone_number,
                template_name=request.template_name,
                language_code=request.language_code,
                parameters=request.template_parameters,
                tenant_id=current_user.tenant_id
            )
        elif request.media_url:
            # Send media message
            result = await whatsapp_api_service.send_media_message(
                db=db,
                phone_number=request.phone_number,
                media_type=request.message_type,
                media_url=request.media_url,
                caption=request.content,
                tenant_id=current_user.tenant_id
            )
        else:
            # Send text message
            result = await whatsapp_api_service.send_text_message(
                db=db,
                phone_number=request.phone_number,
                message=request.content or "",
                tenant_id=current_user.tenant_id
            )
        
        if result.get("status") == "success":
            return {
                "status": "success",
                "message_id": result.get("whatsapp_message_id"),
                "phone_number": request.phone_number
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to send message")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )


@router.post("/send-proactive-message")
async def send_proactive_message(
    phone_number: str,
    message: str,
    template_name: Optional[str] = None,
    template_parameters: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Send a proactive WhatsApp message (for marketing, notifications, etc.)."""
    try:
        result = await whatsapp_orchestrator_service.send_proactive_message(
            db=db,
            phone_number=phone_number,
            message=message,
            tenant_id=current_user.tenant_id,
            template_name=template_name,
            template_parameters=template_parameters
        )
        
        if result.get("status") == "success":
            return {
                "status": "success",
                "message_id": result.get("whatsapp_message_id"),
                "phone_number": phone_number
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("error", "Failed to send proactive message")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending proactive WhatsApp message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send proactive message"
        )


@router.get("/webhook-events")
async def get_webhook_events(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token),
    limit: int = Query(50, le=100),
    offset: int = Query(0, ge=0)
):
    """Get WhatsApp webhook events for debugging."""
    try:
        query = select(WhatsAppWebhookEvent).where(
            WhatsAppWebhookEvent.tenant_id == current_user.tenant_id
        ).order_by(desc(WhatsAppWebhookEvent.created_at)).limit(limit).offset(offset)
        
        result = await db.execute(query)
        events = result.scalars().all()
        
        return [
            {
                "id": event.id,
                "event_type": event.event_type,
                "processed": event.processed,
                "processing_error": event.processing_error,
                "created_at": event.created_at,
                "processed_at": event.processed_at,
                "payload": event.webhook_payload
            }
            for event in events
        ]
        
    except Exception as e:
        logger.error(f"Error getting webhook events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve webhook events"
        )


@router.get("/status")
async def get_whatsapp_status():
    """Get WhatsApp integration status."""
    try:
        # Check if WhatsApp API is configured
        import os
        
        status_info = {
            "configured": bool(os.getenv("WHATSAPP_ACCESS_TOKEN")),
            "phone_number_id": os.getenv("WHATSAPP_PHONE_NUMBER_ID"),
            "api_version": os.getenv("WHATSAPP_API_VERSION", "v18.0"),
            "webhook_configured": bool(os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN"))
        }
        
        return status_info
        
    except Exception as e:
        logger.error(f"Error getting WhatsApp status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get WhatsApp status"
        )
