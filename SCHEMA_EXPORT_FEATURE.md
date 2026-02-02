# Schema Export Feature - Complete Guide

**Date**: February 2, 2026  
**Feature**: Schema Export in JSON & SQL formats  
**Availability**: All authenticated users (Admin, Editor, Viewer)

---

## Overview

Users can now export schemas individually or in bulk in two formats:
- **JSON Format**: Native application format with full metadata
- **SQL Format**: PostgreSQL-compatible CREATE TABLE statements

Exports are available to all authenticated users regardless of role.

---

## Features

### 1. Export Individual Schema
- Export single schema as JSON or SQL
- Download directly to computer
- Available on schema detail page
- File naming: `schema_name_vX.json` or `schema_name_vX.sql`

### 2. Export All Schemas
- Export all schemas at once
- Combine multiple schemas into single file
- Available from main schemas page
- File naming: `all_schemas_YYYY-MM-DD.json` or `.sql`

### 3. Formats

#### JSON Export
```json
{
  "schema_id": 1,
  "schema_name": "Employee",
  "version": 1,
  "created_by": "john_admin",
  "schema_definition": {
    "name": "Employee",
    "fields": [
      {
        "field_name": "employee_id",
        "field_type": "integer",
        "constraints": {"unique": true, "required": true}
      },
      {
        "field_name": "name",
        "field_type": "string",
        "constraints": {"required": true}
      }
    ]
  }
}
```

#### SQL Export
```sql
-- Schema: Employee
-- Version: 1
-- Created by: john_admin
-- Exported: 2026-02-02T20:45:00.123456

CREATE TABLE IF NOT EXISTS employee (
    id SERIAL PRIMARY KEY,
    employee_id INTEGER NOT NULL UNIQUE,
    name VARCHAR(255) NOT NULL
);
```

---

## API Endpoints

### Export Individual Schema as JSON
```
GET /schemas/<schema_id>/export/json
Authorization: Bearer <token>
```

**Response**:
```json
{
  "export_type": "schema_json",
  "export_date": "2026-02-02T20:45:00.123456",
  "id": 1,
  "version": 1,
  "schema_json": {...},
  "created_by": 1,
  "created_by_name": "john_admin"
}
```

---

### Export Individual Schema as SQL
```
GET /schemas/<schema_id>/export/sql
Authorization: Bearer <token>
```

**Response**:
```json
{
  "export_type": "schema_sql",
  "export_date": "2026-02-02T20:45:00.123456",
  "id": 1,
  "version": 1,
  "database_type": "postgresql",
  "table_name": "employee",
  "sql_statement": "CREATE TABLE IF NOT EXISTS employee (...)",
  "created_by": 1,
  "created_by_name": "john_admin"
}
```

---

### Export All Schemas as JSON
```
GET /schemas/export/json
Authorization: Bearer <token>
```

**Response**:
```json
{
  "export_type": "schemas_json",
  "export_date": "2026-02-02T20:45:00.123456",
  "total_schemas": 3,
  "schemas": [
    {
      "id": 1,
      "version": 1,
      "schema_json": {...},
      "created_by": 1,
      "created_by_name": "john_admin"
    },
    ...
  ]
}
```

---

### Export All Schemas as SQL
```
GET /schemas/export/sql
Authorization: Bearer <token>
```

**Response**:
```json
{
  "export_type": "schemas_sql",
  "export_date": "2026-02-02T20:45:00.123456",
  "total_schemas": 3,
  "database_type": "postgresql",
  "sql_statements": [
    "CREATE TABLE IF NOT EXISTS employee (...)",
    "CREATE TABLE IF NOT EXISTS department (...)"
  ],
  "combined_sql": "CREATE TABLE IF NOT EXISTS employee (...)\n\nCREATE TABLE IF NOT EXISTS department (...)"
}
```

---

### Download Schema Export
```
GET /schemas/<schema_id>/export/download/<format>
Authorization: Bearer <token>

Parameters:
  - schema_id: Integer (1-based)
  - format: String ("json" or "sql")
```

**Response**: File download with appropriate MIME type
- JSON: `application/json`
- SQL: `text/plain`

---

## Frontend Usage

### Individual Schema Export

**Location**: Schema detail page

**Button**: 
```
[JSON] [SQL]
```

**Code**:
```typescript
// Export as JSON
handleExportSchema(schemaId, schemaName, 'json')

// Export as SQL
handleExportSchema(schemaId, schemaName, 'sql')
```

**File Download**:
- Filename: `{schema_name}_{version}.{format}`
- Example: `Employee_v1.json` or `Employee_v1.sql`

---

### All Schemas Export

**Location**: Main schemas page (top toolbar)

**Buttons**:
```
[Export JSON] [Export SQL]
```

**Code**:
```typescript
// Export all as JSON
handleExportAllSchemas('json')

// Export all as SQL
handleExportAllSchemas('sql')
```

**File Download**:
- Filename: `all_schemas_{YYYY-MM-DD}.{format}`
- Example: `all_schemas_2026-02-02.json`

---

## Data Type Mapping

| Application Type | SQL Type | Example |
|-----------------|----------|---------|
| integer | INTEGER | 42 |
| int | INTEGER | 42 |
| float | FLOAT | 3.14 |
| double | DOUBLE PRECISION | 3.14159265 |
| string | VARCHAR(255) | "John Doe" |
| text | TEXT | "Long description..." |
| boolean | BOOLEAN | true/false |
| bool | BOOLEAN | true/false |
| date | DATE | 2026-02-02 |
| datetime | TIMESTAMP | 2026-02-02T20:45:00 |
| timestamp | TIMESTAMP | 2026-02-02T20:45:00 |
| array | TEXT[] | ["a", "b"] |
| json | JSONB | {"key": "value"} |
| object | JSONB | {"key": "value"} |

