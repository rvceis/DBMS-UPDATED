#!/usr/bin/env python3
"""
Delete all schemas and related data
"""
from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Starting schema deletion process...")
    
    try:
        # First, fix the missing CASCADE constraints
        print("\nFixing foreign key constraints...")
        
        # Fix schema_versions constraint
        db.session.execute(text("""
            ALTER TABLE schema_versions 
            DROP CONSTRAINT IF EXISTS schema_versions_schema_id_fkey CASCADE;
        """))
        db.session.execute(text("""
            ALTER TABLE schema_versions 
            ADD CONSTRAINT schema_versions_schema_id_fkey 
            FOREIGN KEY (schema_id) 
            REFERENCES schemas(id) 
            ON DELETE CASCADE 
            ON UPDATE CASCADE;
        """))
        print("  ✓ Fixed schema_versions.schema_id constraint")        
        # Fix report_templates constraint
        db.session.execute(text("""
            ALTER TABLE report_templates 
            DROP CONSTRAINT IF EXISTS report_templates_schema_id_fkey CASCADE;
        """))
        db.session.execute(text("""
            ALTER TABLE report_templates 
            ADD CONSTRAINT report_templates_schema_id_fkey 
            FOREIGN KEY (schema_id) 
            REFERENCES schemas(id) 
            ON DELETE CASCADE 
            ON UPDATE CASCADE;
        """))
        print("  ✓ Fixed report_templates.schema_id constraint")        
        db.session.commit()
        print("\nConstraints fixed. Now deleting schemas...\n")
                # Delete report executions first
        exec_count = db.session.execute(text("SELECT COUNT(*) FROM report_executions")).scalar()
        if exec_count > 0:
            db.session.execute(text("DELETE FROM report_executions"))
            print(f"  Deleted {exec_count} report executions")
        
        # Delete report templates
        template_count = db.session.execute(text("SELECT COUNT(*) FROM report_templates")).scalar()
        if template_count > 0:
            db.session.execute(text("DELETE FROM report_templates"))
            print(f"  Deleted {template_count} report templates")
                # Get schema count
        result = db.session.execute(text("SELECT COUNT(*) FROM schemas"))
        schema_count = result.scalar()
        
        if schema_count == 0:
            print("No schemas found.")
        else:
            # Get all schema info
            schemas = db.session.execute(text("""
                SELECT s.id, s.name, 
                       COUNT(DISTINCT m.id) as record_count,
                       COUNT(DISTINCT f.id) as field_count
                FROM schemas s
                LEFT JOIN metadata_records m ON m.schema_id = s.id
                LEFT JOIN schema_fields f ON f.schema_id = s.id
                GROUP BY s.id, s.name
            """)).fetchall()
            
            print(f"Found {schema_count} schemas to delete:")
            for schema in schemas:
                print(f"  - {schema.name} (ID: {schema.id}) - {schema.record_count} records, {schema.field_count} fields")
            
            # Delete all schemas (CASCADE will handle related data)
            db.session.execute(text("DELETE FROM schemas"))
            db.session.commit()
            
            print(f"\n✅ Successfully deleted {schema_count} schemas and all related data")
            
            # Verify deletion
            remaining_schemas = db.session.execute(text("SELECT COUNT(*) FROM schemas")).scalar()
            remaining_records = db.session.execute(text("SELECT COUNT(*) FROM metadata_records")).scalar()
            remaining_rows = db.session.execute(text("SELECT COUNT(*) FROM data_rows")).scalar()
            remaining_fields = db.session.execute(text("SELECT COUNT(*) FROM schema_fields")).scalar()
            remaining_changelogs = db.session.execute(text("SELECT COUNT(*) FROM change_logs")).scalar()
            remaining_versions = db.session.execute(text("SELECT COUNT(*) FROM schema_versions")).scalar()
            
            print(f"\nRemaining in database:")
            print(f"  • Schemas: {remaining_schemas}")
            print(f"  • Metadata Records: {remaining_records}")
            print(f"  • Data Rows: {remaining_rows}")
            print(f"  • Schema Fields: {remaining_fields}")
            print(f"  • Change Logs: {remaining_changelogs}")
            print(f"  • Schema Versions: {remaining_versions}")
            
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
