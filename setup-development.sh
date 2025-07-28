#!/bin/bash

# AI Agent Platform - Development Environment Setup Script
# This script sets up the development environment for the AI Agent Platform

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="ai-agent-platform"
PYTHON_VERSION="3.11"
NODE_VERSION="18"

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

check_system() {
    log_info "Checking system requirements..."
    
    # Check OS
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        log_error "Unsupported operating system: $OSTYPE"
        exit 1
    fi
    
    log_success "Operating system: $OS"
}

install_python() {
    log_info "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_CURRENT=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
        log_info "Python $PYTHON_CURRENT found"
        
        if [[ "$PYTHON_CURRENT" < "$PYTHON_VERSION" ]]; then
            log_warning "Python $PYTHON_VERSION or higher is recommended"
        fi
    else
        log_error "Python 3 is not installed. Please install Python $PYTHON_VERSION or higher."
        exit 1
    fi
    
    # Check if pip is installed
    if ! command -v pip3 &> /dev/null; then
        log_error "pip3 is not installed. Please install pip3."
        exit 1
    fi
    
    log_success "Python environment is ready"
}

install_node() {
    log_info "Checking Node.js installation..."
    
    if command -v node &> /dev/null; then
        NODE_CURRENT=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
        log_info "Node.js v$NODE_CURRENT found"
        
        if [[ "$NODE_CURRENT" -lt "$NODE_VERSION" ]]; then
            log_warning "Node.js v$NODE_VERSION or higher is recommended"
        fi
    else
        log_error "Node.js is not installed. Please install Node.js v$NODE_VERSION or higher."
        exit 1
    fi
    
    # Check if npm is installed
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed. Please install npm."
        exit 1
    fi
    
    log_success "Node.js environment is ready"
}

setup_python_env() {
    log_info "Setting up Python virtual environment..."
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log_info "Creating virtual environment..."
        python3 -m venv venv
    fi
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Upgrade pip
    log_info "Upgrading pip..."
    pip install --upgrade pip
    
    # Install requirements
    log_info "Installing Python dependencies..."
    pip install -r requirements.txt
    
    log_success "Python environment setup completed"
}

setup_frontend() {
    log_info "Setting up frontend environment..."
    
    cd frontend
    
    # Install npm dependencies
    log_info "Installing Node.js dependencies..."
    npm install
    
    cd ..
    
    log_success "Frontend environment setup completed"
}

setup_database() {
    log_info "Setting up development database..."
    
    # Check if PostgreSQL is available
    if command -v psql &> /dev/null; then
        log_info "PostgreSQL found, setting up database..."
        
        # Create database and user (if not exists)
        sudo -u postgres psql -c "CREATE DATABASE ai_agents_dev;" 2>/dev/null || true
        sudo -u postgres psql -c "CREATE USER ai_agents_user WITH PASSWORD 'dev_password';" 2>/dev/null || true
        sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ai_agents_dev TO ai_agents_user;" 2>/dev/null || true
        
        log_success "PostgreSQL database setup completed"
    else
        log_warning "PostgreSQL not found. Using SQLite for development."
        log_info "To use PostgreSQL, install it and run this script again."
    fi
}

setup_redis() {
    log_info "Checking Redis installation..."
    
    if command -v redis-server &> /dev/null; then
        log_info "Redis found"
        
        # Start Redis if not running
        if ! pgrep redis-server > /dev/null; then
            log_info "Starting Redis server..."
            redis-server --daemonize yes
        fi
        
        log_success "Redis setup completed"
    else
        log_warning "Redis not found. Some features may not work optimally."
        log_info "To install Redis:"
        if [[ "$OS" == "linux" ]]; then
            log_info "  Ubuntu/Debian: sudo apt-get install redis-server"
            log_info "  CentOS/RHEL: sudo yum install redis"
        elif [[ "$OS" == "macos" ]]; then
            log_info "  macOS: brew install redis"
        fi
    fi
}

create_env_file() {
    log_info "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        log_info "Creating .env file from template..."
        cp .env.example .env
        
        log_warning "Please edit .env file and add your API keys:"
        log_warning "  - OPENAI_API_KEY"
        log_warning "  - ANTHROPIC_API_KEY (optional)"
        log_warning "  - Other configuration as needed"
    else
        log_info ".env file already exists"
    fi
    
    log_success "Environment configuration ready"
}

create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p data
    mkdir -p agent_documents
    mkdir -p agent_vectors
    mkdir -p vanna_cache
    mkdir -p logs
    
    log_success "Directories created"
}

run_tests() {
    log_info "Running basic tests..."
    
    # Activate virtual environment
    source venv/bin/activate
    
    # Run a simple import test
    python -c "import src.main; print('Backend imports successful')" || {
        log_error "Backend import test failed"
        return 1
    }
    
    # Test frontend build
    cd frontend
    npm run build > /dev/null 2>&1 || {
        log_error "Frontend build test failed"
        cd ..
        return 1
    }
    cd ..
    
    log_success "Basic tests passed"
}

show_next_steps() {
    echo ""
    echo "=========================================="
    echo "  Development Environment Ready!"
    echo "=========================================="
    echo ""
    log_info "Next steps:"
    echo "  1. Edit .env file with your API keys"
    echo "  2. Start the development servers:"
    echo ""
    echo "     Backend:"
    echo "     source venv/bin/activate"
    echo "     python main.py"
    echo ""
    echo "     Frontend (in another terminal):"
    echo "     cd frontend"
    echo "     npm run dev"
    echo ""
    echo "  3. Access the application:"
    echo "     Frontend: http://localhost:3003"
    echo "     Backend API: http://localhost:3006"
    echo "     API Docs: http://localhost:3006/docs"
    echo ""
    log_info "For Docker development, use: docker-compose up"
    echo ""
}

# Main execution
main() {
    echo ""
    echo "=========================================="
    echo "  AI Agent Platform - Development Setup  "
    echo "=========================================="
    echo ""
    
    check_system
    install_python
    install_node
    create_directories
    setup_python_env
    setup_frontend
    setup_database
    setup_redis
    create_env_file
    
    # Run tests
    if run_tests; then
        show_next_steps
        log_success "Development environment setup completed successfully!"
    else
        log_error "Setup completed with some issues. Please check the logs above."
    fi
    
    echo ""
}

# Run main function
main
