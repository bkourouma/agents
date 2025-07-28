# Database Connection Setup Guide

## 📋 Overview

This document provides a comprehensive guide to reproduce the database connection setup from the Chat360 project in another project. The system uses SQLite as the primary database with a well-structured connection management system.

## 🏗️ Architecture Overview

```
Application Layer
    ↓
Database Connection Layer (db.py)
    ↓
SQLite Database (chatbot.sqlite)
```

## 📁 Files Involved

### Core Database Files

1. **`db.py`** - Main database connection and operations
2. **`init_database.py`** - Database initialization script
3. **`setup/database_initializer.py`** - Advanced database setup
4. **`app.py`** - Application startup and database initialization
5. **`.env`** - Environment configuration

### Repository Pattern Files

6. **`chat_assistant/repositories/document_repository.py`** - Document operations
7. **`chat_assistant/repositories/chat_repository.py`** - Chat operations
8. **`db_connection_service.py`** - External database connections

### Service Layer Files

9. **`chat_assistant/services/document_service.py`** - Document business logic
10. **`chat_assistant/services/chat_service.py`** - Chat business logic
11. **`chat_assistant/services/embedding_service.py`** - Embedding operations
12. **`visitor_chat/services/document_service.py`** - Visitor document services
13. **`visitor_chat/services/chat_service.py`** - Visitor chat services

### Component Files

14. **`chat_assistant/utils/tenant_context.py`** - Tenant context management
15. **`chat_assistant/utils/ai_client.py`** - AI client abstraction
16. **`chat_assistant/models/document.py`** - Data models
17. **`chat_assistant/models/chat.py`** - Chat models

### Configuration Files

9. **`production-config.py`** - Production configuration
10. **`voice_assistant/models/base.py`** - SQLAlchemy setup (alternative)

## � Connection Strings and Providers

### Supported Database Providers

The system supports 4 main database providers:

1. **SQLite** - File-based database (default)
2. **PostgreSQL** - Enterprise PostgreSQL
3. **MySQL** - MySQL/MariaDB
4. **SQL Server** - Microsoft SQL Server

### Provider Configuration

```python
# models_db.py
class DatabaseConnectionCreate(BaseModel):
    database_name: str
    provider: str  # 'SQLServer', 'PostgreSQL', 'SQLite', 'MySQL'
    connection_string: str

# Database table schema
CREATE TABLE IF NOT EXISTS tblConnexions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_id INTEGER NOT NULL,
    database_name TEXT NOT NULL,
    provider TEXT NOT NULL, -- 'SQLServer', 'PostgreSQL', 'SQLite', 'MySQL'
    connection_string TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_date TEXT DEFAULT CURRENT_TIMESTAMP,
    last_tested TEXT,
    test_status TEXT, -- 'Success', 'Failed', 'NotTested'
    created_by TEXT NOT NULL,
    FOREIGN KEY(tenant_id) REFERENCES tenants(id)
);
```

### Connection String Formats

#### 1. SQLite Connection Strings

```bash
# File path format
Data Source=C:\path\to\database.sqlite;

# Relative path
Data Source=./data/database.sqlite;

# Memory database
Data Source=:memory:;

# Environment variable format
SQLITE_PATH=sqlite_data/chatbot.sqlite
DATABASE_URL=sqlite:///home/data/chat360.db
```

#### 2. PostgreSQL Connection Strings

```bash
# Standard PostgreSQL URL format
postgresql://username:password@host:port/database

# Semicolon-separated format
Host=localhost;Port=5432;Database=mydb;Username=user;Password=password;

# With SSL
Host=localhost;Port=5432;Database=mydb;Username=user;Password=password;sslmode=require;

# Connection string parsing example
def _parse_postgresql_connection(connection_string: str):
    if connection_string.startswith('postgresql://'):
        # Already in correct format
        conn = psycopg2.connect(connection_string)
    elif '=' in connection_string and ';' in connection_string:
        # Parse semicolon-separated format
        params = {}
        for param in connection_string.split(';'):
            if '=' in param:
                key, value = param.split('=', 1)
                key = key.strip().lower()
                value = value.strip()

                # Map common parameter names to PostgreSQL format
                if key in ['host', 'server']:
                    params['host'] = value
                elif key == 'port':
                    params['port'] = int(value)
                elif key in ['database', 'db']:
                    params['dbname'] = value
                elif key in ['username', 'user', 'uid']:
                    params['user'] = value
                elif key in ['password', 'pwd']:
                    params['password'] = value
                elif key == 'sslmode':
                    params['sslmode'] = value

        conn = psycopg2.connect(**params)
```

