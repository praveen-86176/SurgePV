# Issue Tracker API

A production-grade Issue Tracker API built with FastAPI, SQLite/PostgreSQL, and SQLAlchemy following clean architecture principles.

## 🏗️ Architecture

This project follows clean architecture with clear separation of concerns:

```
app/
├── routers/          # API endpoints and request handling
├── services/         # Business logic layer
├── repositories/     # Data access layer
├── models/          # SQLAlchemy ORM models
├── schemas/         # Pydantic validation schemas
└── core/            # Configuration and database setup
```

## 🔹 Features

### Core Functionality
- ✅ **Issue Management**: Full CRUD with optimistic concurrency control
- ✅ **Comments**: Add comments with validation
- ✅ **Labels**: Globally unique labels with atomic assignment
- ✅ **Bulk Operations**: Transactional bulk status updates
- ✅ **CSV Import**: Batch issue creation with detailed error reporting
- ✅ **Reports**: Analytics for assignee performance and resolution times

### Technical Highlights
- 🔒 Optimistic concurrency control using version fields
- 🔄 Atomic transactions for data consistency
- ✅ Comprehensive validation with Pydantic
- 📊 Performance-optimized queries with proper indexing
- 🧪 Unit tests for core business logic
- 📝 Type hints throughout the codebase
- 🗄️ Database maintenance tools (backup, restore, cleanup, inspection)


## 🚀 Quick Start

### Prerequisites
- Python 3.13+ (or Python 3.11+)
- pip
- Git

### Installation

#### Option 1: Automated Setup (Recommended)

1. **Clone the repository**
```bash
git clone <repository-url>
cd SurgePV
```

2. **Run the setup script**
```bash
chmod +x setup.sh
./setup.sh
```

The setup script will:
- Create a virtual environment
- Install all dependencies
- Set up environment variables
- Initialize the database with sample data
- Start the development server

#### Option 2: Manual Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd SurgePV
```

2. **Create and activate virtual environment**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env if needed (default SQLite configuration works out of the box)
```

5. **Initialize the database**
```bash
python3 scripts/init_db.py
```

When prompted, type `y` to seed sample data (recommended for testing).

6. **Start the development server**

**Recommended (safe startup with port checking):**
```bash
./start_dev.sh
```

**Alternative (manual):**
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
# Or use the virtual environment directly:
./venv/bin/uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

**If you get "Address already in use" error:**
```bash
./kill_server.sh  # Kill existing processes
./start_dev.sh    # Start fresh
```


The API will be available at:
- **API**: `http://localhost:8000`
- **Interactive Docs**: `http://localhost:8000/docs`
- **Alternative Docs**: `http://localhost:8000/redoc`


## 📚 API Endpoints

### Issues
```
POST   /issues                    # Create a new issue
GET    /issues                    # List issues (with filtering & pagination)
GET    /issues/{id}               # Get issue by ID
PATCH  /issues/{id}               # Update issue (version check required)
POST   /issues/{id}/comments      # Add comment to issue
PUT    /issues/{id}/labels        # Replace issue labels (atomic)
POST   /issues/bulk-status        # Bulk update issue status (transactional)
POST   /issues/import             # Import issues from CSV
```

### Reports
```
GET    /reports/top-assignees     # Top assignees by resolved issues
GET    /reports/latency           # Average resolution time per assignee
```

## 📋 API Examples

### Create an Issue
```bash
curl -X POST "http://localhost:8000/issues" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fix login bug",
    "description": "Users cannot log in with email",
    "status": "open",
    "priority": "high",
    "assignee_id": 1
  }'
```

### Update an Issue (with version check)
```bash
curl -X PATCH "http://localhost:8000/issues/1" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Fix critical login bug",
    "status": "in_progress",
    "version": 1
  }'
```

### Add a Comment
```bash
curl -X POST "http://localhost:8000/issues/1/comments" \
  -H "Content-Type: application/json" \
  -d '{
    "body": "Started investigating the issue",
    "author_id": 2
  }'
```

