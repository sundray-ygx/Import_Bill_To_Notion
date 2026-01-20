# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python-based bill import service with multi-user authentication and management capabilities. The service automatically imports payment records from Alipay (支付宝), WeChat Pay (微信支付), and UnionPay (银联) into Notion databases. Features include user authentication, role-based access control, admin management interface, bill history tracking, and multi-tenant support.

### Key Features
- **User Authentication**: Registration, login, password management, JWT-based session handling
- **Multi-User Support**: Each user has isolated data and configuration
- **Admin Dashboard**: User management, system settings, audit logs
- **Bill History**: Track all import operations with detailed status
- **Personal Settings**: Customizable Notion configuration per user
- **Role-Based Access**: Admin and regular user roles with different permissions

## Development Commands

### Running the Application

```bash
# Web service mode (FastAPI + Uvicorn)
python3 -m web_service.main

# Scheduler mode (background automated imports)
python3 main.py --schedule

# CLI mode (single file import)
python3 main.py --file <bill-file-path> [--platform <alipay/wechat/unionpay>]
```

### Testing

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest tests/test_wechat_parser.py -v

# Run tests with coverage
python -m pytest --cov=. --cov-report=html
```

### Dependency Management

```bash
# Install dependencies
pip install -r requirements.txt

# Install web service dependencies
pip install -r web_service/requirements.txt
```

## Architecture

### Core Import Pipeline

The import flow follows this path: `file -> parser -> notion format -> NotionClient -> database`

1. **Entry Points**
   - `main.py` - CLI and scheduler entry point
   - `web_service/main.py` - FastAPI web service entry point

2. **Import Orchestration** (`importer.py`)
   - `import_bill()` - Main function that validates config, detects platform, parses bill, and triggers Notion import
   - Coordinates parser selection and Notion API calls

3. **Parser System** (`parsers/`)
   - `base_parser.py` - Abstract base class defining the parser interface
     - `parse()` - Parse bill file into DataFrame
     - `get_platform()` - Return platform name
     - `to_notion_format()` - Convert parsed data to Notion format (filters "不计收支" records)
     - `_convert_to_notion()` - Abstract method for per-record conversion
   - `__init__.py` - Auto-detection logic: reads first 20 lines, checks platform-specific keywords
   - Platform-specific parsers: `alipay_parser.py`, `wechat_parser.py`, `unionpay_parser.py`

4. **Notion Integration** (`notion_api.py`)
   - `NotionClient` class wraps the `notion_client` SDK
   - `create_page()` - Creates a single page, routes to income/expense database based on "Income Expense" field
   - `batch_import()` - Processes records in batches (default: 10) with detailed logging
   - `verify_connection()` - Tests API key and database access

5. **Configuration** (`config.py`)
   - Uses `python-dotenv` for environment variable management
   - Required: `NOTION_API_KEY`, `NOTION_INCOME_DATABASE_ID`, `NOTION_EXPENSE_DATABASE_ID`
   - Optional: `DEFAULT_BILL_DIR`, `SCHEDULER_CRON`, `LOG_LEVEL`

6. **Utilities** (`utils.py`)
   - `BeijingFormatter` - Custom logging formatter for UTC+8 timezone
   - `setup_logging()` - Configure logging with file and console handlers
   - `read_file_lines()` - Read file with multiple encoding fallbacks
   - `find_header_and_encoding()` - Detect CSV header line and encoding

7. **Scheduler** (`scheduler.py`)
   - `BillScheduler` - Background scheduler using APScheduler
   - `auto_import_bills()` - Automatically import latest bill from DEFAULT_BILL_DIR
   - `get_job_status()` - Get scheduler status and next run time

8. **Authentication System** (`auth.py`, `database.py`, `models.py`, `schemas.py`)
   - `auth.py` - Authentication utilities (password hashing, JWT tokens, session management)
   - `database.py` - Database connection and session management
   - `models.py` - SQLAlchemy ORM models (User, Bill, AuditLog)
   - `schemas.py` - Pydantic schemas for request/response validation
   - `dependencies.py` - FastAPI dependencies for authentication and authorization

9. **User Management** (`web_service/routes/users.py`, `web_service/routes/admin.py`)
   - User registration, login, logout
   - Profile management and password change
   - Admin panel for user management
   - Audit log tracking
   - **Notion Configuration Verification**: Step-by-step verification with real-time progress
     - `GET /api/user/notion-config/verify-step?step={api_key|income_db|expense_db}` - Incremental verification
     - Returns progress status for each step with detailed error messages
     - Frontend displays progress bar and step-by-step status updates

10. **Bill History** (`web_service/routes/bills.py`)
    - Track all bill import operations
    - Store import status and results
    - Per-user bill history with filtering

### Web Service Structure

```
web_service/
├── main.py              # FastAPI app initialization, Uvicorn server
├── routes/
│   ├── __init__.py      # Route package initialization
│   ├── upload.py        # File upload and import endpoints
│   ├── auth.py          # Authentication endpoints (login, register)
│   ├── users.py         # User profile and settings endpoints
│   ├── bills.py         # Bill history and management endpoints
│   └── admin.py         # Admin panel endpoints (user management, audit logs)
├── services/
│   ├── __init__.py      # Service package initialization
│   ├── file_service.py  # File management (list, delete, read)
│   └── user_file_service.py  # User-specific file management
├── templates/           # Jinja2 HTML templates
│   ├── index.html       # Home page
│   ├── login.html       # Login page
│   ├── register.html    # Registration page
│   ├── setup.html       # Initial setup page
│   ├── settings.html    # User settings page
│   ├── history.html     # Bill history page
│   ├── bill_management.html   # Bill upload and management
│   ├── service_management.html # Service status
│   ├── log_management.html     # Log viewer
│   ├── admin/           # Admin panel templates
│   │   ├── users.html      # User management
│   │   ├── settings.html  # System settings
│   │   └── audit_logs.html # Audit logs
│   └── components/      # Reusable components
│       └── navbar.html  # Navigation bar
├── static/             # CSS and JavaScript assets
│   ├── css/
│   │   ├── style.css        # Main stylesheet
│   │   ├── auth.css         # Authentication pages
│   │   ├── admin.css        # Admin panel
│   │   ├── settings.css     # Settings page
│   │   └── history.css      # History page
│   └── js/
│       ├── auth.js          # Authentication logic
│       ├── settings.js      # Settings page logic
│       ├── history.js       # History page logic
│       └── admin-*.js       # Admin panel scripts
├── uploads/            # User-uploaded bill files
└── logs/               # Web service logs
```

### Data Flow

1. **File Upload/Selection** → Platform auto-detection (or manual)
2. **Parsing** → Multiple encoding support (GBK, UTF-8), header row detection, pandas DataFrame
3. **Filtering** → Records with `income_expense == '不计收支'` are excluded
4. **Transformation** → Parser converts to Notion property format
5. **Database Routing** → Records routed to income or expense database based on `Income Expense` field
6. **Batch Import** → 10 records per batch to optimize API usage

### Notion Database Schema Requirements

Both income and expense databases require these properties:
- **Name** (title) - Transaction description
- **Price** (number) - Transaction amount
- **Date** (date) - Transaction date
- **Category** (select) - Transaction category
- **Counterparty** (rich_text) - Merchant/payee name
- **Remarks** (rich_text) - Additional notes
- **Income/Expense** (select) - Used for database routing ("收入" or "支出")
- **Merchant Tracking Number** (rich_text) - Merchant order ID
- **Transaction Number** (rich_text) - Transaction ID
- **Payment Method** (select) - Payment method
- **From** (select) - Payment platform (Alipay/WeChat/UnionPay)

### Key Implementation Details

- **Auto-detection**: Reads first 20 lines in GBK or UTF-8, checks for platform keywords
- **Encoding handling**: Tries GBK first, falls back to UTF-8 for Chinese bill files
- **Batch processing**: Default 10 records per batch to balance API efficiency and error recovery
- **Logging**: Beijing timezone support, masked database IDs in logs
- **Income/Expense routing**: `NotionClient.create_page()` checks `Income Expense.select.name` for "收入" to route to income database

## Environment Configuration

Create a `.env` file (see `.env.example`):

```bash
# Notion Configuration
NOTION_API_KEY=secret_*
NOTION_INCOME_DATABASE_ID=income_db_id
NOTION_EXPENSE_DATABASE_ID=expense_db_id

