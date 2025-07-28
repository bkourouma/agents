"""
WhatsApp models for conversation and message management.
Enhanced for multi-tenant support with proper isolation.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

from src.core.database import Base


class WhatsAppMessageType(str, Enum):
    """WhatsApp message types."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"
    CONTACT = "contact"
    STICKER = "sticker"
    TEMPLATE = "template"
    INTERACTIVE = "interactive"
    BUTTON = "button"
    LIST = "list"


class WhatsAppMessageStatus(str, Enum):
    """WhatsApp message delivery status."""
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    PENDING = "pending"


class WhatsAppConversationStatus(str, Enum):
    """WhatsApp conversation status."""
    ACTIVE = "active"
    CLOSED = "closed"
    ARCHIVED = "archived"


class WhatsAppContact(Base):
    """WhatsApp contact information with tenant isolation."""
    
    __tablename__ = "whatsapp_contacts"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Multi-tenant support
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # WhatsApp contact details
    phone_number = Column(String(20), nullable=False, index=True)
    whatsapp_id = Column(String(100), nullable=False, index=True)  # WhatsApp user ID
    profile_name = Column(String(255))
    
    # Contact metadata
    first_name = Column(String(100))
    last_name = Column(String(100))
    email = Column(String(255))
    language_code = Column(String(10), default="fr")  # Default to French
    timezone = Column(String(50))
    
    # Contact preferences
    opt_in_status = Column(Boolean, default=True)
    blocked = Column(Boolean, default=False)
    tags = Column(JSON)  # Store contact tags as JSON
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    last_seen = Column(DateTime)
    
    # Relationships
    conversations = relationship("WhatsAppConversation", back_populates="contact")
    messages = relationship("WhatsAppMessage", back_populates="contact")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('idx_whatsapp_contacts_tenant_phone', 'tenant_id', 'phone_number', unique=True),
        Index('idx_whatsapp_contacts_tenant_whatsapp_id', 'tenant_id', 'whatsapp_id', unique=True),
        Index('idx_whatsapp_contacts_opt_in', 'tenant_id', 'opt_in_status'),
        Index('idx_whatsapp_contacts_created_at', 'created_at'),
    )


class WhatsAppConversation(Base):
    """WhatsApp conversation with agent routing and tenant isolation."""
    
    __tablename__ = "whatsapp_conversations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Multi-tenant support
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Contact and agent relationships
    contact_id = Column(String(36), ForeignKey("whatsapp_contacts.id"), nullable=False)
    assigned_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    
    # Conversation metadata
    status = Column(String(20), default=WhatsAppConversationStatus.ACTIVE.value)
    subject = Column(String(255))
    priority = Column(String(20), default="normal")  # low, normal, high, urgent
    
    # Orchestrator integration
    orchestrator_conversation_id = Column(String(36))  # Link to orchestrator conversation
    last_agent_response = Column(DateTime)
    auto_response_enabled = Column(Boolean, default=True)
    
    # Business hours and routing
    business_hours_only = Column(Boolean, default=False)
    escalation_rules = Column(JSON)  # Store escalation rules as JSON
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    closed_at = Column(DateTime)
    
    # Relationships
    contact = relationship("WhatsAppContact", back_populates="conversations")
    messages = relationship("WhatsAppMessage", back_populates="conversation")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('idx_whatsapp_conversations_tenant_contact', 'tenant_id', 'contact_id'),
        Index('idx_whatsapp_conversations_tenant_agent', 'tenant_id', 'assigned_agent_id'),
        Index('idx_whatsapp_conversations_status', 'tenant_id', 'status'),
        Index('idx_whatsapp_conversations_created_at', 'created_at'),
    )


