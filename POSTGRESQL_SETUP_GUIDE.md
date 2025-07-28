# PostgreSQL Setup Guide for AI Agent Platform

This guide will help you set up PostgreSQL for the AI Agent Platform with multi-tenant support.

## 🐘 PostgreSQL Installation

### Windows (Recommended)

1. **Download PostgreSQL**:
   - Go to https://www.postgresql.org/download/windows/
   - Download PostgreSQL 15 or later
   - Run the installer

2. **Installation Settings**:
   - Port: `5432` (default)
   - Username: `postgres`
   - Password: Choose a secure password (remember this!)
   - Database: `postgres` (default)

3. **Verify Installation**:
   ```cmd
   psql --version
   ```

### Alternative: Docker PostgreSQL

If you prefer Docker:

```bash
# Run PostgreSQL in Docker
docker run --name ai-agent-postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=ai_agent_platform \
  -p 5432:5432 \
  -d postgres:15

# Verify it's running
docker ps
```

## 🔧 Configuration

### 1. Create Environment File

Copy the PostgreSQL environment configuration:

```bash
# Copy the PostgreSQL environment template
cp .env.postgresql .env
```

### 2. Update Database Credentials

Edit `.env` file and update the PostgreSQL connection:

```env
# Update with your PostgreSQL credentials
DATABASE_URL=postgresql+asyncpg://postgres:YOUR_PASSWORD@localhost:5432/ai_agent_platform
```

Replace `YOUR_PASSWORD` with the password you set during PostgreSQL installation.

### 3. Create Database

Connect to PostgreSQL and create the database:

```sql
-- Connect to PostgreSQL as postgres user
psql -U postgres -h localhost

-- Create the database
CREATE DATABASE ai_agent_platform;

-- Create a dedicated user (optional but recommended)
CREATE USER ai_agent_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_agent_platform TO ai_agent_user;

-- Exit psql
\q
```

## 🚀 Setup and Migration

### 1. Run PostgreSQL Setup Script

The setup script will:
- Create database tables with PostgreSQL optimizations
- Set up Row-Level Security for multi-tenancy
- Create a default tenant
- Migrate existing SQLite data (if any)

```bash
# Run the setup script
python setup_postgresql.py
```

### 2. Verify Setup

Check that everything is working:

```bash
# Test database connection
python -c "
import asyncio
from src.core.database import test_connection
print('Connection successful!' if asyncio.run(test_connection()) else 'Connection failed!')
"
```

## 🏢 Multi-Tenant Features

### PostgreSQL Enhancements

1. **Row-Level Security (RLS)**:
   - Automatic tenant isolation at database level
   - Prevents cross-tenant data access
   - Enforced by PostgreSQL engine

2. **UUID Primary Keys**:
   - Better security and distribution
   - Prevents ID enumeration attacks
   - Suitable for multi-tenant environments

3. **JSONB Support**:
   - Flexible tenant settings and metadata
   - Efficient querying and indexing
   - Schema evolution without migrations

4. **Advanced Indexing**:
   - Composite indexes for tenant-aware queries
   - Partial indexes for active records
   - GIN indexes for JSONB and array columns

### Tenant Isolation

```sql
-- Example: All queries automatically filtered by tenant
SELECT * FROM agents WHERE name = 'My Agent';
-- Automatically becomes:
-- SELECT * FROM agents WHERE tenant_id = current_tenant_id AND name = 'My Agent';
```

## 🔒 Security Features

### Row-Level Security Policies

```sql
-- Users can only see their tenant's data
CREATE POLICY tenant_isolation_users ON users
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Agents are isolated by tenant
CREATE POLICY tenant_isolation_agents ON agents
    USING (tenant_id = current_setting('app.current_tenant_id')::uuid);
```

### Connection Security

```env
# Enable SSL in production
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?ssl=require

# Connection pooling for performance
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30
```

## 📊 Performance Optimizations

