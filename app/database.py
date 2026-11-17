"""Database connection and session management."""
import os
import time
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres_password@db:5432/library_db"
)

# Connect with retries on startup (to allow postgres time to initialize)
def get_engine():
    max_retries = 10
    retry_interval = 2
    for attempt in range(max_retries):
        try:
            engine = create_engine(DATABASE_URL, pool_pre_ping=True)
            with engine.connect():
                return engine
        except Exception:
            if attempt == max_retries - 1:
                raise
            time.sleep(retry_interval)
    return create_engine(DATABASE_URL)

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