class WhatsAppMessage(Base):
    """WhatsApp message with orchestrator integration and tenant isolation."""
    
    __tablename__ = "whatsapp_messages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Multi-tenant support
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    
    # Message relationships
    conversation_id = Column(String(36), ForeignKey("whatsapp_conversations.id"), nullable=False)
    contact_id = Column(String(36), ForeignKey("whatsapp_contacts.id"), nullable=False)
    
    # WhatsApp message details
    whatsapp_message_id = Column(String(100), unique=True, index=True)  # WhatsApp's message ID
    message_type = Column(String(20), default=WhatsAppMessageType.TEXT.value)
    direction = Column(String(10))  # "inbound" or "outbound"
    
    # Message content
    content = Column(Text)  # Text content or caption
    media_url = Column(String(500))  # URL for media files
    media_type = Column(String(50))  # image/jpeg, audio/ogg, etc.
    media_size = Column(Integer)  # File size in bytes
    
    # Message status and delivery
    status = Column(String(20), default=WhatsAppMessageStatus.PENDING.value)
    delivered_at = Column(DateTime)
    read_at = Column(DateTime)
    failed_reason = Column(String(255))
    
    # Agent and orchestrator integration
    processed_by_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True)
    orchestrator_message_id = Column(String(36))  # Link to orchestrator message
    auto_generated = Column(Boolean, default=False)
    
    # Template and interactive messages
    template_name = Column(String(100))
    template_language = Column(String(10))
    interactive_data = Column(JSON)  # Store interactive message data
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    conversation = relationship("WhatsAppConversation", back_populates="messages")
    contact = relationship("WhatsAppContact", back_populates="messages")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('idx_whatsapp_messages_tenant_conversation', 'tenant_id', 'conversation_id'),
        Index('idx_whatsapp_messages_tenant_contact', 'tenant_id', 'contact_id'),
        Index('idx_whatsapp_messages_direction_status', 'direction', 'status'),
        Index('idx_whatsapp_messages_created_at', 'created_at'),
        Index('idx_whatsapp_messages_whatsapp_id', 'whatsapp_message_id'),
    )


class WhatsAppWebhookEvent(Base):
    """WhatsApp webhook event logging for debugging and audit."""
    
    __tablename__ = "whatsapp_webhook_events"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Multi-tenant support (nullable for system-level events)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)
    
    # Webhook event details
    event_type = Column(String(50), nullable=False)  # message, status, etc.
    webhook_payload = Column(JSON, nullable=False)  # Full webhook payload
    processed = Column(Boolean, default=False)
    processing_error = Column(Text)
    
    # Related entities
    message_id = Column(String(36), ForeignKey("whatsapp_messages.id"), nullable=True)
    conversation_id = Column(String(36), ForeignKey("whatsapp_conversations.id"), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=func.now(), nullable=False)
    processed_at = Column(DateTime)
    
    # Table constraints and indexes
    __table_args__ = (
        Index('idx_whatsapp_webhook_events_tenant_type', 'tenant_id', 'event_type'),
        Index('idx_whatsapp_webhook_events_processed', 'processed'),
        Index('idx_whatsapp_webhook_events_created_at', 'created_at'),
    )


# Pydantic models for API
class WhatsAppContactBase(BaseModel):
    """Base WhatsApp contact model."""
    phone_number: str = Field(..., pattern=r'^\+[1-9]\d{1,14}$')
    profile_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    language_code: str = "fr"
    timezone: Optional[str] = None
    tags: Optional[List[str]] = None


class WhatsAppContactCreate(WhatsAppContactBase):
    """WhatsApp contact creation model."""
    whatsapp_id: str


class WhatsAppContactResponse(WhatsAppContactBase):
    """WhatsApp contact response model."""
    id: str
    whatsapp_id: str
    opt_in_status: bool
    blocked: bool
    created_at: datetime
    last_seen: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WhatsAppMessageBase(BaseModel):
    """Base WhatsApp message model."""
    message_type: WhatsAppMessageType = WhatsAppMessageType.TEXT
    content: Optional[str] = None
    media_url: Optional[str] = None
    template_name: Optional[str] = None
    template_language: str = "fr"


class WhatsAppMessageCreate(WhatsAppMessageBase):
    """WhatsApp message creation model."""
    contact_phone_number: str = Field(..., pattern=r'^\+[1-9]\d{1,14}$')


class WhatsAppMessageResponse(WhatsAppMessageBase):
    """WhatsApp message response model."""
    id: str
    conversation_id: str
    direction: str
    status: WhatsAppMessageStatus
    created_at: datetime
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class WhatsAppConversationResponse(BaseModel):
    """WhatsApp conversation response model."""
    id: str
    contact: WhatsAppContactResponse
    status: WhatsAppConversationStatus
    subject: Optional[str] = None
    priority: str
    assigned_agent_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = None
    last_message: Optional[WhatsAppMessageResponse] = None
    
    class Config:
        from_attributes = True


class WhatsAppWebhookPayload(BaseModel):
    """WhatsApp webhook payload model."""
    object: str
    entry: List[Dict[str, Any]]


class WhatsAppSendMessageRequest(BaseModel):
    """Request model for sending WhatsApp messages."""
    phone_number: str = Field(..., pattern=r'^\+[1-9]\d{1,14}$')
    message_type: WhatsAppMessageType = WhatsAppMessageType.TEXT
    content: Optional[str] = None
    media_url: Optional[str] = None
    template_name: Optional[str] = None
    template_parameters: Optional[List[str]] = None
    language_code: str = "fr"
