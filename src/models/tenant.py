"""
Tenant models for multi-tenant support in the AI Agent Platform.
Enhanced for PostgreSQL with advanced features.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, Index, JSON, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid

from src.core.database import Base


class TenantStatus(str, Enum):
    """Tenant status options."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    EXPIRED = "expired"


class TenantPlan(str, Enum):
    """Tenant subscription plans."""
    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class Tenant(Base):
    """Tenant model for multi-tenant isolation."""
    
    __tablename__ = "tenants"
    
    # Primary key - UUID stored as string for SQLite compatibility
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    
    # Basic tenant information
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    domain = Column(String(255), unique=True, nullable=True, index=True)
    
    # Contact information
    contact_email = Column(String(255), nullable=True)
    contact_name = Column(String(255), nullable=True)
    
    # Status and plan
    status = Column(String(20), nullable=False, default=TenantStatus.TRIAL.value, index=True)
    plan = Column(String(20), nullable=False, default=TenantPlan.FREE.value, index=True)
    
    # Database-agnostic features (compatible with SQLite and PostgreSQL)
    settings = Column(JSON, default={}, nullable=False)
    features = Column(JSON, default=[], nullable=False)  # Store as JSON array for SQLite compatibility
    tenant_metadata = Column(JSON, default={}, nullable=False)
    
    # Limits and quotas
    max_users = Column(Integer, default=5, nullable=False)
    max_agents = Column(Integer, default=10, nullable=False)
    max_storage_mb = Column(Integer, default=1000, nullable=False)  # 1GB default
    
    # Billing information
    billing_email = Column(String(255), nullable=True)
    subscription_id = Column(String(255), nullable=True)
    trial_ends_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_activity = Column(DateTime(timezone=True), nullable=True)
    
    # Soft delete
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    users = relationship("User", back_populates="tenant")
    agents = relationship("Agent", back_populates="tenant")
    
    # Table constraints and indexes
    __table_args__ = (
        Index('idx_tenant_slug_active', 'slug', 'is_active'),
        Index('idx_tenant_domain_active', 'domain', 'is_active'),
        Index('idx_tenant_status_plan', 'status', 'plan'),
        Index('idx_tenant_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Tenant(name='{self.name}', slug='{self.slug}', status='{self.status}')>"


# Pydantic models for API
class TenantBase(BaseModel):
    """Base tenant model for shared properties."""
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=100, pattern=r'^[a-z0-9-]+$')
    domain: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_name: Optional[str] = Field(None, max_length=255)
    plan: TenantPlan = TenantPlan.FREE
    settings: Optional[Dict[str, Any]] = {}
    features: Optional[List[str]] = []
    max_users: int = Field(default=5, ge=1, le=1000)
    max_agents: int = Field(default=10, ge=1, le=100)
    max_storage_mb: int = Field(default=1000, ge=100, le=100000)


class TenantCreate(TenantBase):
    """Tenant creation model."""
    billing_email: Optional[EmailStr] = None


class TenantUpdate(BaseModel):
    """Tenant update model."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    domain: Optional[str] = Field(None, max_length=255)
    contact_email: Optional[EmailStr] = None
    contact_name: Optional[str] = Field(None, max_length=255)
    status: Optional[TenantStatus] = None
    plan: Optional[TenantPlan] = None
    settings: Optional[Dict[str, Any]] = None
    features: Optional[List[str]] = None
    max_users: Optional[int] = Field(None, ge=1, le=1000)
    max_agents: Optional[int] = Field(None, ge=1, le=100)
    max_storage_mb: Optional[int] = Field(None, ge=100, le=100000)
    billing_email: Optional[EmailStr] = None


class TenantResponse(TenantBase):
    """Tenant response model."""
    id: uuid.UUID
    status: TenantStatus
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    trial_ends_at: Optional[datetime] = None
    is_active: bool
    
    # Usage statistics (computed fields)
    current_users: Optional[int] = None
    current_agents: Optional[int] = None
    current_storage_mb: Optional[int] = None
    
    class Config:
        from_attributes = True


class TenantStats(BaseModel):
    """Tenant usage statistics."""
    tenant_id: uuid.UUID
    total_users: int
    active_users: int
    total_agents: int
    active_agents: int
    total_conversations: int
    total_messages: int
    storage_used_mb: int
    last_activity: Optional[datetime] = None


class TenantInvitation(BaseModel):
    """Tenant invitation model."""
    tenant_id: uuid.UUID
    email: EmailStr
    role: str = "user"
    invited_by: str
    expires_at: datetime


class TenantSettings(BaseModel):
    """Tenant settings model."""
    # UI preferences
    theme: str = "light"
    language: str = "en"
    timezone: str = "UTC"
    
    # Feature flags
    enable_database_chat: bool = True
    enable_knowledge_base: bool = True
    enable_file_upload: bool = True
    enable_api_access: bool = False
    
    # Limits
    max_conversation_history: int = 100
    max_file_size_mb: int = 10
    max_agents_per_user: int = 5
    
    # Integrations
    allowed_llm_providers: List[str] = ["openai"]
    custom_branding: Dict[str, Any] = {}


class TenantFeatures(BaseModel):
    """Available tenant features."""
    database_chat: bool = True
    knowledge_base: bool = True
    file_upload: bool = True
    api_access: bool = False
    custom_agents: bool = True
    agent_sharing: bool = False
    advanced_analytics: bool = False
    priority_support: bool = False
    custom_branding: bool = False
    sso_integration: bool = False
