"""
Orchestrator models for intent analysis and agent routing.
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON, Float, Index

from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

from src.core.database import Base


class IntentCategory(str, Enum):
    """Intent categories for classification."""
    CUSTOMER_SERVICE = "customer_service"
    FINANCIAL_ANALYSIS = "financial_analysis"
    RESEARCH = "research"
    PROJECT_MANAGEMENT = "project_management"
    CONTENT_CREATION = "content_creation"
    DATA_ANALYSIS = "data_analysis"
    GENERAL = "general"
    TECHNICAL_SUPPORT = "technical_support"
    SALES = "sales"
    UNKNOWN = "unknown"


class RoutingDecision(str, Enum):
    """Routing decision types."""
    SINGLE_AGENT = "single_agent"
    MULTI_AGENT = "multi_agent"
    NO_SUITABLE_AGENT = "no_suitable_agent"
    ESCALATE_TO_HUMAN = "escalate_to_human"


class Conversation(Base):
    """Conversation tracking for orchestrator with multi-tenant support."""

    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True)  # UUID

    # Multi-tenant support
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)

    # Conversation information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String(255), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Conversation metadata
    total_messages = Column(Integer, default=0, nullable=False)
    agents_used = Column(JSON, nullable=True)  # List of agent IDs used
    primary_intent = Column(String(50), nullable=True, index=True)

    # Table constraints and indexes for multi-tenant optimization
    __table_args__ = (
        Index('idx_conversations_tenant_user', 'tenant_id', 'user_id'),
        Index('idx_conversations_tenant_activity', 'tenant_id', 'last_activity'),
        Index('idx_conversations_tenant_intent', 'tenant_id', 'primary_intent'),
        Index('idx_conversations_created_at', 'created_at'),
    )

    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User", back_populates="conversations")
    messages = relationship("ConversationMessage", back_populates="conversation")


class ConversationMessage(Base):
    """Individual messages in conversations with multi-tenant support."""

    __tablename__ = "conversation_messages"

    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant support (inherited from conversation)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)

    # Message information
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False, index=True)
    message_index = Column(Integer, nullable=False)  # Order in conversation

    # Message content
    user_message = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=True)

    # Routing information
    intent_category = Column(String(50), nullable=True, index=True)
    confidence_score = Column(Float, nullable=True)
    selected_agent_id = Column(Integer, ForeignKey("agents.id"), nullable=True, index=True)
    routing_decision = Column(String(50), nullable=True, index=True)
    routing_reasoning = Column(Text, nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    response_time_ms = Column(Integer, nullable=True)
    llm_usage = Column(JSON, nullable=True)

    # Table constraints and indexes for multi-tenant optimization
    __table_args__ = (
        Index('idx_conv_messages_tenant_conv', 'tenant_id', 'conversation_id'),
        Index('idx_conv_messages_tenant_agent', 'tenant_id', 'selected_agent_id'),
        Index('idx_conv_messages_tenant_intent', 'tenant_id', 'intent_category'),
        Index('idx_conv_messages_tenant_decision', 'tenant_id', 'routing_decision'),
        Index('idx_conv_messages_created_at', 'created_at'),
    )

    # Relationships
    tenant = relationship("Tenant")
    conversation = relationship("Conversation", back_populates="messages")
    selected_agent = relationship("Agent")


# Add relationships to existing models
from src.models.user import User
from src.models.agent import Agent

User.conversations = relationship("Conversation", back_populates="user")


# Pydantic models for API
class IntentAnalysis(BaseModel):
    """Intent analysis result."""
    category: IntentCategory
    confidence: float = Field(..., ge=0.0, le=1.0)
    keywords: List[str] = []
    reasoning: str
    suggested_agents: List[int] = []


class AgentMatch(BaseModel):
    """Agent matching result."""
    agent_id: int
    agent_name: str
    agent_type: str
    match_score: float = Field(..., ge=0.0, le=1.0)
    match_reasoning: str


class RoutingResult(BaseModel):
    """Orchestrator routing result."""
    decision: RoutingDecision
    intent_analysis: IntentAnalysis
    selected_agent: Optional[AgentMatch] = None
    alternative_agents: List[AgentMatch] = []
    reasoning: str
    confidence: float = Field(..., ge=0.0, le=1.0)


class OrchestratorRequest(BaseModel):
    """Request to orchestrator for routing."""
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    user_preferences: Optional[Dict[str, Any]] = None


class OrchestratorResponse(BaseModel):
    """Response from orchestrator."""
    conversation_id: str
    message_index: int
    user_message: str
    agent_response: str
    routing_result: RoutingResult
    response_time_ms: int
    usage: Optional[Dict[str, Any]] = None
    debug_info: Optional[str] = None


class ConversationSummary(BaseModel):
    """Conversation summary."""
    id: str
    title: Optional[str]
    created_at: datetime
    last_activity: datetime
    total_messages: int
    primary_intent: Optional[str]
    agents_used: List[int] = []
    
    class Config:
        from_attributes = True


class MessageHistory(BaseModel):
    """Message history item."""
    message_index: int
    user_message: str
    agent_response: Optional[str]
    intent_category: Optional[str]
    confidence_score: Optional[float]
    selected_agent_id: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationDetail(BaseModel):
    """Detailed conversation with messages."""
    conversation: ConversationSummary
    messages: List[MessageHistory]
