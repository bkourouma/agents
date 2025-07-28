"""
Orchestrator service - the main intelligence that routes user queries to appropriate agents.
"""

import uuid
import time
import json
from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from src.models.user import User
from src.models.agent import Agent
from src.models.orchestrator import (
    Conversation, ConversationMessage, IntentCategory, RoutingDecision,
    RoutingResult, OrchestratorRequest, OrchestratorResponse, AgentMatch
)
from src.orchestrator.intent_analyzer import IntentAnalyzer
from src.orchestrator.agent_matcher import AgentMatcher
from src.agents.service import AgentService


class OrchestratorService:
    """Main orchestrator service that coordinates intent analysis and agent routing."""
    
    def __init__(self):
        self.intent_analyzer = IntentAnalyzer()
        self.agent_matcher = AgentMatcher()
    
    async def process_message(
        self,
        db: AsyncSession,
        user: User,
        request: OrchestratorRequest
    ) -> OrchestratorResponse:
        """Process a user message through the orchestrator pipeline."""

        print(f"🎯 Orchestrator processing message: '{request.message}'")
        start_time = time.time()

        try:
            # Get or create conversation
            conversation = await self._get_or_create_conversation(
                db, user, request.conversation_id
            )
            print(f"📝 Using conversation: {conversation.id}")

            # Step 1: Analyze intent
            print(f"🔍 Step 1: Analyzing intent...")
            intent_analysis = await self.intent_analyzer.analyze_intent(
                request.message, request.context
            )
            print(f"✅ Intent analysis result:")
            print(f"   Category: {intent_analysis.category}")
            print(f"   Confidence: {intent_analysis.confidence}")
            print(f"   Keywords: {intent_analysis.keywords}")
            print(f"   Reasoning: {intent_analysis.reasoning}")

            # Step 2: Find matching agents
            print(f"🤖 Step 2: Finding matching agents...")
            agent_matches = await self.agent_matcher.find_matching_agents(
                db, user, intent_analysis
            )
            print(f"✅ Found {len(agent_matches)} matching agents:")
            for i, match in enumerate(agent_matches):
                print(f"   {i+1}. {match.agent_name} (score: {match.match_score:.2f}) - {match.match_reasoning}")

            # Step 3: Make routing decision
            print(f"🎲 Step 3: Making routing decision...")
            routing_result = await self._make_routing_decision(
                intent_analysis, agent_matches, request.user_preferences
            )
            print(f"✅ Routing decision:")
            print(f"   Decision: {routing_result.decision}")
            print(f"   Confidence: {routing_result.confidence}")
            print(f"   Selected agent: {routing_result.selected_agent.agent_name if routing_result.selected_agent else 'None'}")
            print(f"   Reasoning: {routing_result.reasoning}")

            # Step 4: Execute the routing decision
            print(f"⚡ Step 4: Executing routing...")
            agent_response, usage_info = await self._execute_routing(
                db, user, routing_result, request.message, conversation.id
            )
            print(f"✅ Got agent response ({len(agent_response)} characters)")

            # Step 5: Save conversation message
            print(f"💾 Step 5: Saving conversation...")
            message_index = await self._save_conversation_message(
                db, conversation, request.message, agent_response,
                intent_analysis, routing_result
            )

            # Step 6: Update conversation metadata
            await self._update_conversation_metadata(db, conversation, intent_analysis)

            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)

            print(f"🎉 Orchestrator completed successfully in {response_time_ms}ms")

            return OrchestratorResponse(
                conversation_id=conversation.id,
                message_index=message_index,
                user_message=request.message,
                agent_response=agent_response,
                routing_result=routing_result,
                response_time_ms=response_time_ms,
                usage=usage_info,
                debug_info=None
            )

        except Exception as e:
            print(f"❌ Orchestrator error: {type(e).__name__}: {str(e)}")
            import traceback
            traceback.print_exc()

            # Return fallback response
            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)

            # Try to get a fallback conversation
            try:
                conversation = await self._get_or_create_conversation(db, user, request.conversation_id)
                conversation_id = conversation.id
            except:
                conversation_id = str(uuid.uuid4())

            fallback_routing = RoutingResult(
                decision=RoutingDecision.NO_SUITABLE_AGENT,
                intent_analysis=intent_analysis if 'intent_analysis' in locals() else None,
                selected_agent=None,
                alternative_agents=[],
                reasoning=f"Orchestrator error: {str(e)}",
                confidence=0.0
            )

            return OrchestratorResponse(
                conversation_id=conversation_id,
                message_index=1,
                user_message=request.message,
                agent_response=f"I apologize, but I encountered an error processing your request: {str(e)}",
                routing_result=fallback_routing,
                response_time_ms=response_time_ms,
                usage=None,
                debug_info=None
            )
    
    async def _get_or_create_conversation(
        self,
        db: AsyncSession,
        user: User,
        conversation_id: Optional[str]
    ) -> Conversation:
        """Get existing conversation or create a new one with tenant isolation."""

        if conversation_id:
            # Try to get existing conversation with tenant isolation
            result = await db.execute(
                select(Conversation).where(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user.id,
                    Conversation.tenant_id == user.tenant_id
                )
            )
            conversation = result.scalar_one_or_none()

            if conversation:
                # Update last activity
                conversation.last_activity = datetime.utcnow()
                await db.commit()
                return conversation

        # Create new conversation with tenant context
        conversation = Conversation(
            id=str(uuid.uuid4()),
            tenant_id=user.tenant_id,
            user_id=user.id,
            title=None,  # Will be generated later
            total_messages=0,
            agents_used=[],
            primary_intent=None
        )
        
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        return conversation
    
    async def _make_routing_decision(
        self,
        intent_analysis,
        agent_matches: List[AgentMatch],
        user_preferences: Optional[Dict[str, Any]]
    ) -> RoutingResult:
        """Make intelligent routing decision based on analysis."""

        if not agent_matches:
            return RoutingResult(
                decision=RoutingDecision.NO_SUITABLE_AGENT,
                intent_analysis=intent_analysis,
                selected_agent=None,
                alternative_agents=[],
                reasoning="No suitable agents found for this intent",
                confidence=0.0
            )

        # Get the best agent
        best_agent = agent_matches[0]
        alternative_agents = agent_matches[1:5]  # Top 5 alternatives

        # Lower thresholds for better routing
        if best_agent.match_score >= 0.5:  # Lowered from 0.7
            decision = RoutingDecision.SINGLE_AGENT
            confidence = min(intent_analysis.confidence * best_agent.match_score, 1.0)
            reasoning = f"High confidence match: {best_agent.match_reasoning}"
        elif best_agent.match_score >= 0.3:  # Lowered from 0.4
            decision = RoutingDecision.SINGLE_AGENT
            confidence = min(intent_analysis.confidence * best_agent.match_score, 1.0)
            reasoning = f"Moderate confidence match: {best_agent.match_reasoning}"
        elif best_agent.match_score >= 0.1:  # Give low-confidence matches a chance
            decision = RoutingDecision.SINGLE_AGENT
            confidence = 0.3
            reasoning = f"Low confidence match (trying anyway): {best_agent.match_reasoning}"
        else:
            decision = RoutingDecision.NO_SUITABLE_AGENT
            confidence = 0.1
            reasoning = f"Very low confidence match: {best_agent.match_reasoning}"

        # More lenient escalation conditions
        if intent_analysis.confidence < 0.1 or best_agent.match_score < 0.05:
            decision = RoutingDecision.ESCALATE_TO_HUMAN
            reasoning = "Extremely low confidence - recommend human review"

        return RoutingResult(
            decision=decision,
            intent_analysis=intent_analysis,
            selected_agent=best_agent if decision == RoutingDecision.SINGLE_AGENT else None,
            alternative_agents=alternative_agents,
            reasoning=reasoning,
            confidence=confidence
        )
    
    async def _execute_routing(
        self,
        db: AsyncSession,
        user: User,
        routing_result: RoutingResult,
        user_message: str,
        conversation_id: str
    ) -> tuple[str, Optional[Dict[str, Any]]]:
        """Execute the routing decision and get agent response."""

        if routing_result.decision == RoutingDecision.SINGLE_AGENT and routing_result.selected_agent:
            # Route to selected agent
            try:
                print(f"🤖 Routing to agent {routing_result.selected_agent.agent_id}: {routing_result.selected_agent.agent_name}")

                # Check if AgentService exists and has the method we need
                if hasattr(AgentService, 'chat_with_agent'):
                    response_data = await AgentService.chat_with_agent(
                        db, routing_result.selected_agent.agent_id, user_message,
                        user, conversation_id
                    )
                    if response_data and isinstance(response_data, dict):
                        return response_data.get("response", "No response from agent"), response_data.get("usage")
                    else:
                        print(f"⚠️ AgentService returned invalid response: {response_data}")
                        return f"Response from {routing_result.selected_agent.agent_name}: I received your message but couldn't process it properly.", None
                else:
                    # Fallback: try to call agent directly
                    print("⚠️ AgentService.chat_with_agent not available, using fallback")
                    # You'll need to implement this fallback based on your agent system
                    return f"Response from {routing_result.selected_agent.agent_name}: I received your message '{user_message}' but the agent service is not fully configured.", None

            except Exception as e:
                print(f"❌ Agent execution error: {e}")
                return f"I apologize, but I encountered an error while processing your request with {routing_result.selected_agent.agent_name}: {str(e)}", None

        elif routing_result.decision == RoutingDecision.NO_SUITABLE_AGENT:
            return self._generate_no_agent_response(routing_result), None

        elif routing_result.decision == RoutingDecision.ESCALATE_TO_HUMAN:
            return self._generate_escalation_response(routing_result), None

        else:
            return "I'm not sure how to help with that request. Could you please rephrase or provide more details?", None
    
    def _generate_no_agent_response(self, routing_result: RoutingResult) -> str:
        """Generate response when no suitable agent is found."""
        
        base_response = "I don't have a specialized agent available for this type of request."
        
        if routing_result.alternative_agents:
            agent_names = [agent.agent_name for agent in routing_result.alternative_agents[:3]]
            base_response += f" However, you might try asking one of these agents: {', '.join(agent_names)}."
        
        base_response += " You could also try rephrasing your question or creating a custom agent for this type of task."
        
        return base_response
    
    def _generate_escalation_response(self, routing_result: RoutingResult) -> str:
        """Generate response for human escalation."""
        
        return ("I'm having difficulty understanding exactly what you need help with. "
                "This might require human assistance. Could you please provide more specific details "
                "about what you're trying to accomplish?")
    
    async def _save_conversation_message(
        self,
        db: AsyncSession,
        conversation: Conversation,
        user_message: str,
        agent_response: str,
        intent_analysis,
        routing_result: RoutingResult
    ) -> int:
        """Save the conversation message to database."""

        message_index = conversation.total_messages + 1

        message = ConversationMessage(
            tenant_id=conversation.tenant_id,
            conversation_id=conversation.id,
            message_index=message_index,
            user_message=user_message,
            agent_response=agent_response,
            intent_category=intent_analysis.category.value,
            confidence_score=intent_analysis.confidence,
            selected_agent_id=routing_result.selected_agent.agent_id if routing_result.selected_agent else None,
            routing_decision=routing_result.decision.value,
            routing_reasoning=routing_result.reasoning
        )

        db.add(message)

        # Update conversation total messages
        conversation.total_messages = message_index

        # Update agents used list
        if routing_result.selected_agent:
            agents_used = conversation.agents_used or []
            if routing_result.selected_agent.agent_id not in agents_used:
                agents_used.append(routing_result.selected_agent.agent_id)
                conversation.agents_used = agents_used

        await db.commit()
        return message_index
    
    async def _update_conversation_metadata(
        self,
        db: AsyncSession,
        conversation: Conversation,
        intent_analysis
    ):
        """Update conversation metadata."""
        
        # Set primary intent if not set
        if not conversation.primary_intent:
            conversation.primary_intent = intent_analysis.category.value
        
        # Generate title if not set and we have enough messages
        if not conversation.title and conversation.total_messages >= 1:
            conversation.title = self._generate_conversation_title(intent_analysis)
        
        await db.commit()
    
    def _generate_conversation_title(self, intent_analysis) -> str:
        """Generate a conversation title based on intent."""
        
        title_map = {
            IntentCategory.CUSTOMER_SERVICE: "Customer Support",
            IntentCategory.FINANCIAL_ANALYSIS: "Financial Analysis",
            IntentCategory.RESEARCH: "Research Inquiry",
            IntentCategory.PROJECT_MANAGEMENT: "Project Discussion",
            IntentCategory.CONTENT_CREATION: "Content Creation",
            IntentCategory.DATA_ANALYSIS: "Data Analysis",
            IntentCategory.TECHNICAL_SUPPORT: "Technical Support",
            IntentCategory.SALES: "Sales Discussion",
            IntentCategory.GENERAL: "General Conversation"
        }
        
        base_title = title_map.get(intent_analysis.category, "Conversation")
        timestamp = datetime.now().strftime("%m/%d")
        
        return f"{base_title} - {timestamp}"
