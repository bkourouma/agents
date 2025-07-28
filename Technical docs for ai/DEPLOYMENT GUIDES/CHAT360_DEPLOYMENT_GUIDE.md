# Chat360 Application - Complete Deployment Guide

## 🎯 Application Overview

**Chat360** is a comprehensive AI-powered chat platform with multi-tenant support, document processing, database querying, and voice assistant capabilities. The application consists of a FastAPI backend and a React frontend, designed for enterprise deployment.

### Core Features
- **Multi-tenant Chat System** - Isolated environments for different organizations
- **Document Processing & RAG** - PDF upload, processing, and intelligent querying
- **🆕 Optimized RAG System** - QA-based chunking for complete responses
- **Database Chat** - Natural language to SQL conversion using Vanna AI
- **Voice Assistant** - Twilio-integrated voice interactions
- **Admin Dashboard** - User management and system monitoring
- **Authentication & Security** - JWT-based auth with role-based access

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI 0.104.1 with Uvicorn
- **Database**: SQLite (production) / PostgreSQL (enterprise)
- **AI/ML**: OpenAI GPT-4, Langchain, ChromaDB, Vanna AI
- **Authentication**: JWT tokens, bcrypt password hashing
- **File Processing**: PyPDF for document ingestion

### Frontend (React)
- **Framework**: React 18.2.0 with Create React App
- **Styling**: Tailwind CSS
- **Build**: Production-optimized with Nginx serving

### Infrastructure
- **Containerization**: Docker & Docker Compose
- **Reverse Proxy**: Nginx (for frontend)
- **Database**: SQLite for VPS, PostgreSQL for Azure
- **Storage**: Local filesystem (VPS) / Azure Blob Storage (cloud)

## 📁 Project Structure

```
chat360/
├── app.py                          # Main FastAPI application
├── requirements.txt                # Python dependencies
├── Dockerfile                      # Backend container config
├── docker-compose.production.yml   # Production deployment
├── start-dev.bat                   # Development startup script
├── .env                           # Environment variables
│
├── api/                           # API route modules
│   ├── users.py                   # User management
│   ├── chat.py                    # Chat endpoints
│   ├── documents.py               # Document processing
│   ├── database.py                # Database chat
│   ├── tenants.py                 # Multi-tenant management
│   ├── conversations.py           # Chat history
│   └── admin.py                   # Admin interface
│
├── dashboardapp/                  # React frontend
│   ├── package.json               # Node.js dependencies
│   ├── Dockerfile.production      # Frontend container
│   ├── nginx.conf                 # Nginx configuration
│   ├── src/                       # React source code
│   └── public/                    # Static assets
│
├── chat_assistant/                # Enhanced chat system
│   ├── api/                       # Additional API routes
│   ├── services/                  # Business logic
│   ├── models/                    # Data models
│   └── documents/                 # Document processing
│
├── visitor_chat/                  # 🆕 Optimized RAG system
│   ├── utils/
│   │   ├── qa_chunker.py          # QA-based intelligent chunking
│   │   ├── qa_validator.py        # Quality validation
│   │   └── text_splitter.py       # Legacy text splitting
│   ├── services/
│   │   ├── chat_service.py        # Optimized chat responses
│   │   └── document_service.py    # Enhanced document processing
│   └── config.py                  # RAG configuration
│
├── voice_assistant/               # Twilio voice integration
│   ├── main.py                    # Voice app entry point
│   ├── requirements.txt           # Voice-specific deps
│   └── api/                       # Voice endpoints
│
├── data/                          # Application data
│   └── chatbot.sqlite             # Main database
├── docs/                          # PDF documents for RAG
├── static/                        # Static web files
├── templates/                     # HTML templates
├── chroma_db_data/               # Vector database
├── vanna_cache/                  # SQL AI cache
└── logs/                         # Application logs
```

## 🔧 Environment Configuration

### Required Environment Variables

