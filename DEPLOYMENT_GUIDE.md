# AI Agent Platform - Complete Deployment Guide

## 🎯 Application Overview

**AI Agent Platform** is a comprehensive conversational AI platform where business users create specialized AI agents with tools, and an intelligent orchestrator routes user questions to the appropriate agents. The application consists of a FastAPI backend and a React frontend, designed for enterprise deployment.

### Core Features
- **Multi-Agent System** - Specialized AI agents for different domains (Financial, Research, Customer Service)
- **Intelligent Orchestrator** - Intent analysis and smart routing to appropriate agents
- **Tool Integration Framework** - Database connections, APIs, file processing, web search
- **Knowledge Base & RAG** - Document upload, processing, and intelligent querying
- **Database Chat** - Natural language to SQL conversion using Vanna AI
- **Multi-tenant Support** - Isolated environments for different organizations
- **WhatsApp Integration** - Messaging capability for user interactions
- **Admin Dashboard** - User management and system monitoring
- **Authentication & Security** - JWT-based auth with role-based access

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI 0.104.1 with Uvicorn
- **Database**: PostgreSQL (production) / SQLite (development)
- **Caching**: Redis for session management and performance
- **AI/ML**: OpenAI GPT-4, Anthropic Claude, LangChain, ChromaDB, Vanna AI
- **Authentication**: JWT tokens, bcrypt password hashing
- **File Processing**: PyPDF, python-docx, openpyxl for document ingestion

### Frontend (React)
- **Framework**: React 18+ with TypeScript and Vite
- **Styling**: Tailwind CSS
- **State Management**: React Query for API state
- **Build**: Production-optimized with Nginx serving

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Reverse Proxy**: Nginx (for frontend and API routing)
- **Database**: PostgreSQL for production, SQLite for development
- **Caching**: Redis for performance optimization
- **Storage**: Local filesystem (VPS) / Azure Blob Storage (cloud)

## 📁 Project Structure

```
ai_agents/
├── main.py                         # Main FastAPI application
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Backend container config
├── docker-compose.production.yml   # Production deployment
├── docker-compose.yml              # Development deployment
├── .env.example                    # Environment variables template
│
├── src/                            # Source code
│   ├── api/                        # API route modules
│   │   ├── users.py                # User management
│   │   ├── agents.py               # Agent management
│   │   ├── orchestrator.py         # Orchestrator routing
│   │   ├── knowledge_base.py       # Document processing
│   │   ├── database_chat.py        # Database chat (Vanna AI)
│   │   ├── tenants.py              # Multi-tenant management
│   │   ├── insurance.py            # Insurance domain logic
│   │   └── whatsapp.py             # WhatsApp integration
│   ├── core/                       # Core utilities
│   │   ├── database.py             # Database configuration
│   │   ├── auth.py                 # Authentication logic
│   │   └── config.py               # Application configuration
│   ├── models/                     # Data models
│   ├── services/                   # Business logic services
│   └── tools/                      # Tool integration framework
│
├── frontend/                       # React frontend
│   ├── package.json                # Node.js dependencies
│   ├── Dockerfile.production       # Frontend container
│   ├── vite.config.ts              # Vite configuration
│   ├── src/                        # React source code
│   └── public/                     # Static assets
│
├── nginx/                          # Nginx configuration
│   ├── conf.d/                     # Nginx site configs
│   └── ssl/                        # SSL certificates
│
├── data/                           # Application data
│   └── ai_agent_platform.db       # SQLite database (dev)
├── agent_documents/                # Agent-specific documents
├── agent_vectors/                  # Vector database storage
├── vanna_cache/                    # SQL AI cache
└── logs/                           # Application logs
```

## 🔧 Environment Configuration

### Required Environment Variables

