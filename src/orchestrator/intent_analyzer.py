"""
Enhanced Intent analysis engine for the orchestrator.
"""

import re
from typing import List, Dict, Tuple
from src.models.orchestrator import IntentCategory, IntentAnalysis


class IntentAnalyzer:
    """Analyzes user messages to determine intent and extract keywords."""

    # Enhanced intent keywords mapping with French support
    INTENT_KEYWORDS = {
        IntentCategory.RESEARCH: [
            # English research keywords
            "research", "study", "investigate", "analyze", "find", "search", "explore",
            "information", "data", "facts", "evidence", "source", "literature",
            "academic", "scholarly", "paper", "article", "report", "survey",
            "what is", "what does", "tell me about", "explain", "definition",
            "meaning", "describe", "details", "overview", "summary", "what are",
            "modules", "features", "components", "elements", "parts", "functions"
            # French research keywords
            "recherche", "étude", "enquête", "analyser", "trouver", "chercher",
            "explorer", "informations", "données", "faits", "preuves", "sources",
            "qu'est-ce que", "c'est quoi", "que signifie", "définition",
            "expliquer", "expliquez", "dites-moi", "parlez-moi", "décrivez",
            "détails", "aperçu", "résumé", "signification", "quels sont", "quelles sont",
            "modules", "fonctionnalités", "caractéristiques", "composants", "éléments"
        ],
        IntentCategory.CUSTOMER_SERVICE: [
            "help", "support", "issue", "problem", "complaint", "refund", "return",
            "billing", "account", "service", "assistance", "question", "inquiry",
            "cancel", "subscription", "payment", "order", "delivery", "shipping",
            "aide", "aider", "problème", "souci", "réclamation", "remboursement",
            "facturation", "compte", "annuler", "commande", "livraison"
        ],
        IntentCategory.FINANCIAL_ANALYSIS: [
            "financial", "finance", "money", "budget", "investment", "profit", "loss",
            "revenue", "cost", "expense", "analysis", "report", "forecast", "trend",
            "market", "stock", "portfolio", "roi", "cash flow", "balance sheet",
            "financier", "argent", "budget", "investissement", "profit", "perte",
            "revenus", "coût", "dépense", "marché", "actions", "portefeuille"
        ],
        IntentCategory.PROJECT_MANAGEMENT: [
            "project", "task", "deadline", "schedule", "timeline", "milestone",
            "planning", "organize", "coordinate", "manage", "team", "resource",
            "progress", "status", "update", "meeting", "deliverable", "scope",
            "projet", "tâche", "échéance", "planification", "organiser", "gérer",
            "équipe", "progrès", "statut", "réunion", "livrable"
        ],
        IntentCategory.CONTENT_CREATION: [
            "write", "create", "content", "blog", "article", "copy", "marketing",
            "social media", "post", "email", "newsletter", "creative", "design",
            "brand", "message", "campaign", "story", "script", "proposal",
            "écrire", "créer", "contenu", "article", "marketing", "campagne"
        ],
        IntentCategory.DATA_ANALYSIS: [
            "data", "analytics", "statistics", "metrics", "dashboard", "visualization",
            "chart", "graph", "pattern", "insight", "correlation", "regression",
            "database", "sql", "excel", "spreadsheet", "calculation", "formula",
            "données", "statistiques", "métriques", "graphique", "calcul"
        ],
        IntentCategory.TECHNICAL_SUPPORT: [
            "technical", "tech", "software", "hardware", "bug", "error", "crash",
            "install", "setup", "configure", "troubleshoot", "fix", "repair",
            "update", "upgrade", "compatibility", "performance", "security",
            "technique", "logiciel", "matériel", "erreur", "installer", "réparer"
        ],
        IntentCategory.SALES: [
            "sales", "sell", "buy", "purchase", "price", "quote", "proposal",
            "deal", "contract", "negotiation", "lead", "prospect", "customer",
            "client", "revenue", "target", "goal", "commission", "pipeline",
            "vente", "vendre", "acheter", "prix", "devis", "contrat", "client"
        ]
    }
    
    # Enhanced intent patterns with French support
    INTENT_PATTERNS = {
        IntentCategory.RESEARCH: [
            # English patterns
            r"research (about|on|into)",
            r"find (information|data|sources) about",
            r"what does the research say about",
            r"what is .+\?",
            r"what does .+ mean",
            r"tell me about",
            r"explain .+ to me",
            r"i want to (know|learn) about",
            r"information about",
            r"details about",
            r"what are (the|its)",
            r"(modules|features|components) of",
            r"what (modules|features|components) does"
            # French patterns
            r"qu'est-ce que (c'est|est|signifie)",
            r"c'est quoi",
            r"que signifie",
            r"peux-tu (expliquer|me dire)",
            r"pouvez-vous (expliquer|me dire)",
            r"dites-moi",
            r"parlez-moi",
            r"informations? sur",
            r"détails sur",
            r"je veux (savoir|apprendre|connaître)",
            r"recherche sur",
            r"étude de",
            r"quels sont (les|ses)",
            r"quelles sont (les|ses)",
            r"(modules|fonctionnalités|caractéristiques) de"
        ],
        IntentCategory.CUSTOMER_SERVICE: [
            r"i have a (problem|issue|question) with",
            r"can you help me with",
            r"i need (help|support|assistance)",
            r"my (order|account|service) is",
            r"how do i (cancel|return|refund)",
            r"j'ai un (problème|souci) avec",
            r"pouvez-vous m'aider",
            r"j'ai besoin d'aide"
        ],
        IntentCategory.FINANCIAL_ANALYSIS: [
            r"analyze (the|our) (financial|budget|revenue)",
            r"what is (the|our) (profit|loss|roi)",
            r"financial (report|analysis|forecast)",
            r"budget (analysis|planning|review)",
            r"investment (analysis|opportunity|return)"
        ],
        IntentCategory.PROJECT_MANAGEMENT: [
            r"project (status|update|timeline)",
            r"schedule (a|the) (meeting|task|deadline)",
            r"manage (the|this) project",
            r"coordinate (with|the) team",
            r"track (progress|milestones|deliverables)"
        ],
        IntentCategory.CONTENT_CREATION: [
            r"write (a|an) (blog|article|post)",
            r"create (content|copy|marketing)",
            r"draft (a|an) (email|proposal|script)",
            r"social media (post|content|campaign)",
            r"marketing (message|copy|campaign)"
        ],
        IntentCategory.DATA_ANALYSIS: [
            r"analyze (the|this) data",
            r"create (a|an) (chart|graph|dashboard)",
            r"data (analysis|visualization|insights)",
            r"statistical (analysis|test|model)",
            r"database (query|analysis|report)"
        ]
    }

    def __init__(self):
        # Simple fallback system - no LLM dependency for now
        pass
    
    async def analyze_intent(self, message: str, context: Dict = None) -> IntentAnalysis:
        """Analyze the intent of a user message."""

        print(f"🔍 Analyzing intent for: '{message}'")

        # Use rule-based classification
        result = self._rule_based_classification(message)

        print(f"✅ Intent analysis result: {result.category} (confidence: {result.confidence})")

        return result
    
    def _rule_based_classification(self, message: str) -> IntentAnalysis:
        """Rule-based intent classification using keywords and patterns."""
        message_lower = message.lower().strip()

        print(f"🔍 Rule-based classification for: '{message_lower}'")

        # Score each intent category
        intent_scores = {}
        matched_keywords = {}

        # Keyword matching
        for intent, keywords in self.INTENT_KEYWORDS.items():
            score = 0
            keywords_found = []

            for keyword in keywords:
                if keyword in message_lower:
                    score += 1
                    keywords_found.append(keyword)
                    print(f"   ✓ Found keyword '{keyword}' for {intent}")

            # Normalize score by number of keywords (but give some weight to absolute matches)
            normalized_score = (score / len(keywords)) + (score * 0.01)  # Small bonus for multiple matches
            intent_scores[intent] = normalized_score
            matched_keywords[intent] = keywords_found

        # Pattern matching (bonus points)
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    intent_scores[intent] = intent_scores.get(intent, 0) + 0.5  # Significant bonus for pattern match
                    print(f"   ✓ Matched pattern '{pattern}' for {intent}")

        print(f"🔍 Intent scores: {intent_scores}")

        # Find best match
        if not intent_scores or max(intent_scores.values()) == 0:
            print("   → Defaulting to GENERAL (no matches)")
            return IntentAnalysis(
                category=IntentCategory.GENERAL,
                confidence=0.5,  # Higher default confidence
                keywords=[],
                reasoning="No specific intent patterns detected, defaulting to general",
                suggested_agents=[]
            )

        best_intent = max(intent_scores, key=intent_scores.get)
        confidence = min(intent_scores[best_intent] * 2, 1.0)  # Boost confidence

        # Ensure minimum confidence for detected intents
        if confidence < 0.3:
            confidence = 0.3

        print(f"   → Best intent: {best_intent} (confidence: {confidence})")

        return IntentAnalysis(
            category=best_intent,
            confidence=confidence,
            keywords=matched_keywords.get(best_intent, []),
            reasoning=f"Rule-based classification based on keywords: {matched_keywords.get(best_intent, [])}",
            suggested_agents=[]
        )