```bash
# Core Application
ENVIRONMENT=production
DEBUG=false
PORT=8000
HOST=0.0.0.0
WORKERS=2

# OpenAI Configuration (REQUIRED)
OPENAI_API_KEY=sk-proj-your-openai-api-key-here
OPENAI_MODEL=gpt-4o

# Security (REQUIRED)
SECRET_KEY=your-super-secret-key-at-least-32-characters-long
JWT_SECRET_KEY=your-jwt-secret-key-at-least-32-characters-long
ADMIN_PASSWORD=your-secure-admin-password

# Database
DATABASE_URL=sqlite:///app/data/chat360.db
SQLITE_PATH=/app/data/chat360.db

# URLs (for production)
VOICE_BASE_WEBHOOK_URL=https://your-domain.com/api
FRONTEND_URL=https://your-domain.com
BACKEND_URL=https://your-domain.com/api

# Optional: Twilio (Voice Assistant)
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_PHONE_NUMBER=your-twilio-phone-number
```

## 📦 Dependencies

### Backend Dependencies (requirements.txt)
```
# Core Framework
fastapi>=0.100.0,<0.112.0
uvicorn[standard]>=0.20.0,<0.29.0
pydantic>=1.10.0,<3.0.0
python-dotenv>=0.20.0,<1.1.0
python-multipart>=0.0.5,<0.1.0

# AI & Machine Learning
langchain>=0.1.0,<0.2.0
langchain-openai>=0.0.5,<0.2.0
langchain-community>=0.0.20,<0.1.0
langchain-chroma>=0.1.0,<0.2.0
openai>=1.0.0,<2.0.0
tiktoken>=0.4.0

# Document Processing
pypdf>=3.0.0,<4.0.0
chromadb>=0.4.0,<0.5.0

# Database & SQL AI
vanna[chromadb,openai]>=0.7.9
psycopg2-binary>=2.9.0
pymysql>=1.0.0
pyodbc>=4.0.0
pandas>=1.5.0
numpy>=1.21.0

# Authentication & Security
python-jose[cryptography]>=3.3.0,<4.0.0
passlib[bcrypt]>=1.7.4,<2.0.0

# Templates & UI
jinja2>=3.0.0,<4.0.0

# Visualization
plotly>=5.0.0
```

### Frontend Dependencies (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test"
  }
}
```

## 🐳 Docker Configuration

### Backend Dockerfile
```dockerfile
FROM python:3.11-slim AS production

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ curl libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Application code
COPY . .

# Create directories and user
RUN mkdir -p /app/data /app/docs /app/chroma_db /app/templates \
    /app/sqlite_data /app/vanna_cache && \
    adduser --disabled-password --gecos '' --uid 1000 appuser && \
    chown -R appuser:appuser /app

USER appuser

ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV PORT=8000
ENV ENVIRONMENT=production

EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Frontend Dockerfile
```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci --silent
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000
CMD ["nginx", "-g", "daemon off;"]
```

## 🆕 RAG System Optimization

### New Components (v2.1)

The latest version includes an **optimized RAG system** that resolves incomplete response issues:

#### Key Improvements
- **QADelimiterChunker**: Intelligent chunking based on `---QA---` delimiters
- **HybridChunker**: Automatic format detection (QA vs classic)
- **Enhanced Prompts**: Optimized for complete content restitution
- **Quality Validation**: Automated testing and scoring
- **Backward Compatibility**: Existing documents continue to work

#### Performance Gains
- **+100% bullet points** preserved in responses
- **+131% content completeness** (714 → 1653 characters)
- **100/100 quality score** on test documents
- **Automatic format detection** for optimal chunking

#### Deployment Requirements
```bash
# Additional validation scripts
scripts/validate_qa_system.py      # System validation
scripts/demo_qa_improvement.py     # Performance demonstration
tests/test_qa_system.py           # Automated testing

# New configuration (optional)
VISITOR_CHUNK_SIZE=2000           # Fallback chunk size
VISITOR_CHUNK_OVERLAP=400         # Fallback overlap
```