# Database Configuration
DATABASE_URL=sqlite:///./data/users.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Bill File Configuration
DEFAULT_BILL_DIR=./bills
DEFAULT_BILL_PLATFORM=alipay

# Scheduler Configuration
SCHEDULER_ENABLED=false
SCHEDULER_CRON="0 0 1 * *"  # Monthly on 1st at 00:00

# Log Configuration
LOG_LEVEL=INFO

# Application Configuration
APP_NAME=Notion Bill Importer
APP_VERSION=2.0.0
```

## Code Style Guidelines

### General Principles
- Follow PEP 8 for Python code style
- Use type hints for function parameters and return values
- Write docstrings for all classes and public methods
- Keep functions focused and under 50 lines when possible
- Avoid over-engineering - choose the simplest solution that works

### Import Organization
```python
# 1. Standard library imports
import os
import logging
from typing import List, Optional

# 2. Third-party imports
import pandas as pd
from notion_client import Client

# 3. Local imports
from config import Config
from parsers.base_parser import BaseBillParser
```

### Error Handling
- Use specific exception types
- Log errors with context information
- Provide user-friendly error messages
- Never expose sensitive data (API keys, database IDs) in logs

### Logging Best Practices
- Use appropriate log levels (DEBUG, INFO, WARNING, ERROR)
- Include context in log messages (file names, record counts, etc.)
- Mask sensitive information (database IDs, API keys)
- Use structured logging with consistent format

## Adding New Features

### Adding a New Bill Parser

1. Create a new parser file in `parsers/` (e.g., `new_platform_parser.py`)
2. Inherit from `BaseBillParser`
3. Implement required abstract methods:
   ```python
   class NewPlatformParser(BaseBillParser):
       def parse(self) -> pd.DataFrame:
           # Parse CSV and return DataFrame
           pass

       def get_platform(self) -> str:
           return "New Platform"

       def _convert_to_notion(self, record) -> dict:
           # Convert DataFrame row to Notion properties
           pass
   ```
4. Add detection keywords to `parsers/__init__.py`
5. Register the parser in `PARSERS` list and `get_parser_by_platform()`

### Adding a New Web Service Route

1. Create a new route file in `web_service/routes/`
2. Define FastAPI router:
   ```python
   from fastapi import APIRouter, HTTPException

   router = APIRouter()

   @router.get("/endpoint")
   async def get_data():
       return {"data": "value"}
   ```
3. Include router in `web_service/main.py`:
   ```python
   from .routes import new_route
   app.include_router(new_route.router, prefix="/api", tags=["new_route"])
   ```

### Adding Configuration Options

1. Add environment variable to `.env.example`
2. Add field to `Config` class in `config.py`:
   ```python
   NEW_OPTION = os.getenv("NEW_OPTION", "default_value")
   ```
3. Update `validate()` method if required
4. Document in README.md

## Testing Strategy

### Parser Testing
- Test with real bill samples from each platform
- Verify encoding detection for GBK and UTF-8 files
- Test header row detection accuracy
- Validate Notion format output

### Integration Testing
- Test Notion API connection with `verify_connection()`
- Verify database routing (income vs expense)
- Test batch import with various record counts
- Validate error handling for invalid data

### Web Service Testing
- Test file upload endpoint
- Verify platform auto-detection
- Test import status tracking
- Validate file list and delete operations

## Common Tasks

### Debugging Import Issues

1. Enable DEBUG logging in `.env`:
   ```
   LOG_LEVEL=DEBUG
   ```

2. Check parser output:
   ```python
   parser = get_parser(file_path)
   df = parser.parse()
   print(df.head())
   ```

3. Verify Notion format:
   ```python
   records = parser.to_notion_format()
   print(records[0])
   ```

4. Test Notion connection:
   ```python
   client = NotionClient()
   print(client.verify_connection())
   ```

### Updating Notion Database Schema

1. Update schema requirements in CLAUDE.md
2. Modify `_convert_to_notion()` in affected parsers
3. Update `NotionClient._clean_properties()` if needed
4. Test with sample records
5. Update README.md documentation

### Modifying Batch Size

1. Edit `notion_api.py`:
   ```python
   def batch_import(self, records: list, batch_size: int = 20):  # Change from 10
   ```

2. Consider API rate limits and error recovery
3. Test with large datasets

## Deployment Considerations

### Production Configuration
- Use strong, unique API keys
- Set appropriate LOG_LEVEL (INFO or WARNING)
- Configure SCHEDULER_CRON for desired frequency
- Ensure DEFAULT_BILL_DIR has proper permissions

### Running as a Service

#### Using systemd
```bash
# Copy web_service/web_service.service to /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bill-import
sudo systemctl start bill-import
```

#### Using Docker (if implemented)
```bash
docker build -t bill-import .
docker run -d --env-file .env -v ./bills:/app/bills bill-import
```

### Monitoring
- Monitor `bill_import.log` for CLI/scheduler mode
- Monitor `web_service/logs/web_service.log` for web service
- Set up log rotation for long-running deployments
- Track Notion API usage to avoid rate limits

## Security Best Practices

1. **Never commit `.env` files** - Use `.env.example` as template
2. **Rotate API keys regularly** - Especially if repository is public
3. **Limit Notion integration permissions** - Grant only necessary database access
4. **Validate file uploads** - Check file types, sizes, and content
5. **Sanitize user input** - Prevent injection attacks
6. **Use HTTPS in production** - Protect API credentials in transit
7. **Mask sensitive data in logs** - API keys, database IDs, personal info
8. **User data isolation** - Each user's data is isolated by user_id
9. **Secure password storage** - Use bcrypt with salt for password hashing
10. **JWT token security** - Use short expiration times and secure secret keys
11. **SQL injection prevention** - Use SQLAlchemy ORM parameterized queries
12. **Rate limiting** - Implement rate limiting on authentication endpoints

## Troubleshooting

### Common Issues

**Issue**: "Cannot detect format"
- **Solution**: Check if file is valid CSV, verify encoding, use `--platform` flag

**Issue**: "Missing required config"
- **Solution**: Verify `.env` file exists and contains all required fields

**Issue**: Notion API rate limit errors
- **Solution**: Increase batch delay or reduce batch size in `notion_api.py`

**Issue**: Encoding errors when reading CSV
- **Solution**: Ensure file is saved with correct encoding (GBK or UTF-8)

**Issue**: Scheduler not running
- **Solution**: Check `SCHEDULER_ENABLED=true` and verify cron expression syntax

## Project Maintenance

### Regular Updates
- Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- Review and update Notion SDK for new features
- Monitor Notion API changes and deprecations
- Test with latest bill formats from payment platforms

### Documentation Updates
- Update README.md when adding features
- Maintain CLAUDE.md for development guidance
- Document any breaking changes in UPDATE_LOG section
- Keep `.env.example` synchronized with Config class

### Code Review Checklist
- [ ] New code follows project style guidelines
- [ ] Functions have appropriate docstrings
- [ ] Error handling is comprehensive
- [ ] Logging is added at key points
- [ ] Tests are included for new functionality
- [ ] Documentation is updated
- [ ] Sensitive data is properly masked
- [ ] No hardcoded credentials or IDs
