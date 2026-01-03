"""
Create data_rows table migration
Run this to add the new table for ACID-compliant row storage
"""
from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    # Create the SQL
    sql = """
    CREATE TABLE IF NOT EXISTS data_rows (
        id SERIAL PRIMARY KEY,
        record_id INTEGER NOT NULL REFERENCES metadata_records(id) ON DELETE CASCADE ON UPDATE CASCADE,
        row_index INTEGER NOT NULL,
        data JSONB NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    
    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_data_rows_record_id ON data_rows(record_id);
    CREATE INDEX IF NOT EXISTS idx_data_rows_row_index ON data_rows(row_index);
    CREATE INDEX IF NOT EXISTS idx_data_rows_data ON data_rows USING GIN(data);  -- JSONB index for fast queries
    
    -- Create trigger for updated_at
    CREATE OR REPLACE FUNCTION update_data_rows_updated_at()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    
    DROP TRIGGER IF EXISTS data_rows_updated_at_trigger ON data_rows;
    CREATE TRIGGER data_rows_updated_at_trigger
        BEFORE UPDATE ON data_rows
        FOR EACH ROW
        EXECUTE FUNCTION update_data_rows_updated_at();
    """
    
    try:
        # Execute the migration
        db.session.execute(db.text(sql))
        db.session.commit()
        print("✅ data_rows table created successfully!")
        print("✅ Indexes created for optimal query performance")
        print("✅ JSONB GIN index created for fast field queries")
        print("✅ CASCADE delete configured - deleting record deletes all its rows")
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Migration failed: {e}")