## 🚀 Deployment Methods

### Method 1: VPS Deployment (Recommended)

#### Prerequisites
- Ubuntu 20.04+ VPS with 2GB+ RAM
- Docker & Docker Compose installed
- Domain name with SSL certificate
- Nginx reverse proxy configured

#### Deployment Steps
```bash
# 1. Clone/upload application
git clone <repository> /opt/chat360
cd /opt/chat360

# 2. Configure environment
cp .env.example .env
nano .env  # Edit with your values

# 3. Build and deploy
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d

# 4. Verify deployment
docker-compose -f docker-compose.production.yml ps
curl http://localhost:8811/health
```

### Method 2: Azure App Service

#### Prerequisites
- Azure subscription
- Azure CLI installed
- PostgreSQL database (Azure Database for PostgreSQL)

#### Deployment Steps
```bash
# 1. Create Azure resources
az group create --name chat360-rg --location eastus
az appservice plan create --name chat360-plan --resource-group chat360-rg --sku B1
az webapp create --name chat360-app --resource-group chat360-rg --plan chat360-plan

# 2. Configure app settings
az webapp config appsettings set --name chat360-app --resource-group chat360-rg \
  --settings OPENAI_API_KEY="your-key" SECRET_KEY="your-secret"

# 3. Deploy code
az webapp deployment source config-zip --name chat360-app \
  --resource-group chat360-rg --src chat360.zip
```

## 🗄️ Database Setup

### SQLite (VPS Deployment)
```python
# Database initialization
from db import init_db
init_db()  # Creates all required tables
```

### PostgreSQL (Azure/Enterprise)
```sql
-- Create database
CREATE DATABASE chat360db;
CREATE USER chat360user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE chat360db TO chat360user;

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
```

## 🔐 Security Configuration

### SSL/TLS Setup
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    location /api/ {
        proxy_pass http://localhost:8811/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location / {
        proxy_pass http://localhost:3004/;
        proxy_set_header Host $host;
    }
}
```

### Authentication Flow
1. **User Registration**: POST `/api/users/register`
2. **Login**: POST `/api/users/login` → Returns JWT token
3. **Protected Routes**: Include `Authorization: Bearer <token>` header
4. **Admin Access**: Special admin endpoints with elevated permissions

## 📊 Monitoring & Maintenance

### Health Checks
- **Backend**: `GET /health` - Returns system status
- **Database**: Connection and table verification
- **AI Services**: OpenAI API connectivity
- **Storage**: Disk space and file permissions

### Log Management
```bash
# View application logs
docker-compose -f docker-compose.production.yml logs -f

# Backend logs
docker-compose -f docker-compose.production.yml logs chat360-backend

# Frontend logs
docker-compose -f docker-compose.production.yml logs chat360-frontend
```

### Backup Strategy
```bash
# Database backup
sqlite3 /app/data/chat360.db ".backup /backup/chat360_$(date +%Y%m%d).db"

# Document backup
tar -czf /backup/docs_$(date +%Y%m%d).tar.gz /app/docs/

# Configuration backup
cp /opt/chat360/.env /backup/env_$(date +%Y%m%d).backup
```

## 🧪 Testing & Validation

### API Testing
```bash
# Health check
curl https://your-domain.com/api/health

# Authentication test
curl -X POST https://your-domain.com/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your-password"}'

# Chat test
curl -X POST https://your-domain.com/api/chat \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"message":"Hello","tenant_id":"default"}'
```

### Frontend Testing
- Access: `https://your-domain.com`
- Login with admin credentials
- Test chat functionality
- Upload and query documents
- Verify multi-tenant isolation

## 🚨 Troubleshooting

### Common Issues

