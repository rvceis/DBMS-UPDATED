#!/bin/bash
# PostgreSQL Database Inspection Commands for DBMS System
# Database: dbms_db
# User: dbms_user

echo "=========================================="
echo "📊 DBMS PROJECT - PostgreSQL Commands"
echo "=========================================="
echo ""

# Database connection info
DB_NAME="dbms_db"
DB_USER="dbms_user"

echo "🔐 Connect to database:"
echo "  psql -U $DB_USER -d $DB_NAME"
echo ""

echo "📋 List all databases:"
echo "  psql -U $DB_USER -l"
echo ""

echo "📊 List all tables in current database:"
echo "  \\dt"
echo "  (or from shell): psql -U $DB_USER -d $DB_NAME -c '\\dt'"
echo ""

echo "🔍 Describe table structure:"
echo "  \\d table_name"
echo "  Example: \\d field_values"
echo ""

echo "📈 View table with data types and constraints:"
echo "  \\d+ table_name"
echo ""

echo "🎯 Quick queries for this system:"
echo ""
echo "1️⃣  Count all records:"
echo "   SELECT COUNT(*) FROM metadata_records;"
echo ""

echo "2️⃣  Show all schemas:"
echo "   SELECT id, name, version, is_active FROM schemas ORDER BY created_at DESC LIMIT 10;"
echo ""

echo "3️⃣  Show all field types in use:"
echo "   SELECT DISTINCT field_type FROM schema_fields WHERE is_deleted = false;"
echo ""

echo "4️⃣  Show field_values table structure (NEW binary column):"
echo "   \\d+ field_values"
echo ""

echo "5️⃣  Show all asset types:"
echo "   SELECT id, name, description FROM asset_types;"
echo ""

echo "6️⃣  Count records by schema:"
echo "   SELECT s.name, COUNT(mr.id) as record_count"
echo "   FROM schemas s"
echo "   LEFT JOIN metadata_records mr ON s.id = mr.schema_id"
echo "   GROUP BY s.id, s.name"
echo "   ORDER BY record_count DESC;"
echo ""

echo "7️⃣  Show all users:"
echo "   SELECT id, username, email, role FROM users;"
echo ""

echo "8️⃣  Check for binary/file fields:"
echo "   SELECT sf.field_name, sf.field_type, s.name as schema_name"
echo "   FROM schema_fields sf"
echo "   JOIN schemas s ON sf.schema_id = s.id"
echo "   WHERE sf.field_type IN ('file', 'image', 'binary')"
echo "   AND sf.is_deleted = false;"
echo ""

echo "9️⃣  Count values by storage column:"
echo "   SELECT"
echo "     COUNT(CASE WHEN value_text IS NOT NULL THEN 1 END) as text_count,"
echo "     COUNT(CASE WHEN value_int IS NOT NULL THEN 1 END) as int_count,"
echo "     COUNT(CASE WHEN value_float IS NOT NULL THEN 1 END) as float_count,"
echo "     COUNT(CASE WHEN value_bool IS NOT NULL THEN 1 END) as bool_count,"
echo "     COUNT(CASE WHEN value_date IS NOT NULL THEN 1 END) as date_count,"
echo "     COUNT(CASE WHEN value_json IS NOT NULL THEN 1 END) as json_count,"
echo "     COUNT(CASE WHEN value_binary IS NOT NULL THEN 1 END) as binary_count"
echo "   FROM field_values;"
echo ""

echo "🔟  Export query results to CSV:"
echo "   \\copy (SELECT * FROM metadata_records LIMIT 100) TO '/tmp/records.csv' CSV HEADER;"
echo ""

echo "=========================================="
echo "📝 Interactive psql session tips:"
echo "=========================================="
echo "  \\?              - Show all psql commands"
echo "  \\q              - Quit"
echo "  \\l              - List databases"
echo "  \\c dbname       - Connect to database"
echo "  \\dt             - List tables"
echo "  \\du             - List users/roles"
echo "  \\x              - Toggle expanded display"
echo "  \\timing         - Toggle query timing"
echo "  \\i file.sql     - Execute SQL from file"
echo ""

echo "🚀 Quick connect command:"
echo "  psql -U $DB_USER -d $DB_NAME"
echo ""
