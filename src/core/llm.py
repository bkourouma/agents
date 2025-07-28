"""
LLM provider abstraction layer for the AI Agent Platform.
Supports OpenAI and Anthropic with a unified interface.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, AsyncGenerator
from enum import Enum
import os
import asyncio
from dataclasses import dataclass

import openai
import anthropic
from pydantic import BaseModel


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"


class MessageRole(str, Enum):
    """Message roles for conversation."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class LLMMessage:
    """Standardized message format."""
    role: MessageRole
    content: str


@dataclass
class LLMResponse:
    """Standardized LLM response format."""
    content: str
    provider: LLMProvider
    model: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None


class LLMConfig(BaseModel):
    """LLM configuration."""
    provider: LLMProvider
    model: str
    api_key: str
    max_tokens: int = 1000
    temperature: float = 0.7
    timeout: int = 30


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    async def generate(
        self, 
        messages: List[LLMMessage], 
        **kwargs
    ) -> LLMResponse:
        """Generate a response from the LLM."""
        pass
    
    @abstractmethod
    async def stream_generate(
        self, 
        messages: List[LLMMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generate a response from the LLM."""
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = openai.AsyncOpenAI(api_key=config.api_key)
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        **kwargs
    ) -> LLMResponse:
        """Generate a response using OpenAI."""
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role.value, "content": msg.content}
                for msg in messages
            ]
            
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=openai_messages,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                timeout=self.config.timeout
            )
            
            return LLMResponse(
                content=response.choices[0].message.content,
                provider=LLMProvider.OPENAI,
                model=self.config.model,
                usage=response.usage.model_dump() if response.usage else None,
                finish_reason=response.choices[0].finish_reason
            )
            
        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")
    
    async def stream_generate(
        self, 
        messages: List[LLMMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generate a response using OpenAI."""
        try:
            # Convert messages to OpenAI format
            openai_messages = [
                {"role": msg.role.value, "content": msg.content}
                for msg in messages
            ]
            
            stream = await self.client.chat.completions.create(
                model=self.config.model,
                messages=openai_messages,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                stream=True,
                timeout=self.config.timeout
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    
        except Exception as e:
            raise Exception(f"OpenAI streaming error: {str(e)}")


class AnthropicProvider(BaseLLMProvider):
    """Anthropic LLM provider."""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.client = anthropic.AsyncAnthropic(api_key=config.api_key)
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        **kwargs
    ) -> LLMResponse:
        """Generate a response using Anthropic."""
        try:
            # Separate system message from conversation
            system_message = None
            conversation_messages = []
            
            for msg in messages:
                if msg.role == MessageRole.SYSTEM:
                    system_message = msg.content
                else:
                    conversation_messages.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })
            
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                system=system_message,
                messages=conversation_messages,
                timeout=self.config.timeout
            )
            
            return LLMResponse(
                content=response.content[0].text,
                provider=LLMProvider.ANTHROPIC,
                model=self.config.model,
                usage=response.usage.model_dump() if response.usage else None,
                finish_reason=response.stop_reason
            )
            
        except Exception as e:
            raise Exception(f"Anthropic API error: {str(e)}")
    
    async def stream_generate(
        self, 
        messages: List[LLMMessage], 
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generate a response using Anthropic."""
        try:
            # Separate system message from conversation
            system_message = None
            conversation_messages = []
            
            for msg in messages:
                if msg.role == MessageRole.SYSTEM:
                    system_message = msg.content
                else:
                    conversation_messages.append({
                        "role": msg.role.value,
                        "content": msg.content
                    })
            
            async with self.client.messages.stream(
                model=self.config.model,
                max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                system=system_message,
                messages=conversation_messages,
                timeout=self.config.timeout
            ) as stream:
                async for text in stream.text_stream:
                    yield text
                    
        except Exception as e:
            raise Exception(f"Anthropic streaming error: {str(e)}")


class LLMManager:
    """Manager for multiple LLM providers."""
    
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {}
        self.default_provider: Optional[str] = None
    
    def add_provider(self, name: str, provider: BaseLLMProvider, is_default: bool = False):
        """Add an LLM provider."""
        self.providers[name] = provider
        if is_default or self.default_provider is None:
            self.default_provider = name
    
    def get_provider(self, name: Optional[str] = None) -> BaseLLMProvider:
        """Get an LLM provider by name."""
        provider_name = name or self.default_provider
        if provider_name not in self.providers:
            raise ValueError(f"Provider '{provider_name}' not found")
        return self.providers[provider_name]
    
    async def generate(
        self, 
        messages: List[LLMMessage], 
        provider: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response using the specified provider."""
        llm_provider = self.get_provider(provider)
        return await llm_provider.generate(messages, **kwargs)
    
    async def stream_generate(
        self, 
        messages: List[LLMMessage], 
        provider: Optional[str] = None,
        **kwargs
    ) -> AsyncGenerator[str, None]:
        """Stream generate a response using the specified provider."""
        llm_provider = self.get_provider(provider)
        async for chunk in llm_provider.stream_generate(messages, **kwargs):
            yield chunk


# Global LLM manager instance
llm_manager = LLMManager()


def initialize_llm_providers():
    """Initialize LLM providers with environment variables."""
    # OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
    if openai_api_key:
        openai_config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-3.5-turbo",
            api_key=openai_api_key
        )
        openai_provider = OpenAIProvider(openai_config)
        llm_manager.add_provider("openai", openai_provider, is_default=True)
    
    # Anthropic
    anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
    if anthropic_api_key:
        anthropic_config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            model="claude-3-haiku-20240307",
            api_key=anthropic_api_key
        )
        anthropic_provider = AnthropicProvider(anthropic_config)
        llm_manager.add_provider("anthropic", anthropic_provider)


# Initialize providers on import
initialize_llm_providers()