1. **OpenAI API Errors**
   - Verify API key is correct and has credits
   - Check rate limits and usage quotas

2. **Database Connection Issues**
   - Ensure SQLite file permissions are correct
   - Verify database path in environment variables

3. **Docker Build Failures**
   - Check system resources (RAM/disk space)
   - Verify all required files are present

4. **Frontend Not Loading**
   - Check Nginx configuration
   - Verify React build completed successfully

### Performance Optimization
- Enable Redis caching for frequent queries
- Implement database connection pooling
- Use CDN for static assets
- Configure proper logging levels

## 📞 Support & Maintenance

### Regular Maintenance Tasks
- Monitor disk space and clean old logs
- Update dependencies monthly
- Backup database weekly
- Review security logs
- Test disaster recovery procedures

### Scaling Considerations
- Horizontal scaling with load balancer
- Database migration to PostgreSQL
- Implement Redis for session management
- Use cloud storage for documents
- Set up monitoring with Prometheus/Grafana

## 🔄 Development Workflow

### Local Development Setup
```bash
# Windows (using start-dev.bat)
start-dev.bat

# Manual setup
# Backend (Terminal 1)
python -m uvicorn app:app --reload --port 8811

# Frontend (Terminal 2)
cd dashboardapp
npm start  # Runs on port 3000, configured for 3004 in production
```

### Development Ports
- **Backend API**: http://localhost:8811
- **Frontend**: http://localhost:3000 (dev) / 3004 (production)
- **API Documentation**: http://localhost:8811/docs

### Code Structure Details

#### Main Application (app.py)
```python
# Core FastAPI app with all routers
from api.users import router as users_router
from api.documents import router as documents_router
from api.chat import router as chat_router
from api.conversations import router as conversations_router
from api.tenants import router as tenants_router
from api.database import router as database_router
from api.admin import router as admin_router

# Enhanced chat assistant integration
from chat_assistant.api.documents import router as chat_documents_router
```

#### Database Models (db.py)
- **Users**: Authentication and user management
- **Tenants**: Multi-tenant isolation
- **Conversations**: Chat history storage
- **Documents**: PDF document metadata
- **Admin**: Administrative functions
- **Database Connections**: SQL database configurations

#### API Endpoints Structure
```
/api/
├── /users/          # User management (register, login, profile)
├── /chat/           # Chat interactions with AI
├── /documents/      # Document upload and processing
├── /conversations/  # Chat history management
├── /tenants/        # Multi-tenant configuration
├── /database/       # Database chat (SQL generation)
├── /admin/          # Administrative interface
└── /health          # System health check
```

## 🎯 Key Features Implementation

### 1. Multi-Tenant Chat System
- **Isolation**: Each tenant has separate data and configurations
- **Customization**: Tenant-specific prompts and behavior
- **Security**: Row-level security for data access
- **API**: RESTful endpoints for tenant management

### 2. Document Processing Pipeline
- **Upload**: PDF files via REST API
- **Processing**: Text extraction using PyPDF
- **Vectorization**: ChromaDB for semantic search
- **Querying**: RAG (Retrieval Augmented Generation) with OpenAI

### 3. Database Chat (Vanna AI)
- **Schema Learning**: Automatic database schema analysis
- **Query Generation**: Natural language to SQL conversion
- **Execution**: Safe SQL execution with result formatting
- **Caching**: Query result caching for performance

### 4. Voice Assistant Integration
- **Twilio**: Phone call handling and voice processing
- **Speech-to-Text**: Voice input conversion
- **AI Processing**: Same chat logic as text interface
- **Text-to-Speech**: Voice response generation

## 🔧 Advanced Configuration

### Environment-Specific Settings

#### Development (.env.development)
```bash
ENVIRONMENT=development
DEBUG=true
LOG_LEVEL=DEBUG
OPENAI_API_KEY=sk-proj-your-dev-key
SECRET_KEY=dev-secret-key
DATABASE_URL=sqlite:///./data/chat360_dev.db
```

