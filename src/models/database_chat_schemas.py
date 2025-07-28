"""
Pydantic schemas for Database Chat API requests and responses.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

from .database_chat import DataType


class DatabaseProvider(str, Enum):
    """Supported database providers."""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    SQLSERVER = "sqlserver"
    ORACLE = "oracle"
    SQLITE = "sqlite"


class ConnectionStatus(str, Enum):
    """Connection test status."""
    SUCCESS = "Success"
    FAILED = "Failed"
    NOT_TESTED = "NotTested"


class ConnectionTestResult(BaseModel):
    """Result of testing a database connection."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[int] = None
    error_details: Optional[str] = None


class DatabaseProviderInfo(BaseModel):
    """Information about a database provider."""
    name: str
    value: str
    description: str
    default_port: Optional[int] = None
    template: str
    examples: List[str]


class ConnectionStringTemplate(BaseModel):
    """Connection string template for a provider."""
    provider: DatabaseProvider
    template: str
    examples: List[str]
    parameters: List[Dict[str, Any]]


class DatabaseConnectionCreate(BaseModel):
    """Schema for creating a new database connection."""
    name: str = Field(..., min_length=1, max_length=255, description="Connection name")
    database_type: DatabaseProvider = Field(..., description="Database provider type")
    connection_string: Optional[str] = Field(None, description="Manual connection string")

    # Connection parameters (alternative to connection_string)
    host: Optional[str] = Field(None, description="Database host")
    port: Optional[int] = Field(None, description="Database port")
    database: Optional[str] = Field(None, description="Database name")
    username: Optional[str] = Field(None, description="Username")
    password: Optional[str] = Field(None, description="Password")

    # Additional connection options
    ssl_mode: Optional[str] = Field(None, description="SSL mode")
    connection_timeout: Optional[int] = Field(30, description="Connection timeout in seconds")
    additional_params: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional connection parameters")

    # Metadata
    description: Optional[str] = Field(None, description="Connection description")
    is_default: bool = Field(False, description="Set as default connection")
    test_on_create: bool = Field(True, description="Test connection after creation")

    @validator('port')
    def validate_port(cls, v):
        if v is not None and (v < 1 or v > 65535):
            raise ValueError('Port must be between 1 and 65535')
        return v


class DatabaseConnectionUpdate(BaseModel):
    """Schema for updating a database connection."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    ssl_mode: Optional[str] = None
    connection_timeout: Optional[int] = None
    additional_params: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class DatabaseConnectionResponse(BaseModel):
    """Schema for database connection response."""
    id: int
    name: str
    database_type: str
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    ssl_mode: Optional[str] = None
    connection_timeout: Optional[int] = None
    description: Optional[str] = None
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    # Connection status tracking
    last_tested: Optional[datetime] = None
    test_status: Optional[ConnectionStatus] = None
    test_message: Optional[str] = None
    response_time_ms: Optional[int] = None
    created_by: Optional[str] = None

    class Config:
        from_attributes = True


class ExternalTableInfo(BaseModel):
    """Information about a table from an external database."""
    name: str
    schema: Optional[str] = None
    table_type: str = "table"  # table, view, etc.
    row_count: Optional[int] = None
    columns: List[Dict[str, Any]] = Field(default_factory=list)
    description: Optional[str] = None


class ExternalSchemaInfo(BaseModel):
    """Schema information from an external database."""
    connection_id: int
    schemas: List[str] = Field(default_factory=list)
    tables: List[ExternalTableInfo] = Field(default_factory=list)
    total_tables: int = 0
    total_columns: int = 0


class TableImportRequest(BaseModel):
    """Request to import tables from external database."""
    connection_id: int
    selected_tables: List[str] = Field(..., description="List of table names to import")
    schema_name: Optional[str] = Field(None, description="Schema name for tables")
    import_data: bool = Field(False, description="Whether to import actual data")
    sample_size: Optional[int] = Field(1000, description="Number of sample rows to import")


class ConnectionWizardStep(BaseModel):
    """Wizard step information."""
    step: int
    title: str
    description: str
    completed: bool = False
    data: Optional[Dict[str, Any]] = None


class DatabaseTableCreate(BaseModel):
    """Schema for creating a new database table."""
    name: str = Field(..., min_length=1, max_length=255, description="Table name (database identifier)")
    display_name: str = Field(..., min_length=1, max_length=255, description="Human-readable table name")
    description: Optional[str] = Field(None, description="Table description")
    metadata_config: Optional[Dict[str, Any]] = Field(default_factory=dict)

    @validator('name')
    def validate_table_name(cls, v):
        """Validate table name follows database naming conventions."""
        if not v.replace('_', '').isalnum():
            raise ValueError('Table name must contain only alphanumeric characters and underscores')
        if v[0].isdigit():
            raise ValueError('Table name cannot start with a number')
        return v.lower()


class DatabaseColumnCreate(BaseModel):
    """Schema for creating a new database column."""
    name: str = Field(..., min_length=1, max_length=255)
    display_name: str = Field(..., min_length=1, max_length=255)
    data_type: DataType
    max_length: Optional[int] = Field(None, ge=1, le=65535)
    precision: Optional[int] = Field(None, ge=1, le=65)
    scale: Optional[int] = Field(None, ge=0, le=30)
    is_nullable: bool = Field(default=True)
    is_primary_key: bool = Field(default=False)
    is_unique: bool = Field(default=False)
    default_value: Optional[str] = None
    description: Optional[str] = None
    order_index: int = Field(default=0, ge=0)

    @validator('name')
    def validate_column_name(cls, v):
        """Validate column name follows database naming conventions."""
        if not v.replace('_', '').isalnum():
            raise ValueError('Column name must contain only alphanumeric characters and underscores')
        if v[0].isdigit():
            raise ValueError('Column name cannot start with a number')
        return v.lower()


class DatabaseTableUpdate(BaseModel):
    """Schema for updating a database table."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    metadata_config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class DatabaseColumnUpdate(BaseModel):
    """Schema for updating a database column."""
    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    max_length: Optional[int] = Field(None, ge=1, le=65535)
    precision: Optional[int] = Field(None, ge=1, le=65)
    scale: Optional[int] = Field(None, ge=0, le=30)
    is_nullable: Optional[bool] = None
    is_unique: Optional[bool] = None
    default_value: Optional[str] = None
    description: Optional[str] = None
    order_index: Optional[int] = Field(None, ge=0)


