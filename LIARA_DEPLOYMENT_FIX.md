# Liara Deployment Database Fix

## Problem
The SQLite database couldn't be created in the default location on Liara's server, causing the error:
```
sqlite3.OperationalError: unable to open database file
```

## Solution
Updated all database connections to use Liara's persistent storage path `/var/lib/data/` when running in production.

## Changes Made

### 1. Database Configuration (`app/db/database.py`)
- Added environment detection for Liara (`LIARA_APP_ID`)
- Uses `/var/lib/data/smart_dashboard.db` for production
- Falls back to local path for development

### 2. Updated Files
- `app/db/database.py` - Main database configuration
- `app/main.py` - Action logs endpoints
- `app/services/unified_semantic_service.py` - SQLite connections
- `app/services/alert_manager.py` - Alert database
- `app/services/session_storage.py` - Session storage

### 3. Environment Variables
No additional environment variables needed. The system automatically detects Liara environment using `LIARA_APP_ID`.

## How It Works

### Local Development
```python
# Uses local path
DATABASE_URL = "sqlite:///./smart_dashboard.db"
```

### Liara Production
```python
# Uses persistent storage
db_dir = "/var/lib/data"
os.makedirs(db_dir, exist_ok=True)
db_path = os.path.join(db_dir, "smart_dashboard.db")
DATABASE_URL = f"sqlite:///{db_path}"
```

## Deployment Steps

1. **Deploy to Liara** - The changes are already in the code
2. **No environment variables needed** - Automatic detection
3. **Database will be created** in `/var/lib/data/smart_dashboard.db`
4. **Data persists** between deployments

## Verification

After deployment, check the logs for:
```
Database configuration:
  Environment: Liara Production
  Database URL: sqlite:////var/lib/data/smart_dashboard.db
  Database path: /var/lib/data/smart_dashboard.db
```

## Benefits

- ✅ **Persistent storage** - Data survives deployments
- ✅ **Automatic detection** - No manual configuration needed
- ✅ **Development friendly** - Local development unchanged
- ✅ **Production ready** - Works on Liara's infrastructure