#### 3. MySQL Connection Strings

```bash
# Standard MySQL format
Server=localhost;Database=mydb;Uid=user;Pwd=password;

# With port
Server=localhost;Port=3306;Database=mydb;Uid=user;Pwd=password;

# With SSL
Server=localhost;Database=mydb;Uid=user;Pwd=password;SslMode=Required;

# Connection implementation
def _setup_mysql_connection(self, vn, params: Dict[str, str]):
    """Setup MySQL connection for Vanna."""
    import pandas as pd
    import pymysql

    def run_sql(sql: str) -> pd.DataFrame:
        conn = pymysql.connect(
            host=params.get('host', 'localhost'),
            user=params.get('user', 'root'),
            password=params.get('password', ''),
            database=params.get('dbname', ''),
            port=int(params.get('port', 3306))
        )
        result = pd.read_sql(sql, conn)
        conn.close()
        return result

    vn.run_sql = run_sql
```

#### 4. SQL Server Connection Strings

```bash
# Standard SQL Server format
Server=localhost;Database=mydb;User Id=sa;Password=password;

# With instance
Server=localhost\SQLEXPRESS;Database=mydb;User Id=sa;Password=password;

# With Windows Authentication
Server=localhost;Database=mydb;Integrated Security=true;

# With driver specification
Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=mydb;Uid=sa;Pwd=password;

# Auto-driver detection implementation
def _test_sqlserver(connection_string: str) -> ConnectionTestResult:
    try:
        # Available SQL Server drivers (in order of preference)
        drivers = [
            "ODBC Driver 17 for SQL Server",
            "ODBC Driver 13 for SQL Server",
            "SQL Server Native Client 11.0",
            "SQL Server"
        ]

        conn = None

        # Check if connection string already has a driver specified
        if "Driver=" not in connection_string and "DRIVER=" not in connection_string:
            # Try each driver until one works
            for driver in drivers:
                try:
                    test_conn_string = f"Driver={{{driver}}};{connection_string}"
                    conn = pyodbc.connect(test_conn_string)
                    logger.info(f"Connected to SQL Server using driver: {driver}")
                    break
                except Exception as e:
                    logger.debug(f"Failed to connect with driver {driver}: {e}")
                    continue

            if conn is None:
                # Try without driver as last resort
                conn = pyodbc.connect(connection_string)
        else:
            # Driver already specified, use as-is
            conn = pyodbc.connect(connection_string)
```

### Provider Detection and Testing

```python
# db_connection_service.py
class DatabaseConnectionService:

    @staticmethod
    def test_connection(provider: str, connection_string: str) -> ConnectionTestResult:
        """Test a database connection."""
        try:
            if provider.lower() == 'sqlite':
                return DatabaseConnectionService._test_sqlite(connection_string)
            elif provider.lower() == 'postgresql':
                return DatabaseConnectionService._test_postgresql(connection_string)
            elif provider.lower() == 'mysql':
                return DatabaseConnectionService._test_mysql(connection_string)
            elif provider.lower() == 'sqlserver':
                return DatabaseConnectionService._test_sqlserver(connection_string)
            else:
                return ConnectionTestResult(
                    success=False,
                    message="Unsupported database provider",
                    error_details=f"Provider '{provider}' is not supported"
                )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message="Connection test failed",
                error_details=str(e)
            )
```

### Frontend Connection String Examples

```javascript
// dashboardapp/src/pages/database/ConnectionList.js
const getConnectionStringExample = () => {
  switch (formData.provider) {
    case 'SQLServer':
      return 'Server=localhost;Database=mydb;User Id=sa;Password=password;';
    case 'PostgreSQL':
      return 'Host=localhost;Port=5432;Database=mydb;Username=user;Password=password;';
    case 'MySQL':
      return 'Server=localhost;Database=mydb;Uid=user;Pwd=password;';
    case 'SQLite':
      return 'Data Source=C:\\path\\to\\database.sqlite;';
    default:
      return 'Select a provider to see example';
  }
};
```

### Environment Variable Configuration

