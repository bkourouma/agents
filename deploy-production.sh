#!/bin/bash

# AI Agent Platform - Production Deployment Script
# This script deploys the AI Agent Platform to a VPS using Docker Compose

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="ai-agent-platform"
COMPOSE_FILE="docker-compose.production.yml"
ENV_FILE=".env"
BACKUP_DIR="/backup/${PROJECT_NAME}"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Checking system requirements..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error ".env file not found. Please copy .env.production to .env and configure it."
        exit 1
    fi
    
    log_success "System requirements check passed"
}

create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p data
    mkdir -p agent_documents
    mkdir -p agent_vectors
    mkdir -p vanna_cache
    mkdir -p logs
    mkdir -p nginx/ssl
    mkdir -p "$BACKUP_DIR"
    
    log_success "Directories created"
}

backup_existing() {
    if [ -f "$COMPOSE_FILE" ] && docker-compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        log_info "Creating backup of existing deployment..."
        
        # Create backup directory with timestamp
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        BACKUP_PATH="${BACKUP_DIR}/backup_${TIMESTAMP}"
        mkdir -p "$BACKUP_PATH"
        
        # Backup database
        if docker-compose -f "$COMPOSE_FILE" ps postgres | grep -q "Up"; then
            log_info "Backing up PostgreSQL database..."
            docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U ai_agents_user ai_agents_db > "${BACKUP_PATH}/database.sql"
        fi
        
        # Backup data directories
        log_info "Backing up data directories..."
        tar -czf "${BACKUP_PATH}/data.tar.gz" data/ agent_documents/ agent_vectors/ vanna_cache/ 2>/dev/null || true
        
        # Backup configuration
        cp "$ENV_FILE" "${BACKUP_PATH}/env.backup"
        
        log_success "Backup created at $BACKUP_PATH"
    fi
}

deploy() {
    log_info "Starting deployment..."
    
    # Pull latest images
    log_info "Pulling latest Docker images..."
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Build custom images
    log_info "Building application images..."
    docker-compose -f "$COMPOSE_FILE" build --no-cache
    
    # Stop existing services
    log_info "Stopping existing services..."
    docker-compose -f "$COMPOSE_FILE" down
    
    # Start services
    log_info "Starting services..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # Wait for services to be healthy
    log_info "Waiting for services to be healthy..."
    sleep 30
    
    # Check service health
    check_health
}

check_health() {
    log_info "Checking service health..."
    
    # Check if all services are running
    if docker-compose -f "$COMPOSE_FILE" ps | grep -q "Exit"; then
        log_error "Some services failed to start. Check logs with: docker-compose -f $COMPOSE_FILE logs"
        exit 1
    fi
    
    # Check backend health
    for i in {1..30}; do
        if curl -f http://localhost:3006/health &>/dev/null; then
            log_success "Backend is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "Backend health check failed"
            exit 1
        fi
        sleep 2
    done
    
    # Check frontend
    for i in {1..30}; do
        if curl -f http://localhost:3003 &>/dev/null; then
            log_success "Frontend is healthy"
            break
        fi
        if [ $i -eq 30 ]; then
            log_error "Frontend health check failed"
            exit 1
        fi
        sleep 2
    done
    
    log_success "All services are healthy"
}

show_status() {
    log_info "Deployment Status:"
    echo ""
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    log_info "Application URLs:"
    echo "  Frontend: http://localhost:3003"
    echo "  Backend API: http://localhost:3006"
    echo "  API Documentation: http://localhost:3006/docs"
    echo ""
    log_info "To view logs: docker-compose -f $COMPOSE_FILE logs -f"
    log_info "To stop services: docker-compose -f $COMPOSE_FILE down"
}

cleanup() {
    log_info "Cleaning up unused Docker resources..."
    docker system prune -f
    docker volume prune -f
    log_success "Cleanup completed"
}

# Main execution
main() {
    echo ""
    echo "=========================================="
    echo "  AI Agent Platform - Production Deploy  "
    echo "=========================================="
    echo ""
    
    check_requirements
    create_directories
    backup_existing
    deploy
    cleanup
    show_status
    
    echo ""
    log_success "Deployment completed successfully!"
    echo ""
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "backup")
        backup_existing
        ;;
    "health")
        check_health
        ;;
    "status")
        show_status
        ;;
    "logs")
        docker-compose -f "$COMPOSE_FILE" logs -f
        ;;
    "stop")
        docker-compose -f "$COMPOSE_FILE" down
        ;;
    "restart")
        docker-compose -f "$COMPOSE_FILE" restart
        ;;
    *)
        echo "Usage: $0 {deploy|backup|health|status|logs|stop|restart}"
        exit 1
        ;;
esac
