#!/usr/bin/env python3
"""
Migration script to add value_binary column to field_values table
Run this to update the database schema for binary/file/image support
"""
import os
import sys
from sqlalchemy import create_engine, text

# Get database URL from environment
database_url = os.getenv('DATABASE_URL', 'postgresql://dbms_user:dbms_password@localhost:5432/dbms_db')

print(f"🔧 Connecting to database...")
print(f"   URL: {database_url.split('@')[1] if '@' in database_url else database_url}")

try:
    engine = create_engine(database_url)
    
    with engine.connect() as conn:
        # Check if column already exists
        result = conn.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='field_values' AND column_name='value_binary'
        """))
        
        if result.fetchone():
            print("✅ Column 'value_binary' already exists in 'field_values' table")
        else:
            print("📝 Adding 'value_binary' column to 'field_values' table...")
            conn.execute(text("""
                ALTER TABLE field_values 
                ADD COLUMN value_binary BYTEA
            """))
            conn.commit()
            print("✅ Successfully added 'value_binary' column")
    
    print("\n🎉 Migration completed successfully!")
    print("\n📋 Supported field types now include:")
    print("   - string, text, url, email, phone, enum")
    print("   - integer, float, boolean")
    print("   - date, datetime, time")
    print("   - json, array, object")
    print("   - file, image, binary ⭐ NEW")
    
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
