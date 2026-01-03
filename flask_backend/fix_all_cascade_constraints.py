#!/usr/bin/env python3
"""
Fix all missing CASCADE constraints for schema deletion
"""
from app import create_app
from app.extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Fixing all foreign key CASCADE constraints...")
    
    try:
        constraints_to_fix = [
            {
                "table": "change_logs",
                "constraint": "change_logs_schema_id_fkey",
                "column": "schema_id",
                "references": "schemas(id)"
            },
            {
                "table": "schema_versions",
                "constraint": "schema_versions_schema_id_fkey",
                "column": "schema_id",
                "references": "schemas(id)"
            },
            {
                "table": "report_templates",
                "constraint": "report_templates_schema_id_fkey",
                "column": "schema_id",
                "references": "schemas(id)"
            },
            {
                "table": "report_executions",
                "constraint": "report_executions_template_id_fkey",
                "column": "template_id",
                "references": "report_templates(id)"
            },
        ]
        
        for constraint_info in constraints_to_fix:
            table = constraint_info["table"]
            constraint = constraint_info["constraint"]
            column = constraint_info["column"]
            references = constraint_info["references"]
            
            # Drop existing constraint
            db.session.execute(text(f"""
                ALTER TABLE {table}
                DROP CONSTRAINT IF EXISTS {constraint} CASCADE;
            """))
            
            # Add new constraint with CASCADE
            db.session.execute(text(f"""
                ALTER TABLE {table}
                ADD CONSTRAINT {constraint}
                FOREIGN KEY ({column})
                REFERENCES {references}
                ON DELETE CASCADE
                ON UPDATE CASCADE;
            """))
            
            print(f"  ✓ Fixed {table}.{column}")
        
        db.session.commit()
        print(f"\n✅ Successfully fixed {len(constraints_to_fix)} foreign key constraints")
        print("\nSchema deletion should now work properly from the frontend!")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
