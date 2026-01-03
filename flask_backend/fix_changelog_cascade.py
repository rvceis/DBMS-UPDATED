#!/usr/bin/env python3
"""
Fix ChangeLog foreign key to add CASCADE delete constraint
"""
from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Fixing change_logs.schema_id foreign key constraint...")
    
    try:
        # Drop existing foreign key constraint
        db.session.execute(text("""
            ALTER TABLE change_logs 
            DROP CONSTRAINT IF EXISTS change_logs_schema_id_fkey CASCADE;
        """))
        
        # Add new foreign key constraint with CASCADE
        db.session.execute(text("""
            ALTER TABLE change_logs 
            ADD CONSTRAINT change_logs_schema_id_fkey 
            FOREIGN KEY (schema_id) 
            REFERENCES schemas(id) 
            ON DELETE CASCADE 
            ON UPDATE CASCADE;
        """))
        
        db.session.commit()
        print("✅ Successfully added CASCADE constraint to change_logs.schema_id")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
