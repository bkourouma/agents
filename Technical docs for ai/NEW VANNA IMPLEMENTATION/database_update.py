# Updated sections for database_chat.py - Integration with RAG-based Vanna service

# Add these imports at the top
from src.services.vanna_service import vanna_service

# Update the natural language query endpoint
@router.post("/query/natural", response_model=QueryResultResponse)
async def process_natural_language_query(
    query_data: NaturalLanguageQuery,
    db: AsyncSession = Depends(get_db),
    current_user_id: int = 1  # TODO: Get from auth
):
    """Process a natural language query using Vanna AI RAG system."""
    try:
        logger.info(f"[RAG] Processing natural language query: '{query_data.query}'")
        
        # Create query history record
        query_history = QueryHistory(
            user_id=current_user_id,
            natural_language_query=query_data.query,
            execution_status="processing"
        )

        db.add(query_history)
        await db.commit()
        await db.refresh(query_history)

        # Check if Vanna is available
        vanna_available = await vanna_service.is_available()
        logger.info(f"[RAG] Vanna service available: {vanna_available}")

        if not vanna_available:
            logger.error("[RAG] Vanna not available")
            query_history.execution_status = "error"
            query_history.error_message = "Vanna AI is not available. Please check OPENAI_API_KEY environment variable."
            await db.commit()

            return QueryResultResponse(
                success=False,
                error="Vanna AI is not available. Please check OPENAI_API_KEY environment variable.",
                format=query_data.output_format
            )

        # Use Vanna RAG system to generate SQL
        sql_result = await vanna_service.generate_sql(
            question=query_data.query,
            db=db,
            user_id=current_user_id
        )

        if not sql_result["success"]:
            # Update query history with error
            query_history.execution_status = "error"
            query_history.error_message = sql_result["error"]
            await db.commit()

            return QueryResultResponse(
                success=False,
                error=sql_result["error"],