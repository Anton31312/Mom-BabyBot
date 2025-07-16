#!/usr/bin/env python
"""
Database compatibility verification script for Mom&BabyBot Django migration.
This script checks if the existing database is compatible with the migrated application.
"""

import os
import sys
import sqlite3
from pathlib import Path
from datetime import datetime

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mom_baby_bot.settings')

def check_database_files():
    """Check for database files and their structure"""
    print("🔍 Checking database files...")
    
    db_files = ['mom_baby_bot.db', 'db.sqlite3', 'instance/mom_baby_bot.db']
    found_dbs = []
    
    for db_file in db_files:
        db_path = Path(db_file)
        if db_path.exists():
            print(f"✅ Found database file: {db_file}")
            found_dbs.append(db_file)
    
    if not found_dbs:
        print("⚠️ No database files found. A new database will be created on first use.")
        return []
    
    return found_dbs

def check_table_structure(db_file):
    """Check the structure of tables in the database"""
    print(f"\n📊 Checking table structure in {db_file}...")
    
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        
        # Get list of tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"Found tables: {', '.join(tables)}")
        
        # Check users table
        if 'users' in tables:
            print("✅ Users table exists")
            
            # Check columns
            cursor.execute("PRAGMA table_info(users);")
            columns = {row[1]: row[2] for row in cursor.fetchall()}
            
            print("\nUsers table columns:")
            for col_name, col_type in columns.items():
                print(f"  - {col_name} ({col_type})")
            
            # Check for required columns
            required_columns = {
                'id': 'INTEGER',
                'telegram_id': 'INTEGER',
                'username': 'VARCHAR(64)',
                'first_name': 'VARCHAR(64)',
                'last_name': 'VARCHAR(64)',
                'is_pregnant': 'BOOLEAN',
                'pregnancy_week': 'INTEGER',
                'baby_birth_date': 'DATETIME',
                'is_premium': 'BOOLEAN',
                'is_admin': 'BOOLEAN',
                'created_at': 'DATETIME',
                'updated_at': 'DATETIME'
            }
            
            missing_columns = []
            for col_name in required_columns:
                if col_name not in columns:
                    missing_columns.append(col_name)
            
            if missing_columns:
                print(f"⚠️ Missing required columns: {', '.join(missing_columns)}")
            else:
                print("✅ All required columns exist")
            
            # Check for old baby_age column
            if 'baby_age' in columns:
                print("⚠️ Old 'baby_age' column found. This should be migrated to 'baby_birth_date'")
            
            # Check data
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
            print(f"\nFound {user_count} users in database")
            
            if user_count > 0:
                cursor.execute("SELECT * FROM users LIMIT 5;")
                sample_users = cursor.fetchall()
                
                print("\nSample user data:")
                for user in sample_users:
                    print(f"  - User ID: {user[0]}, Telegram ID: {user[1]}, Username: {user[2]}")
        else:
            print("⚠️ Users table not found")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database structure: {e}")

def test_sqlalchemy_connection():
    """Test SQLAlchemy connection to the database"""
    print("\n🔌 Testing SQLAlchemy connection...")
    
    try:
        import django
        django.setup()
        
        from botapp.models import db_manager
        
        # Test connection
        session = db_manager.get_session()
        try:
            # Test simple query
            from botapp.models import User
            user_count = session.query(User).count()
            print(f"✅ SQLAlchemy connection successful. Found {user_count} users.")
            
            # Check if tables exist
            from sqlalchemy import inspect
            inspector = inspect(db_manager.engine)
            tables = inspector.get_table_names()
            print(f"Tables in database: {', '.join(tables)}")
            
            if 'users' in tables:
                # Get column information
                columns = inspector.get_columns('users')
                column_names = [col['name'] for col in columns]
                print(f"Columns in users table: {', '.join(column_names)}")
                
                # Check for baby_birth_date column
                if 'baby_birth_date' in column_names:
                    print("✅ baby_birth_date column exists")
                else:
                    print("⚠️ baby_birth_date column not found")
                
                # Check for old baby_age column
                if 'baby_age' in column_names:
                    print("⚠️ Old baby_age column still exists")
            
        finally:
            db_manager.close_session(session)
            
    except Exception as e:
        print(f"❌ Error testing SQLAlchemy connection: {e}")

def check_data_migration():
    """Check if data migration is needed"""
    print("\n🔄 Checking if data migration is needed...")
    
    try:
        import django
        django.setup()
        
        from botapp.models import db_manager, User
        
        session = db_manager.get_session()
        try:
            # Check if any users have baby_birth_date set
            from sqlalchemy import inspect
            inspector = inspect(db_manager.engine)
            columns = [col['name'] for col in inspector.get_columns('users')]
            
            if 'baby_birth_date' in columns and 'baby_age' in columns:
                # Both columns exist, check if migration is needed
                users_with_age = session.query(User).filter(
                    User.baby_age.isnot(None),
                    User.baby_birth_date.is_(None)
                ).count()
                
                if users_with_age > 0:
                    print(f"⚠️ Found {users_with_age} users with baby_age set but no baby_birth_date")
                    print("   Data migration is needed to convert baby_age to baby_birth_date")
                else:
                    print("✅ No data migration needed")
            elif 'baby_birth_date' in columns:
                print("✅ Database schema is using baby_birth_date column")
            elif 'baby_age' in columns:
                print("⚠️ Database schema is using old baby_age column")
                print("   Schema migration is needed to add baby_birth_date column")
            
        finally:
            db_manager.close_session(session)
            
    except Exception as e:
        print(f"❌ Error checking data migration: {e}")

def main():
    """Main function"""
    print("=" * 60)
    print("Mom&BabyBot Database Compatibility Verification")
    print("=" * 60)
    
    # Check database files
    db_files = check_database_files()
    
    # Check table structure for each database file
    for db_file in db_files:
        check_table_structure(db_file)
    
    # Test SQLAlchemy connection
    test_sqlalchemy_connection()
    
    # Check if data migration is needed
    check_data_migration()
    
    print("\n" + "=" * 60)
    print("Verification complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()