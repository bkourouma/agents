"""
Tenant-aware Vanna AI service for multi-tenant SQL generation.
Ensures complete isolation of training data and models between tenants.
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)

# Check for Vanna availability
try:
    import vanna
    from vanna.openai.openai_chat import OpenAI_Chat
    from vanna.chromadb.chromadb_vector import ChromaDB_VectorStore
    VANNA_AVAILABLE = True
except ImportError:
    VANNA_AVAILABLE = False
    logger.warning("Vanna AI not available - SQL generation will be disabled")


class TenantVannaService:
    """
    Tenant-aware Vanna AI service that provides complete isolation
    of SQL generation models and training data between tenants.
    """
    
    def __init__(self, base_cache_dir: str = "./data/vanna"):
        self.base_cache_dir = Path(base_cache_dir)
        self.base_cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache for tenant-specific Vanna instances
        self.tenant_instances: Dict[str, Any] = {}
        
        # Vanna configuration
        self.default_model = os.getenv('VANNA_MODEL', 'gpt-3.5-turbo')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY not set - Vanna AI will not work")
        
        # Initialize Vanna class if available
        if VANNA_AVAILABLE:
            self._initialize_vanna_class()
    
    def _initialize_vanna_class(self):
        """Initialize the tenant-aware Vanna class."""
        try:
            class TenantVanna(ChromaDB_VectorStore, OpenAI_Chat):
                def __init__(self, config=None):
                    ChromaDB_VectorStore.__init__(self, config=config)
                    OpenAI_Chat.__init__(self, config=config)
            
            self.VannaClass = TenantVanna
            logger.info("Tenant-aware Vanna class initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Vanna class: {e}")
            self.VannaClass = None
    
    def get_tenant_cache_path(self, tenant_id: str, model_name: str = None) -> Path:
        """Get the cache path for a tenant's Vanna instance."""
        model_name = model_name or self.default_model
        # Sanitize model name for filesystem
        safe_model_name = model_name.replace('/', '_').replace(':', '_')
        cache_path = self.base_cache_dir / f"tenant_{tenant_id}" / f"model_{safe_model_name}"
        cache_path.mkdir(parents=True, exist_ok=True)
        return cache_path
    
    def get_tenant_vanna_instance(
        self, 
        tenant_id: str, 
        model_name: str = None,
        force_recreate: bool = False
    ) -> Optional[Any]:
        """
        Get or create a Vanna instance for a specific tenant.
        
        Args:
            tenant_id: The tenant ID
            model_name: The LLM model to use (defaults to configured model)
            force_recreate: Whether to force recreation of the instance
            
        Returns:
            Vanna instance or None if not available
        """
        if not VANNA_AVAILABLE or not self.VannaClass:
            logger.error("Vanna AI not available")
            return None
        
        if not self.openai_api_key:
            logger.error("OpenAI API key not configured")
            return None
        
        model_name = model_name or self.default_model
        instance_key = f"{tenant_id}_{model_name}"
        
        # Return cached instance if available and not forcing recreation
        if instance_key in self.tenant_instances and not force_recreate:
            return self.tenant_instances[instance_key]
        
        try:
            # Get tenant-specific cache path
            cache_path = self.get_tenant_cache_path(tenant_id, model_name)
            
            # Configure Vanna with tenant-specific settings
            config = {
                'api_key': self.openai_api_key,
                'model': model_name,
                'path': str(cache_path),
            }
            
            logger.info(f"Creating Vanna instance for tenant {tenant_id} with model {model_name}")
            logger.info(f"Cache path: {cache_path}")
            
            # Create tenant-specific Vanna instance
            vn = self.VannaClass(config=config)
            
            # Enable LLM to see data for better introspection
            vn.allow_llm_to_see_data = True
            
            # Cache the instance
            self.tenant_instances[instance_key] = vn
            
            logger.info(f"Vanna instance created for tenant {tenant_id}")
            return vn
            
        except Exception as e:
            logger.error(f"Failed to create Vanna instance for tenant {tenant_id}: {e}")
            return None
    
    def train_tenant_model(
        self,
        tenant_id: str,
        training_data: List[Dict[str, str]],
        model_name: str = None
    ) -> bool:
        """
        Train a tenant's Vanna model with question/SQL pairs.
        
        Args:
            tenant_id: The tenant ID
            training_data: List of {"question": str, "sql": str} pairs
            model_name: The LLM model to use
            
        Returns:
            True if training was successful, False otherwise
        """
        try:
            vn = self.get_tenant_vanna_instance(tenant_id, model_name)
            if not vn:
                return False
            
            logger.info(f"Training Vanna model for tenant {tenant_id} with {len(training_data)} examples")
            
            # Train with question/SQL pairs
            for item in training_data:
                if 'question' in item and 'sql' in item:
                    vn.train(question=item['question'], sql=item['sql'])
            
            logger.info(f"Training completed for tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to train model for tenant {tenant_id}: {e}")
            return False
    
    def generate_sql(
        self,
        tenant_id: str,
        question: str,
        model_name: str = None
    ) -> Dict[str, Any]:
        """
        Generate SQL for a natural language question using tenant's model.
        
        Args:
            tenant_id: The tenant ID
            question: Natural language question
            model_name: The LLM model to use
            
        Returns:
            Dictionary with SQL and metadata
        """
        try:
            vn = self.get_tenant_vanna_instance(tenant_id, model_name)
            if not vn:
                return {
                    "success": False,
                    "error": "Vanna instance not available",
                    "sql": None
                }
            
            logger.info(f"Generating SQL for tenant {tenant_id}: {question}")
            
            # Generate SQL using tenant's trained model
            sql = vn.generate_sql(question)
            
            return {
                "success": True,
                "sql": sql,
                "question": question,
                "tenant_id": tenant_id,
                "model_name": model_name or self.default_model,
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to generate SQL for tenant {tenant_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "sql": None,
                "question": question,
                "tenant_id": tenant_id
            }
    
    def execute_sql(
        self,
        tenant_id: str,
        sql: str,
        connection_string: str = None
    ) -> Dict[str, Any]:
        """
        Execute SQL using tenant's database connection.
        
        Args:
            tenant_id: The tenant ID
            sql: SQL query to execute
            connection_string: Database connection string (tenant-specific)
            
        Returns:
            Dictionary with results and metadata
        """
        try:
            vn = self.get_tenant_vanna_instance(tenant_id)
            if not vn:
                return {
                    "success": False,
                    "error": "Vanna instance not available",
                    "results": None
                }
            
            logger.info(f"Executing SQL for tenant {tenant_id}: {sql[:100]}...")
            
            # Connect to tenant's database if connection string provided
            if connection_string:
                vn.connect_to_postgres(connection_string)
            
            # Execute SQL
            results = vn.run_sql(sql)
            
            # Convert results to serializable format
            if isinstance(results, pd.DataFrame):
                results_dict = {
                    "columns": results.columns.tolist(),
                    "data": results.to_dict('records'),
                    "row_count": len(results)
                }
            else:
                results_dict = {"data": results, "row_count": 0}
            
            return {
                "success": True,
                "results": results_dict,
                "sql": sql,
                "tenant_id": tenant_id,
                "executed_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to execute SQL for tenant {tenant_id}: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": None,
                "sql": sql,
                "tenant_id": tenant_id
            }
    
    def get_tenant_training_data(
        self,
        tenant_id: str,
        model_name: str = None
    ) -> List[Dict[str, Any]]:
        """
        Get training data for a tenant's model.
        
        Args:
            tenant_id: The tenant ID
            model_name: The LLM model name
            
        Returns:
            List of training data items
        """
        try:
            vn = self.get_tenant_vanna_instance(tenant_id, model_name)
            if not vn:
                return []
            
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
            logger.error(f"Failed to get training data for tenant {tenant_id}: {e}")
            return []
    
    def remove_tenant_training_data(
        self,
        tenant_id: str,
        training_data_id: str = None,
        model_name: str = None
    ) -> bool:
        """
        Remove training data from a tenant's model.
        
        Args:
            tenant_id: The tenant ID
            training_data_id: Specific training data ID to remove (optional)
            model_name: The LLM model name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            vn = self.get_tenant_vanna_instance(tenant_id, model_name)
            if not vn:
                return False
            
            if training_data_id:
                # Remove specific training data
                vn.remove_training_data(training_data_id)
                logger.info(f"Removed training data {training_data_id} for tenant {tenant_id}")
            else:
                # Remove all training data (reset model)
                training_data = vn.get_training_data()
                if isinstance(training_data, pd.DataFrame) and not training_data.empty:
                    for _, row in training_data.iterrows():
                        if 'id' in row:
                            vn.remove_training_data(row['id'])
                logger.info(f"Removed all training data for tenant {tenant_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove training data for tenant {tenant_id}: {e}")
            return False
    
    def get_tenant_model_stats(
        self,
        tenant_id: str,
        model_name: str = None
    ) -> Dict[str, Any]:
        """
        Get statistics for a tenant's model.
        
        Args:
            tenant_id: The tenant ID
            model_name: The LLM model name
            
        Returns:
            Dictionary with model statistics
        """
        try:
            cache_path = self.get_tenant_cache_path(tenant_id, model_name)
            training_data = self.get_tenant_training_data(tenant_id, model_name)
            
            return {
                "tenant_id": tenant_id,
                "model_name": model_name or self.default_model,
                "cache_path": str(cache_path),
                "training_data_count": len(training_data),
                "cache_exists": cache_path.exists(),
                "last_modified": datetime.fromtimestamp(
                    cache_path.stat().st_mtime
                ).isoformat() if cache_path.exists() else None
            }
            
        except Exception as e:
            logger.error(f"Failed to get model stats for tenant {tenant_id}: {e}")
            return {
                "tenant_id": tenant_id,
                "error": str(e)
            }
    
    def cleanup_tenant_data(self, tenant_id: str) -> bool:
        """
        Clean up all data for a tenant.
        
        Args:
            tenant_id: The tenant ID to clean up
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        try:
            import shutil
            
            # Remove cached instances
            keys_to_remove = [k for k in self.tenant_instances.keys() if k.startswith(f"{tenant_id}_")]
            for key in keys_to_remove:
                del self.tenant_instances[key]
            
            # Remove cache directory
            tenant_cache_path = self.base_cache_dir / f"tenant_{tenant_id}"
            if tenant_cache_path.exists():
                shutil.rmtree(tenant_cache_path)
                logger.info(f"Cleaned up Vanna cache for tenant {tenant_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to cleanup data for tenant {tenant_id}: {e}")
            return False


# Global instance
_tenant_vanna_service = None

def get_tenant_vanna_service() -> TenantVannaService:
    """Get the global tenant Vanna service instance."""
    global _tenant_vanna_service
    if _tenant_vanna_service is None:
        base_cache_dir = os.getenv("VANNA_CACHE_DIR", "./data/vanna")
        _tenant_vanna_service = TenantVannaService(base_cache_dir)
    return _tenant_vanna_service
