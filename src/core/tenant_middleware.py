"""
Tenant-aware middleware for automatic tenant context management.
"""

import logging
from typing import Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import AsyncSessionLocal, set_tenant_context, clear_tenant_context
from src.core.auth import verify_token
from src.models.user import User
from src.models.tenant import Tenant
from sqlalchemy import select

logger = logging.getLogger(__name__)

class TenantContextMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically set tenant context for authenticated requests.
    This ensures all database operations are automatically filtered by tenant.
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs", "/redoc", "/openapi.json", "/health",
            "/api/v1/auth/login", "/api/v1/auth/register", "/api/v1/auth"
        ]
        self.security = HTTPBearer(auto_error=False)
    
    async def dispatch(self, request: Request, call_next):
        """Process request and set tenant context if authenticated."""
        
        # Skip tenant context for excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Clear any existing tenant context
        clear_tenant_context()
        
        try:
            # Extract and verify token
            tenant_id = await self._extract_tenant_from_request(request)
            
            if tenant_id:
                # Set tenant context for this request
                set_tenant_context(str(tenant_id))
                logger.debug(f"Set tenant context: {tenant_id}")
            
            # Process the request
            response = await call_next(request)
            return response
            
        except Exception as e:
            logger.error(f"Tenant middleware error: {e}")
            # Don't fail the request if tenant context fails
            return await call_next(request)
        
        finally:
            # Always clear tenant context after request
            clear_tenant_context()
    
    async def _extract_tenant_from_request(self, request: Request) -> Optional[str]:
        """Extract tenant ID from authenticated user."""
        try:
            # Get authorization header
            authorization = request.headers.get("Authorization")
            if not authorization or not authorization.startswith("Bearer "):
                return None
            
            # Extract token
            token = authorization.split(" ")[1]
            
            # Verify token and get username
            username = verify_token(token)
            if not username:
                return None

            # Get user and tenant from database
            async with AsyncSessionLocal() as db:
                result = await db.execute(
                    select(User).where(User.username == username)
                )
                user = result.scalar_one_or_none()
                
                if user and user.is_active:
                    return str(user.tenant_id)
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to extract tenant from request: {e}")
            return None


class TenantResolver:
    """
    Utility class for tenant resolution and validation.
    """
    
    @staticmethod
    async def get_tenant_by_id(db: AsyncSession, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID."""
        try:
            result = await db.execute(
                select(Tenant).where(
                    Tenant.id == tenant_id,
                    Tenant.is_active == True
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get tenant {tenant_id}: {e}")
            return None
    
    @staticmethod
    async def get_tenant_by_domain(db: AsyncSession, domain: str) -> Optional[Tenant]:
        """Get tenant by domain."""
        try:
            result = await db.execute(
                select(Tenant).where(
                    Tenant.domain == domain,
                    Tenant.is_active == True
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get tenant by domain {domain}: {e}")
            return None
    
    @staticmethod
    async def get_tenant_by_slug(db: AsyncSession, slug: str) -> Optional[Tenant]:
        """Get tenant by slug."""
        try:
            result = await db.execute(
                select(Tenant).where(
                    Tenant.slug == slug,
                    Tenant.is_active == True
                )
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Failed to get tenant by slug {slug}: {e}")
            return None
    
    @staticmethod
    async def validate_user_tenant_access(
        db: AsyncSession, 
        user: User, 
        tenant_id: str
    ) -> bool:
        """Validate that user has access to the specified tenant."""
        try:
            if str(user.tenant_id) != tenant_id:
                return False
            
            # Check if tenant is active
            tenant = await TenantResolver.get_tenant_by_id(db, tenant_id)
            return tenant is not None and tenant.is_active
            
        except Exception as e:
            logger.error(f"Failed to validate user tenant access: {e}")
            return False


def get_current_tenant_id() -> Optional[str]:
    """Get the current tenant ID from context."""
    from src.core.database import get_tenant_context
    return get_tenant_context()


async def require_tenant_context() -> str:
    """Dependency to require tenant context in endpoints."""
    tenant_id = get_current_tenant_id()
    if not tenant_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tenant context required"
        )
    return tenant_id


async def get_current_tenant(
    db: AsyncSession,
    tenant_id: str = None
) -> Optional[Tenant]:
    """Get the current tenant object."""
    if not tenant_id:
        tenant_id = get_current_tenant_id()
    
    if not tenant_id:
        return None
    
    return await TenantResolver.get_tenant_by_id(db, tenant_id)


class TenantAwareService:
    """
    Base class for tenant-aware services.
    Provides common tenant filtering functionality.
    """
    
    @staticmethod
    def add_tenant_filter(query, user: User):
        """Add tenant filter to a SQLAlchemy query."""
        from sqlalchemy import and_
        return query.where(
            and_(
                query.column_descriptions[0]['type'].tenant_id == user.tenant_id,
                query.column_descriptions[0]['type'].is_active == True
            )
        )
    
    @staticmethod
    def validate_tenant_ownership(entity, user: User) -> bool:
        """Validate that an entity belongs to the user's tenant."""
        return (
            hasattr(entity, 'tenant_id') and 
            entity.tenant_id == user.tenant_id and
            getattr(entity, 'is_active', True)
        )


# Tenant context decorators
def require_tenant_admin(func):
    """Decorator to require tenant admin privileges."""
    async def wrapper(*args, **kwargs):
        # This would be implemented based on your auth system
        # For now, just pass through
        return await func(*args, **kwargs)
    return wrapper


def tenant_isolated(func):
    """Decorator to ensure function operates within tenant context."""
    async def wrapper(*args, **kwargs):
        tenant_id = get_current_tenant_id()
        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Tenant context required for this operation"
            )
        return await func(*args, **kwargs)
    return wrapper
