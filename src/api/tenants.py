"""
Tenant management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import uuid

from src.core.database import get_db_without_tenant, get_db
from src.models.tenant import (
    Tenant, TenantCreate, TenantUpdate, TenantResponse, 
    TenantStats, TenantStatus, TenantPlan
)
from src.models.user import User
from src.models.agent import Agent
from src.api.users import get_current_user_from_token
from src.core.tenant_middleware import TenantResolver, require_tenant_admin

router = APIRouter()


@router.post("/", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    tenant_data: TenantCreate,
    db: AsyncSession = Depends(get_db_without_tenant)  # No tenant context for creation
):
    """Create a new tenant (system admin only)."""
    try:
        # Check if slug is already taken
        existing = await TenantResolver.get_tenant_by_slug(db, tenant_data.slug)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant slug already exists"
            )
        
        # Check if domain is already taken (if provided)
        if tenant_data.domain:
            existing_domain = await TenantResolver.get_tenant_by_domain(db, tenant_data.domain)
            if existing_domain:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Tenant domain already exists"
                )
        
        # Create tenant
        tenant = Tenant(
            name=tenant_data.name,
            slug=tenant_data.slug,
            domain=tenant_data.domain,
            contact_email=tenant_data.contact_email,
            contact_name=tenant_data.contact_name,
            plan=tenant_data.plan,
            settings=tenant_data.settings or {},
            features=tenant_data.features or [],
            max_users=tenant_data.max_users,
            max_agents=tenant_data.max_agents,
            max_storage_mb=tenant_data.max_storage_mb,
            billing_email=tenant_data.billing_email,
            status=TenantStatus.ACTIVE
        )
        
        db.add(tenant)
        await db.commit()
        await db.refresh(tenant)
        
        return tenant
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tenant: {str(e)}"
        )


@router.get("/", response_model=List[TenantResponse])
async def list_tenants(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[TenantStatus] = None,
    plan: Optional[TenantPlan] = None,
    db: AsyncSession = Depends(get_db_without_tenant)
):
    """List all tenants (system admin only)."""
    try:
        query = select(Tenant).where(Tenant.is_active == True)
        
        if status:
            query = query.where(Tenant.status == status)
        
        if plan:
            query = query.where(Tenant.plan == plan)
        
        query = query.offset(skip).limit(limit).order_by(Tenant.created_at.desc())
        
        result = await db.execute(query)
        tenants = result.scalars().all()
        
        return tenants
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tenants: {str(e)}"
        )


@router.get("/current", response_model=TenantResponse)
async def get_current_tenant(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Get the current user's tenant."""
    try:
        tenant = await TenantResolver.get_tenant_by_id(db, str(current_user.tenant_id))
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        return tenant
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tenant: {str(e)}"
        )


@router.get("/test")
async def test_tenant_endpoint():
    """Test endpoint to verify tenant router is working."""
    return {"message": "Tenant router is working!", "status": "ok"}


@router.get("/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_without_tenant)
):
    """Get a specific tenant by ID."""
    try:
        print(f"DEBUG: get_tenant called with tenant_id={tenant_id}")
        print(f"DEBUG: current_user.tenant_id={current_user.tenant_id}")
        print(f"DEBUG: current_user.is_superuser={current_user.is_superuser}")

        # Check if user belongs to this tenant or is superuser
        if str(current_user.tenant_id) != tenant_id and not current_user.is_superuser:
            print(f"DEBUG: Access denied - user tenant {current_user.tenant_id} != requested {tenant_id}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant"
            )

        print(f"DEBUG: Calling TenantResolver.get_tenant_by_id with {tenant_id}")
        tenant = await TenantResolver.get_tenant_by_id(db, tenant_id)
        print(f"DEBUG: TenantResolver returned: {tenant}")

        if not tenant:
            print(f"DEBUG: Tenant not found in database")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )

        print(f"DEBUG: Returning tenant: {tenant.name}")
        return tenant

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tenant: {str(e)}"
        )


@router.put("/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: str,
    tenant_data: TenantUpdate,
    db: AsyncSession = Depends(get_db_without_tenant)
):
    """Update a tenant (system admin only)."""
    try:
        tenant = await TenantResolver.get_tenant_by_id(db, tenant_id)
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Update fields that are provided
        update_data = tenant_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(tenant, field):
                setattr(tenant, field, value)
        
        await db.commit()
        await db.refresh(tenant)
        
        return tenant
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tenant: {str(e)}"
        )


