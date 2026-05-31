# Database Migrations

This directory contains SQL migration scripts for the application database.

## Quick Start

Run the migration script to apply all pending migrations:

```bash
./data/migrations/migrate.sh
```

## Applying Individual Migrations

### Migration 001 - Add session_timeout_minutes (2026-02-28)

Added `session_timeout_minutes` column to `users` table for configurable session timeout.

```bash
sqlite3 /home/ygx/python/Import_Bill_To_Notion/data/database.sqlite < /home/ygx/python/Import_Bill_To_Notion/data/migrations/001_add_session_timeout.sql
```

### Migration 002 - Add review fields (2026-02-28)

Added review-related columns to `user_notion_configs` table for monthly, quarterly, and yearly review functionality.

```bash
sqlite3 /home/ygx/python/Import_Bill_To_Notion/data/database.sqlite < /home/ygx/python/Import_Bill_To_Notion/data/migrations/002_add_review_fields.sql
```

## Migration History

| ID | Date | Description |
|----|------|-------------|
| 001 | 2026-02-28 | Add session_timeout_minutes column to users table |
| 002 | 2026-02-28 | Add review-related columns to user_notion_configs table (monthly/quarterly/yearly review DB and template IDs) |

## Current Schema

### users (13 columns)
- id, username, email, password_hash
- is_superuser, is_active, require_password_change
- created_at, updated_at, last_login
- login_attempts, locked_until, session_timeout_minutes

### user_sessions (9 columns)
- id, user_id, token, refresh_token
- expires_at, created_at
- ip_address, user_agent, is_revoked

### user_notion_configs (16 columns)
- id, user_id
- notion_api_key, notion_income_database_id, notion_expense_database_id
- config_name, is_verified, last_verified_at
- notion_monthly_review_db, notion_monthly_template_id
- notion_quarterly_review_db, notion_quarterly_template_id
- notion_yearly_review_db, notion_yearly_template_id
- created_at, updated_at

### user_uploads (10 columns)
- id, user_id
- file_name, original_file_name, file_path, file_size
- platform, upload_type, status
- created_at

### import_history (12 columns)
- id, user_id, upload_id
- total_records, imported_records, skipped_records, failed_records
- status, error_message
- started_at, completed_at, duration_seconds

### system_settings (6 columns)
- id, setting_key, setting_value, description
- updated_by, updated_at

### audit_logs (9 columns)
- id, user_id
- action, resource_type, resource_id
- ip_address, user_agent, details
- created_at

## Creating New Migrations

1. Create a new SQL file with the format `XXX_description.sql` (e.g., `003_add_new_feature.sql`)
2. Add your ALTER TABLE or other SQL statements
3. Update this README with the new migration details
4. The migration script will automatically apply it in order

## Migration Tracking

The `_migrations` table tracks which migrations have been applied:

```sql
SELECT * FROM _migrations ORDER BY id;
```
