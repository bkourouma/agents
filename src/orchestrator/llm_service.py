"""
LLM-Based Orchestrator Service - Uses LLM for intelligent routing decisions.
"""

import uuid
import time
import json
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from src.models.user import User
from src.models.agent import Agent, AgentStatus
from src.models.orchestrator import (
    Conversation, ConversationMessage, RoutingDecision,
    RoutingResult, OrchestratorRequest, OrchestratorResponse, AgentMatch,
    IntentCategory, IntentAnalysis
)
from src.core.llm import llm_manager, LLMMessage, MessageRole


class LLMOrchestratorService:
    """LLM-powered orchestrator that makes intelligent routing decisions."""
    
    def __init__(self):
        self.system_prompt = self._build_system_prompt()
    
    async def process_message(
        self,
        db: AsyncSession,
        user: User,
        request: OrchestratorRequest
    ) -> OrchestratorResponse:
        """Process a user message through the LLM-powered orchestrator."""
        
        print(f"🤖 LLM Orchestrator processing: '{request.message}'")
        start_time = time.time()
        
        try:
            # Get or create conversation
            conversation = await self._get_or_create_conversation(db, user, request.conversation_id)
            
            # Get available agents
            available_agents = await self._get_available_agents(db, user)
            print(f"📋 Found {len(available_agents)} available agents")
            
            # Build conversation context
            conversation_context = await self._build_conversation_context(db, conversation)
            
            # Get LLM routing decision
            print(f"🔍 Calling _get_llm_routing_decision...")
            routing_decision = await self._get_llm_routing_decision(
                request.message,
                available_agents,
                conversation_context,
                request.context
            )
            print(f"🔍 routing_decision type: {type(routing_decision)}")
            print(f"🔍 routing_decision value: {routing_decision}")
            
            if routing_decision:
                print(f"🎯 LLM Decision: {routing_decision['decision']}")
                selected_agent = routing_decision.get('selected_agent', {})
                agent_name = selected_agent.get('name', 'None') if selected_agent else 'None'
                print(f"   Selected: {agent_name}")
                print(f"   Confidence: {routing_decision['confidence']:.2f}")
                print(f"   Reasoning: {routing_decision['reasoning']}")
            else:
                print("🎯 LLM Decision: None (routing_decision is None)")
            
            # Execute the routing decision
            agent_response, usage_info = await self._execute_routing(
                db, user, routing_decision, request.message, conversation.id
            )

            # Build debug information separately
            debug_info = await self._build_debug_info(db, routing_decision, conversation.id, user)

            # Convert to standard format
            routing_result = self._convert_to_routing_result(routing_decision)
            
            # Save conversation message
            message_index = await self._save_conversation_message(
                db, conversation, request.message, agent_response, routing_result
            )
            
            # Update conversation metadata
            await self._update_conversation_metadata(db, conversation, routing_decision)
            
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)
            
            return OrchestratorResponse(
                conversation_id=conversation.id,
                message_index=message_index,
                user_message=request.message,
                agent_response=agent_response,
                routing_result=routing_result,
                response_time_ms=response_time_ms,
                usage=usage_info,
                debug_info=debug_info
            )
            
        except Exception as e:
            print(f"❌ LLM Orchestrator error: {e}")
            import traceback
            traceback.print_exc()
            return await self._create_fallback_response(request, str(e))
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM orchestrator."""
        return """You are an intelligent agent orchestrator for a conversational AI platform. Your job is to analyze user messages and conversation context to select the most appropriate agent to handle each request.

You will be provided with:
1. The user's current message
2. Available agents with their capabilities and specializations
3. Conversation history and context
4. Any additional context

Your task is to:
1. Understand the user's intent and needs
2. Consider the conversation flow and context
3. Match the request to the most suitable agent
4. Provide a confidence score and clear reasoning

