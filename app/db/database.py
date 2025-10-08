from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
from pathlib import Path

# Check if we're running on Liara (production environment)
if os.getenv("LIARA_APP_ID"):
    # Liara production environment - use persistent storage
    db_dir = "/var/lib/data"
    os.makedirs(db_dir, exist_ok=True)
    db_path = os.path.join(db_dir, "smart_dashboard.db")
    DATABASE_URL = f"sqlite:///{db_path}"
else:
    # Local development environment
    PROJECT_ROOT = Path(__file__).parent.parent.parent.absolute()
    DB_PATH = PROJECT_ROOT / "smart_dashboard.db"
    DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

print(f"Database configuration:")
print(f"  Environment: {'Liara Production' if os.getenv('LIARA_APP_ID') else 'Local Development'}")
print(f"  Database URL: {DATABASE_URL}")
print(f"  Database path: {db_path if os.getenv('LIARA_APP_ID') else DB_PATH}")

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