### Indexing Strategy

```sql
-- Tenant-aware composite indexes
CREATE INDEX idx_users_tenant_email ON users(tenant_id, email);
CREATE INDEX idx_agents_tenant_type ON agents(tenant_id, agent_type);

-- Partial indexes for active records
CREATE INDEX idx_agents_active ON agents(tenant_id) WHERE is_active = true;

-- JSONB indexes for settings
CREATE INDEX idx_tenant_settings ON tenants USING GIN (settings);
```

### Query Optimization

```python
# Efficient tenant-aware queries
async def get_user_agents(db: AsyncSession, tenant_id: UUID, user_id: int):
    result = await db.execute(
        select(Agent)
        .where(
            Agent.tenant_id == tenant_id,
            Agent.owner_id == user_id,
            Agent.is_active == True
        )
        .options(selectinload(Agent.tools))
        .order_by(Agent.created_at.desc())
    )
    return result.scalars().all()
```

## 🔄 Migration from SQLite

The setup script automatically handles migration:

1. **Data Export**: Reads all tables from SQLite
2. **Schema Conversion**: Converts SQLite types to PostgreSQL
3. **Tenant Assignment**: Assigns all existing data to default tenant
4. **Relationship Preservation**: Maintains foreign key relationships

### Manual Migration (if needed)

```bash
# Export SQLite data
sqlite3 ai_agent_platform.db .dump > sqlite_dump.sql

# Import to PostgreSQL (after manual conversion)
psql -U postgres -d ai_agent_platform -f converted_dump.sql
```

## 🧪 Testing

### Test Multi-Tenant Isolation

```python
# Test script to verify tenant isolation
import asyncio
from src.core.database import tenant_context, AsyncSessionLocal
from src.models.agent import Agent

async def test_tenant_isolation():
    async with AsyncSessionLocal() as db:
        # Set tenant context
        with tenant_context("tenant-1-uuid"):
            agents_t1 = await db.execute(select(Agent))
            print(f"Tenant 1 agents: {len(agents_t1.scalars().all())}")
        
        with tenant_context("tenant-2-uuid"):
            agents_t2 = await db.execute(select(Agent))
            print(f"Tenant 2 agents: {len(agents_t2.scalars().all())}")

asyncio.run(test_tenant_isolation())
```

## 🚨 Troubleshooting

### Common Issues

1. **Connection Refused**:
   ```bash
   # Check if PostgreSQL is running
   pg_ctl status
   # Or on Windows:
   net start postgresql-x64-15
   ```

2. **Authentication Failed**:
   - Verify username/password in `.env`
   - Check `pg_hba.conf` for authentication settings

3. **Database Does Not Exist**:
   ```sql
   -- Create database manually
   CREATE DATABASE ai_agent_platform;
   ```

4. **Permission Denied**:
   ```sql
   -- Grant permissions
   GRANT ALL PRIVILEGES ON DATABASE ai_agent_platform TO your_user;
   ```

### Logs and Debugging

```bash
# Enable database query logging
export DATABASE_ECHO=true

# Check PostgreSQL logs
tail -f /var/log/postgresql/postgresql-15-main.log
```

## 🎯 Next Steps

After PostgreSQL setup:

1. **Start the Application**:
   ```bash
   python main.py
   ```

2. **Create Additional Tenants**:
   - Use the admin interface
   - Or API endpoints for tenant management

3. **Configure Multi-Tenant Features**:
   - Set up tenant-specific settings
   - Configure user invitations
   - Enable tenant isolation features

## 📚 Additional Resources

- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Row-Level Security Guide](https://www.postgresql.org/docs/current/ddl-rowsecurity.html)
- [JSONB Performance Tips](https://www.postgresql.org/docs/current/datatype-json.html)
- [Multi-Tenant Architecture Patterns](https://docs.microsoft.com/en-us/azure/sql-database/saas-tenancy-app-design-patterns)