IMPORTANT PRINCIPLES:
- **CONVERSATION CONTINUITY IS CRITICAL** - if the user is asking follow-up questions about the same topic, ALWAYS prefer the same agent
- Pay close attention to conversation history - if previous messages mention a specific topic (like "DocuPro"), follow-up questions likely refer to that same topic
- When users say "ses modules" or "its modules", they're referring to the subject discussed in previous messages
- Consider agent specializations and knowledge bases
- Factor in conversation context (previous messages, established topics)
- Be confident in your decisions - users prefer a good attempt over no help
- For ambiguous requests, choose the most general applicable agent

Respond with a JSON object containing:
{
    "decision": "single_agent" | "no_suitable_agent" | "escalate_to_human",
    "selected_agent": {
        "id": <agent_id>,
        "name": "<agent_name>",
        "type": "<agent_type>"
    } | null,
    "confidence": <float 0.0-1.0>,
    "reasoning": "<detailed explanation of your decision>",
    "intent_category": "<research|customer_service|financial_analysis|etc>",
    "alternative_agents": [<list of backup agent IDs>]
}

Be decisive and helpful. Users are counting on you to connect them with the right assistance."""

    async def _get_available_agents(self, db: AsyncSession, user: User) -> List[Dict]:
        """Get all available agents for the user."""
        
        query = select(Agent).where(
            Agent.status == AgentStatus.ACTIVE.value,
            (Agent.owner_id == user.id) | (Agent.is_public == True)
        ).order_by(
            (Agent.owner_id == user.id).desc(),  # User's agents first
            Agent.usage_count.desc()
        )
        
        result = await db.execute(query)
        agents = result.scalars().all()
        
        # Convert to LLM-friendly format
        agent_list = []
        for agent in agents:
            # Get knowledge base info
            kb_info = await self._get_agent_knowledge_info(db, agent.id)
            
            agent_info = {
                "id": agent.id,
                "name": agent.name,
                "type": agent.agent_type,
                "description": agent.description or "",
                "specializations": agent.system_prompt[:200] + "..." if agent.system_prompt else "",
                "tools": agent.tools_config.get("enabled_tools", []) if agent.tools_config else [],
                "knowledge_base": kb_info,
                "usage_count": agent.usage_count,
                "is_users_agent": agent.owner_id == user.id
            }
            agent_list.append(agent_info)
        
        return agent_list
    
    async def _get_agent_knowledge_info(self, db: AsyncSession, agent_id: int) -> Dict:
        """Get knowledge base information for an agent."""
        try:
            from src.tools.knowledge_base import KnowledgeBaseDocument
            
            result = await db.execute(
                select(KnowledgeBaseDocument.title, KnowledgeBaseDocument.content_type)
                .where(
                    KnowledgeBaseDocument.agent_id == agent_id,
                    KnowledgeBaseDocument.is_active == True
                )
                .limit(5)
            )
            
            documents = result.fetchall()
            
            return {
                "document_count": len(documents),
                "sample_documents": [{"title": doc.title, "type": doc.content_type} for doc in documents],
                "has_knowledge_base": len(documents) > 0
            }
        except Exception:
            return {"document_count": 0, "sample_documents": [], "has_knowledge_base": False}
    
    async def _build_conversation_context(self, db: AsyncSession, conversation: Conversation) -> Dict:
        """Build conversation context for the LLM."""
        
        context = {
            "conversation_id": conversation.id,
            "total_messages": conversation.total_messages,
            "primary_intent": conversation.primary_intent,
            "agents_used": conversation.agents_used or [],
            "recent_messages": []
        }
        
        # Get recent messages for context
        if conversation.total_messages > 0:
            result = await db.execute(
                select(ConversationMessage)
                .where(ConversationMessage.conversation_id == conversation.id)
                .order_by(ConversationMessage.message_index.desc())
                .limit(10)  # Increased from 5 to 10 for better context
            )
            
            messages = list(result.scalars().all())
            messages.reverse()  # Chronological order
            
            for msg in messages:
                # No character limit - full context for maximum understanding
                agent_response = msg.agent_response

                context["recent_messages"].append({
                    "user_message": msg.user_message,
                    "agent_response": agent_response,
                    "agent_id": msg.selected_agent_id,
                    "intent": msg.intent_category
                })
        
        return context

    async def _get_llm_routing_decision(
        self,
        message: str,
        available_agents: List[Dict],
        conversation_context: Dict,
        request_context: Optional[Dict] = None
    ) -> Dict:
        """Get routing decision from LLM."""

        # Build the prompt
        prompt = self._build_routing_prompt(message, available_agents, conversation_context, request_context)

        # Debug: Show what context the LLM is receiving
        print(f"🔍 LLM Context Debug:")
        print(f"   Total messages: {conversation_context['total_messages']}")
        print(f"   Recent messages: {len(conversation_context['recent_messages'])}")
        for i, msg in enumerate(conversation_context['recent_messages']):
            print(f"   {i+1}. User: {msg['user_message']}")
            print(f"      Agent: {msg['agent_response'][:100]}...")

        try:
            messages = [
                LLMMessage(role=MessageRole.SYSTEM, content=self.system_prompt),
                LLMMessage(role=MessageRole.USER, content=prompt)
            ]

            response = await llm_manager.generate(
                messages=messages,
                max_tokens=500,
                temperature=0.1  # Low temperature for consistent routing decisions
            )

            # Parse JSON response
            decision_json = json.loads(response.content)

            # Validate and clean the response
            return self._validate_llm_decision(decision_json, available_agents)

        except json.JSONDecodeError as e:
            print(f"❌ JSON parsing error: {e}")
            print(f"Raw response: {response.content}")
            return self._create_fallback_decision(available_agents)

        except Exception as e:
            print(f"❌ LLM routing error: {e}")
            return self._create_fallback_decision(available_agents)

    def _build_routing_prompt(
        self,
        message: str,
        available_agents: List[Dict],
        conversation_context: Dict,
        request_context: Optional[Dict] = None
    ) -> str:
        """Build the detailed prompt for the LLM."""

        prompt = f"""ROUTING REQUEST