```bash
# Core Application
ENVIRONMENT=production
DEBUG=false
PORT=3006
HOST=0.0.0.0
WORKERS=2

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/ai_agents_db
REDIS_URL=redis://localhost:6379/0

# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
OPENAI_MODEL=gpt-4o

# Anthropic Configuration (Optional)
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Security (REQUIRED)
SECRET_KEY=your-super-secret-key-at-least-32-characters-long
JWT_SECRET_KEY=your-jwt-secret-key-at-least-32-characters-long
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# URLs (for production)
FRONTEND_URL=https://your-domain.com
BACKEND_URL=https://your-domain.com/api

# Azure Services (Optional)
AZURE_STORAGE_CONNECTION_STRING=your-azure-storage-connection-string
AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/

# WhatsApp Integration (Optional)
WHATSAPP_ACCESS_TOKEN=your-whatsapp-access-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your-webhook-verify-token
```

## 📦 Dependencies

### Backend Dependencies (requirements.txt)
```
# FastAPI and Web Framework
fastapi==0.104.1
uvicorn[standard]==0.24.0
python-multipart==0.0.6

# Database and ORM
sqlalchemy==2.0.23
alembic==1.12.1
asyncpg==0.29.0
psycopg2-binary==2.9.9
aiosqlite>=0.19.0

# Redis and Caching
redis==5.0.1
aioredis==2.0.1

# Authentication and Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4

# AI and LLM Integration
openai>=1.0.0,<2.0.0
anthropic>=0.7.0
langchain>=0.1.0,<0.2.0
langchain-openai>=0.0.5,<0.2.0
langchain-anthropic>=0.0.1
langchain-chroma>=0.1.0,<0.2.0
chromadb>=0.4.0,<0.5.0

# Vanna AI and Database Chat
vanna[chromadb,openai]>=0.7.0
xlsxwriter>=3.1.0
pyodbc>=4.0.0

# File Processing
python-docx==1.1.0
PyPDF2==3.0.1
pypdf>=3.0.0,<4.0.0
openpyxl==3.1.2
pandas==2.1.4

# Azure Services
azure-storage-blob==12.19.0
azure-identity==1.15.0
azure-keyvault-secrets==4.7.0

# HTTP Client and API Integration
httpx==0.25.2
aiohttp==3.9.1

# Environment and Configuration
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
```

### Frontend Dependencies (package.json)
```json
{
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "@headlessui/react": "^2.2.4",
    "@heroicons/react": "^2.2.0",
    "@tailwindcss/forms": "^0.5.10",
    "@tanstack/react-query": "^5.82.0",
    "axios": "^1.10.0",
    "clsx": "^2.1.1",
    "lucide-react": "^0.525.0",
    "react-hot-toast": "^2.5.2",
    "react-markdown": "^10.1.0",
    "react-router-dom": "^7.6.3",
    "tailwindcss": "^3.4.17"
  },
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "preview": "vite preview"
  }
}
```

## 🚀 Deployment Methods

### Method 1: VPS Deployment (Recommended)

#### Prerequisites
- Ubuntu 20.04+ VPS with 4GB+ RAM
- Docker & Docker Compose installed
- Domain name with SSL certificate
- PostgreSQL and Redis installed (or use Docker containers)

#### Deployment Steps
```bash
# 1. Clone/upload application
git clone <repository> /opt/ai-agents
cd /opt/ai-agents

# 2. Configure environment
cp .env.example .env
nano .env  # Edit with your values

# 3. Build and deploy
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d

# 4. Verify deployment
docker-compose -f docker-compose.production.yml ps
curl http://localhost:3006/health
```

### Method 2: Azure App Service

#### Prerequisites
- Azure subscription
- Azure CLI installed
- Azure Database for PostgreSQL
- Azure Cache for Redis

#### Deployment Steps
```bash
# 1. Create Azure resources
az group create --name ai-agents-rg --location eastus
az appservice plan create --name ai-agents-plan --resource-group ai-agents-rg --sku B2
az webapp create --name ai-agents-app --resource-group ai-agents-rg --plan ai-agents-plan

# 2. Configure app settings
az webapp config appsettings set --name ai-agents-app --resource-group ai-agents-rg \
  --settings OPENAI_API_KEY="your-key" SECRET_KEY="your-secret"

# 3. Deploy code
az webapp deployment source config-zip --name ai-agents-app \
  --resource-group ai-agents-rg --src ai-agents.zip
```

