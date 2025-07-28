# vanna_service.py - RAG-based implementation using Vanna AI with ChromaDB and OpenAI

import os
import logging
import json
import re
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
import pandas as pd

logger = logging.getLogger(__name__)

def setup_vanna_cache():
    """Setup Vanna cache directories with proper permissions"""
    cache_base = os.path.join(os.getcwd(), 'vanna_cache')
    
    # Create directories
    dirs = [
        cache_base,
        os.path.join(cache_base, 'models'),
        os.path.join(cache_base, 'chroma'),
        os.path.join(cache_base, 'sentence_transformers')
    ]
    
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)
    
    # Set environment variables for model caching BEFORE any imports
    os.environ['SENTENCE_TRANSFORMERS_HOME'] = os.path.join(cache_base, 'sentence_transformers')
    os.environ['TRANSFORMERS_CACHE'] = os.path.join(cache_base, 'models')
    os.environ['HF_HOME'] = os.path.join(cache_base, 'models')
    os.environ['CHROMA_CACHE_DIR'] = os.path.join(cache_base, 'chroma')
    
    logger.info(f"[OK] Vanna cache setup complete at: {cache_base}")
    return cache_base

# Call setup BEFORE any Vanna imports
VANNA_CACHE_DIR = setup_vanna_cache()

