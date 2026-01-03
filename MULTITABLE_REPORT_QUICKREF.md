# Multi-Table Report Generation - Quick Reference

## What's New?

✅ **Multi-Table Reports** - Generate reports from multiple schemas in one output  
✅ **Content Inclusion Options** - Choose what to include: records, metadata, schema details, summaries  
✅ **Runtime Customization** - Override content options when generating reports  
✅ **Backward Compatible** - Old single-schema templates still work  

## Quick Start

### 1. Create Multi-Table Template

```bash
curl -X POST http://localhost:5000/api/reports/templates \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Sales Summary",
    "table_configs": [
      {
        "schema_id": 1,
        "fields": ["product", "quantity", "price"],
        "filters": [{"field": "status", "operator": "eq", "value": "active"}],
        "limit": 1000
      },
      {
        "schema_id": 2,
        "fields": ["customer", "total"],
        "limit": 500
      }
    ],
    "include_records": true,
    "include_metadata": true,
    "include_schema_details": false,
    "include_summary": true
  }'
```

### 2. Generate Report

```bash
curl -X POST http://localhost:5000/api/reports/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": 1,
    "format": "csv"
  }'
```

### 3. Generate with Content Override

```bash
curl -X POST http://localhost:5000/api/reports/generate \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": 1,
    "format": "csv",
    "include_records": true,
    "include_metadata": false,
    "include_schema_details": true,
    "include_summary": false
  }'
```

## Content Options

| Option | Default | Description |
|--------|---------|-------------|
| `include_records` | `true` | Include actual data/record content |
| `include_metadata` | `true` | Include field metadata (types, properties) |
| `include_schema_details` | `false` | Include schema name, description, timestamps |
| `include_summary` | `true` | Include summary stats (record count, field count) |

## Table Configuration

Each table in `table_configs` array:

```json
{
  "schema_id": 1,
  "fields": ["field1", "field2"],  // Empty = all fields
  "filters": [
    {"field": "status", "operator": "eq", "value": "active"}
  ],
  "sort": [
    {"field": "created_at", "direction": "desc"}
  ],
  "limit": 1000
}
```

### Supported Filter Operators

- `eq` - Equals
- `contains` - Text contains (case-insensitive)
- `gt` - Greater than
- `lt` - Less than

## Report Output Structure

### CSV Format

```
Report: Sales Summary
Generated: 2024-01-20T14:30:00

Table: Product Sales
Description: Product sales data

SCHEMA INFORMATION
Property,Value
Schema Name,Product Sales
...

FIELD METADATA
Field Name,Type,Searchable,Required
product,text,true,true
...

SUMMARY
Total Records,145
Total Fields,8

RECORDS
ID,Name,product,quantity,price
1,Sale-001,Widget,100,49.99
...

[Next table sections follow...]
```

### PDF Format

- Professional header with title and timestamp
- Per-table pages with organized sections
- Formatted tables for each content type
- Limited to first 50 records per table (with count indicator)

## Testing

Run the test script:

```bash
cd flask_backend
python3 test_multitable_reports.py
```

Expected output:
- Creates multi-table template
- Generates CSV report
- Generates report with overrides
- Tests legacy template compatibility

## API Endpoints Modified

| Endpoint | Method | Changes |
|----------|--------|---------|
| `/api/reports/templates` | POST | Accepts `table_configs` and content options |
| `/api/reports/templates/<id>` | PUT | Updates content options |
| `/api/reports/generate` | POST | Accepts runtime content overrides |

## Model Changes

### ReportTemplate

**New Fields:**
- `table_configs` (JSON) - Multi-table configuration
- `include_records` (Boolean) - Include record content
- `include_metadata` (Boolean) - Include field metadata
- `include_schema_details` (Boolean) - Include schema info
- `include_summary` (Boolean) - Include summary stats

**Legacy Fields (still supported):**
- `schema_id` (Integer) - Single schema
- `query_config` (JSON) - Legacy query config

## Backward Compatibility

Old templates with `schema_id` continue to work:

```json
{
  "name": "Old Style Report",
  "schema_id": 5,
  "query_config": {
    "fields": ["name", "email"],
    "filters": [],
    "limit": 100
  }
}
```

The system automatically detects template type and routes to appropriate generator.

## Examples

### Example 1: Data Inventory Report

Include records and summaries only:

```json
{
  "name": "Data Inventory",
  "table_configs": [
    {"schema_id": 1, "fields": [], "limit": 1000},
    {"schema_id": 2, "fields": [], "limit": 1000}
  ],
  "include_records": true,
  "include_metadata": false,
  "include_schema_details": false,
  "include_summary": true
}
```

### Example 2: Schema Documentation

Metadata and details only (no records):

```json
{
  "name": "Schema Documentation",
  "table_configs": [
    {"schema_id": 1},
    {"schema_id": 2},
    {"schema_id": 3}
  ],
  "include_records": false,
  "include_metadata": true,
  "include_schema_details": true,
  "include_summary": true
}
```

### Example 3: Filtered Sales Report

Specific fields with filters:

```json
{
  "name": "Q1 Sales",
  "table_configs": [
    {
      "schema_id": 5,
      "fields": ["product", "quantity", "revenue"],
      "filters": [
        {"field": "date", "operator": "gt", "value": "2024-01-01"},
        {"field": "status", "operator": "eq", "value": "completed"}
      ],
      "sort": [{"field": "revenue", "direction": "desc"}],
      "limit": 500
    }
  ],
  "include_records": true,
  "include_metadata": false,
  "include_summary": true
}
```

## Files Modified

1. `flask_backend/app/models.py` - ReportTemplate model enhanced
2. `flask_backend/app/routes/reports.py` - Endpoints updated
3. `flask_backend/app/services/report_generator.py` - Multi-table logic added
4. `flask_backend/app/services/report_export_service.py` - Export methods added

## Documentation

- Full guide: `MULTITABLE_REPORT_ENHANCEMENT.md`
- Test script: `flask_backend/test_multitable_reports.py`
- This reference: `MULTITABLE_REPORT_QUICKREF.md`

## Next Steps

1. **Database Migration** - Add new columns to report_templates table
2. **Frontend UI** - Build multi-table template builder
3. **Testing** - Run test script and verify outputs
4. **PDF Generation** - Test PDF format with multiple tables
5. **User Documentation** - Update user guide

## Common Use Cases

### Use Case 1: Comprehensive Data Export

Export all data from multiple related schemas:
- Products + Orders + Customers
- Include all records
- Include summaries
- CSV format for spreadsheet analysis

### Use Case 2: Technical Documentation

Generate schema documentation:
- All schemas in system
- No records (just metadata)
- Include field types and descriptions
- PDF format for documentation

### Use Case 3: Executive Summary

High-level overview:
- Key schemas only
- Summaries only (no individual records)
- Include schema descriptions
- PDF format for presentation

## Troubleshooting

**Template creation fails with "schema_id not found"**
- Verify schema IDs exist in database
- Check user has access to schemas

**Generated report is empty**
- Check `include_records` is `true`
- Verify schemas have records
- Check filters aren't too restrictive

**Report generation timeout**
- Reduce `limit` in table configs
- Reduce number of tables
- Disable expensive sections (metadata, schema_details)

**PDF has formatting issues**
- For many columns, prefer CSV format
- PDF limited to first 50 records per table
- Use fewer fields in `fields` array
