"""
Vanna Database Tool for AI Agent Platform.
Provides natural language database query capabilities using Vanna AI.
Allows agents to query databases using natural language.
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
import json
import logging
import time

from src.services.vanna_service import vanna_service
from src.models.database_chat_schemas import NaturalLanguageQuery, QueryResultResponse

logger = logging.getLogger(__name__)


class VannaDatabaseQueryRequest(BaseModel):
    """Request model for Vanna database queries."""
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language query")
    output_format: str = Field(default="json", description="Output format: json, table, or chart")
    max_results: int = Field(default=100, ge=1, le=1000, description="Maximum number of results")
    connection_id: Optional[int] = Field(default=None, description="Database connection ID")


class VannaDatabaseQueryResult(BaseModel):
    """Result model for Vanna database queries."""
    success: bool
    query: str
    sql_generated: Optional[str] = None
    results: Optional[List[Dict[str, Any]]] = None
    chart_data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None
    row_count: Optional[int] = None
    response: Optional[str] = None  # Formatted response text
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata including artifacts


class VannaDatabaseTool:
    """Vanna database tool implementation for agents."""
    
    def __init__(self, agent_id: int, config: Optional[Dict[str, Any]] = None):
        """Initialize the Vanna database tool for an agent.
        
        Args:
            agent_id: The ID of the agent using this tool
            config: Tool configuration options
        """
        self.agent_id = agent_id
        self.config = config or {}
        
        # Default configuration
        self.max_results = self.config.get("max_results", 100)
        self.enable_visualization = self.config.get("enable_visualization", True)
        self.allowed_operations = self.config.get("allowed_operations", ["SELECT"])
        self.connection_id = self.config.get("connection_id", None)
        
        logger.info(f"🗄️ Vanna database tool initialized for agent {agent_id}")
    
    async def is_available(self) -> bool:
        """Check if Vanna AI service is available."""
        try:
            return await vanna_service.is_available()
        except Exception as e:
            logger.error(f"❌ Failed to check Vanna availability: {e}")
            return False
    
    async def execute_query(
        self, 
        db,
        query_request: VannaDatabaseQueryRequest,
        user_id: int = 1
    ) -> VannaDatabaseQueryResult:
        """Execute a natural language database query using Vanna AI.
        
        Args:
            db: Database session
            query_request: The natural language query request
            user_id: User ID for context
            
        Returns:
            VannaDatabaseQueryResult with query results or error
        """
        start_time = datetime.now()
        
        try:
            logger.info(f"🔍 Agent {self.agent_id} executing query: {query_request.query}")
            
            # Check if Vanna is available
            if not await self.is_available():
                return VannaDatabaseQueryResult(
                    success=False,
                    query=query_request.query,
                    error="Vanna AI is not available. Please check OPENAI_API_KEY environment variable."
                )
            
            # Create Vanna query object
            vanna_query = NaturalLanguageQuery(
                query=query_request.query,
                output_format=query_request.output_format,
                max_results=min(query_request.max_results, self.max_results)
            )
            
            # Use Vanna service to generate and execute SQL
            sql_result = await vanna_service.generate_sql(
                question=query_request.query,
                db=db,
                user_id=user_id
            )
            
            if not sql_result["success"]:
                return VannaDatabaseQueryResult(
                    success=False,
                    query=query_request.query,
                    error=sql_result["error"]
                )
            
            # Execute the generated SQL
            execution_result = await vanna_service.execute_sql(
                sql=sql_result["sql"],
                db=db
            )
            
            if not execution_result["success"]:
                return VannaDatabaseQueryResult(
                    success=False,
                    query=query_request.query,
                    sql_generated=sql_result["sql"],
                    error=execution_result["error"]
                )
            
            # Calculate execution time
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Prepare results
            results = execution_result.get("data", [])
            row_count = len(results) if results else 0
            
            # Generate chart data if visualization is enabled and requested
            chart_data = None
            if (self.enable_visualization and 
                query_request.output_format == "chart" and 
                results):
                try:
                    chart_data = await self._generate_chart_data(results, sql_result["sql"])
                except Exception as e:
                    logger.warning(f"⚠️ Failed to generate chart data: {e}")
            
            logger.info(f"✅ Query executed successfully: {row_count} rows in {execution_time:.2f}s")

            # Create artifact for database results if we have data
            artifacts = []
            response_text = ""

            if row_count == 0:
                response_text = "La requête a été exécutée avec succès, mais aucun résultat n'a été trouvé."
            else:
                # Create artifact for database results
                artifact_data = {
                    "id": f"db-result-{int(time.time() * 1000)}",
                    "type": "database-table",
                    "title": f"Query Results ({row_count} rows)",
                    "content": {
                        "data": results[:query_request.max_results],
                        "columns": list(results[0].keys()) if results else [],
                        "sql": sql_result["sql"],
                        "execution_time_ms": execution_time * 1000,
                        "row_count": row_count
                    },
                    "metadata": {
                        "tool_used": "vanna_database",
                        "execution_time": execution_time * 1000
                    }
                }
                artifacts.append(artifact_data)

                # Create a brief summary response when artifact is present
                if row_count == 1:
                    response_text = f"J'ai trouvé 1 résultat correspondant à votre requête. Les détails sont affichés dans le tableau ci-dessous."
                elif row_count <= 10:
                    response_text = f"J'ai trouvé {row_count} résultats correspondant à votre requête. Tous les détails sont affichés dans le tableau ci-dessous."
                elif row_count <= 100:
                    response_text = f"J'ai trouvé {row_count} résultats correspondant à votre requête. Vous pouvez explorer les données dans le tableau interactif ci-dessous."
                else:
                    response_text = f"J'ai trouvé {row_count} résultats correspondant à votre requête. Le tableau ci-dessous vous permet de parcourir et filtrer toutes les données."

            return VannaDatabaseQueryResult(
                success=True,
                query=query_request.query,
                sql_generated=sql_result["sql"],
                results=results[:query_request.max_results],  # Limit results
                chart_data=chart_data,
                execution_time=execution_time,
                row_count=row_count,
                response=response_text,
                metadata={
                    "sql_query": sql_result["sql"],
                    "execution_time_ms": execution_time * 1000,
                    "row_count": row_count,
                    "database_result": {
                        "data": results[:query_request.max_results],
                        "columns": list(results[0].keys()) if results else [],
                        "sql": sql_result["sql"],
                        "execution_time_ms": execution_time * 1000,
                        "row_count": row_count,
                        "success": True
                    },
                    "artifacts": artifacts,
                    "tool_used": "vanna_database"
                }
            )
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            logger.error(f"❌ Database query failed: {e}")
            
            return VannaDatabaseQueryResult(
                success=False,
                query=query_request.query,
                error=f"Database query failed: {str(e)}",
                execution_time=execution_time
            )
    
    async def _generate_chart_data(self, results: List[Dict], sql: str) -> Optional[Dict[str, Any]]:
        """Generate chart data from query results.
        
        Args:
            results: Query results
            sql: Generated SQL query
            
        Returns:
            Chart configuration data or None
        """
        if not results:
            return None
        
        try:
            # Use Vanna's chart generation if available
            chart_result = await vanna_service.generate_chart(
                sql=sql,
                data=results
            )
            
            if chart_result.get("success"):
                return chart_result.get("chart_data")
            
        except Exception as e:
            logger.warning(f"⚠️ Chart generation failed: {e}")
        
        return None
    
    def get_capabilities(self) -> List[str]:
        """Get list of capabilities this tool provides."""
        return [
            "natural_language_sql",
            "database_query", 
            "data_retrieval",
            "sql_generation",
            "database_introspection"
        ] + (["data_visualization"] if self.enable_visualization else [])
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the tool."""
        return {
            "agent_id": self.agent_id,
            "max_results": self.max_results,
            "visualization_enabled": self.enable_visualization,
            "allowed_operations": self.allowed_operations,
            "connection_id": self.connection_id,
            "capabilities": self.get_capabilities()
        }