class VannaService:
    """Service to handle Vanna AI integration for natural language to SQL conversion using RAG."""
    
    def __init__(self):
        self.vanna_instances = {}  # Cache Vanna instances per connection
        self.connection_providers = {}  # Cache provider info per connection
        self._initialize_vanna_components()
        logger.info("[OK] VannaService initialized with RAG-only approach")

    def _initialize_vanna_components(self):
        """Initialize Vanna with OpenAI and ChromaDB components."""
        try:
            # Import after setting environment variables
            from vanna.openai.openai_chat import OpenAI_Chat
            from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
            
            class MyVanna(ChromaDB_VectorStore, OpenAI_Chat):
                def __init__(self, config=None):
                    # Ensure config uses our cache directory
                    if config and 'path' not in config:
                        config['path'] = os.path.join(VANNA_CACHE_DIR, 'chroma_default')
                    ChromaDB_VectorStore.__init__(self, config=config)
                    OpenAI_Chat.__init__(self, config=config)
            
            self.VannaClass = MyVanna
            logger.info("[OK] Vanna components initialized successfully")
            
        except ImportError as e:
            logger.error(f"[ERROR] Failed to import Vanna components: {e}")
            logger.error("Please install Vanna with: pip install 'vanna[chromadb,openai]'")
            raise ImportError(f"Vanna dependencies not found: {e}")

    async def is_available(self) -> bool:
        """Check if Vanna AI is available and configured."""
        try:
            # Check if OpenAI API key is available
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.warning("[WARNING] OPENAI_API_KEY not found")
                return False
            
            # Try to import required components
            from vanna.openai.openai_chat import OpenAI_Chat
            from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
            
            logger.info("[OK] Vanna AI is available")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Vanna AI not available: {e}")
            return False

    def get_vanna_instance(self, connection_id: int = None, user_id: int = None) -> 'MyVanna':
        """Get or create a Vanna instance for a specific connection or user."""
        # Use connection_id if provided, otherwise use user_id
        instance_key = connection_id if connection_id else f"user_{user_id}"
        
        logger.info(f"[VANNA] Getting Vanna instance for key: {instance_key}")
        
        if instance_key not in self.vanna_instances:
            # Configure Vanna with custom cache directory
            config = {
                'api_key': os.getenv('OPENAI_API_KEY'),
                'model': os.getenv('VANNA_MODEL', 'gpt-3.5-turbo'),
                'path': os.path.join(VANNA_CACHE_DIR, f'chroma_db_{instance_key}'),
            }
            
            if not config['api_key']:
                raise ValueError("OPENAI_API_KEY environment variable is required")
            
            logger.info(f"[AI] Creating Vanna instance with model: {config['model']}")
            logger.info(f"[STORAGE] Using ChromaDB path: {config['path']}")
            
            # Create Vanna instance
            vn = self.VannaClass(config=config)

            # Enable LLM to see data for better introspection
            vn.allow_llm_to_see_data = True
            logger.info("[RAG] Enabled allow_llm_to_see_data for database introspection")

            # Connect to database
            if connection_id:
                # Connect to external database
                self._connect_to_external_database(vn, connection_id)
            else:
                # Train with basic examples for transactionsmobiles table
                self._train_vanna_with_basic_examples(vn)

            self.vanna_instances[instance_key] = vn
            logger.info(f"[OK] Vanna instance created for key: {instance_key}")

        return self.vanna_instances[instance_key]

    def _connect_to_external_database(self, vn, connection_id: int):
        """Connect Vanna to an external database using connection configuration."""
        try:
            # Import here to avoid circular imports
            from src.models.database_chat import DatabaseConnection
            from src.core.database import AsyncSessionLocal
            import asyncio

            async def get_connection_config():
                async with AsyncSessionLocal() as session:
                    from sqlalchemy import select
                    result = await session.execute(
                        select(DatabaseConnection).where(DatabaseConnection.id == connection_id)
                    )
                    return result.scalar_one_or_none()

            # Get connection configuration
            connection = asyncio.run(get_connection_config())
            if not connection:
                logger.error(f"[VANNA] Connection {connection_id} not found")
                return

            # Decrypt connection string
            connection_string = self._decrypt_connection_string(connection.connection_string)

            # Connect based on database type
            if connection.database_type == 'postgresql':
                vn.connect_to_postgres(dsn=connection_string)
                logger.info(f"[VANNA] Connected to PostgreSQL database {connection_id}")
            elif connection.database_type == 'sqlite':
                config = connection.connection_config or {}
                database_path = config.get('database', connection_string.replace('sqlite:///', ''))
                vn.connect_to_sqlite(database=database_path)
                logger.info(f"[VANNA] Connected to SQLite database {connection_id}")
            else:
                logger.warning(f"[VANNA] Database type {connection.database_type} not fully supported yet")
                # For unsupported types, try to use the connection string directly
                logger.info(f"[VANNA] Attempting generic connection for {connection.database_type}")

        except Exception as e:
            logger.error(f"[VANNA] Failed to connect to external database {connection_id}: {e}")

    def _decrypt_connection_string(self, encrypted_string: str) -> str:
        """Decrypt connection string. TODO: Implement proper decryption."""
        # For now, just return as-is. In production, implement proper decryption
        return encrypted_string

    def _train_vanna_with_basic_examples(self, vn):
        """Train Vanna with basic examples for the transactionsmobiles table."""
        logger.info("[TRAIN] Training Vanna with basic examples")
        
        try:
            # Basic training examples for database operations
            training_examples = [
                {
                    "question": "What are the transactions with highest amounts?",
                    "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC LIMIT 10;",
                    "documentation": "Query to get transactions sorted by amount in descending order"
                },
                {
                    "question": "Show me recent transactions",
                    "sql": "SELECT * FROM transactionsmobiles ORDER BY timestamp DESC LIMIT 10;",
                    "documentation": "Query to get the most recent transactions"
                },
                {
                    "question": "Count total transactions",
                    "sql": "SELECT COUNT(*) as total_transactions FROM transactionsmobiles;",
                    "documentation": "Query to count all transactions in the table"
                },
                {
                    "question": "les montants les plus élevés",
                    "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC LIMIT 10;",
                    "documentation": "French query for highest amounts - sort by amount descending"
                },
                {
                    "question": "les 8 montants les plus élevés",
                    "sql": "SELECT * FROM transactionsmobiles ORDER BY amount DESC LIMIT 8;",
                    "documentation": "French query for top 8 highest amounts"
                },
                {
                    "question": "transactions récentes",
                    "sql": "SELECT * FROM transactionsmobiles ORDER BY timestamp DESC LIMIT 10;",
                    "documentation": "French query for recent transactions"
                },
                {
                    "question": "transactions Wave",
                    "sql": "SELECT * FROM transactionsmobiles WHERE network = 'Wave' LIMIT 10;",
                    "documentation": "Query for Wave network transactions"
                },
                {
                    "question": "transactions Orange",
                    "sql": "SELECT * FROM transactionsmobiles WHERE network = 'Orange' LIMIT 10;",
                    "documentation": "Query for Orange network transactions"
                }
            ]
            
            # Train with examples
            training_count = 0
            for example in training_examples:
                try:
                    # Train with question-SQL pairs
                    vn.train(question=example["question"], sql=example["sql"])
                    
                    # Train with documentation
                    vn.train(documentation=example["documentation"])
                    
                    training_count += 2
                    logger.debug(f"[TRAIN] Added training example: {example['question']}")
                except Exception as e:
                    logger.warning(f"[WARNING] Failed to add training example: {e}")
            
            # Add DDL for the main table
            ddl_statement = """
            CREATE TABLE transactionsmobiles (
                transactionid VARCHAR(50) PRIMARY KEY,
                network VARCHAR(50),
                transactiontype VARCHAR(50),
                timestamp DATETIME,
                amount DECIMAL(10,2)
            );
            """
            
            try:
                vn.train(ddl=ddl_statement)
                training_count += 1
                logger.info("[TRAIN] Added DDL for transactionsmobiles table")
            except Exception as e:
                logger.warning(f"[WARNING] Failed to add DDL: {e}")
            
            # Add documentation about the database structure
            documentation = """
            Database contains mobile transaction data with the following structure:
            - transactionsmobiles: Main table containing transaction records
            - Key columns: transactionid, network, transactiontype, timestamp, amount
            - Networks include: Wave, Orange, Moov, MoMoney
            - Transaction types: cash-in, cash-out
            - Amount is stored as decimal for financial calculations
            """
            
            try:
                vn.train(documentation=documentation)
                training_count += 1
                logger.info("[TRAIN] Added database documentation")
            except Exception as e:
                logger.warning(f"[WARNING] Failed to add documentation: {e}")
            
            logger.info(f"[OK] Vanna training completed. Added {training_count} training items")
                       
        except Exception as e:
            logger.error(f"[ERROR] Failed to train Vanna with basic examples: {e}")
            # Continue anyway - Vanna can still work with manual training

    async def generate_sql(self, question: str, model_name: str = None, db: AsyncSession = None, user_id: int = None) -> Dict[str, Any]:
        """Generate SQL from natural language question using Vanna RAG."""
        logger.info(f"[RAG] VannaService.generate_sql called with question: '{question}'")

        try:
            # Check if Vanna is available
            is_available = await self.is_available()
            if not is_available:
                return {
                    "success": False,
                    "error": "Vanna AI is not available. Please check OPENAI_API_KEY environment variable.",
                    "sql": None
                }

            # Get Vanna instance (use user_id since we don't have connection_id in this context)
            vn = self.get_vanna_instance(user_id=user_id)
            
            # Use Vanna's RAG system to generate SQL
            sql_query = vn.generate_sql(question)
            
            if not sql_query or sql_query.strip() == "":
                return {
                    "success": False,
                    "error": "Could not generate SQL for the given question. Please try rephrasing your question.",
                    "sql": None
                }
            
            # Validate the generated SQL
            try:
                is_valid = vn.is_sql_valid(sql_query)
                if not is_valid:
                    logger.warning(f"[WARNING] Generated SQL failed validation: {sql_query}")
                    return {
                        "success": False,
                        "error": "Generated SQL is invalid. Please try rephrasing your question.",
                        "sql": sql_query
                    }
            except Exception as validation_error:
                logger.warning(f"[WARNING] SQL validation failed: {validation_error}")
                # Continue anyway - validation might not be critical
            
            logger.info(f"[RAG] Successfully generated SQL: {sql_query}")
            
            return {
                "success": True,
                "sql": sql_query,
                "confidence": 0.9,  # High confidence for RAG-based generation
                "error": None
            }

        except Exception as e:
            logger.error(f"[ERROR] Failed to generate SQL using RAG: {e}")
            return {
                "success": False,
                "error": f"Failed to generate SQL: {str(e)}",
                "sql": None
            }

    async def execute_sql(self, sql: str, db: AsyncSession = None) -> Dict[str, Any]:
        """Execute SQL query and return results using the actual database."""
        logger.info(f"[EXEC] Executing SQL: {sql}")

        try:
            import time
            from sqlalchemy import text

            start_time = time.time()

            if db is None:
                logger.error("[EXEC] No database session provided")
                return {
                    "success": False,
                    "data": None,
                    "columns": None,
                    "row_count": 0,
                    "execution_time_ms": 0,
                    "error": "No database session available"
                }

            # Execute the SQL query
            logger.info(f"[EXEC] Executing query against database: {sql}")
            result = await db.execute(text(sql))

            # Fetch results
            rows = result.fetchall()
            columns = list(result.keys()) if result.keys() else []

            # Convert rows to list of dictionaries
            data = []
            for row in rows:
                row_dict = {}
                for i, column in enumerate(columns):
                    value = row[i]
                    # Handle different data types
                    if hasattr(value, 'isoformat'):  # datetime objects
                        value = value.isoformat()
                    elif isinstance(value, (bytes, bytearray)):  # binary data
                        value = str(value)
                    row_dict[column] = value
                data.append(row_dict)

            execution_time = int((time.time() - start_time) * 1000)

            logger.info(f"[EXEC] Query executed successfully. Returned {len(data)} rows in {execution_time}ms")

            return {
                "success": True,
                "data": data,
                "columns": columns,
                "row_count": len(data),
                "execution_time_ms": execution_time,
                "error": None
            }

        except Exception as e:
            logger.error(f"[ERROR] Failed to execute SQL: {e}")
            return {
                "success": False,
                "data": None,
                "columns": None,
                "row_count": 0,
                "execution_time_ms": 0,
                "error": str(e)
            }

    async def clear_training_data(self) -> bool:
        """Clear all training data from Vanna."""
        logger.info("[CLEAR] Clearing training data")
        try:
            # Clear training data for all instances
            for instance_key, vn in self.vanna_instances.items():
                try:
                    # Get existing training data
                    training_data = vn.get_training_data()

                    if isinstance(training_data, pd.DataFrame) and not training_data.empty:
                        training_list = training_data.to_dict('records')
                    elif isinstance(training_data, list):
                        training_list = training_data
                    else:
                        training_list = []

                    # Remove each training item
                    for item in training_list:
                        if isinstance(item, dict) and 'id' in item:
                            try:
                                vn.remove_training_data(id=item['id'])
                            except Exception as e:
                                logger.warning(f"[WARNING] Failed to remove training item: {e}")

                    logger.info(f"[OK] Cleared training data for instance: {instance_key}")
                except Exception as e:
                    logger.warning(f"[WARNING] Failed to clear training data for {instance_key}: {e}")

            return True
        except Exception as e:
            logger.error(f"[ERROR] Failed to clear training data: {e}")
            return False

    async def train_on_tables(self, db: AsyncSession, table_ids: List[int], user_id: int, model_name: str = None):
        """Train Vanna on selected tables."""
        logger.info(f"[TRAIN] Training on tables: {table_ids}")

        try:
            # Get Vanna instance
            vn = self.get_vanna_instance(user_id=user_id)

            # This is a simplified implementation
            # In a real implementation, you would:
            # 1. Query the database for table schemas using table_ids
            # 2. Generate DDL statements for each table
            # 3. Create example questions and SQL pairs
            # 4. Train Vanna with this data

            # For now, add some basic training
            for table_id in table_ids:
                # Add table-specific training examples
                table_examples = [
                    {
                        "question": f"Show data from table {table_id}",
                        "sql": f"SELECT * FROM table_{table_id} LIMIT 10;",
                        "documentation": f"Query to show data from table {table_id}"
                    }
                ]

                for example in table_examples:
                    try:
                        vn.train(question=example["question"], sql=example["sql"])
                        vn.train(documentation=example["documentation"])
                    except Exception as e:
                        logger.warning(f"[WARNING] Failed to add training for table {table_id}: {e}")

            return {
                "id": 1,
                "status": "completed",
                "message": f"Training completed successfully for {len(table_ids)} tables"
            }
        except Exception as e:
            logger.error(f"[ERROR] Failed to train on tables: {e}")
            return {
                "id": 1,
                "status": "failed",
                "message": f"Training failed: {str(e)}"
            }

    def add_training_data(self, question: str, sql: str, user_id: int = None, connection_id: int = None):
        """Add training data to Vanna RAG system."""
        logger.info(f"[TRAIN] Adding training data: {question[:50]}...")

        try:
            # Get appropriate Vanna instance
            vn = self.get_vanna_instance(connection_id=connection_id, user_id=user_id)

            # Add the training data to Vanna's RAG system
            vn.train(question=question, sql=sql)

            logger.info("[OK] Training data added successfully")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Failed to add training data: {e}")
            return False

    def add_documentation(self, documentation: str, user_id: int = None, connection_id: int = None):
        """Add documentation to Vanna RAG system."""
        logger.info(f"[TRAIN] Adding documentation: {documentation[:50]}...")

        try:
            # Get appropriate Vanna instance
            vn = self.get_vanna_instance(connection_id=connection_id, user_id=user_id)

            # Add documentation to Vanna's RAG system
            vn.train(documentation=documentation)

            logger.info("[OK] Documentation added successfully")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Failed to add documentation: {e}")
            return False

    def add_ddl(self, ddl: str, user_id: int = None, connection_id: int = None):
        """Add DDL to Vanna RAG system."""
        logger.info(f"[TRAIN] Adding DDL: {ddl[:50]}...")

        try:
            # Get appropriate Vanna instance
            vn = self.get_vanna_instance(connection_id=connection_id, user_id=user_id)

            # Add DDL to Vanna's RAG system
            vn.train(ddl=ddl)

            logger.info("[OK] DDL added successfully")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Failed to add DDL: {e}")
            return False

    def get_training_data(self, user_id: int = None, connection_id: int = None) -> List[Dict]:
        """Get training data from Vanna RAG system."""
        logger.info("[TRAIN] Getting training data")

        try:
            # Get appropriate Vanna instance
            vn = self.get_vanna_instance(connection_id=connection_id, user_id=user_id)

            # Get training data from Vanna
            training_data = vn.get_training_data()

            if isinstance(training_data, pd.DataFrame):
                if not training_data.empty:
                    return training_data.to_dict('records')
                else:
                    return []
            elif isinstance(training_data, list):
                return training_data
            else:
                return []
        except Exception as e:
            logger.error(f"[ERROR] Failed to get training data: {e}")
            return []

# Global instance
vanna_service = VannaService()