#### Production (.env.production)
```bash
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO
WORKERS=4
DATABASE_URL=sqlite:///app/data/chat360.db
# Security keys should be 32+ characters
SECRET_KEY=production-secret-key-32-chars-minimum
JWT_SECRET_KEY=jwt-secret-key-32-chars-minimum
```

#### Azure Cloud (.env.azure)
```bash
ENVIRONMENT=production
DATABASE_URL=postgresql://user:pass@server.postgres.database.azure.com/chat360db
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
AZURE_KEY_VAULT_URL=https://your-keyvault.vault.azure.net/
```

### Docker Compose Configurations

#### Development (docker-compose.yml)
```yaml
version: "3.8"
services:
  chatbot:
    build: .
    ports:
      - "6688:8000"
    environment:
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      SQLITE_PATH: /app/data/chatbot.sqlite
    volumes:
      - ./docs:/app/docs
      - ./static:/app/static
      - ./chroma_db_data:/app/chroma_db
      - ./sqlite_data:/app/data
    command: uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

#### Production (docker-compose.production.yml)
```yaml
services:
  chat360-backend:
    build: .
    container_name: chat360-backend
    restart: unless-stopped
    ports:
      - "8811:8000"
    environment:
      ENVIRONMENT: production
      WORKERS: 2
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      SECRET_KEY: ${SECRET_KEY}
    volumes:
      - ./data:/app/data
      - ./docs:/app/docs
      - ./chroma_db_data:/app/chroma_db
      - ./logs:/app/logs

  chat360-frontend:
    build:
      context: ./dashboardapp
      dockerfile: Dockerfile.production
    container_name: chat360-frontend
    restart: unless-stopped
    ports:
      - "3004:3000"
    environment:
      - NODE_ENV=production
      - REACT_APP_API_URL=https://your-domain.com/api
```

### Nginx Reverse Proxy Configuration
```nginx
upstream backend {
    server localhost:8811;
}

upstream frontend {
    server localhost:3004;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;

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
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files - Now served by React frontend
    # Widget files are now served from React public folder at root level
    # No separate /static/ location needed
}
```

## 📈 Performance & Scaling

### Database Optimization
```python
# SQLite optimizations for production
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;
PRAGMA cache_size = 1000000;
PRAGMA temp_store = memory;
PRAGMA mmap_size = 268435456;
```

### Caching Strategy
- **Application Cache**: In-memory caching for frequent queries
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
    volumes:
      - grafana-storage:/var/lib/grafana

volumes:
  grafana-storage:
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
- **Secrets Management**: Use environment variables or key vaults
- **File Permissions**: Restrict access to configuration files
- **Container Security**: Run containers as non-root users
- **Network Security**: Use private networks for internal communication

## 🚀 Deployment Automation

### CI/CD Pipeline (GitHub Actions)
```yaml
name: Deploy Chat360
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
            cd /opt/chat360
            git pull origin main
            docker-compose -f docker-compose.production.yml down
            docker-compose -f docker-compose.production.yml build
            docker-compose -f docker-compose.production.yml up -d
```

### Backup Automation
```bash
#!/bin/bash
# backup-script.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/chat360"

# Database backup
sqlite3 /opt/chat360/data/chat360.db ".backup $BACKUP_DIR/db_$DATE.db"

# Documents backup
tar -czf $BACKUP_DIR/docs_$DATE.tar.gz /opt/chat360/docs/

# Configuration backup
cp /opt/chat360/.env $BACKUP_DIR/env_$DATE.backup

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "*.db" -mtime +30 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +30 -delete
find $BACKUP_DIR -name "*.backup" -mtime +30 -delete
```

---

**Note**: This comprehensive guide covers all aspects of Chat360 deployment. Ensure proper security measures are in place and test thoroughly before production deployment. For additional support, refer to the individual component documentation in the respective directories.
