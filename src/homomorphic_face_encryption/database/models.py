"""Database models using SQLAlchemy."""

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

Base = declarative_base()

DATABASE_URL = f"postgresql://{os.getenv('DB_USER', 'postgres')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('DB_NAME', 'face_db')}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class User(Base):
    """User model for storing encrypted face embeddings."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    encrypted_embedding = Column(Text, nullable=False)  # Encrypted face features
    created_at = Column(DateTime, server_default="now()")
    consent_given = Column(Boolean, default=False)


class ConsentLog(Base):
    """Log of consent changes for GDPR compliance."""
    __tablename__ = "consent_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, nullable=False)
    action = Column(String, nullable=False)  # 'granted' or 'revoked'
    timestamp = Column(DateTime, server_default="now()")


def create_tables():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Global database session
db = SessionLocal()
