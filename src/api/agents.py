"""
Agent management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.core.database import get_db
from src.models.user import User
from src.models.agent import (
    AgentCreate, AgentUpdate, AgentResponse, AgentChat, AgentChatResponse,
    AgentStatus, AgentType
)
from src.api.users import get_current_user_from_token
from src.agents.service import AgentService
from src.agents.templates import AGENT_TEMPLATES, list_templates

router = APIRouter()


@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    agent: AgentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Create a new agent."""
    try:
        created_agent = await AgentService.create_agent(db, agent, current_user)
        return created_agent
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to create agent: {str(e)}"
        )


@router.post("/from-template/{template_name}", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent_from_template(
    template_name: str,
    agent_name: str,
    customizations: Optional[dict] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Create an agent from a predefined template."""
    try:
        created_agent = await AgentService.create_agent_from_template(
            db, template_name, agent_name, current_user, customizations
        )
        return created_agent
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create agent from template: {str(e)}"
        )


@router.get("/", response_model=List[AgentResponse])
async def list_user_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    agent_type: Optional[AgentType] = None,
    status: Optional[AgentStatus] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """List all agents owned by the current user."""
    agents = await AgentService.get_user_agents(
        db, current_user, skip, limit, agent_type, status
    )
    return agents


@router.get("/public", response_model=List[AgentResponse])
async def list_public_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    agent_type: Optional[AgentType] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """List all public agents within the user's tenant."""
    agents = await AgentService.get_public_agents(db, current_user, skip, limit, agent_type)
    return agents


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Get a specific agent by ID."""
    agent = await AgentService.get_agent(db, agent_id, current_user)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    return agent


@router.put("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: int,
    agent_update: AgentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Update an agent."""
    agent = await AgentService.update_agent(db, agent_id, agent_update, current_user)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found or not owned by user"
        )
    return agent


@router.delete("/{agent_id}")
async def delete_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Delete an agent."""
    success = await AgentService.delete_agent(db, agent_id, current_user)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found or not owned by user"
        )
    return {"message": "Agent deleted successfully"}


@router.post("/{agent_id}/activate", response_model=AgentResponse)
async def activate_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Activate an agent."""
    agent = await AgentService.activate_agent(db, agent_id, current_user)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found or not owned by user"
        )
    return agent


@router.post("/{agent_id}/deactivate", response_model=AgentResponse)
async def deactivate_agent(
    agent_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Deactivate an agent."""
    agent = await AgentService.deactivate_agent(db, agent_id, current_user)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found or not owned by user"
        )
    return agent


@router.post("/{agent_id}/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    agent_id: int,
    chat_request: AgentChat,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Chat with an agent."""
    try:
        response = await AgentService.chat_with_agent(
            db, agent_id, chat_request.message, current_user,
            chat_request.conversation_id, chat_request.context
        )
        return AgentChatResponse(**response)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat failed: {str(e)}"
        )


@router.get("/templates/list")
async def list_agent_templates(
    current_user: User = Depends(get_current_user_from_token)
):
    """List all available agent templates."""
    templates = []
    for name, template in AGENT_TEMPLATES.items():
        templates.append({
            "name": name,
            "display_name": template.name,
            "description": template.description,
            "agent_type": template.agent_type.value,
            "default_tools": template.default_tools,
            "default_capabilities": template.default_capabilities
        })
    return {"templates": templates}


@router.get("/templates/{template_name}")
async def get_agent_template(
    template_name: str,
    current_user: User = Depends(get_current_user_from_token)
):
    """Get details of a specific agent template."""
    if template_name not in AGENT_TEMPLATES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Template not found"
        )
    
    template = AGENT_TEMPLATES[template_name]
    return {
        "name": template_name,
        "template": template.model_dump()
    }
