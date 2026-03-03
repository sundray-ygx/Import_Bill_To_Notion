#!/bin/bash
# Bill Import Service - Startup Script
# This script checks environment configuration before starting the service

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

echo "=================================================="
echo "Bill Import Service - Startup Check"
echo "=================================================="
echo

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo -e "${RED}❌ Error: .env file not found!${NC}"
    echo
    echo "Please run the setup script first:"
    echo "  python3 scripts/setup_env.py"
    echo
    exit 1
fi

# Source .env file
set -a
source .env
set +a

# Check required environment variables
check_env_var() {
    local var_name=$1
    local var_value=${!var_name}

    if [ -z "$var_value" ] || [[ "$var_value" == *"your-"* ]] || [[ "$var_value" == *"change-this"* ]]; then
        echo -e "${YELLOW}⚠️  Warning: $var_name is not configured${NC}"
        return 1
    fi
    return 0
}

# Critical variables for multi-tenant mode
if [ "$MULTI_TENANT_ENABLED" = "true" ]; then
    echo "📋 Checking multi-tenant configuration..."

    MISSING=0

    if ! check_env_var "SECRET_KEY"; then
        MISSING=1
    fi

    if ! check_env_var "PASSWORD_ENCRYPTION_KEY"; then
        MISSING=1
    fi

    if [ $MISSING -eq 1 ]; then
        echo
        echo -e "${RED}❌ Required environment variables are missing!${NC}"
        echo
        echo "Please configure these variables in .env:"
        echo "  - SECRET_KEY"
        echo "  - PASSWORD_ENCRYPTION_KEY"
        echo
        echo "Generate keys with:"
        echo "  python3 -c \"import secrets; print(secrets.token_urlsafe(48))\"  # for SECRET_KEY"
        echo "  python3 -c \"import secrets; print(secrets.token_urlsafe(32))\"  # for PASSWORD_ENCRYPTION_KEY"
        echo
        exit 1
    fi

    echo -e "${GREEN}✅ Multi-tenant configuration OK${NC}"
fi

# Check database directory
DATABASE_PATH=$(echo "$DATABASE_URL" | sed 's|sqlite:///||')
DATABASE_DIR=$(dirname "$DATABASE_PATH")

if [ ! -d "$DATABASE_DIR" ]; then
    echo "📁 Creating database directory: $DATABASE_DIR"
    mkdir -p "$DATABASE_DIR"
fi

# Check uploads directory
UPLOADS_DIR="web_service/uploads"
if [ ! -d "$UPLOADS_DIR" ]; then
    echo "📁 Creating uploads directory: $UPLOADS_DIR"
    mkdir -p "$UPLOADS_DIR"
fi

# Check logs directory
LOGS_DIR="web_service/logs"
if [ ! -d "$LOGS_DIR" ]; then
    echo "📁 Creating logs directory: $LOGS_DIR"
    mkdir -p "$LOGS_DIR"
fi

echo
echo -e "${GREEN}✅ All checks passed! Starting service...${NC}"
echo

# Start the service
exec python3 -m web_service.main
