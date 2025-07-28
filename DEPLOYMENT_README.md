# AI Agent Platform - Deployment Files

This directory contains all the necessary files for deploying the AI Agent Platform in various environments.

## 📁 File Overview

### Core Deployment Files
- **`DEPLOYMENT_GUIDE.md`** - Comprehensive deployment guide with detailed instructions
- **`docker-compose.production.yml`** - Production Docker Compose configuration
- **`docker-compose.yml`** - Development Docker Compose configuration
- **`Dockerfile`** - Production backend container configuration
- **`Dockerfile.dev`** - Development backend container configuration

### Frontend Files
- **`frontend/Dockerfile.production`** - Production frontend container configuration
- **`frontend/nginx.conf`** - Nginx configuration for frontend container

### Nginx Configuration
- **`nginx/conf.d/default.conf`** - Main Nginx reverse proxy configuration

### Environment Templates
- **`.env.example`** - Development environment template
- **`.env.production`** - Production environment template
- **`.env.azure`** - Azure cloud environment template

### Database Setup
- **`init-db.sql`** - PostgreSQL database initialization script

### Deployment Scripts
- **`deploy-production.sh`** - Linux/macOS production deployment script
- **`deploy-production.bat`** - Windows production deployment script
- **`setup-development.sh`** - Linux/macOS development setup script
- **`setup-development.bat`** - Windows development setup script

## 🚀 Quick Start

### Development Setup

#### Windows
```cmd
setup-development.bat
```

#### Linux/macOS
```bash
chmod +x setup-development.sh
./setup-development.sh
```

### Production Deployment

#### Windows
```cmd
# 1. Copy and configure environment
copy .env.production .env
# Edit .env with your values

# 2. Deploy
deploy-production.bat
```

#### Linux/macOS
```bash
# 1. Copy and configure environment
cp .env.production .env
# Edit .env with your values

# 2. Make scripts executable and deploy
chmod +x deploy-production.sh
./deploy-production.sh
```

### Docker Development
```bash
# Start development environment with Docker
docker-compose up

# Or run in background
docker-compose up -d
```

## 🔧 Configuration

### Required Environment Variables
Before deployment, you must configure these essential variables in your `.env` file:

```bash
# AI Service API Keys (REQUIRED)
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Security (REQUIRED)
SECRET_KEY=your-super-secret-key-32-chars-minimum
JWT_SECRET_KEY=your-jwt-secret-key-32-chars-minimum

# Database (Production)
DATABASE_URL=postgresql://user:password@localhost:5432/ai_agents_db
POSTGRES_PASSWORD=your-secure-password

# Redis (Production)
REDIS_PASSWORD=your-redis-password
```

### Optional Services
- **Azure Storage**: For cloud file storage
- **WhatsApp Integration**: For messaging capabilities
- **Azure Key Vault**: For secure secret management

## 🏗️ Architecture

### Development Architecture
```
Frontend (React/Vite) :3003
    ↓
Backend (FastAPI) :3006
    ↓
SQLite Database (local file)
Redis (optional) :6379
```

### Production Architecture
```
Internet → Nginx :80/443
    ↓
Frontend Container :80 ← Backend Container :3006
    ↓
PostgreSQL Container :5432
Redis Container :6379
```

## 📊 Service Ports

### Development
- **Frontend**: http://localhost:3003
- **Backend**: http://localhost:3006
- **API Docs**: http://localhost:3006/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

### Production (Docker)
- **Nginx**: http://localhost:80, https://localhost:443
- **Frontend**: Internal port 80
- **Backend**: Internal port 3006
- **PostgreSQL**: Internal port 5432
- **Redis**: Internal port 6379

## 🔍 Health Checks

### Manual Health Checks
```bash
# Backend health
curl http://localhost:3006/health

# Frontend health
curl http://localhost:3003

# Database health (if using PostgreSQL)
pg_isready -h localhost -p 5432

# Redis health
redis-cli ping
```

### Docker Health Checks
```bash
# Check all services
docker-compose -f docker-compose.production.yml ps

# Check specific service logs
docker-compose -f docker-compose.production.yml logs ai-agents-backend
```

## 🛠️ Maintenance Commands

### Development
```bash
# Start development servers
python main.py                    # Backend
cd frontend && npm run dev        # Frontend

# Run tests
pytest                           # Backend tests
cd frontend && npm test          # Frontend tests
```

### Production
```bash
# View logs
docker-compose -f docker-compose.production.yml logs -f

# Restart services
docker-compose -f docker-compose.production.yml restart

# Update deployment
git pull
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d --build

# Backup
./deploy-production.sh backup
```

## 🚨 Troubleshooting

### Common Issues

1. **Port conflicts**: Ensure ports 3003, 3006, 5432, 6379 are available
2. **Permission errors**: Run scripts with appropriate permissions
3. **Docker issues**: Ensure Docker and Docker Compose are installed and running
4. **Environment variables**: Verify all required variables are set in `.env`
5. **API keys**: Ensure OpenAI/Anthropic API keys are valid and have credits

### Debug Commands
```bash
# Check Docker status
docker --version
docker-compose --version

# Check Python environment
python --version
pip list

# Check Node.js environment
node --version
npm --version

# Check database connection
python -c "from src.core.database import engine; print('Database connection OK')"
```

## 📞 Support

For deployment issues:
1. Check the comprehensive `DEPLOYMENT_GUIDE.md`
2. Review service logs using Docker Compose commands
3. Verify environment configuration
4. Ensure all prerequisites are installed

## 🔄 Updates

To update the deployment:
1. Pull latest code: `git pull`
2. Update dependencies: `pip install -r requirements.txt` and `npm install`
3. Rebuild containers: `docker-compose build --no-cache`
4. Restart services: `docker-compose up -d`

---

**Note**: Always test deployments in a development environment before deploying to production.