### Replace Labels (Atomic)
```bash
curl -X PUT "http://localhost:8000/issues/1/labels" \
  -H "Content-Type: application/json" \
  -d '{
    "label_names": ["bug", "urgent", "backend"]
  }'
```

### Bulk Status Update
```bash
curl -X POST "http://localhost:8000/issues/bulk-status" \
  -H "Content-Type: application/json" \
  -d '{
    "issue_ids": [1, 2, 3],
    "status": "resolved"
  }'
```

### Import from CSV
```bash
curl -X POST "http://localhost:8000/issues/import" \
  -F "file=@sample_issues.csv"
```

CSV format:
```csv
title,description,status,priority,assignee_id
Fix login bug,Users cannot log in,open,high,1
Update docs,Documentation is outdated,open,low,2
```

### Get Reports
```bash
# Top assignees
curl "http://localhost:8000/reports/top-assignees?limit=10"

# Resolution latency
curl "http://localhost:8000/reports/latency"
```

## 🗄️ Database Schema

### Tables
- **users**: User accounts
- **issues**: Issue tracking with version control
- **comments**: Issue comments
- **labels**: Globally unique labels
- **issue_labels**: Many-to-many relationship

### Key Features
- Foreign key constraints for referential integrity
- Unique constraints on critical fields
- Indexes for query performance
- Timestamps for audit trails (using UTC)

## 🧪 Testing

### Run All Tests
```bash
pytest tests/ -v
```

### Run Specific Test File
```bash
pytest tests/test_services.py -v
```

### Run Specific Test
```bash
pytest tests/test_services.py::test_create_issue_success -v
```

### Run with Coverage
```bash
pytest tests/ --cov=app --cov-report=html
```

View coverage report:
```bash
open htmlcov/index.html  # macOS
# or
xdg-open htmlcov/index.html  # Linux
```

### Test Results
All tests are passing:
- ✅ Issue creation with validation
- ✅ Optimistic concurrency control
- ✅ Comment management
- ✅ Label assignment (atomic)
- ✅ Bulk operations
- ✅ Report generation

## 🗄️ Database Maintenance

The project includes comprehensive database maintenance tools in the `scripts/` directory.

### Backup & Restore

**1. Create Backup**
Creates a timestamped backup in the `backups/` directory.
```bash
python3 scripts/backup_db.py backup
```

**2. List Backups**
Shows all available backups.
```bash
python3 scripts/backup_db.py list
```

**3. Restore Database**
Restores from a selected backup (includes safety check to backup current state first).
```bash
python3 scripts/backup_db.py restore
```

### Inspection & Health

**1. View Statistics**
Shows record counts, issue status breakdown, and recent activity.
```bash
python3 scripts/inspect_db.py stats
```

**2. Health Check**
Verifies data integrity (foreign keys, timestamps, orphaned records).
```bash
python3 scripts/inspect_db.py health
```

**3. List Data**
```bash
python3 scripts/inspect_db.py users   # List all users
python3 scripts/inspect_db.py labels  # List all labels
```

### Cleanup & Optimization

**1. Maintenance Summary**
Shows recommendations for cleanup (old issues, unused labels).
```bash
python3 scripts/cleanup_db.py summary
```

**2. Optimize Database**
Runs VACUUM to reclaim space (SQLite only).
```bash
python3 scripts/cleanup_db.py vacuum
```

**3. Clean Old Data**
```bash
python3 scripts/cleanup_db.py old-issues     # Remove resolved issues > 90 days
python3 scripts/cleanup_db.py unused-labels  # Remove labels with no issues
```

### Reset Database

**⚠️ WARNING: Deletes ALL data**
```bash
python3 scripts/init_db.py
# Or using the cleanup tool:
python3 scripts/cleanup_db.py reset
```


## 🔧 Configuration

### Environment Variables

Create a `.env` file (or copy from `.env.example`):