## 🗄️ Database Setup

### PostgreSQL (Production)
```sql
-- Create database and user
CREATE DATABASE ai_agents_db;
CREATE USER ai_agents_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE ai_agents_db TO ai_agents_user;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";  -- For vector similarity search
```

### SQLite (Development)
```python
# Database initialization (automatic on startup)
from src.core.database import create_tables
await create_tables()  # Creates all required tables
```

## 🔐 Security Configuration

### SSL/TLS Setup
```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/nginx/ssl/certificate.crt;
    ssl_certificate_key /etc/nginx/ssl/private.key;
    
    # Backend API
    location /api/ {
        proxy_pass http://localhost:3006/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Frontend
    location / {
        proxy_pass http://localhost:3003/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Authentication Flow
1. **User Registration**: POST `/api/users/register`
2. **Login**: POST `/api/users/login` → Returns JWT token
3. **Protected Routes**: Include `Authorization: Bearer <token>` header
4. **Multi-tenant**: Tenant isolation via JWT claims and RLS policies

## 📊 Monitoring & Maintenance

### Health Checks
- **Backend**: `GET /health` - Returns system status
- **Database**: Connection and table verification
- **AI Services**: OpenAI/Anthropic API connectivity
- **Redis**: Cache connectivity and performance
- **Storage**: Disk space and file permissions

### Log Management
```bash
# View application logs
docker-compose -f docker-compose.production.yml logs -f

# Backend logs
docker-compose -f docker-compose.production.yml logs ai-agents-backend

# Frontend logs
docker-compose -f docker-compose.production.yml logs ai-agents-frontend
```

### Backup Strategy
```bash
# Database backup (PostgreSQL)
pg_dump -h localhost -U ai_agents_user ai_agents_db > backup_$(date +%Y%m%d).sql

# Document backup
tar -czf /backup/documents_$(date +%Y%m%d).tar.gz agent_documents/ agent_vectors/

# Configuration backup
cp .env /backup/env_$(date +%Y%m%d).backup
```

## 🧪 Testing & Validation

### API Testing
```bash
# Health check
curl https://your-domain.com/api/health

# Authentication test
curl -X POST https://your-domain.com/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"alicepassword123"}'

# Agent interaction test
curl -X POST https://your-domain.com/api/orchestrator/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello, I need help with financial analysis","tenant_id":"default"}'
```

### Frontend Testing
- Access: `https://your-domain.com`
- Login with demo credentials (alice/alicepassword123)
- Test agent creation and configuration
- Upload and query documents in knowledge base
- Test database chat functionality
- Verify multi-tenant isolation

## 🚨 Troubleshooting

### Common Issues

1. **OpenAI/Anthropic API Errors**
   - Verify API keys are correct and have credits
   - Check rate limits and usage quotas

2. **Database Connection Issues**
   - Ensure PostgreSQL is running and accessible
   - Verify connection string format and credentials

3. **Redis Connection Issues**
   - Check Redis server status
   - Verify Redis URL configuration

4. **Docker Build Failures**
   - Check system resources (RAM/disk space)
   - Verify all required files are present

5. **Frontend Not Loading**
   - Check Nginx configuration
   - Verify React build completed successfully
   - Check API proxy configuration

### Performance Optimization
- Enable Redis caching for frequent queries
- Implement database connection pooling
- Use CDN for static assets
- Configure proper logging levels
- Optimize vector database queries

## 📞 Support & Maintenance

### Regular Maintenance Tasks
- Monitor disk space and clean old logs
- Update dependencies monthly
- Backup database weekly
- Review security logs
- Test disaster recovery procedures

### Scaling Considerations
- Horizontal scaling with load balancer
- Database read replicas for performance
- Implement Redis Cluster for high availability
- Use cloud storage for documents and vectors
- Set up monitoring with Prometheus/Grafana