USER MESSAGE: "{message}"

AVAILABLE AGENTS:
"""

        for i, agent in enumerate(available_agents, 1):
            kb_info = agent['knowledge_base']
            kb_desc = f"({kb_info['document_count']} documents)" if kb_info['has_knowledge_base'] else "(no knowledge base)"

            prompt += f"""{i}. {agent['name']} (ID: {agent['id']})
   - Type: {agent['type']}
   - Description: {agent['description']}
   - Tools: {', '.join(agent['tools'])}
   - Knowledge Base: {kb_desc}
   - Usage: {agent['usage_count']} interactions
   - Owner: {'User' if agent['is_users_agent'] else 'Public'}

"""

        prompt += f"""
CONVERSATION CONTEXT:
- Total messages: {conversation_context['total_messages']}
- Primary intent: {conversation_context.get('primary_intent', 'None')}
- Agents used: {conversation_context.get('agents_used', [])}

RECENT CONVERSATION:
"""

        if conversation_context['recent_messages']:
            for msg in conversation_context['recent_messages']:
                prompt += f"User: {msg['user_message']}\n"
                prompt += f"Agent {msg['agent_id']}: {msg['agent_response']}\n\n"
        else:
            prompt += "No previous messages (new conversation)\n"

        if request_context:
            prompt += f"\nADDITIONAL CONTEXT: {json.dumps(request_context, indent=2)}\n"

        prompt += """
Please analyze this request and select the most appropriate agent. Consider:
1. **CONVERSATION CONTEXT FIRST** - Look at recent messages to understand what the user is discussing
2. **FOLLOW-UP DETECTION** - If this seems like a follow-up question about a previous topic, use the same agent
3. **PRONOUN RESOLUTION** - If the user says "ses modules", "its features", etc., they're referring to the subject from previous messages
4. The user's specific question or need
5. Agent specializations and knowledge bases
6. Agent capabilities and tools

