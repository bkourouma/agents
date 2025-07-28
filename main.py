"""
Main FastAPI application for the AI Agent Platform.
Simplified version for initial setup.
"""

import time
import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from src.core.database import create_tables
from src.api.users import router as users_router
from src.api.llm import router as llm_router
from src.api.agents import router as agents_router
from src.api.orchestrator import router as orchestrator_router
from src.api.knowledge_base import router as knowledge_base_router
from src.api.database_chat import router as database_chat_router
from src.api.insurance import router as insurance_router
from src.api.tenants import router as tenants_router
from src.api.whatsapp import router as whatsapp_router

# Import models to ensure they are registered with SQLAlchemy
import src.models.tenant
import src.models.user
import src.models.agent
import src.models.orchestrator
import src.models.database_chat

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup - create database tables and PostgreSQL features
    await create_tables()
    print("Database tables created")

    # Create RLS policies for multi-tenant isolation (PostgreSQL only)
    try:
        from src.core.database import create_tenant_policies
        await create_tenant_policies()
        print("Row-Level Security policies created")
    except Exception as e:
        print(f"RLS policies creation skipped: {e}")

    yield

    # Shutdown
    print("Application shutting down")


# Create FastAPI application
app = FastAPI(
    title="AI Agent Platform",
    version="1.0.0",
    description="Conversational AI platform with intelligent agent orchestration",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Add tenant context middleware
from src.core.tenant_middleware import TenantContextMiddleware
app.add_middleware(TenantContextMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3003", "http://localhost:3004", "http://localhost:5173", "http://localhost:3006", "null"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time header to responses."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    print(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred"
        }
    )


@app.get("/")
async def root():
    """Root endpoint for health check."""
    return {
        "message": "AI Agent Platform API",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint for Azure Web Apps."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }


@app.get("/api/v1/status")
async def api_status():
    """API status endpoint."""
    return {
        "api_status": "operational",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "redoc": "/redoc",
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "llm": "/api/v1/llm",
            "agents": "/api/v1/agents",
            "knowledge_base": "/api/v1/agents/{agent_id}/knowledge-base",
            "orchestrator": "/api/v1/orchestrator",
            "database_chat": "/api/v1/database",
            "tenants": "/api/v1/tenants",
            "insurance": "/api/insurance",
            "whatsapp": "/api/v1/whatsapp"
        }
    }


# Include API routers
app.include_router(users_router, prefix="/api/v1/auth", tags=["authentication"])
app.include_router(tenants_router, prefix="/api/v1/tenants", tags=["tenants"])
app.include_router(llm_router, prefix="/api/v1/llm", tags=["llm"])
app.include_router(agents_router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(knowledge_base_router, prefix="/api/v1", tags=["knowledge-base"])
app.include_router(orchestrator_router, prefix="/api/v1/orchestrator", tags=["orchestrator"])
app.include_router(database_chat_router, prefix="/api/v1/database", tags=["database-chat"])
app.include_router(insurance_router, tags=["insurance"])
app.include_router(whatsapp_router, prefix="/api/v1/whatsapp", tags=["whatsapp"])


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=3006,
        reload=True,
        log_level="info"
    )
