#!/usr/bin/env python3
"""
PostgreSQL Database Setup and Migration Script
Creates database and all tables from SQLAlchemy models
"""
import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import ProgrammingError, OperationalError

# Add current directory to path to import from flask_backend/app
current_dir = os.path.dirname(__file__)
sys.path.insert(0, current_dir)

from app import create_app
from app.extensions import db
from app.models import (
    User, AssetType, SchemaModel, SchemaField, SchemaVersion,
    MetadataRecord, FieldValue, ChangeLog, ReportTemplate, ReportExecution
)
from werkzeug.security import generate_password_hash

def create_database():
    """Create the PostgreSQL database if it doesn't exist"""
    # Get database URL from environment
    from dotenv import load_dotenv
    load_dotenv()
    database_url = os.getenv('DATABASE_URL', 'sqlite:///dev.db')
    
    print(f"📦 Database URL: {database_url}")
    
    # Parse database name from URL
    # Format: postgresql://user:pass@host:port/dbname
    if 'postgresql://' in database_url:
        db_name = database_url.split('/')[-1].split('?')[0]
        # Create URL without database name for initial connection
        base_url = '/'.join(database_url.split('/')[:-1]) + '/postgres'
        
        print(f"🔧 Creating database '{db_name}' if it doesn't exist...")
        
        try:
            # Connect to default 'postgres' database
            engine = create_engine(base_url, isolation_level="AUTOCOMMIT")
            with engine.connect() as conn:
                # Check if database exists
                result = conn.execute(
                    text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                    {"dbname": db_name}
                )
                exists = result.fetchone()
                
                if not exists:
                    print(f"   Creating database '{db_name}'...")
                    conn.execute(text(f'CREATE DATABASE {db_name}'))
                    print(f"   ✅ Database '{db_name}' created successfully!")
                else:
                    print(f"   ℹ️  Database '{db_name}' already exists")
            
            engine.dispose()
        except OperationalError as e:
            if "already exists" in str(e):
                print(f"   ℹ️  Database '{db_name}' already exists")
            else:
                print(f"   ❌ Error creating database: {e}")
                raise
    else:
        print("   ℹ️  Not using PostgreSQL, skipping database creation")

def create_all_tables(app):
    """Create all tables from SQLAlchemy models"""
    print("\n🔨 Creating all tables from models...")
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Verify tables were created
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        print(f"\n✅ Created {len(tables)} tables:")
        for table in sorted(tables):
            print(f"   ✓ {table}")
        
        return tables

def seed_initial_data(app):
    """Seed initial data (admin user and asset types)"""
    print("\n🌱 Seeding initial data...")
    
    with app.app_context():
        # Check if admin user exists
        admin = User.query.filter_by(email='admin@test.com').first()
        if not admin:
            print("   Creating admin user...")
            admin = User(
                username='admin',
                email='admin@test.com',
                password_hash=generate_password_hash('password'),
                role='admin'
            )
            db.session.add(admin)
            print("   ✅ Admin user created (admin@test.com / password)")
        else:
            print("   ℹ️  Admin user already exists")
        
        # Create asset types
        asset_types = [
            'Image', 'Video', 'Audio', 'Document', 
            'Dataset', '3D Model', 'Code', 'Other'
        ]
        
        existing_types = {at.name for at in AssetType.query.all()}
        new_types = [at for at in asset_types if at not in existing_types]
        
        if new_types:
            print(f"   Creating {len(new_types)} asset types...")
            for at_name in new_types:
                asset_type = AssetType(name=at_name)
                db.session.add(asset_type)
            print(f"   ✅ Created asset types: {', '.join(new_types)}")
        else:
            print("   ℹ️  Asset types already exist")
        
        db.session.commit()
        print("   ✅ Initial data seeded successfully!")

def migrate_from_sqlite(app, sqlite_path):
    """Migrate data from SQLite to PostgreSQL (optional)"""
    if not os.path.exists(sqlite_path):
        print(f"\n   ℹ️  No SQLite database found at {sqlite_path}, skipping migration")
        return
    
    print(f"\n📊 Migrating data from SQLite ({sqlite_path})...")
    
    from sqlalchemy import create_engine as create_sqlite_engine
    sqlite_engine = create_sqlite_engine(f'sqlite:///{sqlite_path}')
    
    with app.app_context():
        # Get table list from SQLite
        sqlite_inspector = inspect(sqlite_engine)
        sqlite_tables = sqlite_inspector.get_table_names()
        
        print(f"   Found {len(sqlite_tables)} tables in SQLite")
        
        # Migrate data table by table
        tables_to_migrate = [
            'users', 'asset_types', 'schemas', 'schema_fields',
            'metadata_records', 'field_values', 'change_logs',
            'schema_versions', 'report_templates', 'report_executions'
        ]
        
        for table in tables_to_migrate:
            if table in sqlite_tables:
                try:
                    # Read from SQLite
                    with sqlite_engine.connect() as sqlite_conn:
                        result = sqlite_conn.execute(text(f'SELECT COUNT(*) FROM {table}'))
                        count = result.scalar()
                        
                        if count > 0:
                            print(f"   Migrating {count} rows from {table}...")
                            # Use pandas for easy migration
                            import pandas as pd
                            df = pd.read_sql_table(table, sqlite_engine)
                            df.to_sql(table, db.engine, if_exists='append', index=False)
                            print(f"   ✅ Migrated {count} rows from {table}")
                        else:
                            print(f"   ℹ️  Table {table} is empty, skipping")
                except Exception as e:
                    print(f"   ⚠️  Error migrating {table}: {e}")
    
    sqlite_engine.dispose()

def main():
    print("=" * 80)
    print("🚀 PostgreSQL Database Setup & Migration")
    print("=" * 80)
    
    # Create database
    create_database()
    
    # Create Flask app
    app = create_app()
    
    # Create all tables
    tables = create_all_tables(app)
    
    # Seed initial data
    seed_initial_data(app)
    
    # Optional: Migrate from SQLite
    sqlite_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        'instance', 'database.db'
    )
    
    migrate_choice = input("\n❓ Migrate data from SQLite? (y/N): ").strip().lower()
    if migrate_choice == 'y':
        try:
            migrate_from_sqlite(app, sqlite_path)
        except Exception as e:
            print(f"   ❌ Migration error: {e}")
            print("   Continuing without migration...")
    
    print("\n" + "=" * 80)
    print("✅ PostgreSQL setup complete!")
    print("=" * 80)
    print("\n📋 Summary:")
    print(f"   • Database: Ready")
    print(f"   • Tables: {len(tables)} created")
    print(f"   • Admin user: admin@test.com / password")
    print(f"   • Status: 🟢 Ready to use")
    print("\n🚀 Start the server: python3 main.py")
    print("=" * 80)

if __name__ == '__main__':
    main()
