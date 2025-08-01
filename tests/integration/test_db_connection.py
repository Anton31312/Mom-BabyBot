"""
Test SQLite database connection.
"""

import sqlite3
import os

# No dotenv, use hardcoded values

def test_sqlite_connection():
    """Test SQLite database connection."""
    print("Testing SQLite database connection...")
    
    db_path = os.getenv('DB_NAME', 'data/mom_baby_bot.db')
    print(f"Database path: {db_path}")
    
    try:
        # Connect to SQLite database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Test connection with a simple query
        cursor.execute("SELECT sqlite_version();")
        version = cursor.fetchone()
        print(f"SQLite version: {version[0]}")
        
        # Create a test table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_table (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL
        );
        """)
        
        # Insert a test record
        cursor.execute("INSERT INTO test_table (name) VALUES (?)", ("Test Record",))
        conn.commit()
        
        # Query the test record
        cursor.execute("SELECT * FROM test_table")
        records = cursor.fetchall()
        print(f"Test records: {records}")
        
        # Close connection
        cursor.close()
        conn.close()
        
        print("SQLite database connection test successful!")
        return True
        
    except Exception as e:
        print(f"Error testing SQLite database connection: {e}")
        return False

if __name__ == "__main__":
    test_sqlite_connection()