## 🔄 Development Workflow

### Local Development Setup
```bash
# Windows (using setup-development.bat)
setup-development.bat

# Linux/macOS (using setup-development.sh)
./setup-development.sh

# Manual setup
# Backend (Terminal 1)
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate.bat  # Windows
python main.py

# Frontend (Terminal 2)
cd frontend
npm run dev
```

### Development Ports
- **Backend API**: http://localhost:3006
- **Frontend**: http://localhost:3003
- **API Documentation**: http://localhost:3006/docs
- **PostgreSQL**: localhost:5432 (if using PostgreSQL)
- **Redis**: localhost:6379 (if using Redis)

### Code Structure Details

#### Main Application (main.py)
```python
# Core FastAPI app with all routers
from src.api.users import router as users_router
from src.api.agents import router as agents_router
from src.api.orchestrator import router as orchestrator_router
from src.api.knowledge_base import router as knowledge_base_router
from src.api.database_chat import router as database_chat_router
from src.api.tenants import router as tenants_router
from src.api.insurance import router as insurance_router
from src.api.whatsapp import router as whatsapp_router
```

#### Database Models
- **Users**: Authentication and user management
- **Tenants**: Multi-tenant isolation
- **Agents**: AI agent configurations and tools
- **Orchestrator**: Intent analysis and routing logic
- **Knowledge Base**: Document storage and vector embeddings
- **Database Chat**: SQL database connections and Vanna AI integration
- **Insurance**: Domain-specific insurance logic

#### API Endpoints Structure
```
/api/
├── /users/          # User management (register, login, profile)
├── /agents/         # Agent creation and management
├── /orchestrator/   # Intent analysis and routing
├── /knowledge_base/ # Document upload and RAG queries
├── /database_chat/  # Natural language to SQL
├── /tenants/        # Multi-tenant configuration
├── /insurance/      # Insurance domain endpoints
├── /whatsapp/       # WhatsApp integration
└── /health          # System health check
```

## 🎯 Key Features Implementation

### 1. Multi-Agent System
- **Agent Creation**: Visual interface for business users
- **Tool Assignment**: Database connections, APIs, file access
- **Orchestrator Routing**: Intelligent request routing to appropriate agents
- **Context Management**: Conversation state across agent interactions

### 2. Knowledge Base & RAG
- **Document Upload**: PDF, Word, Excel file processing
- **Vector Storage**: ChromaDB for semantic search
- **Chunking Strategy**: Intelligent document segmentation
- **Retrieval**: Context-aware document querying

### 3. Database Chat (Vanna AI)
- **Schema Learning**: Automatic database schema analysis
- **Query Generation**: Natural language to SQL conversion
- **Multi-Database**: PostgreSQL, MySQL, SQL Server support
- **Training**: Custom training data for domain-specific queries

### 4. Multi-Tenant Architecture
- **Isolation**: Row-level security for data separation
- **Customization**: Tenant-specific configurations
- **Scaling**: Horizontal scaling support
- **Security**: JWT-based tenant identification

### 5. WhatsApp Integration
- **Webhook**: Message receiving and processing
- **Business API**: WhatsApp Business API integration
- **Agent Routing**: Route WhatsApp messages to appropriate agents
- **Response Formatting**: Format agent responses for WhatsApp

## 🔧 Advanced Configuration

### Environment-Specific Settings

#### Development (.env)
```bash
ENVIRONMENT=development
DEBUG=true
DATABASE_URL=sqlite:///./ai_agent_platform.db
REDIS_URL=redis://localhost:6379/0
CORS_ORIGINS=["http://localhost:3003"]
```

#### Production (.env.production)
```bash
ENVIRONMENT=production
DEBUG=false
DATABASE_URL=postgresql://user:pass@localhost:5432/ai_agents_db
REDIS_URL=redis://:password@localhost:6379/0
CORS_ORIGINS=["https://your-domain.com"]
```

