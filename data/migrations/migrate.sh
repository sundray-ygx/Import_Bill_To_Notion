#!/bin/bash
# Database Migration Script
# This script applies all pending migrations to the database

set -e

# Configuration
DB_PATH="/home/ygx/python/Import_Bill_To_Notion/data/database.sqlite"
MIGRATIONS_DIR="/home/ygx/python/Import_Bill_To_Notion/data/migrations"
LOCK_FILE="${MIGRATIONS_DIR}/.migrate_lock"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    log_error "Database not found at $DB_PATH"
    exit 1
fi

# Create migrations table if not exists
sqlite3 "$DB_PATH" "
CREATE TABLE IF NOT EXISTS _migrations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_id TEXT UNIQUE NOT NULL,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
" 2>/dev/null

# Get applied migrations
applied_migrations=$(sqlite3 "$DB_PATH" "SELECT migration_id FROM _migrations ORDER BY id;" 2>/dev/null || echo "")

# Apply migrations in order
for migration_file in "${MIGRATIONS_DIR}"/[0-9][0-9][0-9]_*.sql; do
    if [ ! -f "$migration_file" ]; then
        log_warn "No migration files found in $MIGRATIONS_DIR"
        exit 0
    fi

    migration_name=$(basename "$migration_file")
    migration_id="${migration_name%.sql}"

    # Check if migration already applied
    if echo "$applied_migrations" | grep -q "^${migration_id}$"; then
        log_info "Skipping already applied migration: $migration_id"
        continue
    fi

    # Apply migration
    log_info "Applying migration: $migration_id"
    if sqlite3 "$DB_PATH" < "$migration_file"; then
        sqlite3 "$DB_PATH" "INSERT INTO _migrations (migration_id) VALUES ('$migration_id');"
        log_info "Migration applied successfully: $migration_id"
    else
        log_error "Failed to apply migration: $migration_id"
        exit 1
    fi
done

log_info "All migrations applied successfully"
