#!/bin/bash
# Docker management script for TelegramNewsFeedBot

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if .env file exists
check_env_file() {
    if [[ ! -f ".env" ]]; then
        print_warning ".env file not found"
        if [[ -f ".env.docker" ]]; then
            print_status "Example .env.docker file available. Copy it to .env and update with your values:"
            echo "  cp .env.docker .env"
            echo "  nano .env  # Edit with your bot token and admin IDs"
        elif [[ -f ".env.example" ]]; then
            print_status "Example .env.example file available. Copy it to .env and update with your values:"
            echo "  cp .env.example .env"
            echo "  nano .env  # Edit with your bot token and admin IDs"
        fi
        return 1
    fi
    return 0
}

# Function to create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    mkdir -p data logs media_cache
    print_status "Directories created: data/, logs/, media_cache/"
}

# Function to build the Docker image
build_image() {
    print_status "Building Docker image..."
    docker build -t telegram-news-bot .
    print_status "Docker image built successfully"
}

# Function to run with docker-compose (production)
run_production() {
    if ! check_env_file; then
        exit 1
    fi
    
    create_directories
    print_status "Starting bot in production mode with docker-compose..."
    docker compose up -d
    print_status "Bot started. Use 'docker compose logs -f telegram-bot' to view logs"
}

# Function to run with docker-compose (development)
run_development() {
    if ! check_env_file; then
        exit 1
    fi
    
    create_directories
    print_status "Starting bot in development mode with PostgreSQL and management tools..."
    docker compose -f docker-compose.dev.yml up -d
    print_status "Development environment started!"
    echo ""
    echo "Access the management interfaces:"
    echo "  📊 pgAdmin (Database): http://localhost:8080 (admin@newsbot.dev / admin)"
    echo "  🔧 Redis Commander: http://localhost:8081"
    echo ""
    print_status "Use 'docker compose -f docker-compose.dev.yml logs -f telegram-bot' to view logs"
}

# Function to run with plain docker
run_docker() {
    if ! check_env_file; then
        exit 1
    fi
    
    create_directories
    build_image
    
    print_status "Starting bot with plain Docker..."
    docker run -d \
        --name telegram-news-bot \
        --env-file .env \
        -v "$(pwd)/data:/app/data" \
        -v "$(pwd)/logs:/app/logs" \
        -v "$(pwd)/media_cache:/app/media_cache" \
        --restart unless-stopped \
        telegram-news-bot
    
    print_status "Bot started. Use 'docker logs -f telegram-news-bot' to view logs"
}

# Function to stop services
stop_services() {
    print_status "Stopping services..."
    
    # Stop docker-compose services
    if docker compose ps &>/dev/null; then
        docker compose down
    fi
    
    if docker compose -f docker-compose.dev.yml ps &>/dev/null; then
        docker compose -f docker-compose.dev.yml down
    fi
    
    # Stop standalone container
    if docker ps -q -f name=telegram-news-bot | grep -q .; then
        docker stop telegram-news-bot
        docker rm telegram-news-bot
    fi
    
    print_status "All services stopped"
}

# Function to show logs
show_logs() {
    if docker compose ps -q telegram-bot &>/dev/null; then
        docker compose logs -f telegram-bot
    elif docker compose -f docker-compose.dev.yml ps -q telegram-bot &>/dev/null; then
        docker compose -f docker-compose.dev.yml logs -f telegram-bot
    elif docker ps -q -f name=telegram-news-bot | grep -q .; then
        docker logs -f telegram-news-bot
    else
        print_error "No running bot container found"
        exit 1
    fi
}

# Function to show status
show_status() {
    print_status "Checking service status..."
    
    echo ""
    echo "Docker Compose (Production):"
    if docker compose ps &>/dev/null; then
        docker compose ps
    else
        echo "  Not running"
    fi
    
    echo ""
    echo "Docker Compose (Development):"
    if docker compose -f docker-compose.dev.yml ps &>/dev/null; then
        docker compose -f docker-compose.dev.yml ps
    else
        echo "  Not running"
    fi
    
    echo ""
    echo "Standalone Container:"
    if docker ps -f name=telegram-news-bot --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -q telegram-news-bot; then
        docker ps -f name=telegram-news-bot --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    else
        echo "  Not running"
    fi
}

# Help function
show_help() {
    echo "Docker management script for TelegramNewsFeedBot"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  prod, production     Start in production mode (docker-compose with Redis)"
    echo "  dev, development     Start in development mode (PostgreSQL + management tools)"
    echo "  docker               Start with plain Docker (no external services)"
    echo "  build                Build the Docker image"
    echo "  stop                 Stop all services"
    echo "  logs                 Show logs from the bot"
    echo "  status               Show status of all services"
    echo "  help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 prod              # Start production environment"
    echo "  $0 dev               # Start development environment"
    echo "  $0 logs              # View bot logs"
    echo "  $0 stop              # Stop all services"
}

# Main script logic
case "${1:-help}" in
    "prod"|"production")
        run_production
        ;;
    "dev"|"development")
        run_development
        ;;
    "docker")
        run_docker
        ;;
    "build")
        build_image
        ;;
    "stop")
        stop_services
        ;;
    "logs")
        show_logs
        ;;
    "status")
        show_status
        ;;
    "help"|*)
        show_help
        ;;
esac