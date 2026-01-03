#!/usr/bin/env python3
"""
Database migration: Add multi-table report generation columns
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from sqlalchemy import text

def run_migration():
    """Add new columns to report_templates table"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("Multi-Table Report Generation Migration")
        print("=" * 60)
        
        # Check if columns already exist
        print("\n🔍 Checking existing columns...")
        result = db.session.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'report_templates'
            ORDER BY ordinal_position
        """))
        
        existing_columns = [row[0] for row in result]
        print(f"Found {len(existing_columns)} existing columns")
        
        new_columns = [
            'table_configs',
            'include_records',
            'include_metadata',
            'include_schema_details',
            'include_summary'
        ]
        
        columns_to_add = [col for col in new_columns if col not in existing_columns]
        
        if not columns_to_add:
            print("\n✅ All columns already exist. No migration needed.")
            return
        
        print(f"\n📝 Adding {len(columns_to_add)} new columns:")
        for col in columns_to_add:
            print(f"   - {col}")
        
        # Add columns
        try:
            print("\n🔧 Executing migration...")
            
            if 'table_configs' in columns_to_add:
                db.session.execute(text("""
                    ALTER TABLE report_templates 
                    ADD COLUMN table_configs JSON
                """))
                print("   ✅ Added table_configs (JSON)")
            
            if 'include_records' in columns_to_add:
                db.session.execute(text("""
                    ALTER TABLE report_templates 
                    ADD COLUMN include_records BOOLEAN DEFAULT TRUE
                """))
                print("   ✅ Added include_records (BOOLEAN)")
            
            if 'include_metadata' in columns_to_add:
                db.session.execute(text("""
                    ALTER TABLE report_templates 
                    ADD COLUMN include_metadata BOOLEAN DEFAULT TRUE
                """))
                print("   ✅ Added include_metadata (BOOLEAN)")
            
            if 'include_schema_details' in columns_to_add:
                db.session.execute(text("""
                    ALTER TABLE report_templates 
                    ADD COLUMN include_schema_details BOOLEAN DEFAULT FALSE
                """))
                print("   ✅ Added include_schema_details (BOOLEAN)")
            
            if 'include_summary' in columns_to_add:
                db.session.execute(text("""
                    ALTER TABLE report_templates 
                    ADD COLUMN include_summary BOOLEAN DEFAULT TRUE
                """))
                print("   ✅ Added include_summary (BOOLEAN)")
            
            db.session.commit()
            print("\n✅ Migration completed successfully!")
            
            # Verify columns
            print("\n🔍 Verifying new columns...")
            result = db.session.execute(text("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name = 'report_templates'
                AND column_name IN ('table_configs', 'include_records', 'include_metadata', 
                                  'include_schema_details', 'include_summary')
                ORDER BY column_name
            """))
            
            print("\nNew columns:")
            for row in result:
                print(f"   {row[0]:25} {row[1]:15} default: {row[2]}")
            
            # Update existing templates with default values
            print("\n🔄 Updating existing templates with default values...")
            result = db.session.execute(text("""
                UPDATE report_templates
                SET 
                    include_records = TRUE,
                    include_metadata = TRUE,
                    include_schema_details = FALSE,
                    include_summary = TRUE
                WHERE include_records IS NULL
            """))
            
            db.session.commit()
            print(f"   ✅ Updated {result.rowcount} existing templates")
            
            # Show summary
            print("\n📊 Summary:")
            result = db.session.execute(text("SELECT COUNT(*) FROM report_templates"))
            total = result.scalar()
            print(f"   Total templates: {total}")
            
            result = db.session.execute(text("""
                SELECT COUNT(*) FROM report_templates 
                WHERE table_configs IS NOT NULL
            """))
            multi_table = result.scalar()
            print(f"   Multi-table templates: {multi_table}")
            print(f"   Single-table templates: {total - multi_table}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Migration failed: {str(e)}")
            raise
        
        print("\n" + "=" * 60)
        print("Migration completed successfully!")
        print("=" * 60)

if __name__ == "__main__":
    run_migration()
