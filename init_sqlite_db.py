"""
Initialize SQLite database for local development.
"""

import os
import logging
import django
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings')

# Initialize Django
django.setup()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def init_sqlite_db():
    """Initialize SQLite database for local development."""
    try:
        from sqlalchemy import create_engine, text
        from botapp.models import Base

        # Create SQLite database engine
        engine = create_engine('sqlite:///mom_baby_bot.db', echo=True)

        # Create all tables
        logger.info("Creating database tables...")
        Base.metadata.create_all(engine)

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT 'Database initialized successfully'"))
            for row in result:
                logger.info(row[0])

        logger.info("SQLite database initialized successfully!")
        return True

    except Exception as e:
        logger.error(f"Error initializing SQLite database: {e}")
        return False


if __name__ == "__main__":
    logger.info("Starting SQLite database initialization...")
    success = init_sqlite_db()
    if success:
        logger.info("Database initialization completed successfully.")
    else:
        logger.error("Database initialization failed.")
