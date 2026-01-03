# Multi-Table Report Generation with Content Inclusion

## Overview

Enhanced the report generation system to support:
1. **Multi-table Reports** - Generate reports from multiple schemas/tables in a single output
2. **Content Inclusion Options** - Choose what to include: records, metadata, schema details, summaries
3. **Flexible Customization** - Override content options at generation time
4. **Backward Compatibility** - Legacy single-table templates still work

## Key Features

### 1. Multi-Table Templates

Create templates that span multiple tables with per-table configuration:

```json
{
  "name": "Comprehensive Data Report",
  "table_configs": [
    {
      "schema_id": 1,
      "fields": ["name", "status"],
      "filters": [{"field": "status", "operator": "eq", "value": "active"}],
      "sort": [{"field": "created_at", "direction": "desc"}],
      "limit": 1000
    },
    {
      "schema_id": 2,
      "fields": ["title", "author"],
      "filters": [],
      "limit": 500
    }
  ],
  "include_records": true,
  "include_metadata": true,
  "include_schema_details": false,
  "include_summary": true
}
```

### 2. Content Options

Four boolean flags control report content:

- **`include_records`** (default: true) - Include actual data/record content
- **`include_metadata`** (default: true) - Include field metadata (types, properties)
- **`include_schema_details`** (default: false) - Include schema name, description, timestamps
- **`include_summary`** (default: true) - Include summary stats (record count, field count)

### 3. Report Output Sections

Generated reports contain sections for each configured table:

```
[SCHEMA INFORMATION]  - if include_schema_details=true
Schema Name: users
Description: User management table
Created: 2024-01-15T10:30:00

[FIELD METADATA]  - if include_metadata=true
Field Name | Type | Searchable | Required
id         | int  | true       | true
name       | text | true       | false
email      | text | true       | true

[SUMMARY]  - if include_summary=true
Total Records: 1,245
Total Fields: 12

[RECORDS]  - if include_records=true
id | name | email | status | ...
1  | John | j@... | active | ...
2  | Jane | jane@ | active | ...
...
```

## API Usage

### Create Multi-Table Template

```bash
POST /api/reports/templates

{
  "name": "Sales Report",
  "description": "Complete sales data with summaries",
  "table_configs": [
    {
      "schema_id": 3,
      "fields": ["product", "quantity", "price"],
      "filters": [{"field": "date", "operator": "gt", "value": "2024-01-01"}]
    },
    {
      "schema_id": 4,
      "fields": ["customer", "total"],
      "limit": 500
    }
  ],
  "include_records": true,
  "include_metadata": true,
  "include_schema_details": true,
  "include_summary": true,
  "is_public": false
}
```

### Generate Report with Content Options Override

```bash
POST /api/reports/generate

{
  "template_id": 5,
  "format": "csv",
  "include_records": true,
  "include_metadata": false,
  "include_schema_details": true,
  "include_summary": false,
  "params": {
    "limit": 100
  }
}
```

### Update Template

```bash
PUT /api/reports/templates/5

{
  "name": "Updated Sales Report",
  "table_configs": [...],
  "include_metadata": false,
  "include_summary": true
}
```

## Export Formats

### CSV Export

Multi-table CSV contains:
- Report header (title, generated date)
- Per-table sections separated by blank lines
- Schema information rows (if enabled)
- Field metadata table (if enabled)
- Summary statistics (if enabled)
- Record data rows (if enabled)

Example structure:
```
Report: Sales Report
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
```

### PDF Export

Multi-table PDF contains:
- Professional header with report title and generation timestamp
- Per-table pages with organized sections
- Schema information box (if enabled)
- Formatted field metadata table (if enabled)
- Summary statistics (if enabled)
- Records in formatted table (first 50 rows, if enabled)
- "Showing X of Y records" message for large datasets

## Backend Implementation

### Modified Files

1. **`flask_backend/app/models.py`**
   - Added to `ReportTemplate` model:
     - `table_configs` (JSON) - Multi-table configuration
     - `include_records` (Boolean)
     - `include_metadata` (Boolean)
     - `include_schema_details` (Boolean)
     - `include_summary` (Boolean)

2. **`flask_backend/app/routes/reports.py`**
   - `POST /templates` - Now accepts `table_configs` and content options
   - `PUT /templates/<id>` - Updated to handle new fields
   - `POST /generate` - Accepts runtime content option overrides

3. **`flask_backend/app/services/report_generator.py`**
   - `generate_report()` - Dispatches to multi-table or single-table method
   - `_generate_multitable_report()` - NEW: Handles multi-table logic
   - `_collect_multitable_data()` - NEW: Collects data from all tables
   - `_query_records()` - NEW: Queries records with field/filter selection
   - `_generate_single_table_report()` - Refactored legacy method

