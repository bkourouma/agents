"""
LLM API endpoints for testing and basic chat functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional
import json

from src.core.llm import (
    llm_manager, 
    LLMMessage, 
    MessageRole, 
    LLMProvider
)
from src.models.user import User
from src.api.users import get_current_user_from_token

router = APIRouter()


class ChatMessage(BaseModel):
    """Chat message model for API."""
    role: MessageRole
    content: str = Field(..., min_length=1, max_length=10000)


class ChatRequest(BaseModel):
    """Chat request model."""
    messages: List[ChatMessage] = Field(..., min_items=1, max_items=50)
    provider: Optional[str] = None
    model: Optional[str] = None
    max_tokens: Optional[int] = Field(None, ge=1, le=4000)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    stream: bool = False


class ChatResponse(BaseModel):
    """Chat response model."""
    content: str
    provider: str
    model: str
    usage: Optional[dict] = None
    finish_reason: Optional[str] = None


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Generate a chat response using the specified LLM provider.
    """
    try:
        # Convert API messages to LLM messages
        llm_messages = [
            LLMMessage(role=msg.role, content=msg.content)
            for msg in request.messages
        ]
        
        # Generate response
        response = await llm_manager.generate(
            messages=llm_messages,
            provider=request.provider,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        
        return ChatResponse(
            content=response.content,
            provider=response.provider.value,
            model=response.model,
            usage=response.usage,
            finish_reason=response.finish_reason
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM generation failed: {str(e)}"
        )


@router.post("/chat/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Stream a chat response using the specified LLM provider.
    """
    try:
        # Convert API messages to LLM messages
        llm_messages = [
            LLMMessage(role=msg.role, content=msg.content)
            for msg in request.messages
        ]
        
        async def generate_stream():
            try:
                async for chunk in llm_manager.stream_generate(
                    messages=llm_messages,
                    provider=request.provider,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature
                ):
                    # Send as Server-Sent Events format
                    yield f"data: {json.dumps({'content': chunk})}\n\n"
                
                # Send end marker
                yield f"data: {json.dumps({'done': True})}\n\n"
                
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return StreamingResponse(
            generate_stream(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM streaming failed: {str(e)}"
        )


@router.get("/providers")
async def list_providers(
    current_user: User = Depends(get_current_user_from_token)
):
    """
    List available LLM providers.
    """
    return {
        "providers": list(llm_manager.providers.keys()),
        "default_provider": llm_manager.default_provider,
        "total_providers": len(llm_manager.providers)
    }


@router.post("/test")
async def test_llm(
    provider: Optional[str] = None,
    current_user: User = Depends(get_current_user_from_token)
):
    """
    Test LLM connectivity with a simple prompt.
    """
    try:
        test_messages = [
            LLMMessage(
                role=MessageRole.SYSTEM,
                content="You are a helpful AI assistant. Respond briefly and clearly."
            ),
            LLMMessage(
                role=MessageRole.USER,
                content="Hello! Please respond with a brief greeting and confirm you're working correctly."
            )
        ]
        
        response = await llm_manager.generate(
            messages=test_messages,
            provider=provider,
            max_tokens=100,
            temperature=0.7
        )
        
        return {
            "status": "success",
            "provider": response.provider.value,
            "model": response.model,
            "response": response.content,
            "usage": response.usage
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"LLM test failed: {str(e)}"
        )
