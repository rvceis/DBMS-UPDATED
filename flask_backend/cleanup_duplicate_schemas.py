#!/usr/bin/env python3
"""
Script to clean up duplicate schemas in the database.
Keeps the oldest schema for each unique (name, asset_type_id) combination
and migrates records to use it.
"""

from app import create_app
from app.models import SchemaModel, MetadataRecord
from app.extensions import db
from sqlalchemy import func

def cleanup_duplicate_schemas():
    """Remove duplicate schemas and consolidate records"""
    app = create_app()
    
    with app.app_context():
        print("\n" + "="*70)
        print("🧹 CLEANING UP DUPLICATE SCHEMAS")
        print("="*70)
        
        # Find duplicate schemas (same name and asset_type_id)
        duplicates = db.session.query(
            SchemaModel.name,
            SchemaModel.asset_type_id,
            func.count(SchemaModel.id).label('count')
        ).group_by(
            SchemaModel.name,
            SchemaModel.asset_type_id
        ).having(
            func.count(SchemaModel.id) > 1
        ).all()
        
        if not duplicates:
            print("✅ No duplicate schemas found!")
            return
        
        print(f"\n📊 Found {len(duplicates)} sets of duplicate schemas:\n")
        
        total_removed = 0
        total_migrated = 0
        
        for name, asset_type_id, count in duplicates:
            print(f"  • Schema: '{name}' (Asset Type ID: {asset_type_id}) - {count} duplicates")
            
            # Get all schemas with this name and asset_type_id, ordered by creation date
            schemas = SchemaModel.query.filter_by(
                name=name,
                asset_type_id=asset_type_id
            ).order_by(SchemaModel.created_at.asc()).all()
            
            if not schemas:
                continue
            
            # Keep the oldest one
            primary_schema = schemas[0]
            duplicate_schemas = schemas[1:]
            
            print(f"    → Keeping schema ID {primary_schema.id} (created {primary_schema.created_at})")
            
            # Migrate all records from duplicate schemas to the primary schema
            for dup_schema in duplicate_schemas:
                records = MetadataRecord.query.filter_by(schema_id=dup_schema.id).all()
                
                if records:
                    print(f"    → Migrating {len(records)} records from schema ID {dup_schema.id}")
                    for record in records:
                        record.schema_id = primary_schema.id
                    total_migrated += len(records)
                
                # Delete the duplicate schema
                print(f"    → Deleting duplicate schema ID {dup_schema.id}")
                db.session.delete(dup_schema)
                total_removed += 1
        
        # Commit all changes
        try:
            db.session.commit()
            print(f"\n✅ Cleanup completed successfully!")
            print(f"   • Removed {total_removed} duplicate schemas")
            print(f"   • Migrated {total_migrated} records")
            
            # Show final schema count
            remaining_schemas = SchemaModel.query.count()
            print(f"   • Total schemas remaining: {remaining_schemas}")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ Error during cleanup: {str(e)}")
            raise

if __name__ == "__main__":
    cleanup_duplicate_schemas()