---

## Constraints Included in SQL

When exporting to SQL, the following constraints are included:

```sql
CREATE TABLE employee (
    id SERIAL PRIMARY KEY,
    -- NOT NULL constraint from "required": true
    employee_id INTEGER NOT NULL,
    -- UNIQUE constraint from "unique": true
    email VARCHAR(255) UNIQUE,
    -- Combined constraints
    name VARCHAR(255) NOT NULL UNIQUE
);
```

---

## Import Exported SQL

After exporting a schema as SQL, you can import it into a PostgreSQL database:

```bash
# 1. Connect to your database
psql -U username -d database_name

# 2. Run the SQL file
\i /path/to/schema_name_v1.sql

# 3. Verify table created
\dt schema_name
```

Or from command line:

```bash
psql -U username -d database_name -f /path/to/schema_name_v1.sql
```

---

## Import Exported JSON

Use exported JSON to:

1. **Recreate schema in another MetaDB instance**:
```bash
curl -X POST http://other-instance:5000/schemas \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d @exported_schema.json
```

2. **Backup schema configuration**:
```bash
# Save to version control
git add employee_v1.json
git commit -m "Backup: Employee schema v1"
```

3. **Document schema structure**:
```bash
# Convert JSON to formatted documentation
cat employee_v1.json | jq '.schema_definition.fields[] | {name, type, constraints}'
```

---

## Permission Matrix

| Role | Can Export Own | Can Export Others | Can Export All |
|------|----------------|------------------|----------------|
| **Admin** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Editor** | ✅ Yes | ✅ Yes | ✅ Yes |
| **Viewer** | ✅ Yes | ✅ Yes | ✅ Yes |

**Note**: All authenticated users can export any schema. There are no export restrictions. Only deletion is restricted based on ownership.

---

## Use Cases

### 1. Database Migration
```
1. Export schema as SQL
2. Connect to target PostgreSQL database
3. Run SQL script
4. Create records in new database
```

### 2. Schema Backup
```
1. Export all schemas as JSON
2. Commit to Git
3. Track changes over time
```

### 3. Schema Documentation
```
1. Export schema as JSON
2. Generate documentation
3. Share with team
```

### 4. Schema Replication
```
1. Export from Source instance as JSON
2. Save to file
3. Import to Target instance via API
```

### 5. Multi-Database Support
```
1. Export schema as SQL
2. Modify for specific DB (MySQL, SQL Server, etc.)
3. Deploy to different database
```

---

## Testing

### Test Individual Export
```bash
# Get token
TOKEN=$(curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@test.com", "password": "password"}' \
  | jq -r '.access_token')

# Export schema 1 as JSON
curl http://localhost:5000/schemas/1/export/json \
  -H "Authorization: Bearer $TOKEN" \
  | jq .

# Download schema 1 as JSON file
curl http://localhost:5000/schemas/1/export/download/json \
  -H "Authorization: Bearer $TOKEN" \
  -o schema_1.json

# Download schema 1 as SQL file
curl http://localhost:5000/schemas/1/export/download/sql \
  -H "Authorization: Bearer $TOKEN" \
  -o schema_1.sql
```

### Test All Schemas Export
```bash
# Export all schemas as JSON
curl http://localhost:5000/schemas/export/json \
  -H "Authorization: Bearer $TOKEN" \
  | jq .

# Export all schemas as SQL
curl http://localhost:5000/schemas/export/sql \
  -H "Authorization: Bearer $TOKEN" \
  | jq '.combined_sql'
```

### Frontend Test
```
1. Login to application
2. Navigate to Schemas page
3. Click "Export JSON" or "Export SQL" button
4. Verify file downloads to computer
5. Check filename: all_schemas_2026-02-02.json
```

---

## Troubleshooting

### Export Button Not Working
- **Issue**: Button doesn't respond
- **Solution**: Check browser console for errors, verify token is valid

### Export File Empty
- **Issue**: Downloaded file is empty
- **Solution**: Verify schema has fields defined, check network response

### SQL File Not Importing
- **Issue**: `ERROR: syntax error` when importing
- **Solution**: 
  - Verify table names are valid identifiers
  - Check PostgreSQL version compatibility
  - Ensure field types are supported

### Large Export Takes Time
- **Issue**: Exporting 1000+ schemas is slow
- **Solution**: 
  - Export schemas individually
  - Export in batches (50-100 at a time)
  - Consider using direct database query for bulk export

---

## Supported Databases

Exported SQL is formatted for:
- ✅ **PostgreSQL** (Primary support)
- ⚠️ **MySQL** (May need type adjustments)
- ⚠️ **SQL Server** (May need syntax changes)
- ⚠️ **SQLite** (Simplified version)

To adapt for other databases, modify the SQL type mapping in `map_to_sql_type()` function in backend.

---

## Future Enhancements

- [ ] Export as CSV
- [ ] Export as YAML
- [ ] Export as OpenAPI/Swagger spec
- [ ] Export as GraphQL schema
- [ ] Export with sample data
- [ ] Scheduled export jobs
- [ ] Export to cloud storage (S3, GCS)
- [ ] Version comparison export
- [ ] Export validation rules

---

## Files Modified

1. ✅ `/flask_backend/app/routes/schemas.py` - Added 5 new export endpoints + helper function
2. ✅ `/Frontend/src/pages/Schemas.tsx` - Added export handlers and buttons

---

## Summary

✅ Export individual schemas (JSON/SQL)  
✅ Export all schemas (JSON/SQL)  
✅ Download files to computer  
✅ Available to all authenticated users  
✅ Comprehensive metadata included  
✅ PostgreSQL-compatible SQL output  
✅ User-friendly frontend interface
