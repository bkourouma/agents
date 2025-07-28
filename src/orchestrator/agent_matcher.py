"""
Agent matching system for the orchestrator.
"""

from typing import List, Dict, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from src.models.agent import Agent, AgentType, AgentStatus
from src.models.user import User
from src.models.orchestrator import IntentCategory, IntentAnalysis, AgentMatch


class AgentMatcher:
    """Matches user intents to appropriate agents."""
    
    # Intent to agent type mapping
    INTENT_TO_AGENT_TYPE = {
        IntentCategory.CUSTOMER_SERVICE: [AgentType.CUSTOMER_SERVICE, AgentType.GENERAL],
        IntentCategory.FINANCIAL_ANALYSIS: [AgentType.FINANCIAL_ANALYSIS, AgentType.DATA_ANALYSIS],
        IntentCategory.RESEARCH: [AgentType.RESEARCH, AgentType.GENERAL],
        IntentCategory.PROJECT_MANAGEMENT: [AgentType.PROJECT_MANAGEMENT, AgentType.GENERAL],
        IntentCategory.CONTENT_CREATION: [AgentType.CONTENT_CREATION, AgentType.GENERAL],
        IntentCategory.DATA_ANALYSIS: [AgentType.DATA_ANALYSIS, AgentType.FINANCIAL_ANALYSIS],
        IntentCategory.TECHNICAL_SUPPORT: [AgentType.CUSTOMER_SERVICE, AgentType.GENERAL],
        IntentCategory.SALES: [AgentType.CUSTOMER_SERVICE, AgentType.GENERAL],
        IntentCategory.GENERAL: [AgentType.GENERAL],
        IntentCategory.UNKNOWN: [AgentType.GENERAL]
    }
    
    def __init__(self):
        pass
    
    async def find_matching_agents(
        self, 
        db: AsyncSession, 
        user: User, 
        intent_analysis: IntentAnalysis,
        limit: int = 5
    ) -> List[AgentMatch]:
        """Find agents that match the given intent."""
        
        # Get relevant agent types for this intent
        relevant_types = self.INTENT_TO_AGENT_TYPE.get(
            intent_analysis.category, 
            [AgentType.GENERAL]
        )
        
        # Query for matching agents
        agents = await self._query_matching_agents(db, user, relevant_types)
        
        # Score and rank agents
        agent_matches = []
        for agent in agents:
            match_score = self._calculate_match_score(agent, intent_analysis)
            reasoning = self._generate_match_reasoning(agent, intent_analysis, match_score)
            
            agent_match = AgentMatch(
                agent_id=agent.id,
                agent_name=agent.name,
                agent_type=agent.agent_type,
                match_score=match_score,
                match_reasoning=reasoning
            )
            agent_matches.append(agent_match)
        
        # Sort by match score (descending) and return top matches
        agent_matches.sort(key=lambda x: x.match_score, reverse=True)
        return agent_matches[:limit]
    
    async def _query_matching_agents(
        self, 
        db: AsyncSession, 
        user: User, 
        relevant_types: List[AgentType]
    ) -> List[Agent]:
        """Query database for agents matching the criteria."""
        
        # Convert enum values to strings for database query
        type_values = [agent_type.value for agent_type in relevant_types]
        
        # Query for user's own agents + public agents
        query = select(Agent).where(
            and_(
                Agent.status == AgentStatus.ACTIVE.value,
                Agent.agent_type.in_(type_values),
                # User's own agents OR public agents
                (Agent.owner_id == user.id) | (Agent.is_public == True)
            )
        ).order_by(
            # Prioritize user's own agents
            Agent.owner_id == user.id,
            # Then by usage count (more used = better)
            Agent.usage_count.desc(),
            # Then by creation date (newer = better)
            Agent.created_at.desc()
        )
        
        result = await db.execute(query)
        return result.scalars().all()
    
    def _calculate_match_score(self, agent: Agent, intent_analysis: IntentAnalysis) -> float:
        """Calculate how well an agent matches the intent."""
        score = 0.0
        
        # Base score from agent type matching
        relevant_types = self.INTENT_TO_AGENT_TYPE.get(intent_analysis.category, [])
        try:
            agent_type_enum = AgentType(agent.agent_type)
            if agent_type_enum in relevant_types:
                # Primary match gets higher score
                if relevant_types.index(agent_type_enum) == 0:
                    score += 0.6
                else:
                    score += 0.4
        except ValueError:
            # Unknown agent type
            score += 0.2
        
        # Keyword matching in agent description and system prompt
        keywords_score = self._calculate_keyword_match(agent, intent_analysis.keywords)
        score += keywords_score * 0.3
        
        # Usage-based scoring (popular agents get slight boost)
        if agent.usage_count > 0:
            usage_boost = min(agent.usage_count / 100.0, 0.1)  # Max 0.1 boost
            score += usage_boost
        
        # Ensure score is between 0 and 1
        return min(max(score, 0.0), 1.0)
    
    def _calculate_keyword_match(self, agent: Agent, keywords: List[str]) -> float:
        """Calculate keyword matching score."""
        if not keywords:
            return 0.0
        
        # Combine agent text fields for keyword matching
        agent_text = " ".join(filter(None, [
            agent.name,
            agent.description or "",
            agent.system_prompt,
            agent.personality or "",
            agent.instructions or ""
        ])).lower()
        
        # Count keyword matches
        matches = 0
        for keyword in keywords:
            if keyword.lower() in agent_text:
                matches += 1
        
        # Return ratio of matched keywords
        return matches / len(keywords) if keywords else 0.0
    
    def _generate_match_reasoning(
        self, 
        agent: Agent, 
        intent_analysis: IntentAnalysis, 
        match_score: float
    ) -> str:
        """Generate human-readable reasoning for the match."""
        
        reasons = []
        
        # Agent type reasoning
        relevant_types = self.INTENT_TO_AGENT_TYPE.get(intent_analysis.category, [])
        try:
            agent_type_enum = AgentType(agent.agent_type)
            if agent_type_enum in relevant_types:
                if relevant_types.index(agent_type_enum) == 0:
                    reasons.append(f"Primary match for {intent_analysis.category.value} intent")
                else:
                    reasons.append(f"Secondary match for {intent_analysis.category.value} intent")
        except ValueError:
            reasons.append("General purpose agent")
        
        # Keyword matching
        if intent_analysis.keywords:
            keyword_score = self._calculate_keyword_match(agent, intent_analysis.keywords)
            if keyword_score > 0.5:
                reasons.append(f"Strong keyword match ({keyword_score:.1%})")
            elif keyword_score > 0.2:
                reasons.append(f"Moderate keyword match ({keyword_score:.1%})")
        
        # Usage-based reasoning
        if agent.usage_count > 10:
            reasons.append(f"Experienced agent ({agent.usage_count} previous interactions)")
        elif agent.usage_count > 0:
            reasons.append(f"Some experience ({agent.usage_count} interactions)")
        else:
            reasons.append("New agent")
        
        # Ownership
        # Note: We'd need user context to determine ownership
        # For now, we'll skip this reasoning
        
        if not reasons:
            reasons.append("Available agent")
        
        return "; ".join(reasons)
    
    async def get_best_agent(
        self, 
        db: AsyncSession, 
        user: User, 
        intent_analysis: IntentAnalysis
    ) -> AgentMatch:
        """Get the single best matching agent."""
        
        matches = await self.find_matching_agents(db, user, intent_analysis, limit=1)
        
        if not matches:
            # No suitable agents found - this shouldn't happen if there's at least one general agent
            return AgentMatch(
                agent_id=0,
                agent_name="No suitable agent",
                agent_type="general",
                match_score=0.0,
                match_reasoning="No active agents found for this intent"
            )
        
        return matches[0]
    
    async def get_agent_recommendations(
        self, 
        db: AsyncSession, 
        user: User, 
        intent_analysis: IntentAnalysis,
        exclude_agent_id: int = None
    ) -> List[AgentMatch]:
        """Get agent recommendations, optionally excluding a specific agent."""
        
        matches = await self.find_matching_agents(db, user, intent_analysis, limit=10)
        
        # Filter out excluded agent if specified
        if exclude_agent_id:
            matches = [match for match in matches if match.agent_id != exclude_agent_id]
        
        return matches[:5]  # Return top 5 recommendations
