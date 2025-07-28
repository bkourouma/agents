# Docker Production Deployment Guide

## Quick Setup

### 1. Clone and Setup
```bash
git clone <repository>
cd chat360
```

### 2. Create Production Configuration
```bash
# Copy and customize docker-compose for your server
cp docker-compose.production.example.yml docker-compose.production.yml

# Edit the file to customize URLs and settings
nano docker-compose.production.yml
```

### 3. Create Environment File
```bash
# Create .env file with your secrets
cat > .env << EOF
OPENAI_API_KEY=your_openai_api_key_here
SECRET_KEY=your_secret_key_here
JWT_SECRET_KEY=your_jwt_secret_here
ADMIN_PASSWORD=your_admin_password_here
EOF
```

### 4. Deploy
```bash
# Build and start all services
docker-compose -f docker-compose.production.yml up -d

# Check status
docker-compose -f docker-compose.production.yml ps
```

## Configuration Details

### Frontend Environment Variables

In `docker-compose.production.yml`, customize these for your domain:

```yaml
chat360-frontend:
  build:
    context: ./dashboardapp
    dockerfile: Dockerfile.production
    args:
      REACT_APP_API_URL: https://your-domain.com/api
      REACT_APP_WS_URL: wss://your-domain.com/ws
      NODE_ENV: production
```

**Important**: These are build arguments, not runtime environment variables. The URLs are baked into the build at build time.

### Backend Configuration

The backend automatically uses:
- Port 8811 (mapped from internal 8000)
- SQLite database in `./data/` volume
- Logs in `./logs/` volume

### Nginx Proxy

- Serves frontend on port 8080
- Proxies API calls to backend
- Handles SSL termination (if configured)

## Service Architecture

```
Internet → Nginx (8080) → Frontend (3004) + Backend (8811)
```

- **Frontend**: React app served by Nginx on port 3004
- **Backend**: FastAPI on port 8811
- **Nginx**: Reverse proxy on port 8080

## Maintenance Commands

```bash
# View logs
docker-compose -f docker-compose.production.yml logs -f

# Restart services
docker-compose -f docker-compose.production.yml restart

# Update and redeploy
git pull
docker-compose -f docker-compose.production.yml down
docker-compose -f docker-compose.production.yml up -d --build

# Backup data
tar -czf backup-$(date +%Y%m%d).tar.gz data/ sqlite_data/ chroma_db_data/
```

## Troubleshooting

### Frontend shows "Connection Refused" or connects to localhost:8811
1. **Check build arguments**: Ensure `REACT_APP_API_URL` is set in build args, not environment
2. **Rebuild frontend**: The API URL is baked in at build time
   ```bash
   docker-compose -f docker-compose.production.yml stop chat360-frontend
   docker-compose -f docker-compose.production.yml rm -f chat360-frontend
   docker-compose -f docker-compose.production.yml up -d --build chat360-frontend
   ```
3. **Verify build args**: Check what was built into the container
   ```bash
   docker exec chat360-frontend grep -r "localhost:8811" /usr/share/nginx/html/ || echo "No localhost found"
   ```
4. **Check backend**: Verify backend is running: `docker logs chat360-backend`

### Backend not starting
1. Check environment variables in `.env`
2. Verify OpenAI API key is valid
3. Check logs: `docker logs chat360-backend`

### SSL/HTTPS Issues
1. Configure SSL certificates in `./nginx/ssl/`
2. Update nginx configuration for HTTPS
3. Ensure `REACT_APP_API_URL` uses `https://`

## Security Notes

- Change default passwords in `.env`
- Use strong JWT secrets
- Configure proper SSL certificates
- Restrict access to sensitive ports
- Regular backups of data volumes
