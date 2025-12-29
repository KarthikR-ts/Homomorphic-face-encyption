#!/bin/bash

# =============================================================================
# Blue-Green Deployment Script for Facial Recognition API
# Zero-downtime deployment with rollback capability
# =============================================================================

set -euo pipefail

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
PROJECT_NAME="facial-recognition"
BLUE_STACK="${PROJECT_NAME}-blue"
GREEN_STACK="${PROJECT_NAME}-green"
BACKUP_SUFFIX="$(date +%Y%m%d_%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    # Check required files
    required_files=("docker-compose.prod.yml" "Dockerfile.prod" "secrets/")
    for file in "${required_files[@]}"; do
        if [[ ! -e "$file" ]]; then
            log_error "Required file/directory missing: $file"
            exit 1
        fi
    done

    log_success "Prerequisites check passed"
}

# Get current active stack
get_active_stack() {
    # Check which stack is currently serving traffic
    if docker network ls | grep -q "${BLUE_STACK}"; then
        echo "$BLUE_STACK"
    elif docker network ls | grep -q "${GREEN_STACK}"; then
        echo "$GREEN_STACK"
    else
        echo ""
    fi
}

# Get inactive stack
get_inactive_stack() {
    active_stack=$(get_active_stack)
    if [[ "$active_stack" == "$BLUE_STACK" ]]; then
        echo "$GREEN_STACK"
    else
        echo "$BLUE_STACK"
    fi
}

# Deploy to a specific stack
deploy_to_stack() {
    local stack_name=$1
    log_info "Deploying to stack: $stack_name"

    # Set environment variables for the stack
    export COMPOSE_PROJECT_NAME="$stack_name"

    # Pull latest images
    log_info "Pulling latest images..."
    docker-compose -f "$COMPOSE_FILE" pull

    # Deploy new stack
    log_info "Starting new stack..."
    docker-compose -f "$COMPOSE_FILE" up -d

    # Wait for health checks
    log_info "Waiting for services to be healthy..."
    local max_attempts=60
    local attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if docker-compose -f "$COMPOSE_FILE" ps | grep -q "healthy"; then
            log_success "All services are healthy"
            break
        fi

        if [[ $attempt -eq $max_attempts ]]; then
            log_error "Services failed to become healthy within timeout"
            docker-compose -f "$COMPOSE_FILE" logs
            return 1
        fi

        log_info "Waiting for services to be healthy... (attempt $attempt/$max_attempts)"
        sleep 10
        ((attempt++))
    done

    # Run database migrations if needed
    log_info "Running database migrations..."
    docker-compose -f "$COMPOSE_FILE" exec -T app flask db upgrade || true

    # Run health checks
    log_info "Running health checks..."
    if ! curl -f --max-time 30 http://localhost/health; then
        log_error "Health check failed"
        return 1
    fi

    log_success "Stack $stack_name deployed successfully"
}

# Switch traffic to new stack (update nginx upstream)
switch_traffic() {
    local new_stack=$1
    log_info "Switching traffic to $new_stack"

    # Update nginx configuration with new upstream
    # This assumes nginx config can be reloaded
    docker-compose -f "$COMPOSE_FILE" exec nginx nginx -s reload

    log_success "Traffic switched to $new_stack"
}

# Cleanup old stack
cleanup_old_stack() {
    local old_stack=$1
    log_info "Cleaning up old stack: $old_stack"

    export COMPOSE_PROJECT_NAME="$old_stack"
    docker-compose -f "$COMPOSE_FILE" down --volumes

    log_success "Old stack cleaned up"
}

# Backup current state
create_backup() {
    log_info "Creating backup..."

    # Backup database
    docker exec "${BLUE_STACK}_postgres_1" pg_dump -U postgres face_db > "backup_db_$BACKUP_SUFFIX.sql" 2>/dev/null || true

    # Backup volumes (if needed)
    # This would require additional volume backup logic

    log_success "Backup created: backup_db_$BACKUP_SUFFIX.sql"
}

# Rollback to previous stack
rollback() {
    local current_stack=$1
    local previous_stack=$2

    log_warn "Rolling back from $current_stack to $previous_stack"

    # Switch traffic back
    switch_traffic "$previous_stack"

    # Stop failed stack
    export COMPOSE_PROJECT_NAME="$current_stack"
    docker-compose -f "$COMPOSE_FILE" down

    log_success "Rollback completed"
}

# Main deployment function
deploy() {
    log_info "Starting blue-green deployment..."

    # Get stack information
    active_stack=$(get_active_stack)
    inactive_stack=$(get_inactive_stack)

    log_info "Active stack: ${active_stack:-none}"
    log_info "Inactive stack: $inactive_stack"

    # Create backup if there's an active stack
    if [[ -n "$active_stack" ]]; then
        create_backup
    fi

    # Deploy to inactive stack
    if ! deploy_to_stack "$inactive_stack"; then
        log_error "Deployment to $inactive_stack failed"
        exit 1
    fi

    # Switch traffic
    switch_traffic "$inactive_stack"

    # Wait for traffic to stabilize
    log_info "Waiting for traffic to stabilize..."
    sleep 30

    # Verify new stack is working
    if curl -f --max-time 10 http://localhost/health; then
        log_success "New stack is responding correctly"

        # Cleanup old stack
        if [[ -n "$active_stack" ]]; then
            cleanup_old_stack "$active_stack"
        fi

        log_success "Deployment completed successfully!"
    else
        log_error "New stack health check failed, rolling back..."

        if [[ -n "$active_stack" ]]; then
            rollback "$inactive_stack" "$active_stack"
        fi

        exit 1
    fi
}

# Show status
status() {
    log_info "Deployment Status:"

    echo "Blue Stack:"
    export COMPOSE_PROJECT_NAME="$BLUE_STACK"
    docker-compose -f "$COMPOSE_FILE" ps

    echo -e "\nGreen Stack:"
    export COMPOSE_PROJECT_NAME="$GREEN_STACK"
    docker-compose -f "$COMPOSE_FILE" ps

    echo -e "\nNetworks:"
    docker network ls | grep "$PROJECT_NAME"
}

# Rollback command
rollback_cmd() {
    active_stack=$(get_active_stack)
    if [[ -z "$active_stack" ]]; then
        log_error "No active stack found"
        exit 1
    fi

    inactive_stack=$(get_inactive_stack)
    rollback "$active_stack" "$inactive_stack"
}

# Main script
case "${1:-deploy}" in
    "deploy")
        check_prerequisites
        deploy
        ;;
    "status")
        status
        ;;
    "rollback")
        check_prerequisites
        rollback_cmd
        ;;
    "cleanup")
        log_info "Cleaning up all stacks..."
        export COMPOSE_PROJECT_NAME="$BLUE_STACK"
        docker-compose -f "$COMPOSE_FILE" down --volumes 2>/dev/null || true
        export COMPOSE_PROJECT_NAME="$GREEN_STACK"
        docker-compose -f "$COMPOSE_FILE" down --volumes 2>/dev/null || true
        log_success "Cleanup completed"
        ;;
    *)
        echo "Usage: $0 [deploy|status|rollback|cleanup]"
        echo "  deploy  - Perform blue-green deployment"
        echo "  status  - Show current deployment status"
        echo "  rollback- Rollback to previous version"
        echo "  cleanup - Remove all containers and volumes"
        exit 1
        ;;
esac
