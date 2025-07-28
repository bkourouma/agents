"""
Orchestrator API endpoints for intelligent agent routing.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from src.core.database import get_db
from src.models.user import User
from src.models.orchestrator import (
    OrchestratorRequest, OrchestratorResponse, ConversationSummary,
    ConversationDetail, IntentAnalysis, RoutingResult, MessageHistory
)
from src.api.users import get_current_user_from_token
from src.orchestrator.llm_service import llm_orchestrator_service
from src.orchestrator.intent_analyzer import IntentAnalyzer
from src.orchestrator.agent_matcher import AgentMatcher

router = APIRouter()

# Use the LLM-based orchestrator service


@router.post("/chat", response_model=OrchestratorResponse)
async def orchestrated_chat(
    request: OrchestratorRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Send a message through the orchestrator for intelligent agent routing.
    This is the main endpoint that users interact with.
    """
    try:
        response = await llm_orchestrator_service.process_message(db, current_user, request)
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Orchestrator processing failed: {str(e)}"
        )


@router.post("/analyze-intent", response_model=IntentAnalysis)
async def analyze_intent(
    message: str,
    context: Optional[dict] = None,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Analyze the intent of a message without routing to an agent.
    Useful for debugging and understanding the orchestrator's decision-making.
    """
    try:
        intent_analyzer = IntentAnalyzer()
        analysis = await intent_analyzer.analyze_intent(message, context)
        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Intent analysis failed: {str(e)}"
        )


@router.post("/find-agents")
async def find_matching_agents(
    message: str,
    context: Optional[dict] = None,
    limit: int = Query(5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Find agents that match a given message without executing the routing.
    Useful for showing users their options before committing to a conversation.
    """
    try:
        # Analyze intent first
        intent_analyzer = IntentAnalyzer()
        intent_analysis = await intent_analyzer.analyze_intent(message, context)
        
        # Find matching agents
        agent_matcher = AgentMatcher()
        agent_matches = await agent_matcher.find_matching_agents(
            db, current_user, intent_analysis, limit
        )
        
        return {
            "intent_analysis": intent_analysis,
            "matching_agents": agent_matches,
            "total_matches": len(agent_matches)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent matching failed: {str(e)}"
        )


@router.get("/conversations", response_model=List[ConversationSummary])
async def list_conversations(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """List all conversations for the current user with tenant isolation."""
    try:
        from sqlalchemy import select
        from src.models.orchestrator import Conversation

        query = select(Conversation).where(
            Conversation.user_id == current_user.id,
            Conversation.tenant_id == current_user.tenant_id
        ).order_by(
            Conversation.last_activity.desc()
        ).offset(skip).limit(limit)

        result = await db.execute(query)
        conversations = result.scalars().all()

        return [ConversationSummary.model_validate(conv) for conv in conversations]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list conversations: {str(e)}"
        )


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Get detailed conversation history including all messages."""
    try:
        from sqlalchemy import select
        from src.models.orchestrator import Conversation, ConversationMessage
        
        # Get conversation with tenant isolation
        conv_result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id,
                Conversation.tenant_id == current_user.tenant_id
            )
        )
        conversation = conv_result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found in your tenant"
            )

        # Get messages with tenant isolation
        msg_result = await db.execute(
            select(ConversationMessage).where(
                ConversationMessage.conversation_id == conversation_id,
                ConversationMessage.tenant_id == current_user.tenant_id
            ).order_by(ConversationMessage.message_index)
        )
        messages = msg_result.scalars().all()
        
        return ConversationDetail(
            conversation=ConversationSummary.model_validate(conversation),
            messages=[MessageHistory.model_validate(msg) for msg in messages]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get conversation: {str(e)}"
        )


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Delete a conversation and all its messages."""
    try:
        from sqlalchemy import select, delete
        from src.models.orchestrator import Conversation, ConversationMessage
        
        # Check if conversation exists and belongs to user
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.user_id == current_user.id
            )
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Delete messages first (due to foreign key constraint)
        await db.execute(
            delete(ConversationMessage).where(
                ConversationMessage.conversation_id == conversation_id
            )
        )
        
        # Delete conversation
        await db.execute(
            delete(Conversation).where(Conversation.id == conversation_id)
        )
        
        await db.commit()
        
        return {"message": "Conversation deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete conversation: {str(e)}"
        )


@router.get("/stats")
async def get_orchestrator_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Get orchestrator usage statistics for the current user."""
    try:
        from sqlalchemy import select, func
        from src.models.orchestrator import Conversation, ConversationMessage
        
        # Get conversation count
        conv_count_result = await db.execute(
            select(func.count(Conversation.id)).where(
                Conversation.user_id == current_user.id
            )
        )
        conversation_count = conv_count_result.scalar()
        
        # Get message count
        msg_count_result = await db.execute(
            select(func.count(ConversationMessage.id)).join(Conversation).where(
                Conversation.user_id == current_user.id
            )
        )
        message_count = msg_count_result.scalar()
        
        # Get intent distribution
        intent_dist_result = await db.execute(
            select(
                ConversationMessage.intent_category,
                func.count(ConversationMessage.id)
            ).join(Conversation).where(
                Conversation.user_id == current_user.id
            ).group_by(ConversationMessage.intent_category)
        )
        intent_distribution = dict(intent_dist_result.fetchall())
        
        return {
            "total_conversations": conversation_count,
            "total_messages": message_count,
            "intent_distribution": intent_distribution,
            "average_messages_per_conversation": round(message_count / max(conversation_count, 1), 2)
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )
