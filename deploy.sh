#!/bin/bash
# ===========================================
# AI Anti-Spam Shield - DigitalOcean Deployment Script
# ===========================================
# Usage: ./deploy.sh [setup|deploy|ssl|update|logs|status|backup|restore]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/ai-anti-spam-shield"
BACKUP_DIR="/opt/backups"
COMPOSE_FILE="docker-compose.prod.yml"

# Helper functions
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        log_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Initial server setup
setup_server() {
    log_info "Setting up DigitalOcean Droplet..."

    # Update system
    log_info "Updating system packages..."
    apt-get update && apt-get upgrade -y

    # Install required packages
    log_info "Installing required packages..."
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release \
        git \
        ufw \
        fail2ban \
        htop \
        ncdu

    # Install Docker
    log_info "Installing Docker..."
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
        rm get-docker.sh
        systemctl enable docker
        systemctl start docker
    else
        log_info "Docker already installed"
    fi

    # Install Docker Compose
    log_info "Installing Docker Compose..."
    if ! command -v docker-compose &> /dev/null; then
        curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
        chmod +x /usr/local/bin/docker-compose
    else
        log_info "Docker Compose already installed"
    fi

    # Configure firewall
    log_info "Configuring firewall..."
    ufw default deny incoming
    ufw default allow outgoing
    ufw allow ssh
    ufw allow http
    ufw allow https
    ufw --force enable

    # Configure fail2ban
    log_info "Configuring fail2ban..."
    systemctl enable fail2ban
    systemctl start fail2ban

    # Create application directory
    log_info "Creating application directory..."
    mkdir -p $APP_DIR
    mkdir -p $BACKUP_DIR

    # Create swap file (for smaller droplets)
    if [ ! -f /swapfile ]; then
        log_info "Creating swap file..."
        fallocate -l 2G /swapfile
        chmod 600 /swapfile
        mkswap /swapfile
        swapon /swapfile
        echo '/swapfile none swap sw 0 0' | tee -a /etc/fstab
    fi

    log_success "Server setup complete!"
    log_info "Next steps:"
    echo "  1. Copy your project files to $APP_DIR"
    echo "  2. Configure .env file from .env.production template"
    echo "  3. Run: ./deploy.sh deploy"
    echo "  4. Run: ./deploy.sh ssl (to set up SSL certificates)"
}

# Generate secure secrets
generate_secrets() {
    log_info "Generating secure secrets..."

    echo "# Generated secrets - copy these to your .env file"
    echo "# ================================================"
    echo ""
    echo "DB_PASSWORD=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)"
    echo "JWT_SECRET=$(openssl rand -base64 64 | tr -dc 'a-zA-Z0-9' | head -c 64)"
    echo "JWT_REFRESH_SECRET=$(openssl rand -base64 64 | tr -dc 'a-zA-Z0-9' | head -c 64)"
    echo "ENCRYPTION_KEY=$(openssl rand -base64 32 | tr -dc 'a-zA-Z0-9' | head -c 32)"
    echo "GRAFANA_PASSWORD=$(openssl rand -base64 16 | tr -dc 'a-zA-Z0-9' | head -c 16)"
}

# Deploy application
deploy() {
    log_info "Deploying AI Anti-Spam Shield..."
    cd $APP_DIR

    # Check if .env exists
    if [ ! -f .env ]; then
        log_error ".env file not found! Copy .env.production to .env and configure it."
        exit 1
    fi

    # Create required directories
    mkdir -p certbot/conf certbot/www

    # Pull latest images and build
    log_info "Building Docker images..."
    docker-compose -f $COMPOSE_FILE build --no-cache

    # Start services
    log_info "Starting services..."
    docker-compose -f $COMPOSE_FILE up -d

    # Wait for services to be healthy
    log_info "Waiting for services to start..."
    sleep 30

    # Run database migrations
    log_info "Running database migrations..."
    docker-compose -f $COMPOSE_FILE exec -T backend npx prisma migrate deploy || log_warning "Migration failed or not needed"

    # Show status
    docker-compose -f $COMPOSE_FILE ps

    log_success "Deployment complete!"
    log_info "Access your API at: http://$(curl -s ifconfig.me)"
}

# Setup SSL with Let's Encrypt
setup_ssl() {
    log_info "Setting up SSL certificates..."
    cd $APP_DIR

    # Check domain configuration
    if [ -z "$1" ]; then
        log_error "Please provide your domain: ./deploy.sh ssl your-domain.com email@example.com"
        exit 1
    fi

    DOMAIN=$1
    EMAIL=${2:-admin@$DOMAIN}

    log_info "Domain: $DOMAIN"
    log_info "Email: $EMAIL"

    # Stop nginx temporarily
    docker-compose -f $COMPOSE_FILE stop nginx || true

    # Get certificates
    log_info "Obtaining SSL certificate..."
    docker run --rm \
        -v "$APP_DIR/certbot/conf:/etc/letsencrypt" \
        -v "$APP_DIR/certbot/www:/var/www/certbot" \
        -p 80:80 \
        certbot/certbot certonly \
        --standalone \
        --email $EMAIL \
        --agree-tos \
        --no-eff-email \
        -d $DOMAIN

    # Update nginx configuration
    log_info "Updating Nginx configuration for SSL..."
    sed -i "s/your-domain.com/$DOMAIN/g" nginx/conf.d/default.conf

    # Enable HTTPS configuration in nginx
    sed -i 's/# server {/server {/g' nginx/conf.d/default.conf
    sed -i 's/#     listen 443/    listen 443/g' nginx/conf.d/default.conf
    sed -i 's/#     /    /g' nginx/conf.d/default.conf

    # Enable HTTP to HTTPS redirect
    sed -i 's/# location \/ {$/location \/ {/g' nginx/conf.d/default.conf
    sed -i 's/#     return 301/    return 301/g' nginx/conf.d/default.conf

    # Restart nginx
    docker-compose -f $COMPOSE_FILE up -d nginx

    log_success "SSL setup complete!"
    log_info "Your API is now available at: https://$DOMAIN"
}

# Update application
update() {
    log_info "Updating AI Anti-Spam Shield..."
    cd $APP_DIR

    # Pull latest code (if using git)
    if [ -d .git ]; then
        log_info "Pulling latest code..."
        git pull origin main
    fi

    # Rebuild and restart
    log_info "Rebuilding containers..."
    docker-compose -f $COMPOSE_FILE build --no-cache
    docker-compose -f $COMPOSE_FILE up -d

    # Run migrations
    log_info "Running migrations..."
    docker-compose -f $COMPOSE_FILE exec -T backend npx prisma migrate deploy || log_warning "Migration failed or not needed"

    log_success "Update complete!"
}

# View logs
view_logs() {
    cd $APP_DIR
    SERVICE=${1:-""}

    if [ -z "$SERVICE" ]; then
        docker-compose -f $COMPOSE_FILE logs -f --tail=100
    else
        docker-compose -f $COMPOSE_FILE logs -f --tail=100 $SERVICE
    fi
}

# Check status
check_status() {
    cd $APP_DIR

    log_info "Container Status:"
    docker-compose -f $COMPOSE_FILE ps

    echo ""
    log_info "Resource Usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"

    echo ""
    log_info "Disk Usage:"
    df -h | grep -E '^/dev|Filesystem'

    echo ""
    log_info "Docker Disk Usage:"
    docker system df
}

# Backup database
backup() {
    log_info "Creating backup..."
    cd $APP_DIR

    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/aishield_backup_$TIMESTAMP.sql"

    # Backup PostgreSQL
    docker-compose -f $COMPOSE_FILE exec -T postgres pg_dump -U aishield aishield > $BACKUP_FILE
    gzip $BACKUP_FILE

    log_success "Backup created: ${BACKUP_FILE}.gz"

    # Keep only last 7 backups
    ls -t $BACKUP_DIR/*.gz | tail -n +8 | xargs -r rm
    log_info "Old backups cleaned up"
}

# Restore database
restore() {
    if [ -z "$1" ]; then
        log_error "Please provide backup file: ./deploy.sh restore /path/to/backup.sql.gz"
        exit 1
    fi

    cd $APP_DIR
    BACKUP_FILE=$1

    log_warning "This will overwrite the current database!"
    read -p "Are you sure? (y/N) " -n 1 -r
    echo

    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Restoring from $BACKUP_FILE..."

        if [[ $BACKUP_FILE == *.gz ]]; then
            gunzip -c $BACKUP_FILE | docker-compose -f $COMPOSE_FILE exec -T postgres psql -U aishield aishield
        else
            cat $BACKUP_FILE | docker-compose -f $COMPOSE_FILE exec -T postgres psql -U aishield aishield
        fi

        log_success "Restore complete!"
    else
        log_info "Restore cancelled"
    fi
}

# Stop all services
stop() {
    log_info "Stopping all services..."
    cd $APP_DIR
    docker-compose -f $COMPOSE_FILE down
    log_success "All services stopped"
}

# Clean up Docker resources
cleanup() {
    log_info "Cleaning up Docker resources..."
    docker system prune -af
    docker volume prune -f
    log_success "Cleanup complete"
}

# Main script
case "${1:-}" in
    setup)
        check_root
        setup_server
        ;;
    secrets)
        generate_secrets
        ;;
    deploy)
        check_root
        deploy
        ;;
    ssl)
        check_root
        setup_ssl "$2" "$3"
        ;;
    update)
        check_root
        update
        ;;
    logs)
        view_logs "$2"
        ;;
    status)
        check_status
        ;;
    backup)
        check_root
        backup
        ;;
    restore)
        check_root
        restore "$2"
        ;;
    stop)
        check_root
        stop
        ;;
    cleanup)
        check_root
        cleanup
        ;;
    *)
        echo "AI Anti-Spam Shield - Deployment Script"
        echo ""
        echo "Usage: $0 {command}"
        echo ""
        echo "Commands:"
        echo "  setup    - Initial server setup (install Docker, configure firewall)"
        echo "  secrets  - Generate secure secrets for .env file"
        echo "  deploy   - Deploy the application"
        echo "  ssl      - Setup SSL certificates (./deploy.sh ssl domain.com email@example.com)"
        echo "  update   - Update and redeploy the application"
        echo "  logs     - View logs (./deploy.sh logs [service])"
        echo "  status   - Check service status"
        echo "  backup   - Backup the database"
        echo "  restore  - Restore database from backup"
        echo "  stop     - Stop all services"
        echo "  cleanup  - Clean up Docker resources"
        ;;
esac