#### Azure Cloud (.env.azure)
```bash
ENVIRONMENT=production
DATABASE_URL=postgresql://user@server:pass@server.postgres.database.azure.com/db
REDIS_URL=rediss://:pass@cache.redis.cache.windows.net:6380/0
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
```

### Docker Compose Configurations

#### Development (docker-compose.yml)
```yaml
version: "3.8"
services:
  ai-agents-backend-dev:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "3006:3006"
    volumes:
      - .:/app  # Mount source for hot reload
    command: ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "3006", "--reload"]
```

#### Production (docker-compose.production.yml)
```yaml
services:
  ai-agents-backend:
    build: .
    ports:
      - "3006:3006"
    environment:
      ENVIRONMENT: production
      WORKERS: 4
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
```

### Nginx Reverse Proxy Configuration
```nginx
upstream backend {
    server ai-agents-backend:3006;
}

upstream frontend {
    server ai-agents-frontend:80;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/certificate.crt;
    ssl_certificate_key /etc/nginx/ssl/private.key;

    # Backend API
    location /api/ {
        proxy_pass http://backend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Frontend
    location / {
        proxy_pass http://frontend/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📈 Performance & Scaling

### Database Optimization
```sql
-- PostgreSQL optimizations for production
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '1GB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET max_connections = 200;
```

### Caching Strategy
- **Application Cache**: Redis for session management
- **Vector Cache**: ChromaDB persistence for document embeddings
- **SQL Cache**: Vanna AI query result caching
- **Static Assets**: CDN or Nginx caching for frontend assets

### Monitoring Setup
```yaml
# docker-compose.monitoring.yml
version: "3.8"
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
```

## 🔒 Security Best Practices

### API Security
- **Rate Limiting**: Implement request rate limiting
- **Input Validation**: Strict input validation and sanitization
- **SQL Injection**: Use parameterized queries only
- **CORS**: Configure appropriate CORS policies
- **HTTPS**: Enforce HTTPS in production

### Authentication Security
```python
# JWT token configuration
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24
JWT_REFRESH_EXPIRATION_DAYS = 30

# Password hashing
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

### Environment Security
- **Secrets Management**: Use environment variables or Azure Key Vault
- **File Permissions**: Restrict access to configuration files
- **Container Security**: Run containers as non-root users
- **Network Security**: Use private networks for internal communication

## 🚀 Deployment Automation

### CI/CD Pipeline (GitHub Actions)
```yaml
name: Deploy AI Agent Platform
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Deploy to VPS
        uses: appleboy/ssh-action@v0.1.5
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            cd /opt/ai-agents
            git pull origin main
            ./deploy-production.sh
```

### Backup Automation
```bash
#!/bin/bash
# backup-script.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/ai-agents"

# Database backup
pg_dump -h localhost -U ai_agents_user ai_agents_db > $BACKUP_DIR/db_$DATE.sql

# Documents backup
tar -czf $BACKUP_DIR/documents_$DATE.tar.gz agent_documents/ agent_vectors/

# Configuration backup
cp .env $BACKUP_DIR/env_$DATE.backup

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.sql" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.backup" -mtime +30 -delete
```

## 📋 Quick Start Commands

### Development
```bash
# Setup development environment
./setup-development.sh  # Linux/macOS
setup-development.bat   # Windows

# Start with Docker
docker-compose up

# Start manually
source venv/bin/activate && python main.py  # Backend
cd frontend && npm run dev                   # Frontend
```

### Production
```bash
# Deploy to production
./deploy-production.sh  # Linux/macOS
deploy-production.bat   # Windows

# Manual Docker deployment
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps
```

### Maintenance
```bash
# View logs
docker-compose -f docker-compose.production.yml logs -f

# Backup
./deploy-production.sh backup

# Health check
curl http://localhost:3006/health

# Update deployment
git pull && ./deploy-production.sh
```

---

**Note**: This comprehensive guide covers all aspects of AI Agent Platform deployment. Ensure proper security measures are in place and test thoroughly before production deployment. For additional support, refer to the individual component documentation in the respective directories.