# Tool configuration for agent integration
VANNA_DATABASE_TOOL_CONFIG = {
    "name": "vanna_database",
    "display_name": "Database Query",
    "description": "Query databases using natural language with Vanna AI. Convert questions into SQL and execute them safely.",
    "capabilities": [
        "natural_language_sql",
        "database_query",
        "data_retrieval", 
        "sql_generation",
        "database_introspection",
        "data_visualization",
        "query_optimization"
    ],
    "configuration_schema": {
        "max_results": {
            "type": "integer", 
            "default": 100,
            "min": 1,
            "max": 1000,
            "description": "Maximum number of results to return"
        },
        "enable_visualization": {
            "type": "boolean", 
            "default": True,
            "description": "Enable automatic chart generation for query results"
        },
        "allowed_operations": {
            "type": "array", 
            "default": ["SELECT"],
            "items": {"type": "string"},
            "description": "Allowed SQL operations (SELECT, INSERT, UPDATE, DELETE)"
        },
        "connection_id": {
            "type": "integer",
            "default": None,
            "description": "Specific database connection ID to use"
        },
        "auto_limit": {
            "type": "boolean",
            "default": True,
            "description": "Automatically add LIMIT clause to prevent large result sets"
        }
    },
    "requirements": [
        "OPENAI_API_KEY environment variable",
        "Vanna AI service availability",
        "Database connection configured"
    ],
    "examples": [
        "Show me the top 10 customers by revenue",
        "What are the sales trends for the last 6 months?",
        "Find all orders placed yesterday",
        "Calculate average order value by region",
        "List products with low inventory"
    ]
}