```bash
# .env file
# Primary SQLite database
SQLITE_PATH=sqlite_data/chatbot.sqlite
DATABASE_URL=sqlite:///home/data/chat360.db

# Alternative database URLs for different providers
# DATABASE_URL=postgresql://user:password@localhost:5432/mydb
# DATABASE_URL=mysql://user:password@localhost:3306/mydb
```

### Creating Database Connections

```python
# Example: Creating a new database connection
from db import create_database_connection
from db_connection_service import DatabaseConnectionService

def create_new_connection(tenant_id: int, created_by: str):
    """Example of creating different database connections"""

    # SQLite connection
    sqlite_conn_id = create_database_connection(
        tenant_id=tenant_id,
        database_name="Local SQLite DB",
        provider="SQLite",
        connection_string="Data Source=./data/local.sqlite;",
        created_by=created_by
    )

    # PostgreSQL connection
    postgres_conn_id = create_database_connection(
        tenant_id=tenant_id,
        database_name="Production PostgreSQL",
        provider="PostgreSQL",
        connection_string="Host=localhost;Port=5432;Database=myapp;Username=user;Password=secret;",
        created_by=created_by
    )

    # MySQL connection
    mysql_conn_id = create_database_connection(
        tenant_id=tenant_id,
        database_name="Analytics MySQL",
        provider="MySQL",
        connection_string="Server=localhost;Database=analytics;Uid=user;Pwd=secret;",
        created_by=created_by
    )

    # SQL Server connection
    sqlserver_conn_id = create_database_connection(
        tenant_id=tenant_id,
        database_name="Enterprise SQL Server",
        provider="SQLServer",
        connection_string="Server=localhost;Database=enterprise;User Id=sa;Password=secret;",
        created_by=created_by
    )

    return {
        "sqlite": sqlite_conn_id,
        "postgresql": postgres_conn_id,
        "mysql": mysql_conn_id,
        "sqlserver": sqlserver_conn_id
    }

# Test connections
def test_all_connections(tenant_id: int):
    """Test all connections for a tenant"""
    from db import get_database_connections

    connections = get_database_connections(tenant_id)
    results = []

    for conn in connections:
        conn_id, tenant_id, db_name, provider, conn_string, is_active, created_date, last_tested, test_status, created_by = conn

        # Test the connection
        test_result = DatabaseConnectionService.test_connection(provider, conn_string)

        results.append({
            "connection_id": conn_id,
            "database_name": db_name,
            "provider": provider,
            "test_success": test_result.success,
            "test_message": test_result.message
        })

    return results
```

### Using Connections in Services

```python
# Example service using database connections
class DatabaseChatService:

    def __init__(self, tenant_id: int, connection_id: int):
        self.tenant_id = tenant_id
        self.connection_id = connection_id
        self.connection_info = self._get_connection_info()

    def _get_connection_info(self):
        """Get connection information"""
        from db import get_database_connection_secure
        return get_database_connection_secure(self.connection_id, self.tenant_id)

    def execute_query(self, sql_query: str):
        """Execute a query on the connected database"""
        if not self.connection_info:
            raise ValueError("Connection not found or access denied")

        conn_id, tenant_id, db_name, provider, conn_string, is_active, created_date, last_tested, test_status, created_by = self.connection_info

        if not is_active:
            raise ValueError("Connection is not active")

        # Use the appropriate connection method based on provider
        if provider.lower() == 'sqlite':
            return self._execute_sqlite_query(conn_string, sql_query)
        elif provider.lower() == 'postgresql':
            return self._execute_postgresql_query(conn_string, sql_query)
        elif provider.lower() == 'mysql':
            return self._execute_mysql_query(conn_string, sql_query)
        elif provider.lower() == 'sqlserver':
            return self._execute_sqlserver_query(conn_string, sql_query)
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def _execute_sqlite_query(self, conn_string: str, sql_query: str):
        """Execute SQLite query"""
        import sqlite3
        import pandas as pd

        # Extract database path
        if "Data Source=" in conn_string:
            db_path = conn_string.split("Data Source=")[1].split(";")[0]
        else:
            db_path = conn_string

        conn = sqlite3.connect(db_path)
        try:
            result = pd.read_sql(sql_query, conn)
            return result.to_dict('records')
        finally:
            conn.close()

    def _execute_postgresql_query(self, conn_string: str, sql_query: str):
        """Execute PostgreSQL query"""
        import psycopg2
        import pandas as pd

        conn = psycopg2.connect(conn_string)
        try:
            result = pd.read_sql(sql_query, conn)
            return result.to_dict('records')
        finally:
            conn.close()

    def _execute_mysql_query(self, conn_string: str, sql_query: str):
        """Execute MySQL query"""
        import pymysql
        import pandas as pd

        # Parse connection string
        params = self._parse_connection_params(conn_string)

        conn = pymysql.connect(
            host=params.get('host', 'localhost'),
            user=params.get('user', 'root'),
            password=params.get('password', ''),
            database=params.get('database', ''),
            port=int(params.get('port', 3306))
        )
        try:
            result = pd.read_sql(sql_query, conn)
            return result.to_dict('records')
        finally:
            conn.close()

    def _execute_sqlserver_query(self, conn_string: str, sql_query: str):
        """Execute SQL Server query"""
        import pyodbc
        import pandas as pd

        conn = pyodbc.connect(conn_string)
        try:
            result = pd.read_sql(sql_query, conn)
            return result.to_dict('records')
        finally:
            conn.close()

    def _parse_connection_params(self, conn_string: str) -> dict:
        """Parse semicolon-separated connection string"""
        params = {}
        for param in conn_string.split(';'):
            if '=' in param:
                key, value = param.split('=', 1)
                key = key.strip().lower()
                value = value.strip()

                # Normalize parameter names
                if key in ['server', 'host']:
                    params['host'] = value
                elif key in ['database', 'db']:
                    params['database'] = value
                elif key in ['uid', 'user', 'username']:
                    params['user'] = value
                elif key in ['pwd', 'password']:
                    params['password'] = value
                elif key == 'port':
                    params['port'] = value

        return params
```

