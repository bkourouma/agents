"""
Agent service layer for business logic and operations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

from src.models.agent import Agent, AgentCreate, AgentUpdate, AgentStatus, AgentType
from src.models.user import User
from src.agents.templates import get_template, AGENT_TEMPLATES
from src.core.llm import llm_manager, LLMMessage, MessageRole


class AgentService:
    """Service class for agent operations."""
    
    @staticmethod
    async def create_agent(
        db: AsyncSession,
        agent_data: AgentCreate,
        owner: User
    ) -> Agent:
        """Create a new agent with tenant isolation."""
        # Convert temperature to string for database storage
        agent = Agent(
            tenant_id=owner.tenant_id,  # Inherit tenant from owner
            name=agent_data.name,
            description=agent_data.description,
            agent_type=agent_data.agent_type.value,
            system_prompt=agent_data.system_prompt,
            personality=agent_data.personality,
            instructions=agent_data.instructions,
            llm_provider=agent_data.llm_provider,
            llm_model=agent_data.llm_model,
            temperature=str(agent_data.temperature),
            max_tokens=agent_data.max_tokens,
            tools_config=agent_data.tools_config,
            capabilities=agent_data.capabilities,
            is_public=agent_data.is_public,
            owner_id=owner.id,
            status=AgentStatus.DRAFT.value,
            is_active=True
        )

        db.add(agent)
        await db.commit()
        await db.refresh(agent)
        return agent
    
    @staticmethod
    async def create_agent_from_template(
        db: AsyncSession,
        template_name: str,
        agent_name: str,
        owner: User,
        customizations: Optional[Dict[str, Any]] = None
    ) -> Agent:
        """Create an agent from a predefined template."""
        template = get_template(template_name)
        
        # Start with template defaults
        agent_data = {
            "name": agent_name,
            "description": template.description,
            "agent_type": template.agent_type,
            "system_prompt": template.system_prompt,
            "personality": template.personality,
            "instructions": template.instructions,
            "capabilities": template.default_capabilities,
            "tools_config": {"enabled_tools": template.default_tools} if template.default_tools else None
        }
        
        # Apply customizations if provided
        if customizations:
            agent_data.update(customizations)
        
        # Create agent
        create_data = AgentCreate(**agent_data)
        return await AgentService.create_agent(db, create_data, owner)
    
    @staticmethod
    async def get_agent(db: AsyncSession, agent_id: int, user: User) -> Optional[Agent]:
        """Get an agent by ID with tenant isolation (must be owned by user or public within tenant)."""
        result = await db.execute(
            select(Agent).where(
                and_(
                    Agent.id == agent_id,
                    Agent.tenant_id == user.tenant_id,  # Tenant isolation
                    Agent.is_active == True,
                    or_(Agent.owner_id == user.id, Agent.is_public == True)
                )
            )
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def get_user_agents(
        db: AsyncSession,
        user: User,
        skip: int = 0,
        limit: int = 100,
        agent_type: Optional[AgentType] = None,
        status: Optional[AgentStatus] = None
    ) -> List[Agent]:
        """Get all agents owned by a user with tenant isolation."""
        query = select(Agent).where(
            and_(
                Agent.owner_id == user.id,
                Agent.tenant_id == user.tenant_id,  # Tenant isolation
                Agent.is_active == True
            )
        )

        if agent_type:
            query = query.where(Agent.agent_type == agent_type.value)

        if status:
            query = query.where(Agent.status == status.value)

        query = query.offset(skip).limit(limit).order_by(Agent.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def get_public_agents(
        db: AsyncSession,
        user: User,  # Added user parameter for tenant context
        skip: int = 0,
        limit: int = 100,
        agent_type: Optional[AgentType] = None
    ) -> List[Agent]:
        """Get all public agents within the user's tenant."""
        query = select(Agent).where(
            and_(
                Agent.is_public == True,
                Agent.status == AgentStatus.ACTIVE.value,
                Agent.tenant_id == user.tenant_id,  # Tenant isolation
                Agent.is_active == True
            )
        )

        if agent_type:
            query = query.where(Agent.agent_type == agent_type.value)

        query = query.offset(skip).limit(limit).order_by(Agent.created_at.desc())

        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod
    async def update_agent(
        db: AsyncSession,
        agent_id: int,
        agent_data: AgentUpdate,
        user: User
    ) -> Optional[Agent]:
        """Update an agent with tenant isolation (must be owned by user)."""
        result = await db.execute(
            select(Agent).where(
                and_(
                    Agent.id == agent_id,
                    Agent.owner_id == user.id,
                    Agent.tenant_id == user.tenant_id,  # Tenant isolation
                    Agent.is_active == True
                )
            )
        )
        agent = result.scalar_one_or_none()

        if not agent:
            return None
        
        # Update fields that are provided
        update_data = agent_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "agent_type" and value:
                setattr(agent, field, value.value)
            elif field == "status" and value:
                setattr(agent, field, value.value)
            elif field == "temperature" and value is not None:
                setattr(agent, field, str(value))
            else:
                setattr(agent, field, value)
        
        await db.commit()
        await db.refresh(agent)
        return agent
    
    @staticmethod
    async def delete_agent(db: AsyncSession, agent_id: int, user: User) -> bool:
        """Delete an agent with tenant isolation (must be owned by user)."""
        result = await db.execute(
            select(Agent).where(
                and_(
                    Agent.id == agent_id,
                    Agent.owner_id == user.id,
                    Agent.tenant_id == user.tenant_id,  # Tenant isolation
                    Agent.is_active == True
                )
            )
        )
        agent = result.scalar_one_or_none()

        if not agent:
            return False

        # Soft delete - mark as inactive instead of hard delete
        agent.is_active = False
        await db.commit()
        return True
    
    @staticmethod
    async def activate_agent(db: AsyncSession, agent_id: int, user: User) -> Optional[Agent]:
        """Activate an agent."""
        agent = await AgentService.get_agent(db, agent_id, user)
        if not agent or agent.owner_id != user.id:
            return None
        
        agent.status = AgentStatus.ACTIVE.value
        await db.commit()
        await db.refresh(agent)
        return agent
    
    @staticmethod
    async def deactivate_agent(db: AsyncSession, agent_id: int, user: User) -> Optional[Agent]:
        """Deactivate an agent."""
        agent = await AgentService.get_agent(db, agent_id, user)
        if not agent or agent.owner_id != user.id:
            return None
        
        agent.status = AgentStatus.INACTIVE.value
        await db.commit()
        await db.refresh(agent)
        return agent
    
    @staticmethod
    async def chat_with_agent(
        db: AsyncSession,
        agent_id: int,
        message: str,
        user: User,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Chat with an agent."""
        # Get the agent
        agent = await AgentService.get_agent(db, agent_id, user)
        if not agent:
            raise ValueError("Agent not found or not accessible")
        
        if agent.status != AgentStatus.ACTIVE.value:
            raise ValueError("Agent is not active")
        
        # Generate conversation ID if not provided
        if not conversation_id:
            conversation_id = str(uuid.uuid4())
        
        # Prepare messages for LLM
        messages = [
            LLMMessage(role=MessageRole.SYSTEM, content=agent.system_prompt)
        ]

        # Add personality if defined
        if agent.personality:
            personality_msg = f"Your personality: {agent.personality}"
            if agent.instructions:
                personality_msg += f"\n\nAdditional instructions: {agent.instructions}"
            messages.append(LLMMessage(role=MessageRole.SYSTEM, content=personality_msg))

        # Add conversation history for context
        print(f"🔍 Agent Service Debug: conversation_id = {conversation_id}")
        if conversation_id:
            try:
                from sqlalchemy import select
                from src.models.orchestrator import Conversation, ConversationMessage

                print(f"🔍 Looking for conversation with ID: {conversation_id} for user: {user.id}")

                # Get conversation
                result = await db.execute(
                    select(Conversation).where(
                        Conversation.id == conversation_id,
                        Conversation.user_id == user.id
                    )
                )
                conversation = result.scalar_one_or_none()
                print(f"🔍 Found conversation: {conversation is not None}")

                if conversation:
                    print(f"🔍 Conversation total_messages: {conversation.total_messages}")

                    if conversation.total_messages > 0:
                        # Get recent conversation messages for context
                        result = await db.execute(
                            select(ConversationMessage)
                            .where(ConversationMessage.conversation_id == conversation.id)
                            .order_by(ConversationMessage.message_index.asc())
                            .limit(10)  # Last 10 messages for context
                        )

                        conversation_messages = list(result.scalars().all())
                        print(f"🔄 Adding {len(conversation_messages)} conversation messages for context")

                        for conv_msg in conversation_messages:
                            print(f"   📝 User: {conv_msg.user_message[:50]}...")
                            print(f"   🤖 Agent: {conv_msg.agent_response[:50]}...")
                            # Add user message
                            messages.append(LLMMessage(role=MessageRole.USER, content=conv_msg.user_message))
                            # Add assistant response
                            messages.append(LLMMessage(role=MessageRole.ASSISTANT, content=conv_msg.agent_response))
                    else:
                        print(f"🔍 No messages in conversation yet")
                else:
                    print(f"🔍 No conversation found with ID {conversation_id}")

            except Exception as e:
                print(f"⚠️ Failed to load conversation history: {e}")
                import traceback
                traceback.print_exc()
                # Continue without conversation history

        # Search knowledge base if enabled
        knowledge_context = ""
        if (agent.tools_config and
            "knowledge_base" in agent.tools_config.get("enabled_tools", [])):
            try:
                print(f"🔍 Enhanced knowledge base search enabled for agent {agent.id}")
                print(f"🔍 Searching for: {message}")

                # Use enhanced knowledge base manager
                from src.tools.knowledge_base import get_enhanced_knowledge_base_manager, KnowledgeBaseSearchRequest
                kb_manager = get_enhanced_knowledge_base_manager(agent.id)
                search_request = KnowledgeBaseSearchRequest(query=message, limit=10)
                search_results = await kb_manager.search_documents(db, search_request)

                print(f"🔍 Found {len(search_results)} search results")
                if search_results:
                    knowledge_context = "\n\nRelevant information from knowledge base:\n"
                    for result in search_results:
                        print(f"🔍 Result: {result.title} (score: {result.relevance_score:.3f})")
                        knowledge_context += f"\n--- {result.title} ---\n{result.content_snippet}\n"
                    knowledge_context += "\nPlease provide a comprehensive answer based on this detailed information from the knowledge base. Include specific details, features, and functionalities mentioned in the documents.\n"
                    print(f"🔍 Knowledge context added: {len(knowledge_context)} characters")
                else:
                    print("🔍 No relevant documents found in knowledge base")
            except Exception as e:
                # If knowledge base search fails, continue without it
                print(f"❌ Enhanced knowledge base search failed: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"🔍 Knowledge base not enabled for agent {agent.id}")
            print(f"🔍 Agent tools_config: {agent.tools_config}")

        # Check for database queries if Vanna database tool is enabled
        database_context = ""
        tool_metadata = {}
        if (agent.tools_config and
            "vanna_database" in agent.tools_config.get("enabled_tools", [])):
            try:
                print(f"🗄️ Vanna database tool enabled for agent {agent.id}")

                # Import Vanna database tool
                from src.tools.vanna_database import (
                    get_vanna_database_tool,
                    VannaDatabaseQueryRequest,
                    format_query_result_for_agent,
                    detect_database_intent
                )

                # Check if the message appears to be a database query
                is_database_query = await detect_database_intent(message)

                if is_database_query:
                    print(f"🗄️ Database intent detected in message: {message}")

                    # Get tool configuration from agent
                    tool_config = agent.tools_config.get("vanna_database_config", {})
                    vanna_tool = get_vanna_database_tool(agent.id, tool_config)

                    # Check if Vanna is available
                    if await vanna_tool.is_available():
                        # Create query request
                        query_request = VannaDatabaseQueryRequest(
                            query=message,
                            output_format="json",
                            max_results=tool_config.get("max_results", 100)
                        )

                        # Execute the database query
                        query_result = await vanna_tool.execute_query(
                            db=db,
                            query_request=query_request,
                            user_id=user.id
                        )

                        # Store tool metadata for response
                        if query_result.metadata:
                            tool_metadata.update(query_result.metadata)

                        # Use the response from the tool if available, otherwise format it
                        if query_result.response:
                            database_context = "\n\n" + query_result.response
                        else:
                            database_context = "\n\n" + format_query_result_for_agent(query_result)

                        print(f"🗄️ Database query executed: {query_result.success}")

                        if query_result.success:
                            print(f"🗄️ Query returned {query_result.row_count} rows")
                        else:
                            print(f"🗄️ Query failed: {query_result.error}")
                    else:
                        database_context = "\n\n❌ **Database Query Tool Unavailable**\n\nThe Vanna AI service is not available. Please check the OPENAI_API_KEY configuration."
                        print("🗄️ Vanna AI service not available")
                else:
                    print(f"🗄️ No database intent detected in message")

            except Exception as e:
                print(f"❌ Vanna database tool failed: {e}")
                import traceback
                traceback.print_exc()
                database_context = f"\n\n❌ **Database Query Error**\n\nFailed to execute database query: {str(e)}"
        else:
            print(f"🗄️ Vanna database tool not enabled for agent {agent.id}")

        # Add user message with knowledge base and database context
        user_message_with_context = message + knowledge_context + database_context
        messages.append(LLMMessage(role=MessageRole.USER, content=user_message_with_context))
        
        # Generate response using LLM
        response = await llm_manager.generate(
            messages=messages,
            provider=agent.llm_provider,
            max_tokens=agent.max_tokens,
            temperature=float(agent.temperature)
        )
        
        # Update agent usage statistics
        agent.usage_count += 1
        agent.last_used = datetime.utcnow()
        await db.commit()
        
        return {
            "response": response.content,
            "agent_id": agent.id,
            "conversation_id": conversation_id,
            "usage": response.usage,
            "tools_used": ["vanna_database"] if tool_metadata else [],
            "model_used": response.model,
            "provider_used": response.provider.value,
            "metadata": tool_metadata if tool_metadata else None
        }
