#!/usr/bin/env python
"""
Простой тест подключения к базе данных
"""
import os
import sys

def test_postgresql_connection():
    """Тест прямого подключения к PostgreSQL"""
    database_url = os.getenv('DATABASE_URL', '')
    
    if not database_url:
        print("❌ DATABASE_URL не установлена")
        return False
    
    if not database_url.startswith('postgresql'):
        print(f"⚠️ DATABASE_URL не PostgreSQL: {database_url[:30]}...")
        return False
    
    try:
        import psycopg2
        from urllib.parse import urlparse
        
        parsed = urlparse(database_url)
        
        print(f"🔗 Подключение к PostgreSQL:")
        print(f"   Host: {parsed.hostname}")
        print(f"   Port: {parsed.port or 5432}")
        print(f"   Database: {parsed.path[1:] if parsed.path else 'postgres'}")
        print(f"   User: {parsed.username}")
        
        conn = psycopg2.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path[1:] if parsed.path else 'postgres'
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT version()")
        version = cursor.fetchone()
        print(f"✅ PostgreSQL подключение работает: {version[0][:50]}...")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
        return False

def main():
    print("🧪 Простой тест подключения к базе данных\n")
    
    if test_postgresql_connection():
        print("\n🎉 Тест прошел успешно!")
        return 0
    else:
        print("\n❌ Тест не прошел")
        return 1

if __name__ == "__main__":
    sys.exit(main())