## �🔧 Core Database Setup

### 1. Main Database Configuration (`db.py`)

```python
import os
import sqlite3
from datetime import datetime, timedelta
import json
from typing import List, Dict, Optional

# Path to your SQLite file: from env if set, otherwise default
DB_PATH = os.getenv("SQLITE_PATH", "sqlite_data/chatbot.sqlite")

def init_db():
    """
    Initialize the SQLite database and create all necessary tables if they do not exist.
    """
    # Ensure the directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Table: tenants (clients)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS tenants (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        company_name TEXT DEFAULT 'BMI',
        assistant_name TEXT DEFAULT 'Akissi',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # Table: users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(tenant_id) REFERENCES tenants(id),
        UNIQUE(tenant_id, username)
    );
    """)

    # Table: documents (PDFs)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        tenant_id    INTEGER NOT NULL,
        filename     TEXT    NOT NULL,
        title        TEXT,
        description  TEXT,
        uploaded_at  TEXT    NOT NULL,
        uploaded_by  TEXT    NOT NULL,
        is_active    INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY(tenant_id) REFERENCES tenants(id)
    );
    """)

    # Chat Documents Table (for knowledge base)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS chat_documents (
        id TEXT PRIMARY KEY,
        tenant_id TEXT NOT NULL,
        title TEXT NOT NULL,
        content TEXT,
        document_type TEXT,
        embedding_vector TEXT, -- JSON string of float array
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    );
    """)

    # Additional tables...
    # (Add other tables as needed)

    conn.commit()
    conn.close()

def get_db_connection():
    """Get a database connection."""
    return sqlite3.connect(DB_PATH)
```

### 2. Environment Configuration (`.env`)

```bash
# Database Configuration
SQLITE_PATH=sqlite_data/chatbot.sqlite

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Application Configuration
PORT=8811
HOST=0.0.0.0
DEBUG=true

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here

# Logging
LOG_LEVEL=INFO
```

### 3. Application Startup (`app.py`)

```python
import os
from fastapi import FastAPI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Your Application",
    description="Multi-tenant application with database integration",
    version="1.0.0"
)

# === STARTUP LOGIC ===
@app.on_event("startup")
def _startup():
    from db import init_db
    init_db()
    print("[OK] Database initialized.")
    
    # Additional startup logic...

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8811))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "true").lower() == "true"
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info" if debug else "warning"
    )
```

### 4. Database Initialization Script (`init_database.py`)

