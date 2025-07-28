# Database Connection Setup Guide

## 📋 Overview

This guide provides comprehensive information on setting up database connections in the AI Agent Platform with enhanced provider support, connection string formats, and testing capabilities.

## 🔌 Supported Database Providers

The system supports 5 main database providers with comprehensive connection string formats and automatic testing:

### 1. SQLite - File-based Database (Default)
- **Use Case**: Development, small applications, local storage
- **Default Port**: None (file-based)
- **Driver**: aiosqlite

**Connection String Formats:**
```bash
# File path format
Data Source=C:\path\to\database.sqlite;

# Relative path
Data Source=./data/database.sqlite;

# Memory database
Data Source=:memory:;

# SQLAlchemy URL format
sqlite:///./data/database.db
```

**Configuration Parameters:**
- `database`: Path to SQLite database file (required)

### 2. PostgreSQL - Enterprise Database
- **Use Case**: Production applications, complex queries, ACID compliance
- **Default Port**: 5432
- **Driver**: asyncpg

**Connection String Formats:**
```bash
# Standard PostgreSQL URL format
postgresql://username:password@host:port/database

# Semicolon-separated format
Host=localhost;Port=5432;Database=mydb;Username=user;Password=password;

# With SSL
Host=localhost;Port=5432;Database=mydb;Username=user;Password=password;sslmode=require;
```

**Configuration Parameters:**
- `host`: Database server hostname (required)
- `port`: Database server port (default: 5432)
- `database`: Database name (required)
- `username`: Database username (required)
- `password`: Database password (required)
- `sslmode`: SSL mode (optional: disable, allow, prefer, require)

### 3. MySQL - Popular Relational Database
- **Use Case**: Web applications, content management, e-commerce
- **Default Port**: 3306
- **Driver**: aiomysql

**Connection String Formats:**
```bash
# Standard MySQL URL format
mysql://username:password@host:port/database

# Semicolon-separated format
Server=localhost;Database=mydb;Uid=user;Pwd=password;

# With port specification
Server=localhost;Port=3306;Database=mydb;Uid=user;Pwd=password;

# With SSL
Server=localhost;Database=mydb;Uid=user;Pwd=password;SslMode=Required;
```

**Configuration Parameters:**
- `host`: Database server hostname (required)
- `port`: Database server port (default: 3306)
- `database`: Database name (required)
- `username`: Database username (required)
- `password`: Database password (required)

### 4. SQL Server - Microsoft Database
- **Use Case**: Enterprise applications, Windows environments, .NET applications
- **Default Port**: 1433
- **Driver**: pyodbc with ODBC drivers

**Connection String Formats:**
```bash
# Standard SQL Server format
Server=localhost;Database=mydb;User Id=sa;Password=password;

# With instance
Server=localhost\SQLEXPRESS;Database=mydb;User Id=sa;Password=password;

# With Windows Authentication
Server=localhost;Database=mydb;Integrated Security=true;

# With driver specification
Driver={ODBC Driver 17 for SQL Server};Server=localhost;Database=mydb;Uid=sa;Pwd=password;
```

**Configuration Parameters:**
- `host`: SQL Server hostname (required)
- `port`: SQL Server port (default: 1433)
- `database`: Database name (required)
- `username`: SQL Server username (required)
- `password`: SQL Server password (required)

**Auto-Driver Detection:**
The system automatically detects and uses the best available ODBC driver:
1. ODBC Driver 17 for SQL Server (preferred)
2. ODBC Driver 13 for SQL Server
3. ODBC Driver 11 for SQL Server
4. SQL Server Native Client 11.0
5. SQL Server Native Client 10.0
6. SQL Server (fallback)

### 5. Oracle - Enterprise Database
- **Use Case**: Large enterprise applications, complex transactions, high performance
- **Default Port**: 1521
- **Driver**: cx_oracle (not currently installed)

**Connection String Formats:**
```bash
# Oracle URL format
oracle+cx_oracle://username:password@host:port/database

# Service name format
oracle+cx_oracle://system:password@localhost:1521/xe
```

**Configuration Parameters:**
- `host`: Oracle server hostname (required)
- `port`: Oracle server port (default: 1521)
- `database`: Oracle service name (required)
- `username`: Oracle username (required)
- `password`: Oracle password (required)

## 🔧 Enhanced Features

### Connection Testing
- **Real-time Testing**: Test connections before saving
- **Response Time Tracking**: Monitor connection performance
- **Detailed Error Messages**: Specific error diagnosis
- **Auto-retry Logic**: Intelligent retry mechanisms

### Connection String Parsing
- **Multiple Formats**: Support for URL and semicolon-separated formats
- **Parameter Validation**: Automatic validation of connection parameters
- **Template Generation**: Dynamic template generation for each provider

### Provider Detection
- **Auto-detection**: Automatic detection of available database drivers
- **Fallback Support**: Graceful fallback to alternative drivers
- **Compatibility Checking**: Driver compatibility verification

## 📚 API Endpoints

### Get Supported Providers
```http
GET /api/v1/database/providers
```

### Get Connection String Template
```http
GET /api/v1/database/providers/{provider}/template
```

### Test Connection String
```http
POST /api/v1/database/connections/test-string
```

### Create Connection
```http
POST /api/v1/database/connections
```

### Test Existing Connection
```http
POST /api/v1/database/connections/{id}/test
```

## 🛠️ Frontend Integration

### Provider Selection
- Dynamic provider list from API
- Provider descriptions and default ports
- Connection string examples
- Template display

### Connection Builder
- Assisted configuration mode
- Manual connection string mode
- Real-time validation
- Connection testing

### Enhanced UI Features
- Connection string examples
- Template suggestions
- Error handling
- Progress indicators

## 🔒 Security Considerations

### Connection String Encryption
- TODO: Implement proper encryption for stored connection strings
- Currently using placeholder encryption functions
- Production deployment requires proper encryption implementation

### Password Handling
- Passwords are not displayed in logs
- Secure transmission over HTTPS
- Encrypted storage in database

## 📝 Best Practices

### Connection Configuration
1. Always test connections before saving
2. Use SSL/TLS when available
3. Configure appropriate timeouts
4. Use least-privilege database users

### Error Handling
1. Provide specific error messages
2. Log connection attempts for debugging
3. Implement retry logic for transient failures
4. Monitor connection health

### Performance
1. Use connection pooling
2. Monitor response times
3. Set appropriate timeouts
4. Cache connection metadata

## 🚀 Future Enhancements

### Planned Features
- Connection pooling configuration
- Advanced SSL/TLS options
- Connection health monitoring
- Backup and restore functionality
- Multi-tenant connection isolation

### Driver Support
- Additional database providers
- Cloud database services
- NoSQL database support
- Time-series databases

## 📞 Support

For issues with database connections:
1. Check connection string format
2. Verify database server accessibility
3. Confirm driver installation
4. Review error logs
5. Test with minimal configuration

## 🔄 Migration Guide

### From Previous Version
1. Existing connections will be automatically migrated
2. Connection strings will be validated and updated
3. New testing features will be available
4. Enhanced error reporting will be enabled

### Breaking Changes
- Connection string format validation is now stricter
- Some legacy connection formats may need updating
- New required fields for connection metadata