4. **`flask_backend/app/services/report_export_service.py`**
   - `export_multitable_csv()` - NEW: Exports multi-table data to CSV
   - `export_multitable_pdf()` - NEW: Exports multi-table data to PDF

### New Helper Methods

**`_query_records(schema, query_config)`**
- Filters records based on query_config
- Supports operators: eq, contains, gt, lt
- Applies sorting and limits
- Returns list of record dictionaries

**`_collect_multitable_data(template, params)`**
- Iterates through each table_config
- Builds report_data structure with sections
- Includes schema info, metadata, summary, records based on flags
- Returns comprehensive report structure

## Data Structure

### Template Storage

```python
ReportTemplate {
  id: int,
  name: str,
  description: str,
  schema_id: int (legacy, nullable),
  table_configs: [{
    schema_id: int,
    fields: [str],
    filters: [{field, operator, value}],
    sort: [{field, direction}],
    limit: int
  }],
  include_records: bool,
  include_metadata: bool,
  include_schema_details: bool,
  include_summary: bool,
  query_config: dict (legacy),
  ...
}
```

### Report Data Structure

```python
{
  "title": str,
  "description": str,
  "generated_at": ISO datetime,
  "include_records": bool,
  "include_metadata": bool,
  "include_schema_details": bool,
  "include_summary": bool,
  "tables": [{
    "schema_id": int,
    "schema_name": str,
    "schema_description": str,
    "data": [
      {
        "type": "schema_info",
        "schema_name": str,
        "schema_description": str,
        ...
      },
      {
        "type": "field_metadata",
        "field_name": str,
        "field_type": str,
        ...
      },
      {
        "type": "summary",
        "total_records": int,
        "total_fields": int
      },
      {
        "type": "record",
        "record_id": int,
        "record_name": str,
        "content": {...}
      }
    ]
  }]
}
```

## Usage Examples

### Example 1: Simple Multi-Table Report

```python
# Create template
POST /api/reports/templates
{
  "name": "Data Inventory",
  "table_configs": [
    {"schema_id": 1, "fields": []},
    {"schema_id": 2, "fields": []}
  ],
  "include_records": true,
  "include_metadata": false,
  "include_summary": true
}

# Generate
POST /api/reports/generate
{
  "template_id": 1,
  "format": "csv"
}
```

### Example 2: Detailed Report with Metadata

```python
POST /api/reports/templates
{
  "name": "Schema Documentation",
  "table_configs": [
    {"schema_id": 1}
  ],
  "include_records": false,
  "include_metadata": true,
  "include_schema_details": true,
  "include_summary": true
}
```

### Example 3: Runtime Customization

```python
# Template includes everything
POST /api/reports/templates
{
  "name": "Full Report",
  "table_configs": [...],
  "include_records": true,
  "include_metadata": true,
  "include_schema_details": true,
  "include_summary": true
}

# Generate but exclude schema details
POST /api/reports/generate
{
  "template_id": 1,
  "format": "csv",
  "include_schema_details": false
}
```

## Backward Compatibility

Legacy templates using single `schema_id` continue to work:

```python
# Old style still works
POST /api/reports/templates
{
  "name": "Legacy Report",
  "schema_id": 5,
  "query_config": {...}
}

# Generates as before
POST /api/reports/generate
{
  "template_id": 1,
  "format": "csv"
}
```

The system automatically detects whether a template uses `table_configs` or `schema_id` and dispatches to the appropriate generation method.

## Frontend Integration (Next Steps)

1. **Template Builder UI**
   - Multi-table selector
   - Per-table field/filter configuration
   - Content inclusion checkboxes

2. **Report Generation Dialog**
   - Format selector (CSV/PDF)
   - Content option overrides
   - Report preview

3. **Template List**
   - Display table count
   - Show enabled content options

## Testing Checklist

- [ ] Create multi-table template via API
- [ ] Generate CSV from multi-table template
- [ ] Generate PDF from multi-table template
- [ ] Override content options at generation time
- [ ] Verify backward compatibility with single-table templates
- [ ] Test with empty content options
- [ ] Test with large datasets (>1000 records)
- [ ] Verify field filtering works
- [ ] Verify record filtering works
- [ ] Check PDF pagination with many tables
- [ ] Verify CSV section headers and formatting

## Future Enhancements

1. **Advanced Filtering** - Date range, regex, JSON path filters
2. **Charting** - Include summary charts in PDF
3. **Email Distribution** - Send reports via email
4. **Scheduling** - Automated report generation
5. **Data Validation** - Pre-generation validation checks
6. **Custom Sections** - User-defined sections and calculations
7. **Multi-Sheet Excel** - One sheet per table
8. **HTML Export** - Web-viewable reports