```env
# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./issue_tracker.db
DATABASE_ECHO=false

# API Configuration
API_TITLE=Issue Tracker API
API_VERSION=1.0.0
API_DESCRIPTION=A production-grade issue tracking system

# For PostgreSQL (optional):
# DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/issue_tracker
```

### Switching to PostgreSQL

1. Update `.env`:
```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/issue_tracker
```

2. Install PostgreSQL driver (already in requirements.txt):
```bash
pip install asyncpg psycopg2-binary
```

3. Create the database:
```bash
createdb issue_tracker
```

4. Initialize:
```bash
python3 scripts/init_db.py
```

## 📦 Dependencies

### Core
- **fastapi**: Modern web framework
- **uvicorn**: ASGI server
- **sqlalchemy**: ORM with async support
- **pydantic**: Data validation
- **asyncpg**: Async PostgreSQL driver
- **alembic**: Database migrations
- **python-dotenv**: Environment management

### Development & Testing
- **pytest**: Testing framework
- **pytest-asyncio**: Async test support
- **httpx**: HTTP client for testing
- **black**: Code formatting
- **isort**: Import sorting
- **mypy**: Type checking

### Utilities
- **pandas**: CSV processing
- **python-multipart**: File upload support

## 🏛️ Design Decisions

### Optimistic Concurrency Control
Uses a `version` field on issues to prevent lost updates in concurrent scenarios. When updating an issue, the client must provide the current version number. If another user has updated the issue in the meantime, the update will fail with a 409 Conflict error.

### Atomic Label Updates
`PUT /issues/{id}/labels` replaces all labels in a single transaction to avoid partial updates and ensure consistency.

### Transactional Bulk Operations
Bulk status updates execute in a single transaction with complete rollback on any failure, ensuring all-or-nothing semantics.

### CSV Import Error Handling
Each row is validated independently, with detailed error reporting for failed rows while successfully importing valid rows.

### UTC Timestamps
All timestamps use `datetime.now(UTC)` for Python 3.13 compatibility and proper timezone handling.

## 📈 Performance Considerations

- Indexed foreign keys and frequently queried fields
- Async database operations for better concurrency
- Connection pooling for efficient resource usage
- Pagination for large result sets
- Eager loading of relationships to avoid N+1 queries

## 🔒 Security

- Input validation with Pydantic
- SQL injection prevention via ORM
- Foreign key constraints for data integrity
- Transaction isolation for consistency
- Environment-based configuration

## 🛠️ Development

### Code Formatting
```bash
black app/ tests/
isort app/ tests/
```

### Type Checking
```bash
mypy app/
```

### Running in Production

```bash
# Use production ASGI server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📁 Project Structure

```
SurgePV/
├── app/
│   ├── core/              # Configuration and database
│   ├── models/            # SQLAlchemy models
│   ├── schemas/           # Pydantic schemas
│   ├── repositories/      # Data access layer
│   ├── services/          # Business logic
│   ├── routers/           # API endpoints
│   └── main.py           # Application entry point
├── tests/
│   ├── conftest.py       # Test configuration
│   └── test_services.py  # Service tests
├── scripts/
│   ├── init_db.py        # Database initialization
│   └── migrate.py        # Database migrations
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
├── pyproject.toml       # Project configuration
└── README.md            # This file
```

## 🐛 Troubleshooting

### Python command not found
Use `python3` instead of `python` on macOS/Linux:
```bash
python3 scripts/init_db.py
```

### Module not found errors
Ensure virtual environment is activated:
```bash
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

### Database errors
Reinitialize the database:
```bash
rm issue_tracker.db  # Remove old database
python3 scripts/init_db.py
```

### Port already in use
Change the port:
```bash
uvicorn app.main:app --reload --port 8001
```

## 📝 License

MIT License - feel free to use this project as a reference or starting point.

## 🤝 Contributing

This is a demonstration project showcasing production-ready backend engineering practices.

---

**Built with ❤️ using FastAPI, SQLAlchemy, and Python 3.13**