```python
#!/usr/bin/env python3
"""
Database initialization script for Chat360 platform.
Run this script to set up the database with all required tables.
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db import init_db

def main():
    """Initialize the database with all tables."""
    print("[LAUNCH] Initializing database...")
    
    try:
        init_db()
        print("[OK] Database initialization completed successfully!")
        print("[LIST] Tables created/verified:")
        print("   - tenants")
        print("   - users") 
        print("   - documents")
        print("   - chat_documents")
        print("   - All indexes created")
        print("\n[SUCCESS] Your database is ready!")
        
    except Exception as e:
        print(f"[ERROR] Error during database initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

## 🏛️ Repository Pattern Implementation

### 1. Base Repository Pattern

```python
# repositories/base_repository.py
import sqlite3
import json
from typing import Optional, List, Dict, Any
from db import get_db_connection

class BaseRepository:
    """Base repository class with common database operations"""
    
    def __init__(self):
        self.db_path = None  # Will use get_db_connection()
    
    def execute_query(self, query: str, params: tuple = None) -> List[Dict]:
        """Execute a SELECT query and return results as list of dictionaries"""
        conn = get_db_connection()
        conn.row_factory = sqlite3.Row  # Enable column access by name
        cur = conn.cursor()
        
        try:
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)
            
            rows = cur.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()
    
    def execute_insert(self, query: str, params: tuple) -> int:
        """Execute an INSERT query and return the last row ID"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute(query, params)
            conn.commit()
            return cur.lastrowid
        finally:
            conn.close()
    
    def execute_update(self, query: str, params: tuple) -> int:
        """Execute an UPDATE/DELETE query and return affected rows count"""
        conn = get_db_connection()
        cur = conn.cursor()
        
        try:
            cur.execute(query, params)
            conn.commit()
            return cur.rowcount
        finally:
            conn.close()
```

### 2. Document Repository Example

```python
# repositories/document_repository.py
from typing import Optional, List
from .base_repository import BaseRepository
from models.document import ChatDocument

class DocumentRepository(BaseRepository):
    """Repository for ChatDocument CRUD operations"""
    
    def create_document(self, document: ChatDocument) -> ChatDocument:
        """Create a new chat document"""
        query = """
            INSERT INTO chat_documents (
                id, tenant_id, title, content, document_type, 
                embedding_vector, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        params = (
            document.id,
            document.tenant_id,
            document.title,
            document.content,
            document.document_type,
            json.dumps(document.embedding_vector),
            document.created_at.isoformat(),
            document.updated_at.isoformat()
        )
        
        self.execute_insert(query, params)
        return document
    
    def get_document_by_id(self, tenant_id: str, document_id: str) -> Optional[ChatDocument]:
        """Get document by ID and tenant"""
        query = """
            SELECT id, tenant_id, title, content, document_type, 
                   embedding_vector, created_at, updated_at
            FROM chat_documents 
            WHERE tenant_id = ? AND id = ?
        """
        
        results = self.execute_query(query, (tenant_id, document_id))
        if results:
            return self._row_to_document(results[0])
        return None
    
    def get_documents_by_tenant(self, tenant_id: str, limit: int = 100, offset: int = 0) -> List[ChatDocument]:
        """Get all documents for a tenant with pagination"""
        query = """
            SELECT id, tenant_id, title, content, document_type, 
                   embedding_vector, created_at, updated_at
            FROM chat_documents 
            WHERE tenant_id = ?
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """
        
        results = self.execute_query(query, (tenant_id, limit, offset))
        return [self._row_to_document(row) for row in results]
    
    def _row_to_document(self, row: Dict) -> ChatDocument:
        """Convert database row to ChatDocument object"""
        return ChatDocument.from_dict(row)
```

## 🔧 Advanced Database Setup

### 1. Database Initializer Class (`setup/database_initializer.py`)

```python
import os
import sqlite3
from typing import Dict
from pathlib import Path

class DatabaseInitializer:
    def __init__(self, db_path: str = None):
        self.db_path = db_path or os.getenv('SQLITE_PATH', './chat360.db')
        self.connection = None
    
    def connect(self):
        """Establish database connection"""
        try:
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            return True
        except Exception as e:
            print(f"Database connection failed: {e}")
            return False
    
    def disconnect(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
    
    def initialize_schema(self) -> Dict[str, bool]:
        """Initialize database schema with all required tables"""
        
        if not self.connect():
            return {"success": False, "error": "Connection failed"}
        
        try:
            cursor = self.connection.cursor()
            
            # Create tenants table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tenants (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT UNIQUE NOT NULL,
                    name TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            
            # Create documents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tenant_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    original_filename TEXT,
                    content_type TEXT,
                    file_size INTEGER,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processed BOOLEAN DEFAULT 0,
                    metadata TEXT,
                    FOREIGN KEY (tenant_id) REFERENCES tenants (tenant_id)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_tenant ON documents(tenant_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_documents_processed ON documents(processed)")
            
            self.connection.commit()
            return {"success": True}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
        finally:
            self.disconnect()
```

## 🔌 External Database Connections

### 1. Database Connection Service (`db_connection_service.py`)

```python
import sqlite3
import psycopg2
import pymysql
import pyodbc
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class ConnectionTestResult:
    def __init__(self, success: bool, message: str, error_details: str = None):
        self.success = success
        self.message = message
        self.error_details = error_details

class DatabaseConnectionService:
    
    @staticmethod
    def test_connection(provider: str, connection_string: str) -> ConnectionTestResult:
        """Test a database connection."""
        try:
            if provider.lower() == 'sqlite':
                return DatabaseConnectionService._test_sqlite(connection_string)
            elif provider.lower() == 'postgresql':
                return DatabaseConnectionService._test_postgresql(connection_string)
            elif provider.lower() == 'mysql':
                return DatabaseConnectionService._test_mysql(connection_string)
            elif provider.lower() == 'sqlserver':
                return DatabaseConnectionService._test_sqlserver(connection_string)
            else:
                return ConnectionTestResult(
                    success=False,
                    message="Unsupported database provider",
                    error_details=f"Provider '{provider}' is not supported"
                )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message="Connection test failed",
                error_details=str(e)
            )
    
    @staticmethod
    def _test_sqlite(connection_string: str) -> ConnectionTestResult:
        """Test SQLite connection."""
        try:
            # Extract database path
            if "Data Source=" in connection_string:
                db_path = connection_string.split("Data Source=")[1].split(";")[0]
            else:
                db_path = connection_string
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            
            return ConnectionTestResult(
                success=True,
                message="SQLite connection successful"
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message="SQLite connection failed",
                error_details=str(e)
            )
    
    @staticmethod
    def _test_postgresql(connection_string: str) -> ConnectionTestResult:
        """Test PostgreSQL connection."""
        try:
            conn = psycopg2.connect(connection_string)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            
            return ConnectionTestResult(
                success=True,
                message="PostgreSQL connection successful"
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message="PostgreSQL connection failed",
                error_details=str(e)
            )

## 🚀 Production Configuration

### 1. Production Settings (`production-config.py`)

```python
from pydantic import BaseSettings, Field
from typing import Optional

class ProductionSettings(BaseSettings):
    """Production configuration settings"""

    # Application
    app_name: str = Field(default="Chat360", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")

    # Server
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8811, env="PORT")

    # Database Configuration (SQLite)
    database_url: str = Field(default="sqlite:///home/data/chat360.db", env="DATABASE_URL")
    sqlite_path: str = Field(default="/home/data/chat360.db", env="SQLITE_PATH")

    # Pool settings (not needed for SQLite but kept for compatibility)
    db_pool_size: int = Field(default=1, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=0, env="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")

    # Security
    secret_key: str = Field(..., env="SECRET_KEY")
    jwt_secret: str = Field(..., env="JWT_SECRET")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Global settings instance
settings = ProductionSettings()
```

### 2. SQLAlchemy Alternative Setup (`voice_assistant/models/base.py`)

```python
"""
Database base configuration and session management using SQLAlchemy
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Generator

from config import settings

# Create database engine
if settings.database_url.startswith("sqlite"):
    # SQLite specific configuration
    engine = create_engine(
        settings.database_url,
        connect_args={
            "check_same_thread": False,
            "timeout": 20
        },
        poolclass=StaticPool,
        echo=settings.debug
    )
else:
    # PostgreSQL/MySQL configuration
    engine = create_engine(
        settings.database_url,
        echo=settings.debug
    )

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

def get_db() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)
```

## 🔄 Database Operations

### 1. Core Database Functions (`db.py` - Extended)

```python
# === Database Connection Management ===

def create_database_connection(tenant_id: int, database_name: str, provider: str,
                             connection_string: str, created_by: str):
    """Create a new database connection for a tenant."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    try:
        cur.execute("""
            INSERT INTO tblConnexions (
                tenant_id, database_name, provider, connection_string,
                created_date, created_by, test_status
            ) VALUES (?, ?, ?, ?, ?, ?, 'NotTested');
        """, (tenant_id, database_name, provider, connection_string, ts, created_by))
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()

def get_database_connections(tenant_id: int, active_only: bool = True):
    """Get all database connections for a tenant."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if active_only:
        cur.execute("SELECT * FROM tblConnexions WHERE tenant_id=? AND is_active = 1 ORDER BY created_date DESC", (tenant_id,))
    else:
        cur.execute("SELECT * FROM tblConnexions WHERE tenant_id=? ORDER BY created_date DESC", (tenant_id,))
    connections = cur.fetchall()
    conn.close()
    return connections

def get_database_connection_secure(connection_id: int, tenant_id: int):
    """Get a specific database connection by ID with tenant validation."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM tblConnexions WHERE id = ? AND tenant_id = ?", (connection_id, tenant_id))
    connection = cur.fetchone()
    conn.close()
    return connection

# === Document Management ===

def add_document(tenant_id: int, filename: str, title: str, description: str, uploaded_by: str):
    """Add a new document to the system for a tenant."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    cur.execute("""
        INSERT INTO documents (
            tenant_id,
            filename,
            title,
            description,
            uploaded_at,
            uploaded_by
        ) VALUES (?, ?, ?, ?, ?, ?);
    """, (tenant_id, filename, title, description, ts, uploaded_by))
    conn.commit()
    conn.close()

# === Chat Management ===

def save_database_chat_message(tenant_id: int, connection_id: int, session_id: str,
                              user_name: str, role: str, message: str,
                              query_executed: str = None, query_result: str = None):
    """Save database chat message with optional query and result information."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    cur.execute("""
        INSERT INTO database_conversations (
            tenant_id,
            connection_id,
            session_id,
            timestamp,
            message,
            role,
            user_name,
            query_executed,
            query_result
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (tenant_id, connection_id, session_id, ts, message, role,
          user_name or "", query_executed, query_result))
    conn.commit()
    conn.close()
```

## 🛠️ Implementation Steps

### Step 1: Project Structure Setup

```
your_project/
├── db.py                           # Main database module
├── init_database.py               # Database initialization script
├── app.py                         # FastAPI application
├── .env                           # Environment configuration
├── requirements.txt               # Dependencies
├── setup/
│   └── database_initializer.py    # Advanced setup
├── repositories/
│   ├── base_repository.py         # Base repository pattern
│   └── document_repository.py     # Document operations
├── models/
│   └── document.py               # Data models
└── sqlite_data/                  # Database storage directory
    └── chatbot.sqlite            # SQLite database file
```

### Step 2: Install Dependencies

```bash
pip install fastapi uvicorn python-dotenv sqlite3
# Optional: SQLAlchemy for advanced ORM features
pip install sqlalchemy
# Optional: External database support
pip install psycopg2-binary pymysql pyodbc
```

### Step 3: Environment Setup

Create `.env` file:
```bash
SQLITE_PATH=sqlite_data/chatbot.sqlite
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here
PORT=8811
HOST=0.0.0.0
DEBUG=true
```

### Step 4: Database Initialization

```bash
# Run database initialization
python init_database.py

# Or initialize programmatically
python -c "from db import init_db; init_db()"
```

### Step 5: Application Startup

```python
# app.py
from fastapi import FastAPI
from db import init_db

app = FastAPI()

@app.on_event("startup")
def startup():
    init_db()
    print("Database initialized")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8811, reload=True)
```

## 🔍 Testing Database Connection

### 1. Basic Connection Test

```python
# test_db_connection.py
import os
from db import get_db_connection, DB_PATH

def test_connection():
    """Test basic database connection"""
    try:
        print(f"Testing connection to: {DB_PATH}")

        # Test connection
        conn = get_db_connection()
        cursor = conn.cursor()

        # Test basic query
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

        # Test table existence
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name IN ('tenants', 'documents', 'chat_documents')
        """)
        tables = [row[0] for row in cursor.fetchall()]

        conn.close()

        print("✅ Database connection successful")
        print(f"✅ Found tables: {tables}")
        return True

    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()
```

### 2. Repository Test

```python
# test_repository.py
from repositories.document_repository import DocumentRepository
from models.document import ChatDocument

def test_repository():
    """Test repository operations"""
    repo = DocumentRepository()

    # Create test document
    doc = ChatDocument(
        tenant_id="test_tenant",
        title="Test Document",
        content="This is a test document",
        document_type="test"
    )

    try:
        # Test create
        created_doc = repo.create_document(doc)
        print(f"✅ Document created: {created_doc.id}")

        # Test retrieve
        retrieved_doc = repo.get_document_by_id("test_tenant", created_doc.id)
        print(f"✅ Document retrieved: {retrieved_doc.title}")

        # Test list
        docs = repo.get_documents_by_tenant("test_tenant")
        print(f"✅ Found {len(docs)} documents for tenant")

        return True

    except Exception as e:
        print(f"❌ Repository test failed: {e}")
        return False

if __name__ == "__main__":
    test_repository()
```

## 🔒 Security Considerations

### 1. Connection String Security

```python
# utils/security.py
import os
from cryptography.fernet import Fernet

class ConnectionStringEncryption:
    def __init__(self):
        # In production, store this key securely
        self.key = os.getenv("ENCRYPTION_KEY", Fernet.generate_key())
        self.cipher = Fernet(self.key)

    def encrypt_connection_string(self, connection_string: str) -> str:
        """Encrypt a connection string"""
        return self.cipher.encrypt(connection_string.encode()).decode()

    def decrypt_connection_string(self, encrypted_string: str) -> str:
        """Decrypt a connection string"""
        return self.cipher.decrypt(encrypted_string.encode()).decode()
```

### 2. Tenant Isolation

```python
# utils/tenant_security.py
def validate_tenant_access(tenant_id: str, user_tenant_id: str) -> bool:
    """Validate that user has access to the specified tenant"""
    return tenant_id == user_tenant_id

def get_tenant_scoped_query(base_query: str, tenant_id: str) -> str:
    """Add tenant filtering to queries"""
    if "WHERE" in base_query.upper():
        return f"{base_query} AND tenant_id = '{tenant_id}'"
    else:
        return f"{base_query} WHERE tenant_id = '{tenant_id}'"
```

## 📊 Monitoring and Maintenance

### 1. Database Health Check

```python
# utils/health_check.py
import sqlite3
import os
from datetime import datetime

def database_health_check() -> dict:
    """Perform comprehensive database health check"""
    health_status = {
        "timestamp": datetime.utcnow().isoformat(),
        "database_accessible": False,
        "tables_exist": False,
        "data_integrity": False,
        "disk_space": None,
        "connection_count": 0
    }

    try:
        # Check database accessibility
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        health_status["database_accessible"] = True

        # Check required tables
        cursor.execute("""
            SELECT COUNT(*) FROM sqlite_master
            WHERE type='table' AND name IN ('tenants', 'documents', 'chat_documents')
        """)
        table_count = cursor.fetchone()[0]
        health_status["tables_exist"] = table_count >= 3

        # Check data integrity
        cursor.execute("PRAGMA integrity_check")
        integrity_result = cursor.fetchone()[0]
        health_status["data_integrity"] = integrity_result == "ok"

        # Check disk space
        if os.path.exists(DB_PATH):
            stat = os.stat(DB_PATH)
            health_status["disk_space"] = stat.st_size

        conn.close()

    except Exception as e:
        health_status["error"] = str(e)

    return health_status
```

## 🚀 Deployment Considerations

### 1. Docker Configuration

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /app/sqlite_data

# Initialize database
RUN python init_database.py

# Expose port
EXPOSE 8811

# Start application
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8811"]
```

### 2. Docker Compose

```yaml
# docker-compose.yml
version: "3.8"

services:
  app:
    build: .
    ports:
      - "8811:8811"
    environment:
      SQLITE_PATH: /app/data/chatbot.sqlite
      SECRET_KEY: ${SECRET_KEY}
      JWT_SECRET: ${JWT_SECRET}
    volumes:
      - ./sqlite_data:/app/data
      - ./logs:/app/logs
    restart: unless-stopped
```

---

## 📝 Summary

This database connection setup provides:

1. **Simple SQLite-based architecture** with environment configuration
2. **Repository pattern** for clean data access
3. **Multi-tenant support** with proper isolation
4. **External database connectivity** for advanced use cases
5. **Production-ready configuration** with security considerations
6. **Comprehensive testing** and monitoring capabilities

The system is designed to be easily reproducible and scalable, making it perfect for multi-tenant applications with document management and chat capabilities.
```
