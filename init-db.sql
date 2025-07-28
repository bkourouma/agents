-- AI Agent Platform - Database Initialization Script
-- This script sets up the PostgreSQL database with required extensions and initial configuration

-- Enable required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Enable vector extension if available (for future vector similarity search)
-- CREATE EXTENSION IF NOT EXISTS "vector";

-- Create database user if not exists (for manual setup)
-- Note: In Docker, this is handled by environment variables
-- DO $$ 
-- BEGIN
--     IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'ai_agents_user') THEN
--         CREATE USER ai_agents_user WITH PASSWORD 'secure_password';
--     END IF;
-- END
-- $$;

-- Grant necessary permissions
-- GRANT ALL PRIVILEGES ON DATABASE ai_agents_db TO ai_agents_user;
-- GRANT ALL PRIVILEGES ON SCHEMA public TO ai_agents_user;

-- Set default search path
-- ALTER USER ai_agents_user SET search_path TO public;

-- Configure PostgreSQL for better performance
ALTER SYSTEM SET shared_preload_libraries = 'pg_stat_statements';
ALTER SYSTEM SET max_connections = 200;
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';
ALTER SYSTEM SET default_statistics_target = 100;
ALTER SYSTEM SET random_page_cost = 1.1;
ALTER SYSTEM SET effective_io_concurrency = 200;

-- Create a function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create initial database schema will be handled by SQLAlchemy/Alembic
-- This script only sets up the database environment

-- Log successful initialization
DO $$
BEGIN
    RAISE NOTICE 'AI Agent Platform database initialization completed successfully';
END
$$;
