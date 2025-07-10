#!/bin/bash
# Production deployment script for MCP Associative Memory Server

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BACKUP_DIR="$PROJECT_ROOT/backups"
DATA_DIR="$PROJECT_ROOT/data"
LOGS_DIR="$PROJECT_ROOT/logs"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if .env file exists
    if [ ! -f "$PROJECT_ROOT/.env" ]; then
        warning ".env file not found. Creating from .env.example..."
        cp "$PROJECT_ROOT/.env.example" "$PROJECT_ROOT/.env"
        warning "Please edit .env file with your configuration before proceeding."
        exit 1
    fi
    
    log "Prerequisites check completed."
}

# Create required directories
create_directories() {
    log "Creating required directories..."
    
    mkdir -p "$DATA_DIR"
    mkdir -p "$LOGS_DIR"
    mkdir -p "$BACKUP_DIR"
    
    # Set proper permissions
    chmod 755 "$DATA_DIR" "$LOGS_DIR" "$BACKUP_DIR"
    
    log "Directories created successfully."
}

# Backup existing data
backup_data() {
    if [ -d "$DATA_DIR" ] && [ "$(ls -A $DATA_DIR)" ]; then
        log "Backing up existing data..."
        
        backup_timestamp=$(date +%Y%m%d_%H%M%S)
        backup_path="$BACKUP_DIR/data_backup_$backup_timestamp.tar.gz"
        
        tar -czf "$backup_path" -C "$PROJECT_ROOT" data/
        log "Data backed up to: $backup_path"
    else
        log "No existing data to backup."
    fi
}

# Build Docker image
build_image() {
    log "Building Docker image..."
    
    cd "$PROJECT_ROOT"
    docker-compose build --no-cache mcp-assoc-memory
    
    log "Docker image built successfully."
}

# Run health check
health_check() {
    log "Running health check..."
    
    # Wait for service to be ready
    max_attempts=30
    attempt=0
    
    while [ $attempt -lt $max_attempts ]; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log "Health check passed!"
            return 0
        fi
        
        attempt=$((attempt + 1))
        log "Waiting for service to be ready... ($attempt/$max_attempts)"
        sleep 2
    done
    
    error "Health check failed after $max_attempts attempts."
    return 1
}

# Deploy service
deploy() {
    log "Deploying MCP Associative Memory Server..."
    
    cd "$PROJECT_ROOT"
    
    # Stop existing containers
    docker-compose down --remove-orphans
    
    # Start new containers
    docker-compose up -d
    
    log "Service deployed successfully."
    
    # Run health check
    sleep 10  # Give service time to start
    health_check
}

# Display service information
show_info() {
    log "Deployment completed successfully!"
    echo
    echo -e "${BLUE}Service Information:${NC}"
    echo -e "  Server URL: http://localhost:8000"
    echo -e "  Health Check: http://localhost:8000/health"
    echo -e "  Metrics: http://localhost:8000/metrics"
    echo
    echo -e "${BLUE}Management Commands:${NC}"
    echo -e "  View logs: docker-compose logs -f mcp-assoc-memory"
    echo -e "  Stop service: docker-compose down"
    echo -e "  Restart service: docker-compose restart"
    echo -e "  Update service: $0"
    echo
    echo -e "${BLUE}Data Locations:${NC}"
    echo -e "  Data directory: $DATA_DIR"
    echo -e "  Logs directory: $LOGS_DIR"
    echo -e "  Backups directory: $BACKUP_DIR"
}

# Main deployment function
main() {
    log "Starting MCP Associative Memory Server deployment..."
    
    check_prerequisites
    create_directories
    backup_data
    build_image
    deploy
    show_info
    
    log "Deployment completed successfully!"
}

# Run main function
main "$@"