CRITICAL: If there's any conversation history, prioritize continuity over everything else.

Respond with valid JSON only."""

        return prompt

    def _validate_llm_decision(self, decision: Dict, available_agents: List[Dict]) -> Dict:
        """Validate and clean the LLM decision."""

        # Ensure required fields and normalize case
        decision.setdefault("decision", "no_suitable_agent")
        decision["decision"] = decision["decision"].lower()  # Normalize to lowercase
        decision.setdefault("confidence", 0.5)
        decision.setdefault("reasoning", "LLM routing decision")
        decision.setdefault("intent_category", "general")
        decision.setdefault("alternative_agents", [])

        # Validate intent_category
        from src.models.orchestrator import IntentCategory
        valid_categories = [e.value for e in IntentCategory]
        if decision["intent_category"].lower() not in valid_categories:
            print(f"⚠️ Invalid intent_category '{decision['intent_category']}', defaulting to 'general'")
            decision["intent_category"] = "general"
        else:
            decision["intent_category"] = decision["intent_category"].lower()

        # Validate selected agent
        if decision.get("selected_agent"):
            agent_id = decision["selected_agent"].get("id")
            if agent_id:
                # Find the agent in available agents
                matching_agent = next((a for a in available_agents if a["id"] == agent_id), None)
                if not matching_agent:
                    print(f"⚠️ LLM selected invalid agent ID {agent_id}, falling back")
                    decision["decision"] = "no_suitable_agent"
                    decision["selected_agent"] = None
                else:
                    # Ensure agent info is complete
                    decision["selected_agent"] = {
                        "id": matching_agent["id"],
                        "name": matching_agent["name"],
                        "type": matching_agent["type"]
                    }

        # Ensure confidence is in valid range
        decision["confidence"] = max(0.0, min(1.0, float(decision["confidence"])))

        return decision

    def _create_fallback_decision(self, available_agents: List[Dict]) -> Dict:
        """Create a fallback decision when LLM fails."""

        if available_agents:
            # Choose the first available agent (usually user's most-used agent)
            fallback_agent = available_agents[0]
            return {
                "decision": "single_agent",
                "selected_agent": {
                    "id": fallback_agent["id"],
                    "name": fallback_agent["name"],
                    "type": fallback_agent["type"]
                },
                "confidence": 0.4,
                "reasoning": "Fallback decision due to LLM routing error - selected most suitable available agent",
                "intent_category": "general",
                "alternative_agents": [a["id"] for a in available_agents[1:3]]
            }
        else:
            return {
                "decision": "no_suitable_agent",
                "selected_agent": None,
                "confidence": 0.0,
                "reasoning": "No agents available for routing",
                "intent_category": "general",
                "alternative_agents": []
            }

    async def _execute_routing(
        self,
        db: AsyncSession,
        user: User,
        routing_decision: Dict,
        user_message: str,
        conversation_id: str
    ) -> tuple[str, Optional[Dict[str, Any]]]:
        """Execute the routing decision."""

        if routing_decision["decision"] == "single_agent" and routing_decision.get("selected_agent"):
            try:
                # Import and use AgentService
                from src.agents.service import AgentService

                agent_id = routing_decision["selected_agent"]["id"]

                if hasattr(AgentService, 'chat_with_agent'):
                    response_data = await AgentService.chat_with_agent(
                        db, agent_id, user_message, user, conversation_id
                    )
                    if response_data and isinstance(response_data, dict):
                        return response_data.get("response", "No response from agent"), response_data.get("usage")
                    else:
                        print(f"⚠️ AgentService returned invalid response: {response_data}")
                        agent_name = routing_decision["selected_agent"]["name"]
                        return f"Hello! I'm {agent_name}. I received your message: '{user_message}' but couldn't process it properly.", None
                else:
                    # Simple fallback response
                    agent_name = routing_decision["selected_agent"]["name"]
                    return f"Hello! I'm {agent_name}. I received your message: '{user_message}'. How can I help you further?", None

            except Exception as e:
                print(f"❌ Agent execution error: {e}")
                agent_name = routing_decision["selected_agent"]["name"]
                return f"I apologize, but I encountered an error while processing your request with {agent_name}: {str(e)}", None

        elif routing_decision["decision"] == "no_suitable_agent":
            return self._generate_no_agent_response(routing_decision), None

        else:
            return "I'm having difficulty processing your request. Could you please rephrase or provide more details?", None

    def _generate_no_agent_response(self, routing_decision: Dict) -> str:
        """Generate response when no suitable agent is found."""
        base_response = "I don't have a specialized agent available for this specific request at the moment."

        if routing_decision.get("reasoning"):
            base_response += f" {routing_decision['reasoning']}"

        base_response += " You might try rephrasing your question or ask about something else I can help with."

        return base_response

    async def _build_debug_info(self, db: AsyncSession, routing_decision: Dict, conversation_id: str, user: User) -> str:
        """Build debug information to append to agent response."""

        debug_lines = []
        debug_lines.append("---")
        debug_lines.append("🔍 **DEBUG INFO**")

        # Routing Decision
        debug_lines.append(f"**Decision:** {routing_decision['decision']}")
        debug_lines.append(f"**Confidence:** {routing_decision['confidence']:.2f}")
        debug_lines.append(f"**Reasoning:** {routing_decision['reasoning']}")

        # Selected Agent
        if routing_decision.get('selected_agent'):
            agent = routing_decision['selected_agent']
            debug_lines.append(f"**Selected Agent:** {agent['name']} (ID: {agent['id']})")

        # Conversation History
        try:

            result = await db.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user.id
                )
            )
            conversation = result.scalar_one_or_none()

            if conversation:
                debug_lines.append(f"**Conversation ID:** {conversation_id}")
                debug_lines.append(f"**Total Messages:** {conversation.total_messages}")

                # Get recent messages
                result = await db.execute(
                    select(ConversationMessage)
                    .where(ConversationMessage.conversation_id == conversation.id)
                    .order_by(ConversationMessage.message_index.asc())
                    .limit(5)  # Last 5 for debug display
                )

                messages = list(result.scalars().all())
                if messages:
                    debug_lines.append("**Recent Conversation:**")
                    for i, msg in enumerate(messages, 1):
                        debug_lines.append(f"  {i}. User: {msg.user_message[:60]}...")
                        debug_lines.append(f"     Agent: {msg.agent_response[:60]}...")
                else:
                    debug_lines.append("**Recent Conversation:** No previous messages")
            else:
                debug_lines.append(f"**Conversation:** Not found (ID: {conversation_id})")

        except Exception as e:
            debug_lines.append(f"**Conversation History Error:** {str(e)}")

        debug_lines.append("---")

        return "\n".join(debug_lines)

    def _convert_to_routing_result(self, llm_decision: Dict) -> RoutingResult:
        """Convert LLM decision to standard RoutingResult format."""

        # Create intent analysis with validated category
        intent_category_str = llm_decision.get("intent_category", "general").lower()

        # Validate intent category - map invalid values to 'general'
        valid_categories = [e.value for e in IntentCategory]
        if intent_category_str not in valid_categories:
            print(f"⚠️ Invalid intent_category '{intent_category_str}', defaulting to 'general'")
            intent_category_str = "general"

        intent_analysis = IntentAnalysis(
            category=IntentCategory(intent_category_str),
            confidence=llm_decision["confidence"],
            keywords=[],  # LLM doesn't use keywords
            reasoning=f"LLM-based classification: {llm_decision['reasoning']}",
            suggested_agents=llm_decision.get("alternative_agents", [])
        )

        # Create agent match if selected
        selected_agent = None
        if llm_decision.get("selected_agent"):
            selected_agent = AgentMatch(
                agent_id=llm_decision["selected_agent"]["id"],
                agent_name=llm_decision["selected_agent"]["name"],
                agent_type=llm_decision["selected_agent"]["type"],
                match_score=llm_decision["confidence"],
                match_reasoning=llm_decision["reasoning"]
            )

        return RoutingResult(
            decision=RoutingDecision(llm_decision["decision"]),
            intent_analysis=intent_analysis,
            selected_agent=selected_agent,
            alternative_agents=[],  # Could be populated from alternative_agents
            reasoning=llm_decision["reasoning"],
            confidence=llm_decision["confidence"]
        )

    async def _get_or_create_conversation(self, db: AsyncSession, user: User, conversation_id: Optional[str]) -> Conversation:
        """Get or create conversation with tenant isolation."""
        if conversation_id:
            result = await db.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user.id,
                    Conversation.tenant_id == user.tenant_id
                )
            )
            conversation = result.scalar_one_or_none()

            if conversation:
                conversation.last_activity = datetime.utcnow()
                await db.commit()
                return conversation

        conversation = Conversation(
            id=str(uuid.uuid4()),
            tenant_id=user.tenant_id,
            user_id=user.id,
            title=None,
            total_messages=0,
            agents_used=[],
            primary_intent=None
        )

        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation

    async def _save_conversation_message(self, db: AsyncSession, conversation: Conversation, user_message: str, agent_response: str, routing_result: RoutingResult) -> int:
        """Save conversation message."""
        message_index = conversation.total_messages + 1

        message = ConversationMessage(
            tenant_id=conversation.tenant_id,
            conversation_id=conversation.id,
            message_index=message_index,
            user_message=user_message,
            agent_response=agent_response,
            intent_category=routing_result.intent_analysis.category.value,
            confidence_score=routing_result.confidence,
            selected_agent_id=routing_result.selected_agent.agent_id if routing_result.selected_agent else None,
            routing_decision=routing_result.decision.value,
            routing_reasoning=routing_result.reasoning
        )

        db.add(message)
        conversation.total_messages = message_index

        if routing_result.selected_agent:
            agents_used = conversation.agents_used or []
            if routing_result.selected_agent.agent_id not in agents_used:
                agents_used.append(routing_result.selected_agent.agent_id)
                conversation.agents_used = agents_used

        await db.commit()
        return message_index

    async def _update_conversation_metadata(self, db: AsyncSession, conversation: Conversation, routing_decision: Dict):
        """Update conversation metadata."""
        if not conversation.primary_intent:
            conversation.primary_intent = routing_decision.get("intent_category", "general")

        if not conversation.title and conversation.total_messages >= 1:
            conversation.title = f"Conversation - {datetime.now().strftime('%m/%d')}"

        await db.commit()

    async def _create_fallback_response(self, request: OrchestratorRequest, error_msg: str) -> OrchestratorResponse:
        """Create fallback response for errors."""
        fallback_routing = RoutingResult(
            decision=RoutingDecision.NO_SUITABLE_AGENT,
            intent_analysis=IntentAnalysis(
                category=IntentCategory.GENERAL,
                confidence=0.0,
                keywords=[],
                reasoning=f"Error in orchestrator: {error_msg}",
                suggested_agents=[]
            ),
            selected_agent=None,
            alternative_agents=[],
            reasoning=f"Orchestrator error: {error_msg}",
            confidence=0.0
        )

        return OrchestratorResponse(
            conversation_id=str(uuid.uuid4()),
            message_index=1,
            user_message=request.message,
            agent_response=f"I apologize, but I encountered an error processing your request: {error_msg}",
            routing_result=fallback_routing,
            response_time_ms=0,
            usage=None,
            debug_info=None
        )


# Create a singleton instance
llm_orchestrator_service = LLMOrchestratorService()
