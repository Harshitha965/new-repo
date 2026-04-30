from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os

# SQLite database for skills state tracking (local, lightweight)
# Resolve absolute path: backend/skills.db
# __file__ is at backend/app/skills/database/session.py
# Go up 3 levels: database → skills → app → backend
_backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
_db_path = os.path.join(_backend_dir, "skills.db")

SQLALCHEMY_DATABASE_URL = f"sqlite:///{_db_path}"

# To switch to Supabase, use this instead:
# SQLALCHEMY_DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD_HERE@db.YOUR_SUPABASE_ID.supabase.co:5432/postgres"

# Connect to DB
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_skills_db():
    """Create all skills tables if they don't exist. Safe to call multiple times."""
    # Import models here to avoid circular imports — models import Base from this module
    from app.skills.database.models import SkillDefinition
    Base.metadata.create_all(bind=engine)

