# Schema and Record Content Viewer - Feature Guide

## Overview

Two new features have been added to view and manage schema and record content:

1. **Schema Content Viewer** - View complete schema metadata and all records
2. **Enhanced Record Detail View** - Already available in the Detail Drawer

---

## Backend Endpoints

### 1. View Schema Content Summary
**Endpoint**: `GET /api/data/schema/<schema_id>/content`

**Purpose**: Get schema metadata, field definitions, and summary statistics

**Response**:
```json
{
  "schema": {
    "id": 24,
    "name": "Test Schema",
    "version": 1,
    "asset_type_id": 5,
    "created_at": "2026-01-02T15:38:30.474928",
    "created_by": 8,
    "is_active": true,
    "allow_additional_fields": true,
    "parent_schema_id": null
  },
  "summary": {
    "record_count": 2,
    "field_count": 3,
    "fields": [
      {
        "name": "name",
        "type": "string",
        "required": false,
        "description": "Auto-detected string field"
      },
      {
        "name": "age",
        "type": "integer",
        "required": false,
        "description": "Auto-detected integer field"
      },
      {
        "name": "city",
        "type": "string",
        "required": false,
        "description": "Auto-detected string field"
      }
    ],
    "tags": ["important", "test"],
    "asset_types": [
      {
        "id": 5,
        "name": "Dataset"
      }
    ]
  }
}
```

### 2. View All Records in Schema
**Endpoint**: `GET /api/data/schema/<schema_id>/records`

**Parameters**:
- `limit` (default: 100) - Number of records to return
- `offset` (default: 0) - Pagination offset
- `search` (optional) - Search by record name
- `tag` (optional) - Filter by tag

**Response**:
```json
{
  "schema": { /* schema object */ },
  "records": [
    {
      "id": 24,
      "name": "Record 1",
      "schema_id": 10,
      "asset_type_id": 5,
      "tag": "important",
      "created_at": "2026-01-02T15:38:30",
      "values": {
        "name": "Alice",
        "age": 30,
        "city": "NYC"
      }
    },
    /* ... more records ... */
  ],
  "total": 150,
  "limit": 100,
  "offset": 0
}
```

---

## Frontend Components

### SchemaContentViewer Component

**Location**: `Frontend/src/components/SchemaContentViewer.tsx`

**Usage**:
```typescript
import SchemaContentViewer from '@/components/SchemaContentViewer';

<SchemaContentViewer 
  schemaId={24}
  schemaName="Test Schema"
/>
```

**Features**:

#### Overview Tab
- **Statistics**: Shows total record count and field count
- **Fields Table**: Lists all fields with type, requirement status
- **Tags**: Shows all unique tags used in records
- **Asset Types**: Shows asset types used in records
- **Download**: Export schema content as JSON

#### Records Tab
- **Record List**: Shows first 50 records in the schema
- **Record Details**: ID, Name, Tag, Creation Date
- **Pagination**: Supports limit/offset parameters

---

## Frontend Integration

### 1. Schemas Page
The "View Content" button has been added to the Schema Editor:

```
[Schemas] → [Select Schema] → [View Content] button appears
```

**Location**: `Frontend/src/pages/Schemas.tsx` line 199

**Functionality**:
- Opens dialog showing schema overview and records
- Two tabs: Overview and Records
- Download schema content as JSON

### 2. Data Page
The existing Detail Drawer shows individual record content:

```
[Data] → [Click on Record] → [Detail Drawer Opens]
```

**Features**:
- View record ID, Schema, Asset Type
- View all data values in JSON format
- Edit record data
- Edit record name and tag

---

## How to Use

### View Schema Overview and Records

1. Go to **Schemas** page
2. Select a schema from the list
3. Click **"View Content"** button
4. View schema overview:
   - Total records and fields
   - Field definitions with types
   - Tags and asset types used
   - Download JSON
5. Click **"Records"** tab to view all records in schema

### View Individual Record Details

1. Go to **Data** page
2. Click on any record row
3. Detail drawer opens showing:
   - Record ID, Name, Schema, Asset Type, Tag
   - Complete data values in JSON format
   - Creation timestamp
   - Edit button to modify record

### Filter and Search

**In Data Page**:
- Use filters to narrow down records
- Filter by Schema, Asset Type, Tag
- Search by record name

**In Schema Content Viewer Records Tab**:
- Search by record name (added as parameter)
- Filter by tag

---

## Example Workflows

### Workflow 1: Audit Schema Usage
1. Go to Schemas page
2. Click "View Content" on a schema
3. Check:
   - How many records use this schema (Overview tab)
   - What fields are defined
   - What tags are used
   - Download summary for documentation

### Workflow 2: Find Records with Specific Content
1. Go to Data page
2. Select schema filter
3. Use search to find records by name
4. Click on record to view full details
5. Edit if needed

### Workflow 3: Export Schema Structure
1. Go to Schemas page
2. Select schema
3. Click "View Content"
4. Click "Download as JSON"
5. Use JSON file for backup or migration

---

## Code Examples

### Getting Schema Content via API
```typescript
const response = await fetch(`/api/data/schema/24/content`, {
  headers: {
    Authorization: `Bearer ${token}`,
  },
});
const data = await response.json();
console.log(data.summary.record_count); // Number of records
console.log(data.summary.fields);       // Field definitions
```

### Getting Records in Schema
```typescript
const response = await fetch(`/api/data/schema/24/records?limit=50&search=Alice`, {
  headers: {
    Authorization: `Bearer ${token}`,
  },
});
const data = await response.json();
data.records.forEach(record => {
  console.log(record.name, record.values);
});
```

### Viewing Record in Detail Drawer (Frontend)
```typescript
// Click on a record in the DataPage table
// The detail drawer automatically opens showing:
// - Record metadata (ID, Schema, AssetType, Tag)
// - Complete data values in JSON
// - Edit capabilities
```

---

## Features Summary

| Feature | Location | Capability |
|---------|----------|------------|
| Schema Overview | Schemas Page | View schema stats, fields, tags, asset types |
| Records List | Schema Content Viewer | View all records in schema, paginated |
| Record Details | Data Page Detail Drawer | View complete record data in JSON |
| Record Edit | Data Page Detail Drawer | Edit record name, tag, values |
| JSON Download | Schema Content Viewer | Export schema content as JSON file |
| Search Records | Data Page | Search by name, filter by schema/asset/tag |

---

## Performance Notes

- Schema overview query is optimized with indexed filters
- Records list supports pagination (default 100 records per page)
- Tag and asset type lookups are cached in response
- All queries have proper authorization checks

---

## Future Enhancements

Possible additions:
- Export records as CSV/Excel
- Bulk edit records
- Record versioning/history
- Advanced schema statistics (field usage, data type distribution)
- Record count by tag/asset type charts

---

## File Changes

### Backend
- `flask_backend/app/routes/data.py` - Added 2 new endpoints (lines 463-544)

### Frontend
- `Frontend/src/components/SchemaContentViewer.tsx` - New component
- `Frontend/src/pages/Schemas.tsx` - Added SchemaContentViewer button (line 40 import, line 199 button)

---

## Related Documentation

- [Data Management Guide](DATA_IMPORT_GUIDE.md)
- [Schema Management](BACKEND_ARCHITECTURE.md)
- [Form Validation](FEATURES_AND_VALIDATION_SUMMARY.md)