class DatabaseTableResponse(BaseModel):
    """Schema for database table response."""
    id: int
    name: str
    display_name: str
    description: Optional[str]
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    is_active: bool
    metadata_config: Dict[str, Any]
    columns: List['DatabaseColumnResponse'] = []

    class Config:
        from_attributes = True


class DatabaseColumnResponse(BaseModel):
    """Schema for database column response."""
    id: int
    table_id: int
    name: str
    display_name: str
    data_type: DataType
    max_length: Optional[int]
    precision: Optional[int]
    scale: Optional[int]
    is_nullable: bool
    is_primary_key: bool
    is_unique: bool
    default_value: Optional[str]
    description: Optional[str]
    order_index: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class NaturalLanguageQuery(BaseModel):
    """Schema for natural language query request."""
    query: str = Field(..., min_length=1, max_length=1000, description="Natural language query")
    table_ids: Optional[List[int]] = Field(None, description="Specific tables to query (optional)")
    output_format: str = Field(default="json", description="Output format: json, text, or table")
    max_results: int = Field(default=100, ge=1, le=1000, description="Maximum number of results")


class QueryExecutionRequest(BaseModel):
    """Schema for direct SQL query execution."""
    sql: str = Field(..., min_length=1, description="SQL query to execute")
    table_id: Optional[int] = Field(None, description="Associated table ID")


class QueryHistoryResponse(BaseModel):
    """Schema for query history response."""
    id: int
    user_id: int
    table_id: Optional[int]
    natural_language_query: str
    generated_sql: Optional[str]
    execution_status: str
    error_message: Optional[str]
    result_count: Optional[int]
    execution_time_ms: Optional[int]
    created_at: datetime
    is_favorite: bool
    result_preview: Optional[Dict[str, Any]]

    class Config:
        from_attributes = True


class VannaTrainingRequest(BaseModel):
    """Schema for Vanna AI training request."""
    table_ids: List[int] = Field(..., min_items=1, description="Tables to include in training")
    model_name: str = Field(..., min_length=1, max_length=255, description="Model name")
    training_config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class VannaTrainingResponse(BaseModel):
    """Schema for Vanna training session response."""
    id: int
    user_id: int
    table_id: int
    model_name: str
    training_status: str
    training_started_at: Optional[datetime]
    training_completed_at: Optional[datetime]
    error_message: Optional[str]
    training_config: Dict[str, Any]
    training_metrics: Dict[str, Any]
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class DataImportRequest(BaseModel):
    """Schema for data import request."""
    table_id: int
    import_config: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DataImportResponse(BaseModel):
    """Schema for data import session response."""
    id: int
    user_id: int
    table_id: int
    filename: str
    file_size: Optional[int]
    import_status: str
    rows_processed: int
    rows_imported: int
    rows_failed: int
    error_message: Optional[str]
    import_config: Dict[str, Any]
    validation_results: Dict[str, Any]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime

    class Config:
        from_attributes = True


class QueryResultResponse(BaseModel):
    """Schema for query result response."""
    success: bool
    data: Optional[List[Dict[str, Any]]] = None
    columns: Optional[List[str]] = None
    row_count: int = 0
    execution_time_ms: int = 0
    sql: Optional[str] = None
    error: Optional[str] = None
    format: str = "json"


class DatabaseSchemaResponse(BaseModel):
    """Schema for complete database schema response."""
    tables: List[DatabaseTableResponse]
    total_tables: int
    total_columns: int


class VannaTrainingDataCreate(BaseModel):
    """Schema for creating Vanna training data."""
    table_id: int
    model_name: str
    question: str
    sql: str
    is_generated: bool = False
    confidence_score: float = 1.0
    generation_model: Optional[str] = None


class VannaTrainingDataUpdate(BaseModel):
    """Schema for updating Vanna training data."""
    question: Optional[str] = None
    sql: Optional[str] = None
    is_active: Optional[bool] = None
    confidence_score: Optional[float] = None
    validation_status: Optional[str] = None


class VannaTrainingDataResponse(BaseModel):
    """Schema for Vanna training data response."""
    id: int
    user_id: int
    table_id: int
    model_name: str
    question: str
    sql: str
    is_generated: bool
    is_active: bool
    confidence_score: float
    generation_model: Optional[str]
    validation_status: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class GenerateTrainingDataRequest(BaseModel):
    """Schema for generating training data request."""
    table_ids: List[int]
    model_name: str
    llm_model: str = "gpt-3.5-turbo"
    num_questions: int = Field(default=10, ge=1, le=100)
    avoid_duplicates: bool = True
    prompt: Optional[str] = Field(default=None, description="Optional prompt to guide question generation (e.g., 'generate questions about aggregate functions')")


class GenerateTrainingDataResponse(BaseModel):
    """Schema for generated training data response."""
    generated_count: int
    training_data: List[VannaTrainingDataResponse]
    duplicates_avoided: int = 0


# Update forward references
DatabaseTableResponse.model_rebuild()