@router.put("/current", response_model=TenantResponse)
async def update_current_tenant(
    tenant_data: TenantUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Update the current tenant (tenant admin only)."""
    try:
        if not current_user.is_tenant_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant admin privileges required"
            )
        
        tenant = await TenantResolver.get_tenant_by_id(db, str(current_user.tenant_id))
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Limit what tenant admins can update
        allowed_fields = ['name', 'contact_email', 'contact_name', 'settings']
        update_data = tenant_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            if field in allowed_fields and hasattr(tenant, field):
                setattr(tenant, field, value)
        
        await db.commit()
        await db.refresh(tenant)
        
        return tenant
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update tenant: {str(e)}"
        )


@router.get("/{tenant_id}/stats", response_model=TenantStats)
async def get_tenant_stats(
    tenant_id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_without_tenant)
):
    """Get tenant usage statistics."""
    try:
        # Check if user belongs to this tenant or is superuser
        if str(current_user.tenant_id) != tenant_id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant"
            )

        tenant = await TenantResolver.get_tenant_by_id(db, tenant_id)

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Get user counts
        user_count_result = await db.execute(
            select(func.count(User.id)).where(
                User.tenant_id == tenant_id,
                User.is_active == True
            )
        )
        total_users = user_count_result.scalar() or 0
        
        # Get agent counts
        agent_count_result = await db.execute(
            select(func.count(Agent.id)).where(
                Agent.tenant_id == tenant_id,
                Agent.is_active == True
            )
        )
        total_agents = agent_count_result.scalar() or 0
        
        # Get active agent counts
        active_agent_count_result = await db.execute(
            select(func.count(Agent.id)).where(
                Agent.tenant_id == tenant_id,
                Agent.is_active == True,
                Agent.status == "active"
            )
        )
        active_agents = active_agent_count_result.scalar() or 0
        
        return TenantStats(
            tenant_id=uuid.UUID(tenant_id),
            total_users=total_users,
            active_users=total_users,  # Simplified for now
            total_agents=total_agents,
            active_agents=active_agents,
            total_conversations=0,  # TODO: Implement when conversation model is updated
            total_messages=0,  # TODO: Implement when conversation model is updated
            storage_used_mb=0,  # TODO: Implement storage calculation
            last_activity=tenant.last_activity
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tenant stats: {str(e)}"
        )


@router.get("/{tenant_id}/usage", response_model=dict)
async def get_tenant_usage(
    tenant_id: str,
    current_user: User = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_db_without_tenant)
):
    """Get tenant usage information with limits."""
    try:
        # Check if user belongs to this tenant or is superuser
        if str(current_user.tenant_id) != tenant_id and not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant"
            )

        tenant = await TenantResolver.get_tenant_by_id(db, tenant_id)

        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )

        # Get current usage
        user_count_result = await db.execute(
            select(func.count(User.id)).where(
                User.tenant_id == tenant_id,
                User.is_active == True
            )
        )
        current_users = user_count_result.scalar() or 0

        # Calculate usage percentages
        user_percentage = (current_users / tenant.max_users * 100) if tenant.max_users > 0 else 0
        agent_percentage = 0  # TODO: Implement when agent counts are available
        storage_percentage = 0  # TODO: Implement storage calculation

        return {
            "users": {
                "current": current_users,
                "limit": tenant.max_users,
                "percentage": user_percentage
            },
            "agents": {
                "current": 0,  # TODO: Implement
                "limit": tenant.max_agents,
                "percentage": agent_percentage
            },
            "storage": {
                "current_mb": 0,  # TODO: Implement
                "limit_mb": tenant.max_storage_mb,
                "percentage": storage_percentage
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get tenant usage: {str(e)}"
        )


@router.delete("/{tenant_id}")
async def delete_tenant(
    tenant_id: str,
    db: AsyncSession = Depends(get_db_without_tenant)
):
    """Soft delete a tenant (system admin only)."""
    try:
        tenant = await TenantResolver.get_tenant_by_id(db, tenant_id)
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant not found"
            )
        
        # Soft delete - mark as inactive
        tenant.is_active = False
        tenant.status = TenantStatus.SUSPENDED
        
        await db.commit()
        
        return {"message": "Tenant deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete tenant: {str(e)}"
        )
