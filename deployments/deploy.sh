#!/bin/bash

# NID Extraction API - Docker Deployment Script
# Supports PaddleOCR (front) and EasyOCR (back - Bengali/English)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

print_header() {
    echo ""
    echo "=========================================="
    echo "$1"
    echo "=========================================="
    echo ""
}

# Check prerequisites
check_prerequisites() {
    print_header "Checking Prerequisites"
    
    # Check Docker
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version | cut -d ' ' -f3 | cut -d ',' -f1)
        print_success "Docker installed: $DOCKER_VERSION"
    else
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        COMPOSE_VERSION=$(docker-compose --version | cut -d ' ' -f4 | cut -d ',' -f1)
        print_success "Docker Compose installed: $COMPOSE_VERSION"
    else
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check disk space
    AVAILABLE_SPACE=$(df -BG . | tail -1 | awk '{print $4}' | sed 's/G//')
    if [ "$AVAILABLE_SPACE" -lt 10 ]; then
        print_error "Insufficient disk space. Need at least 10GB, have ${AVAILABLE_SPACE}GB"
        exit 1
    else
        print_success "Disk space available: ${AVAILABLE_SPACE}GB"
    fi
}

# Build and deploy
deploy() {
    print_header "Building and Deploying"
    
    print_info "Building Docker image..."
    docker-compose build --no-cache
    print_success "Image built successfully"
    
    print_info "Starting containers..."
    docker-compose up -d
    print_success "Containers started"
    
    print_info "Waiting for application to be ready..."
    sleep 10
    
    # Wait for health check
    MAX_RETRIES=30
    RETRY_COUNT=0
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            print_success "Application is healthy!"
            break
        fi
        RETRY_COUNT=$((RETRY_COUNT+1))
        echo -n "."
        sleep 2
    done
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        print_error "Application failed to start within expected time"
        print_info "Check logs with: docker-compose logs -f"
        exit 1
    fi
}

# Show status
show_status() {
    print_header "Deployment Status"
    
    # Container status
    print_info "Container Status:"
    docker-compose ps
    
    echo ""
    
    # Resource usage
    print_info "Resource Usage:"
    docker stats --no-stream nid-extraction-api
    
    echo ""
    
    # Endpoints
    print_header "API Endpoints"
    echo "  🌐 API Root:       http://localhost:8000"
    echo "  📊 Health Check:   http://localhost:8000/health"
    echo "  📚 API Docs:       http://localhost:8000/docs"
    echo "  📈 Metrics:        http://localhost:8000/metrics"
    echo ""
}

# Test deployment
test_deployment() {
    print_header "Testing Deployment"
    
    print_info "Testing health endpoint..."
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
    if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
        print_success "Health check passed"
    else
        print_error "Health check failed"
        echo "$HEALTH_RESPONSE"
    fi
    
    print_info "Testing root endpoint..."
    ROOT_RESPONSE=$(curl -s http://localhost:8000/)
    if echo "$ROOT_RESPONSE" | grep -q "NID Information Extraction API"; then
        print_success "Root endpoint working"
    else
        print_error "Root endpoint failed"
    fi
}

# Show logs
show_logs() {
    print_header "Application Logs"
    print_info "Press Ctrl+C to exit logs"
    sleep 2
    docker-compose logs -f --tail=50
}

# Main menu
show_menu() {
    echo ""
    echo "=========================================="
    echo "NID Extraction API - Docker Deployment"
    echo "=========================================="
    echo ""
    echo "1) Deploy (Build and Start)"
    echo "2) Start (existing containers)"
    echo "3) Stop"
    echo "4) Restart"
    echo "5) View Logs"
    echo "6) View Status"
    echo "7) Test Deployment"
    echo "8) Clean (remove containers and volumes)"
    echo "9) Exit"
    echo ""
    read -p "Select option [1-9]: " choice
    
    case $choice in
        1)
            check_prerequisites
            deploy
            show_status
            test_deployment
            ;;
        2)
            print_info "Starting containers..."
            docker-compose up -d
            print_success "Containers started"
            show_status
            ;;
        3)
            print_info "Stopping containers..."
            docker-compose down
            print_success "Containers stopped"
            ;;
        4)
            print_info "Restarting containers..."
            docker-compose restart
            print_success "Containers restarted"
            show_status
            ;;
        5)
            show_logs
            ;;
        6)
            show_status
            ;;
        7)
            test_deployment
            ;;
        8)
            read -p "This will remove all containers and volumes. Continue? (y/N): " confirm
            if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
                print_info "Cleaning up..."
                docker-compose down -v
                print_success "Cleanup complete"
            else
                print_info "Cleanup cancelled"
            fi
            ;;
        9)
            print_info "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid option"
            ;;
    esac
    
    # Show menu again
    show_menu
}

# Run
if [ "$1" = "--auto" ]; then
    # Automated deployment
    check_prerequisites
    deploy
    show_status
    test_deployment
else
    # Interactive menu
    show_menu
fi
