import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from utils.logger import logger

# Get database connection parameters from environment or use defaults
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "db")

# Construct database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Log connection parameters (with masked password)
logger.info(
    f"Connecting to PostgreSQL database at {DB_HOST}:{DB_PORT} as user {DB_USER}"
)

# Create engine with echo=True to see SQL commands
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a single Base to be imported by models
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def initialize_database():
    """Import all models and create tables"""
    try:
        # Test the connection first
        logger.info("Testing database connection...")
        with engine.connect() as conn:
            logger.info("Database connection successful!")

        # This import is needed to register models with Base.metadata
        logger.info("Registering models...")
        from models.epg import EPGChannelModel, EPGProgramModel

        # Now create all tables
        logger.info("Creating tables if they don't exist...")
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialization complete!")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise
