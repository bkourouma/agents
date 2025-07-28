"""
Agent models for the AI Agent Platform.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

from src.core.database import Base


class AgentType(str, Enum):
    """Predefined agent types."""
    CUSTOMER_SERVICE = "customer_service"
    FINANCIAL_ANALYSIS = "financial_analysis"
    RESEARCH = "research"
    PROJECT_MANAGEMENT = "project_management"
    CONTENT_CREATION = "content_creation"
    DATA_ANALYSIS = "data_analysis"
    GENERAL = "general"


class AgentStatus(str, Enum):
    """Agent status."""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"


class Agent(Base):
    """Agent database model with multi-tenant support."""

    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant support
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)

    # Basic agent information
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    agent_type = Column(String(50), nullable=False, default=AgentType.GENERAL.value, index=True)
    status = Column(String(20), nullable=False, default=AgentStatus.DRAFT.value, index=True)

    # Owner relationship
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="agents")
    owner = relationship("User", back_populates="agents")
    
    # Agent configuration
    system_prompt = Column(Text, nullable=False)
    personality = Column(Text, nullable=True)
    instructions = Column(Text, nullable=True)
    
    # LLM configuration
    llm_provider = Column(String(50), nullable=False, default="openai")
    llm_model = Column(String(100), nullable=False, default="gpt-3.5-turbo")
    temperature = Column(String(10), nullable=False, default="0.7")
    max_tokens = Column(Integer, nullable=False, default=1000)
    
    # Tools and capabilities
    tools_config = Column(JSON, nullable=True)  # JSON configuration for tools
    capabilities = Column(JSON, nullable=True)  # List of capabilities
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_used = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)
    
    # Configuration flags
    is_public = Column(Boolean, default=False, nullable=False)
    is_template = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Table constraints and indexes
    __table_args__ = (
        Index('idx_agents_tenant_owner', 'tenant_id', 'owner_id'),
        Index('idx_agents_tenant_type', 'tenant_id', 'agent_type'),
        Index('idx_agents_tenant_status', 'tenant_id', 'status'),
        Index('idx_agents_tenant_active', 'tenant_id', 'is_active'),
        Index('idx_agents_created_at', 'created_at'),
    )

    # Relationships (defined after imports to avoid circular dependencies)
    # knowledge_documents = relationship("KnowledgeBaseDocument", back_populates="agent")


# Pydantic models for API
class AgentBase(BaseModel):
    """Base agent model for shared properties."""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    agent_type: AgentType = AgentType.GENERAL
    system_prompt: str = Field(..., min_length=10, max_length=5000)
    personality: Optional[str] = Field(None, max_length=1000)
    instructions: Optional[str] = Field(None, max_length=2000)
    llm_provider: str = Field(default="openai", max_length=50)
    llm_model: str = Field(default="gpt-3.5-turbo", max_length=100)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=1000, ge=1, le=4000)
    tools_config: Optional[Dict[str, Any]] = None
    capabilities: Optional[List[str]] = None
    is_public: bool = False


class AgentCreate(AgentBase):
    """Agent creation model."""
    pass


class AgentUpdate(BaseModel):
    """Agent update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    agent_type: Optional[AgentType] = None
    status: Optional[AgentStatus] = None
    system_prompt: Optional[str] = Field(None, min_length=10, max_length=5000)
    personality: Optional[str] = Field(None, max_length=1000)
    instructions: Optional[str] = Field(None, max_length=2000)
    llm_provider: Optional[str] = Field(None, max_length=50)
    llm_model: Optional[str] = Field(None, max_length=100)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=4000)
    tools_config: Optional[Dict[str, Any]] = None
    capabilities: Optional[List[str]] = None
    is_public: Optional[bool] = None


class AgentResponse(AgentBase):
    """Agent response model."""
    id: int
    tenant_id: str
    status: AgentStatus
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    usage_count: int
    is_template: bool
    is_active: bool

    class Config:
        from_attributes = True


class AgentTemplate(BaseModel):
    """Agent template model."""
    name: str
    description: str
    agent_type: AgentType
    system_prompt: str
    personality: Optional[str] = None
    instructions: Optional[str] = None
    default_tools: Optional[List[str]] = None
    default_capabilities: Optional[List[str]] = None


class AgentChat(BaseModel):
    """Agent chat request model."""
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class AgentChatResponse(BaseModel):
    """Agent chat response model."""
    response: str
    agent_id: int
    conversation_id: str
    usage: Optional[Dict[str, Any]] = None
    tools_used: Optional[List[str]] = None
    model_used: Optional[str] = None
    provider_used: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