def get_vanna_database_tool(agent_id: int, config: Optional[Dict[str, Any]] = None) -> VannaDatabaseTool:
    """Get a Vanna database tool instance for an agent.

    Args:
        agent_id: The ID of the agent
        config: Optional tool configuration

    Returns:
        VannaDatabaseTool instance
    """
    return VannaDatabaseTool(agent_id, config)


def format_query_result_for_agent(result: VannaDatabaseQueryResult) -> str:
    """Format query result for display in agent chat with concise summary.

    Args:
        result: The query result to format

    Returns:
        Formatted string for agent response (brief summary when artifacts are present)
    """
    if not result.success:
        return f"❌ **Database Query Failed**\n\nError: {result.error}"

    if not result.results:
        return f"✅ **Query Executed Successfully**\n\nNo results found for your query."

    # Provide a brief summary since detailed data will be in artifacts
    row_count = result.row_count or len(result.results)

    if row_count == 1:
        response = f"✅ **Query Successful** - Found 1 result matching your query."
    elif row_count <= 10:
        response = f"✅ **Query Successful** - Found {row_count} results matching your query."
    elif row_count <= 100:
        response = f"✅ **Query Successful** - Found {row_count} results. You can explore the data in the interactive table."
    else:
        response = f"✅ **Query Successful** - Found {row_count} results. Use the table below to browse and filter the data."

    if result.execution_time:
        response += f" (executed in {result.execution_time:.2f}s)"

    if result.chart_data:
        response += f"\n\n📊 **Chart visualization available**"

    return response


async def detect_database_intent(message: str) -> bool:
    """Detect if a message contains database-related intent.

    Args:
        message: The user message to analyze

    Returns:
        True if the message appears to be database-related
    """
    database_keywords = [
        # Query words (English)
        "show", "find", "get", "list", "count", "sum", "average", "total", "max", "min",
        # Query words (French)
        "montre", "trouve", "affiche", "liste", "compte", "somme", "moyenne", "total", "maximum", "minimum",
        "donne", "récupère", "cherche", "recherche",
        # Data words (English)
        "data", "records", "rows", "table", "database", "query", "sql",
        # Data words (French)
        "données", "enregistrements", "lignes", "table", "base de données", "requête",
        # Business terms (English)
        "sales", "customers", "orders", "products", "transactions", "revenue", "profit",
        "inventory", "users", "accounts", "payments", "reports",
        # Business terms (French)
        "ventes", "clients", "commandes", "produits", "transactions", "revenus", "bénéfices",
        "inventaire", "utilisateurs", "comptes", "paiements", "rapports",
        # Time-based (English)
        "today", "yesterday", "last week", "last month", "this year", "recent",
        # Time-based (French)
        "aujourd'hui", "hier", "dernière semaine", "dernier mois", "cette année", "récent",
        "dernières", "derniers", "récentes", "récents",
        # Comparison words (English)
        "top", "bottom", "highest", "lowest", "best", "worst", "most", "least",
        # Comparison words (French)
        "haut", "bas", "plus élevé", "plus bas", "meilleur", "pire", "plus", "moins"
    ]

    message_lower = message.lower()

    # Check for database keywords
    keyword_matches = sum(1 for keyword in database_keywords if keyword in message_lower)

    # Check for question patterns that suggest data queries
    question_patterns = [
        # English patterns
        "how many", "what are", "show me", "find all", "list the", "get the",
        "which", "who has", "when did", "where are",
        # French patterns
        "combien de", "quels sont", "montre moi", "trouve tous", "liste les", "donne moi",
        "lesquels", "qui a", "quand", "où sont", "quelle est", "quel est"
    ]

    pattern_matches = sum(1 for pattern in question_patterns if pattern in message_lower)

    # Return True if we have enough indicators
    return keyword_matches >= 2 or pattern_matches >= 1
