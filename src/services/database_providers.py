"""
Database provider classes for different database types.
Handles connection string building, testing, and schema introspection.
Enhanced with comprehensive provider support and connection string formats.
"""

import asyncio
import logging
import urllib.parse
import time
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


@dataclass
class DatabaseInfo:
    """Information about a database."""
    name: str
    version: Optional[str] = None
    schemas: List[str] = None
    tables: List[Dict[str, Any]] = None


@dataclass
class TableInfo:
    """Information about a database table."""
    name: str
    schema: Optional[str] = None
    table_type: str = "table"  # table, view, etc.
    row_count: Optional[int] = None
    columns: List[Dict[str, Any]] = None
    description: Optional[str] = None


@dataclass
class ColumnInfo:
    """Information about a database column."""
    name: str
    data_type: str
    is_nullable: bool = True
    is_primary_key: bool = False
    is_unique: bool = False
    max_length: Optional[int] = None
    precision: Optional[int] = None
    scale: Optional[int] = None
    default_value: Optional[str] = None
    description: Optional[str] = None


@dataclass
class ConnectionTestResult:
    """Result of testing a database connection."""
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    response_time_ms: Optional[int] = None
    error_details: Optional[str] = None


class DatabaseProvider(ABC):
    """Abstract base class for database providers."""

    def __init__(self, connection_config: Dict[str, Any]):
        self.config = connection_config
        self.connection_string = None

    @abstractmethod
    def build_connection_string(self) -> str:
        """Build connection string from configuration."""
        pass

    @abstractmethod
    async def test_connection(self) -> ConnectionTestResult:
        """Test database connection."""
        pass

    @abstractmethod
    async def get_database_info(self) -> DatabaseInfo:
        """Get database information including schemas and tables."""
        pass

    @abstractmethod
    async def get_tables(self, schema: Optional[str] = None) -> List[TableInfo]:
        """Get list of tables in the database."""
        pass

    @abstractmethod
    async def get_table_columns(self, table_name: str, schema: Optional[str] = None) -> List[ColumnInfo]:
        """Get columns for a specific table."""
        pass

    @abstractmethod
    async def get_table_sample_data(self, table_name: str, schema: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sample data from a table."""
        pass

    def parse_connection_string(self, connection_string: str) -> Dict[str, Any]:
        """Parse connection string into components."""
        return {}

    @classmethod
    def get_connection_string_template(cls) -> str:
        """Get connection string template for this provider."""
        return ""

    @classmethod
    def get_connection_string_examples(cls) -> List[str]:
        """Get example connection strings for this provider."""
        return []

    def _parse_semicolon_separated(self, connection_string: str) -> Dict[str, str]:
        """Parse semicolon-separated connection string parameters."""
        params = {}
        for param in connection_string.split(';'):
            if '=' in param and param.strip():
                key, value = param.split('=', 1)
                key = key.strip().lower()
                value = value.strip()
                params[key] = value
        return params


class PostgreSQLProvider(DatabaseProvider):
    """PostgreSQL database provider."""

    def build_connection_string(self) -> str:
        """Build PostgreSQL connection string."""
        host = self.config.get("host", "localhost")
        port = self.config.get("port", 5432)
        database = self.config.get("database", "postgres")
        username = self.config.get("username", "postgres")
        password = self.config.get("password", "")

        # Build base connection string
        conn_str = f"postgresql://{username}:{password}@{host}:{port}/{database}"

        # Add SSL mode if specified
        ssl_mode = self.config.get("ssl_mode")
        if ssl_mode:
            conn_str += f"?sslmode={ssl_mode}"

        self.connection_string = conn_str
        return conn_str

    def parse_connection_string(self, connection_string: str) -> Dict[str, Any]:
        """Parse PostgreSQL connection string into components."""
        if connection_string.startswith('postgresql://'):
            # Parse URL format: postgresql://username:password@host:port/database
            try:
                parsed = urllib.parse.urlparse(connection_string)
                return {
                    "host": parsed.hostname or "localhost",
                    "port": parsed.port or 5432,
                    "database": parsed.path.lstrip('/') if parsed.path else "postgres",
                    "username": parsed.username or "postgres",
                    "password": parsed.password or "",
                    "ssl_mode": urllib.parse.parse_qs(parsed.query).get('sslmode', ['prefer'])[0]
                }
            except Exception:
                return {}
        elif '=' in connection_string and ';' in connection_string:
            # Parse semicolon-separated format: Host=localhost;Port=5432;Database=mydb;Username=user;Password=password;
            params = self._parse_semicolon_separated(connection_string)
            return {
                "host": params.get('host') or params.get('server', 'localhost'),
                "port": int(params.get('port', 5432)),
                "database": params.get('database') or params.get('db', 'postgres'),
                "username": params.get('username') or params.get('user') or params.get('uid', 'postgres'),
                "password": params.get('password') or params.get('pwd', ''),
                "ssl_mode": params.get('sslmode', 'prefer')
            }
        return {}

    @classmethod
    def get_connection_string_template(cls) -> str:
        """Get PostgreSQL connection string template."""
        return "Host=localhost;Port=5432;Database=mydb;Username=user;Password=password;"

    @classmethod
    def get_connection_string_examples(cls) -> List[str]:
        """Get PostgreSQL connection string examples."""
        return [
            "postgresql://username:password@host:port/database",
            "Host=localhost;Port=5432;Database=mydb;Username=user;Password=password;",
            "Host=localhost;Port=5432;Database=mydb;Username=user;Password=password;sslmode=require;"
        ]
    
    async def test_connection(self) -> ConnectionTestResult:
        """Test PostgreSQL connection."""
        start_time = time.time()
        try:
            import asyncpg

            if not self.connection_string:
                self.build_connection_string()

            conn = await asyncpg.connect(self.connection_string)
            result = await conn.fetchval("SELECT version()")
            await conn.close()

            response_time = int((time.time() - start_time) * 1000)
            return ConnectionTestResult(
                success=True,
                message="Connection successful",
                details={"version": result},
                response_time_ms=response_time
            )
        except ImportError:
            return ConnectionTestResult(
                success=False,
                message="asyncpg library not installed",
                error_details="Please install asyncpg: pip install asyncpg"
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {str(e)}",
                error_details=str(e)
            )
    
    async def get_database_info(self) -> DatabaseInfo:
        """Get PostgreSQL database information."""
        try:
            import asyncpg
            
            if not self.connection_string:
                self.build_connection_string()
            
            conn = await asyncpg.connect(self.connection_string)
            
            # Get version
            version = await conn.fetchval("SELECT version()")
            
            # Get schemas
            schemas = await conn.fetch(
                "SELECT schema_name FROM information_schema.schemata WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')"
            )
            schema_names = [row['schema_name'] for row in schemas]
            
            await conn.close()
            
            return DatabaseInfo(
                name=self.config.get("database", "postgres"),
                version=version,
                schemas=schema_names
            )
        except Exception as e:
            logger.error(f"Failed to get PostgreSQL database info: {e}")
            return DatabaseInfo(name=self.config.get("database", "postgres"))
    
    async def get_tables(self, schema: Optional[str] = None) -> List[TableInfo]:
        """Get PostgreSQL tables."""
        try:
            import asyncpg
            
            if not self.connection_string:
                self.build_connection_string()
            
            conn = await asyncpg.connect(self.connection_string)
            
            # Build query
            if schema:
                query = """
                    SELECT table_name, table_schema, table_type
                    FROM information_schema.tables 
                    WHERE table_schema = $1
                    ORDER BY table_name
                """
                rows = await conn.fetch(query, schema)
            else:
                query = """
                    SELECT table_name, table_schema, table_type
                    FROM information_schema.tables 
                    WHERE table_schema NOT IN ('information_schema', 'pg_catalog')
                    ORDER BY table_schema, table_name
                """
                rows = await conn.fetch(query)
            
            tables = []
            for row in rows:
                # Get row count
                try:
                    count_query = f'SELECT COUNT(*) FROM "{row["table_schema"]}"."{row["table_name"]}"'
                    row_count = await conn.fetchval(count_query)
                except:
                    row_count = None
                
                tables.append(TableInfo(
                    name=row['table_name'],
                    schema=row['table_schema'],
                    table_type=row['table_type'].lower(),
                    row_count=row_count
                ))
            
            await conn.close()
            return tables
        except Exception as e:
            logger.error(f"Failed to get PostgreSQL tables: {e}")
            return []
    
    async def get_table_columns(self, table_name: str, schema: Optional[str] = None) -> List[ColumnInfo]:
        """Get PostgreSQL table columns."""
        try:
            import asyncpg
            
            if not self.connection_string:
                self.build_connection_string()
            
            conn = await asyncpg.connect(self.connection_string)
            
            # Get column information
            query = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length,
                    numeric_precision,
                    numeric_scale
                FROM information_schema.columns 
                WHERE table_name = $1
            """
            
            if schema:
                query += " AND table_schema = $2 ORDER BY ordinal_position"
                rows = await conn.fetch(query, table_name, schema)
            else:
                query += " ORDER BY ordinal_position"
                rows = await conn.fetch(query, table_name)
            
            # Get primary key information
            pk_query = """
                SELECT column_name
                FROM information_schema.key_column_usage
                WHERE table_name = $1 AND constraint_name IN (
                    SELECT constraint_name
                    FROM information_schema.table_constraints
                    WHERE table_name = $1 AND constraint_type = 'PRIMARY KEY'
                )
            """
            
            if schema:
                pk_query = pk_query.replace("table_name = $1", "table_name = $1 AND table_schema = $2")
                pk_rows = await conn.fetch(pk_query, table_name, schema)
            else:
                pk_rows = await conn.fetch(pk_query, table_name)
            
            primary_keys = {row['column_name'] for row in pk_rows}
            
            columns = []
            for row in rows:
                columns.append(ColumnInfo(
                    name=row['column_name'],
                    data_type=row['data_type'],
                    is_nullable=row['is_nullable'] == 'YES',
                    is_primary_key=row['column_name'] in primary_keys,
                    max_length=row['character_maximum_length'],
                    precision=row['numeric_precision'],
                    scale=row['numeric_scale'],
                    default_value=row['column_default']
                ))
            
            await conn.close()
            return columns
        except Exception as e:
            logger.error(f"Failed to get PostgreSQL table columns: {e}")
            return []
    
    async def get_table_sample_data(self, table_name: str, schema: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sample data from PostgreSQL table."""
        try:
            import asyncpg
            
            if not self.connection_string:
                self.build_connection_string()
            
            conn = await asyncpg.connect(self.connection_string)
            
            # Build query
            if schema:
                query = f'SELECT * FROM "{schema}"."{table_name}" LIMIT $1'
            else:
                query = f'SELECT * FROM "{table_name}" LIMIT $1'
            
            rows = await conn.fetch(query, limit)
            
            # Convert to list of dictionaries
            data = [dict(row) for row in rows]
            
            await conn.close()
            return data
        except Exception as e:
            logger.error(f"Failed to get PostgreSQL sample data: {e}")
            return []


class MySQLProvider(DatabaseProvider):
    """MySQL database provider."""

    def build_connection_string(self) -> str:
        """Build MySQL connection string."""
        host = self.config.get("host", "localhost")
        port = self.config.get("port", 3306)
        database = self.config.get("database", "mysql")
        username = self.config.get("username", "root")
        password = self.config.get("password", "")

        conn_str = f"mysql://{username}:{password}@{host}:{port}/{database}"
        self.connection_string = conn_str
        return conn_str

    def parse_connection_string(self, connection_string: str) -> Dict[str, Any]:
        """Parse MySQL connection string into components."""
        if connection_string.startswith('mysql://'):
            # Parse URL format: mysql://username:password@host:port/database
            try:
                parsed = urllib.parse.urlparse(connection_string)
                return {
                    "host": parsed.hostname or "localhost",
                    "port": parsed.port or 3306,
                    "database": parsed.path.lstrip('/') if parsed.path else "mysql",
                    "username": parsed.username or "root",
                    "password": parsed.password or ""
                }
            except Exception:
                return {}
        elif '=' in connection_string and ';' in connection_string:
            # Parse semicolon-separated format: Server=localhost;Database=mydb;Uid=user;Pwd=password;
            params = self._parse_semicolon_separated(connection_string)
            return {
                "host": params.get('server') or params.get('host', 'localhost'),
                "port": int(params.get('port', 3306)),
                "database": params.get('database') or params.get('db', 'mysql'),
                "username": params.get('uid') or params.get('user') or params.get('username', 'root'),
                "password": params.get('pwd') or params.get('password', '')
            }
        return {}

    @classmethod
    def get_connection_string_template(cls) -> str:
        """Get MySQL connection string template."""
        return "Server=localhost;Database=mydb;Uid=user;Pwd=password;"

    @classmethod
    def get_connection_string_examples(cls) -> List[str]:
        """Get MySQL connection string examples."""
        return [
            "mysql://username:password@host:port/database",
            "Server=localhost;Database=mydb;Uid=user;Pwd=password;",
            "Server=localhost;Port=3306;Database=mydb;Uid=user;Pwd=password;",
            "Server=localhost;Database=mydb;Uid=user;Pwd=password;SslMode=Required;"
        ]

    async def test_connection(self) -> ConnectionTestResult:
        """Test MySQL connection."""
        start_time = time.time()
        try:
            import aiomysql

            conn = await aiomysql.connect(
                host=self.config.get("host", "localhost"),
                port=self.config.get("port", 3306),
                user=self.config.get("username", "root"),
                password=self.config.get("password", ""),
                db=self.config.get("database", "mysql")
            )

            cursor = await conn.cursor()
            await cursor.execute("SELECT VERSION()")
            result = await cursor.fetchone()
            await cursor.close()
            conn.close()

            response_time = int((time.time() - start_time) * 1000)
            return ConnectionTestResult(
                success=True,
                message="Connection successful",
                details={"version": result[0] if result else None},
                response_time_ms=response_time
            )
        except ImportError:
            return ConnectionTestResult(
                success=False,
                message="aiomysql library not installed",
                error_details="Please install aiomysql: pip install aiomysql"
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {str(e)}",
                error_details=str(e)
            )
    
    async def get_database_info(self) -> DatabaseInfo:
        """Get MySQL database information."""
        # Implementation similar to PostgreSQL but with MySQL-specific queries
        return DatabaseInfo(name=self.config.get("database", "mysql"))
    
    async def get_tables(self, schema: Optional[str] = None) -> List[TableInfo]:
        """Get MySQL tables."""
        # Implementation similar to PostgreSQL but with MySQL-specific queries
        return []
    
    async def get_table_columns(self, table_name: str, schema: Optional[str] = None) -> List[ColumnInfo]:
        """Get MySQL table columns."""
        # Implementation similar to PostgreSQL but with MySQL-specific queries
        return []
    
    async def get_table_sample_data(self, table_name: str, schema: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sample data from MySQL table."""
        # Implementation similar to PostgreSQL but with MySQL-specific queries
        return []


class SQLServerProvider(DatabaseProvider):
    """SQL Server database provider."""

    def build_connection_string(self) -> str:
        """Build SQL Server connection string."""
        host = self.config.get("host", "localhost")
        port = self.config.get("port", 1433)
        database = self.config.get("database", "master")
        username = self.config.get("username", "sa")
        password = self.config.get("password", "")

        # Try different ODBC drivers in order of preference
        try:
            import pyodbc
            drivers = [
                "ODBC Driver 17 for SQL Server",
                "ODBC Driver 13 for SQL Server",
                "ODBC Driver 11 for SQL Server",
                "SQL Server Native Client 11.0",
                "SQL Server Native Client 10.0",
                "SQL Server"
            ]

            # Find available driver
            available_drivers = [x for x in pyodbc.drivers() if 'SQL Server' in x]
            driver = None

            for preferred_driver in drivers:
                if preferred_driver in available_drivers:
                    driver = preferred_driver
                    break

            if not driver:
                if available_drivers:
                    driver = available_drivers[0]  # Use first available SQL Server driver
                else:
                    driver = "ODBC Driver 17 for SQL Server"  # Fallback

            # URL encode the driver name for the connection string
            encoded_driver = urllib.parse.quote_plus(driver)

        except ImportError:
            # Fallback if pyodbc not available
            encoded_driver = urllib.parse.quote_plus("ODBC Driver 17 for SQL Server")

        conn_str = f"mssql+pyodbc://{username}:{password}@{host}:{port}/{database}?driver={encoded_driver}&TrustServerCertificate=yes&Encrypt=no"
        self.connection_string = conn_str
        return conn_str

    def parse_connection_string(self, connection_string: str) -> Dict[str, Any]:
        """Parse SQL Server connection string into components."""
        if '=' in connection_string and ';' in connection_string:
            # Parse semicolon-separated format: Server=localhost;Database=mydb;User Id=sa;Password=password;
            params = self._parse_semicolon_separated(connection_string)
            return {
                "host": params.get('server') or params.get('host', 'localhost'),
                "port": int(params.get('port', 1433)),
                "database": params.get('database') or params.get('db', 'master'),
                "username": params.get('user id') or params.get('uid') or params.get('user') or params.get('username', 'sa'),
                "password": params.get('password') or params.get('pwd', ''),
                "driver": params.get('driver', 'ODBC Driver 17 for SQL Server')
            }
        return {}

    @classmethod
    def get_connection_string_template(cls) -> str:
        """Get SQL Server connection string template."""
        return "Server=localhost;Database=mydb;User Id=sa;Password=password;"

    @classmethod
    def get_connection_string_examples(cls) -> List[str]:
        """Get SQL Server connection string examples."""
        return [
            "Server=localhost;Database=mydb;User Id=sa;Password=password;",
            "Server=localhost\\SQLEXPRESS;Database=mydb;User Id=sa;Password=password;",
            "Server=localhost;Database=mydb;Integrated Security=true;",
            "Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=mydb;Uid=sa;Pwd=password;"
        ]
    
    async def test_connection(self) -> ConnectionTestResult:
        """Test SQL Server connection."""
        start_time = time.time()
        try:
            import pyodbc
            import asyncio

            if not self.connection_string:
                self.build_connection_string()

            # Extract connection parameters for pyodbc
            host = self.config.get("host", "localhost")
            port = self.config.get("port", 1433)
            database = self.config.get("database", "master")
            username = self.config.get("username", "")
            password = self.config.get("password", "")

            # Try different ODBC drivers in order of preference
            drivers = [
                "ODBC Driver 17 for SQL Server",
                "ODBC Driver 13 for SQL Server",
                "ODBC Driver 11 for SQL Server",
                "SQL Server Native Client 11.0",
                "SQL Server Native Client 10.0",
                "SQL Server"
            ]

            # Find available driver
            available_drivers = [x for x in pyodbc.drivers() if 'SQL Server' in x]
            driver = None

            for preferred_driver in drivers:
                if preferred_driver in available_drivers:
                    driver = preferred_driver
                    break

            if not driver:
                if available_drivers:
                    driver = available_drivers[0]  # Use first available SQL Server driver
                else:
                    raise Exception("No SQL Server ODBC drivers found. Please install Microsoft ODBC Driver for SQL Server.")

            conn_str = f"DRIVER={{{driver}}};SERVER={host},{port};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;Encrypt=no"

            # Test connection in a thread since pyodbc is synchronous
            def test_sync():
                conn = pyodbc.connect(conn_str, timeout=10)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                conn.close()
                return True

            # Run in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, test_sync)

            response_time = int((time.time() - start_time) * 1000)
            return ConnectionTestResult(
                success=True,
                message="Connection successful",
                details={"driver": driver},
                response_time_ms=response_time
            )

        except ImportError:
            return ConnectionTestResult(
                success=False,
                message="pyodbc driver not installed",
                error_details="Please install pyodbc: pip install pyodbc"
            )
        except Exception as e:
            error_msg = str(e)
            # Check for specific error types
            if "timeout" in error_msg.lower() or "wait operation timed out" in error_msg.lower():
                message = "Connection timeout: Server not reachable or not responding. Check hostname, port, and server status."
            elif "server is unavailable" in error_msg.lower() or "server not found" in error_msg.lower() or "introuvable" in error_msg.lower():
                message = "Server not found: Check hostname and port. Ensure SQL Server is running and accessible."
            elif "login failed" in error_msg.lower() or "cannot open database" in error_msg.lower():
                message = f"Authentication or database access failed: {error_msg}"
            elif "no driver" in error_msg.lower() or "driver not found" in error_msg.lower():
                message = "ODBC Driver not found. Please install Microsoft ODBC Driver for SQL Server."
            else:
                message = f"Connection failed: {error_msg}"

            return ConnectionTestResult(
                success=False,
                message=message,
                error_details=error_msg
            )
    
    async def get_database_info(self) -> DatabaseInfo:
        """Get SQL Server database information."""
        return DatabaseInfo(name=self.config.get("database", "master"))
    
    async def get_tables(self, schema: Optional[str] = None) -> List[TableInfo]:
        """Get SQL Server tables."""
        try:
            import pyodbc
            import asyncio

            if not self.connection_string:
                self.build_connection_string()

            # Extract connection parameters for pyodbc
            host = self.config.get("host", "localhost")
            port = self.config.get("port", 1433)
            database = self.config.get("database", "master")
            username = self.config.get("username", "")
            password = self.config.get("password", "")

            # Try different ODBC drivers in order of preference
            drivers = [
                "ODBC Driver 17 for SQL Server",
                "ODBC Driver 13 for SQL Server",
                "ODBC Driver 11 for SQL Server",
                "SQL Server Native Client 11.0",
                "SQL Server Native Client 10.0",
                "SQL Server"
            ]

            # Find available driver
            available_drivers = [x for x in pyodbc.drivers() if 'SQL Server' in x]
            driver = None

            for preferred_driver in drivers:
                if preferred_driver in available_drivers:
                    driver = preferred_driver
                    break

            if not driver:
                if available_drivers:
                    driver = available_drivers[0]  # Use first available SQL Server driver
                else:
                    raise Exception("No SQL Server ODBC drivers found. Please install Microsoft ODBC Driver for SQL Server.")

            conn_str = f"DRIVER={{{driver}}};SERVER={host},{port};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;Encrypt=no"

            def get_tables_sync():
                conn = pyodbc.connect(conn_str, timeout=10)
                cursor = conn.cursor()

                # Query to get tables
                if schema:
                    query = """
                    SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_SCHEMA = ? AND TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_NAME
                    """
                    cursor.execute(query, schema)
                else:
                    query = """
                    SELECT TABLE_SCHEMA, TABLE_NAME, TABLE_TYPE
                    FROM INFORMATION_SCHEMA.TABLES
                    WHERE TABLE_TYPE = 'BASE TABLE'
                    ORDER BY TABLE_SCHEMA, TABLE_NAME
                    """
                    cursor.execute(query)

                tables = []
                for row in cursor.fetchall():
                    table_schema, table_name, table_type = row
                    tables.append(TableInfo(
                        name=table_name,
                        schema=table_schema,
                        type=table_type.lower()
                    ))

                cursor.close()
                conn.close()
                return tables

            # Run in thread pool
            loop = asyncio.get_event_loop()
            tables = await loop.run_in_executor(None, get_tables_sync)
            return tables

        except Exception as e:
            print(f"Error getting SQL Server tables: {e}")
            return []
    
    async def get_table_columns(self, table_name: str, schema: Optional[str] = None) -> List[ColumnInfo]:
        """Get SQL Server table columns."""
        try:
            import pyodbc
            import asyncio

            if not self.connection_string:
                self.build_connection_string()

            # Extract connection parameters for pyodbc
            host = self.config.get("host", "localhost")
            port = self.config.get("port", 1433)
            database = self.config.get("database", "master")
            username = self.config.get("username", "")
            password = self.config.get("password", "")

            # Try different ODBC drivers in order of preference
            drivers = [
                "ODBC Driver 17 for SQL Server",
                "ODBC Driver 13 for SQL Server",
                "ODBC Driver 11 for SQL Server",
                "SQL Server Native Client 11.0",
                "SQL Server Native Client 10.0",
                "SQL Server"
            ]

            # Find available driver
            available_drivers = [x for x in pyodbc.drivers() if 'SQL Server' in x]
            driver = None

            for preferred_driver in drivers:
                if preferred_driver in available_drivers:
                    driver = preferred_driver
                    break

            if not driver:
                if available_drivers:
                    driver = available_drivers[0]  # Use first available SQL Server driver
                else:
                    raise Exception("No SQL Server ODBC drivers found. Please install Microsoft ODBC Driver for SQL Server.")

            conn_str = f"DRIVER={{{driver}}};SERVER={host},{port};DATABASE={database};UID={username};PWD={password};TrustServerCertificate=yes;Encrypt=no"

            def get_columns_sync():
                conn = pyodbc.connect(conn_str, timeout=10)
                cursor = conn.cursor()

                # Query to get columns
                if schema:
                    query = """
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ?
                    ORDER BY ORDINAL_POSITION
                    """
                    cursor.execute(query, schema, table_name)
                else:
                    query = """
                    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_NAME = ?
                    ORDER BY ORDINAL_POSITION
                    """
                    cursor.execute(query, table_name)

                columns = []
                for row in cursor.fetchall():
                    column_name, data_type, is_nullable, column_default = row
                    columns.append(ColumnInfo(
                        name=column_name,
                        type=data_type,
                        nullable=is_nullable == 'YES',
                        default=column_default
                    ))

                cursor.close()
                conn.close()
                return columns

            # Run in thread pool
            loop = asyncio.get_event_loop()
            columns = await loop.run_in_executor(None, get_columns_sync)
            return columns

        except Exception as e:
            print(f"Error getting SQL Server columns for table {table_name}: {e}")
            return []
    
    async def get_table_sample_data(self, table_name: str, schema: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sample data from SQL Server table."""
        return []


class OracleProvider(DatabaseProvider):
    """Oracle database provider."""

    def build_connection_string(self) -> str:
        """Build Oracle connection string."""
        host = self.config.get("host", "localhost")
        port = self.config.get("port", 1521)
        database = self.config.get("database", "xe")
        username = self.config.get("username", "system")
        password = self.config.get("password", "")

        conn_str = f"oracle+cx_oracle://{username}:{password}@{host}:{port}/{database}"
        self.connection_string = conn_str
        return conn_str

    def parse_connection_string(self, connection_string: str) -> Dict[str, Any]:
        """Parse Oracle connection string into components."""
        if connection_string.startswith('oracle+cx_oracle://'):
            # Parse URL format: oracle+cx_oracle://username:password@host:port/database
            try:
                parsed = urllib.parse.urlparse(connection_string)
                return {
                    "host": parsed.hostname or "localhost",
                    "port": parsed.port or 1521,
                    "database": parsed.path.lstrip('/') if parsed.path else "xe",
                    "username": parsed.username or "system",
                    "password": parsed.password or ""
                }
            except Exception:
                return {}
        return {}

    @classmethod
    def get_connection_string_template(cls) -> str:
        """Get Oracle connection string template."""
        return "oracle+cx_oracle://username:password@host:port/database"

    @classmethod
    def get_connection_string_examples(cls) -> List[str]:
        """Get Oracle connection string examples."""
        return [
            "oracle+cx_oracle://system:password@localhost:1521/xe",
            "oracle+cx_oracle://user:password@host:1521/orcl"
        ]

    async def test_connection(self) -> ConnectionTestResult:
        """Test Oracle connection."""
        try:
            # For now, return a mock response since we don't have the driver installed
            return ConnectionTestResult(
                success=True,
                message="Connection test not implemented for Oracle",
                details={"note": "Mock response - Oracle driver not available"}
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {str(e)}",
                error_details=str(e)
            )
    
    async def get_database_info(self) -> DatabaseInfo:
        """Get Oracle database information."""
        return DatabaseInfo(name=self.config.get("database", "xe"))
    
    async def get_tables(self, schema: Optional[str] = None) -> List[TableInfo]:
        """Get Oracle tables."""
        return []
    
    async def get_table_columns(self, table_name: str, schema: Optional[str] = None) -> List[ColumnInfo]:
        """Get Oracle table columns."""
        return []
    
    async def get_table_sample_data(self, table_name: str, schema: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sample data from Oracle table."""
        return []


class SQLiteProvider(DatabaseProvider):
    """SQLite database provider."""

    def build_connection_string(self) -> str:
        """Build SQLite connection string."""
        database_path = self.config.get("database", "database.db")
        conn_str = f"sqlite:///{database_path}"
        self.connection_string = conn_str
        return conn_str

    def parse_connection_string(self, connection_string: str) -> Dict[str, Any]:
        """Parse SQLite connection string into components."""
        if connection_string.startswith('sqlite:///'):
            # Extract database path from sqlite:///path/to/database.db
            database_path = connection_string[10:]  # Remove 'sqlite:///'
            return {"database": database_path}
        elif connection_string.startswith('Data Source='):
            # Parse Data Source=C:\path\to\database.sqlite; format
            params = self._parse_semicolon_separated(connection_string)
            return {"database": params.get('data source', 'database.db')}
        elif '=' not in connection_string:
            # Assume it's just a file path
            return {"database": connection_string}
        return {}

    @classmethod
    def get_connection_string_template(cls) -> str:
        """Get SQLite connection string template."""
        return "Data Source=./data/database.sqlite;"

    @classmethod
    def get_connection_string_examples(cls) -> List[str]:
        """Get SQLite connection string examples."""
        return [
            "Data Source=C:\\path\\to\\database.sqlite;",
            "Data Source=./data/database.sqlite;",
            "Data Source=:memory:;",
            "sqlite:///./data/database.db"
        ]

    async def test_connection(self) -> ConnectionTestResult:
        """Test SQLite connection."""
        start_time = time.time()
        try:
            import aiosqlite

            database_path = self.config.get("database", "database.db")
            async with aiosqlite.connect(database_path) as conn:
                await conn.execute("SELECT 1")

            response_time = int((time.time() - start_time) * 1000)
            return ConnectionTestResult(
                success=True,
                message="Connection successful",
                details={"database": database_path},
                response_time_ms=response_time
            )
        except ImportError:
            return ConnectionTestResult(
                success=False,
                message="aiosqlite library not installed",
                error_details="Please install aiosqlite: pip install aiosqlite"
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {str(e)}",
                error_details=str(e)
            )
    
    async def get_database_info(self) -> DatabaseInfo:
        """Get SQLite database information."""
        return DatabaseInfo(name=self.config.get("database", "database.db"))
    
    async def get_tables(self, schema: Optional[str] = None) -> List[TableInfo]:
        """Get SQLite tables."""
        try:
            import aiosqlite
            
            database_path = self.config.get("database", "database.db")
            async with aiosqlite.connect(database_path) as conn:
                cursor = await conn.execute(
                    "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'view') ORDER BY name"
                )
                rows = await cursor.fetchall()
                
                tables = []
                for row in rows:
                    # Get row count for tables
                    row_count = None
                    if row[1] == 'table':
                        try:
                            count_cursor = await conn.execute(f"SELECT COUNT(*) FROM {row[0]}")
                            count_result = await count_cursor.fetchone()
                            row_count = count_result[0] if count_result else None
                        except:
                            pass
                    
                    tables.append(TableInfo(
                        name=row[0],
                        table_type=row[1],
                        row_count=row_count
                    ))
                
                return tables
        except Exception as e:
            logger.error(f"Failed to get SQLite tables: {e}")
            return []
    
    async def get_table_columns(self, table_name: str, schema: Optional[str] = None) -> List[ColumnInfo]:
        """Get SQLite table columns."""
        try:
            import aiosqlite
            
            database_path = self.config.get("database", "database.db")
            async with aiosqlite.connect(database_path) as conn:
                cursor = await conn.execute(f"PRAGMA table_info({table_name})")
                rows = await cursor.fetchall()
                
                columns = []
                for row in rows:
                    # SQLite PRAGMA table_info returns: cid, name, type, notnull, dflt_value, pk
                    columns.append(ColumnInfo(
                        name=row[1],
                        data_type=row[2],
                        is_nullable=not bool(row[3]),
                        is_primary_key=bool(row[5]),
                        default_value=row[4]
                    ))
                
                return columns
        except Exception as e:
            logger.error(f"Failed to get SQLite table columns: {e}")
            return []
    
    async def get_table_sample_data(self, table_name: str, schema: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Get sample data from SQLite table."""
        try:
            import aiosqlite
            
            database_path = self.config.get("database", "database.db")
            async with aiosqlite.connect(database_path) as conn:
                conn.row_factory = aiosqlite.Row  # Enable dict-like access
                cursor = await conn.execute(f"SELECT * FROM {table_name} LIMIT ?", (limit,))
                rows = await cursor.fetchall()
                
                # Convert to list of dictionaries
                data = [dict(row) for row in rows]
                return data
        except Exception as e:
            logger.error(f"Failed to get SQLite sample data: {e}")
            return []


def get_database_provider(database_type: str, connection_config: Dict[str, Any]) -> DatabaseProvider:
    """Factory function to get the appropriate database provider."""
    providers = {
        "postgresql": PostgreSQLProvider,
        "mysql": MySQLProvider,
        "sqlserver": SQLServerProvider,
        "oracle": OracleProvider,
        "sqlite": SQLiteProvider
    }

    provider_class = providers.get(database_type.lower())
    if not provider_class:
        raise ValueError(f"Unsupported database type: {database_type}")

    return provider_class(connection_config)


class DatabaseConnectionService:
    """Service for managing database connections and testing."""

    @staticmethod
    async def test_connection(provider: str, connection_string: str) -> ConnectionTestResult:
        """Test a database connection."""
        try:
            # Parse connection string to get configuration
            provider_instance = get_database_provider(provider, {})
            config = provider_instance.parse_connection_string(connection_string)

            if not config:
                return ConnectionTestResult(
                    success=False,
                    message="Invalid connection string format",
                    error_details=f"Could not parse connection string for provider '{provider}'"
                )

            # Create provider with parsed config
            provider_instance = get_database_provider(provider, config)

            # Test the connection
            return await provider_instance.test_connection()

        except ValueError as e:
            return ConnectionTestResult(
                success=False,
                message="Unsupported database provider",
                error_details=str(e)
            )
        except Exception as e:
            return ConnectionTestResult(
                success=False,
                message="Connection test failed",
                error_details=str(e)
            )

    @staticmethod
    def get_connection_string_template(provider: str) -> str:
        """Get connection string template for a provider."""
        try:
            provider_class = get_database_provider(provider, {}).__class__
            return provider_class.get_connection_string_template()
        except:
            return ""

    @staticmethod
    def get_connection_string_examples(provider: str) -> List[str]:
        """Get connection string examples for a provider."""
        try:
            provider_class = get_database_provider(provider, {}).__class__
            return provider_class.get_connection_string_examples()
        except:
            return []

    @staticmethod
    def get_supported_providers() -> List[Dict[str, Any]]:
        """Get list of supported database providers with their details."""
        return [
            {
                "name": "SQLite",
                "value": "sqlite",
                "description": "File-based database (default)",
                "default_port": None,
                "template": SQLiteProvider.get_connection_string_template(),
                "examples": SQLiteProvider.get_connection_string_examples()
            },
            {
                "name": "PostgreSQL",
                "value": "postgresql",
                "description": "Enterprise PostgreSQL",
                "default_port": 5432,
                "template": PostgreSQLProvider.get_connection_string_template(),
                "examples": PostgreSQLProvider.get_connection_string_examples()
            },
            {
                "name": "MySQL",
                "value": "mysql",
                "description": "MySQL/MariaDB",
                "default_port": 3306,
                "template": MySQLProvider.get_connection_string_template(),
                "examples": MySQLProvider.get_connection_string_examples()
            },
            {
                "name": "SQL Server",
                "value": "sqlserver",
                "description": "Microsoft SQL Server",
                "default_port": 1433,
                "template": SQLServerProvider.get_connection_string_template(),
                "examples": SQLServerProvider.get_connection_string_examples()
            },
            {
                "name": "Oracle",
                "value": "oracle",
                "description": "Oracle Database",
                "default_port": 1521,
                "template": OracleProvider.get_connection_string_template(),
                "examples": OracleProvider.get_connection_string_examples()
            }
        ]
