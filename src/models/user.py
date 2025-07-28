"""
User models for authentication and authorization.
Enhanced for multi-tenant support.
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Index
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
import uuid

from src.core.database import Base


class User(Base):
    """User database model with multi-tenant support."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant support
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)

    # User credentials and basic info
    email = Column(String(255), nullable=False, index=True)
    username = Column(String(100), nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)

    # Status and permissions
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    is_tenant_admin = Column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Profile information
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Relationships
    tenant = relationship("Tenant", back_populates="users")
    agents = relationship("Agent", back_populates="owner")
    # conversations relationship is defined in orchestrator.py to avoid circular imports

    # Table constraints and indexes
    __table_args__ = (
        # Unique constraints within tenant
        Index('idx_users_tenant_email', 'tenant_id', 'email', unique=True),
        Index('idx_users_tenant_username', 'tenant_id', 'username', unique=True),
        Index('idx_users_tenant_active', 'tenant_id', 'is_active'),
        Index('idx_users_created_at', 'created_at'),
    )


# Pydantic models for API
class UserBase(BaseModel):
    """Base user model for shared properties."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    full_name: Optional[str] = None
    bio: Optional[str] = None
    is_active: bool = True


class UserCreate(UserBase):
    """User creation model."""
    password: str = Field(..., min_length=8, max_length=100)


class UserUpdate(BaseModel):
    """User update model."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=100)
    full_name: Optional[str] = None
    bio: Optional[str] = None
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """User response model."""
    id: int
    tenant_id: str
    is_superuser: bool
    is_tenant_admin: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    avatar_url: Optional[str] = None

    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    """User login model."""
    username: str
    password: str


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class TokenData(BaseModel):
    """Token data model."""
    username: Optional[str] = None
