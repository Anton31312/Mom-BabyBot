"""
Create SQLite database for local development.
"""

import sqlite3
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_sqlite_db():
    """Create SQLite database for local development."""
    db_path = 'mom_baby_bot.db'
    logger.info(f"Creating SQLite database at: {db_path}")
    
    try:
        # Connect to SQLite database (creates it if it doesn't exist)
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create basic tables needed for the bot
        logger.info("Creating users table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            language_code TEXT,
            is_premium BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        logger.info("Creating children table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS children (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            name TEXT,
            birth_date DATE,
            gender TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """)
        
        logger.info("Creating vaccines table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS vaccines (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            recommended_age_months INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)
        
        logger.info("Creating child_vaccines table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS child_vaccines (
            id INTEGER PRIMARY KEY,
            child_id INTEGER NOT NULL,
            vaccine_id INTEGER NOT NULL,
            scheduled_date DATE,
            administered_date DATE,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (child_id) REFERENCES children (id),
            FOREIGN KEY (vaccine_id) REFERENCES vaccines (id)
        );
        """)
        
        logger.info("Creating notification_preferences table...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notification_preferences (
            id INTEGER PRIMARY KEY,
            user_id INTEGER NOT NULL,
            notification_type TEXT NOT NULL,
            enabled BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        """)
        
        # Commit changes and close connection
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info("SQLite database created successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error creating SQLite database: {e}")
        return False

if __name__ == "__main__":
    create_sqlite_db()