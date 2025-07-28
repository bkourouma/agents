"""
Database Chat Models for the AI Agent Platform.
Defines SQLAlchemy models for database schema management, data operations, and query history.
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, JSON, ForeignKey, Enum, Float, Index

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, Dict, Any, List
import uuid

from src.core.database import Base


class DataType(PyEnum):
    """Supported data types for database columns."""
    INTEGER = "INTEGER"
    VARCHAR = "VARCHAR"
    TEXT = "TEXT"
    BOOLEAN = "BOOLEAN"
    DATETIME = "DATETIME"
    DATE = "DATE"
    TIME = "TIME"
    DECIMAL = "DECIMAL"
    FLOAT = "FLOAT"
    JSON = "JSON"


class DatabaseTable(Base):
    """Model for user-created database tables with multi-tenant support."""
    __tablename__ = "database_tables"

    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant support
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)

    # Table information
    name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=False, index=True)
    description = Column(Text)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Metadata for table configuration
    metadata_config = Column(JSON, default={})

    # Table constraints and indexes for multi-tenant optimization
    __table_args__ = (
        Index('idx_db_tables_tenant_user', 'tenant_id', 'user_id'),
        Index('idx_db_tables_tenant_name', 'tenant_id', 'name'),
        Index('idx_db_tables_tenant_active', 'tenant_id', 'is_active'),
        Index('idx_db_tables_created_at', 'created_at'),
    )

    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User")
    columns = relationship("DatabaseColumn", back_populates="table", cascade="all, delete-orphan")
    query_history = relationship("QueryHistory", back_populates="table")
    training_sessions = relationship("VannaTrainingSession", back_populates="table")
    training_data = relationship("VannaTrainingData", back_populates="table")

    def __repr__(self):
        return f"<DatabaseTable(name='{self.name}', display_name='{self.display_name}', tenant_id='{self.tenant_id}')>"


class DatabaseColumn(Base):
    """Model for columns in user-created database tables with multi-tenant support."""
    __tablename__ = "database_columns"

    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant support (inherited from table)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)

    # Column information
    table_id = Column(Integer, ForeignKey("database_tables.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    data_type = Column(Enum(DataType), nullable=False, index=True)
    max_length = Column(Integer)  # For VARCHAR types
    precision = Column(Integer)   # For DECIMAL types
    scale = Column(Integer)       # For DECIMAL types
    is_nullable = Column(Boolean, default=True, nullable=False)
    is_primary_key = Column(Boolean, default=False, nullable=False)
    is_unique = Column(Boolean, default=False, nullable=False)
    default_value = Column(String(255))
    description = Column(Text)
    order_index = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Table constraints and indexes for multi-tenant optimization
    __table_args__ = (
        Index('idx_db_columns_tenant_table', 'tenant_id', 'table_id'),
        Index('idx_db_columns_tenant_name', 'tenant_id', 'name'),
        Index('idx_db_columns_tenant_type', 'tenant_id', 'data_type'),
        Index('idx_db_columns_created_at', 'created_at'),
    )

    # Relationships
    tenant = relationship("Tenant")
    table = relationship("DatabaseTable", back_populates="columns")

    def __repr__(self):
        return f"<DatabaseColumn(name='{self.name}', type='{self.data_type.value}', tenant_id='{self.tenant_id}')>"


class QueryHistory(Base):
    """Model for storing natural language query history with multi-tenant support."""
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant support
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)

    # Query information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    table_id = Column(Integer, ForeignKey("database_tables.id"), nullable=True, index=True)
    natural_language_query = Column(Text, nullable=False)
    generated_sql = Column(Text)
    execution_status = Column(String(50), default="pending", nullable=False, index=True)  # pending, success, error
    error_message = Column(Text)
    result_count = Column(Integer)
    execution_time_ms = Column(Integer)
    is_favorite = Column(Boolean, default=False, nullable=False, index=True)

    # Store query results (limited size)
    result_preview = Column(JSON)  # First few rows for preview

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Table constraints and indexes for multi-tenant optimization
    __table_args__ = (
        Index('idx_query_history_tenant_user', 'tenant_id', 'user_id'),
        Index('idx_query_history_tenant_table', 'tenant_id', 'table_id'),
        Index('idx_query_history_tenant_status', 'tenant_id', 'execution_status'),
        Index('idx_query_history_tenant_favorite', 'tenant_id', 'is_favorite'),
        Index('idx_query_history_created_at', 'created_at'),
    )

    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User")
    table = relationship("DatabaseTable", back_populates="query_history")

    def __repr__(self):
        return f"<QueryHistory(id={self.id}, status='{self.execution_status}', tenant_id='{self.tenant_id}')>"


class VannaTrainingSession(Base):
    """Model for tracking Vanna AI training sessions with multi-tenant support."""
    __tablename__ = "vanna_training_sessions"

    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant support
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)

    # Training session information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    table_id = Column(Integer, ForeignKey("database_tables.id"), nullable=False, index=True)
    model_name = Column(String(255), nullable=False, index=True)
    training_status = Column(String(50), default="pending", nullable=False, index=True)  # pending, training, completed, failed
    training_started_at = Column(DateTime(timezone=True), nullable=True)
    training_completed_at = Column(DateTime(timezone=True), nullable=True)
    error_message = Column(Text)

    # Training configuration
    training_config = Column(JSON, default={}, nullable=False)

    # Training metrics
    training_metrics = Column(JSON, default={}, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Table constraints and indexes for multi-tenant optimization
    __table_args__ = (
        Index('idx_vanna_sessions_tenant_user', 'tenant_id', 'user_id'),
        Index('idx_vanna_sessions_tenant_table', 'tenant_id', 'table_id'),
        Index('idx_vanna_sessions_tenant_model', 'tenant_id', 'model_name'),
        Index('idx_vanna_sessions_tenant_status', 'tenant_id', 'training_status'),
        Index('idx_vanna_sessions_created_at', 'created_at'),
    )

    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User")
    table = relationship("DatabaseTable", back_populates="training_sessions")

    def __repr__(self):
        return f"<VannaTrainingSession(model='{self.model_name}', status='{self.training_status}', tenant_id='{self.tenant_id}')>"


class DataImportSession(Base):
    """Model for tracking data import sessions (Excel, CSV, etc.)."""
    __tablename__ = "data_import_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    table_id = Column(Integer, ForeignKey("database_tables.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    file_size = Column(Integer)
    import_status = Column(String(50), default="pending")  # pending, processing, completed, failed
    rows_processed = Column(Integer, default=0)
    rows_imported = Column(Integer, default=0)
    rows_failed = Column(Integer, default=0)
    error_message = Column(Text)
    
    # Import configuration
    import_config = Column(JSON, default={})
    
    # Validation results
    validation_results = Column(JSON, default={})
    
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self):
        return f"<DataImportSession(filename='{self.filename}', status='{self.import_status}')>"


class VannaTrainingData(Base):
    """Model for storing Vanna AI training question/SQL pairs with multi-tenant support."""
    __tablename__ = "vanna_training_data"

    id = Column(Integer, primary_key=True, index=True)

    # Multi-tenant support
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)

    # Training data information
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    table_id = Column(Integer, ForeignKey("database_tables.id"), nullable=False, index=True)
    model_name = Column(String(255), nullable=False, index=True)
    question = Column(Text, nullable=False)
    sql = Column(Text, nullable=False)
    is_generated = Column(Boolean, default=False, nullable=False, index=True)  # True if generated by LLM, False if manually added
    is_active = Column(Boolean, default=True, nullable=False, index=True)  # Can be disabled without deletion
    confidence_score = Column(Float, default=1.0, nullable=False)  # Quality score for the training pair

    # Metadata
    generation_model = Column(String(100))  # Which LLM model generated this (if generated)
    validation_status = Column(String(50), default="pending", nullable=False, index=True)  # pending, validated, rejected

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    # Table constraints and indexes for multi-tenant optimization
    __table_args__ = (
        Index('idx_vanna_data_tenant_user', 'tenant_id', 'user_id'),
        Index('idx_vanna_data_tenant_table', 'tenant_id', 'table_id'),
        Index('idx_vanna_data_tenant_model', 'tenant_id', 'model_name'),
        Index('idx_vanna_data_tenant_active', 'tenant_id', 'is_active'),
        Index('idx_vanna_data_tenant_generated', 'tenant_id', 'is_generated'),
        Index('idx_vanna_data_tenant_status', 'tenant_id', 'validation_status'),
        Index('idx_vanna_data_created_at', 'created_at'),
    )

    # Relationships
    tenant = relationship("Tenant")
    user = relationship("User")
    table = relationship("DatabaseTable", back_populates="training_data")

    def __repr__(self):
        return f"<VannaTrainingData(question='{self.question[:50]}...', model='{self.model_name}', tenant_id='{self.tenant_id}')>"


class DatabaseConnection(Base):
    """Model for storing database connection configurations."""
    __tablename__ = "database_connections"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    database_type = Column(String(50), nullable=False)  # sqlite, postgresql, mysql, sqlserver, oracle
    connection_string = Column(Text)  # Encrypted connection string
    is_active = Column(Boolean, default=True)
    is_default = Column(Boolean, default=False)

    # Connection metadata and configuration
    connection_config = Column(JSON, default={})

    # Connection status tracking
    last_tested = Column(DateTime(timezone=True))
    test_status = Column(String(50))  # 'Success', 'Failed', 'NotTested'
    test_message = Column(Text)
    response_time_ms = Column(Integer)

    # Additional metadata
    created_by = Column(String(255))
    description = Column(Text)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    def __repr__(self):
        return f"<DatabaseConnection(name='{self.name}', type='{self.database_type}', status='{self.test_status}')>"
