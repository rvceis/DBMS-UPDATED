# Data Import & Update Features

## Overview
This document explains the new data import, schema adaptation, and record update features added to the DBMS system.

## Features

### 1. File Import (Multiple Formats)

#### Supported Formats
- **CSV** - Comma-separated values
- **TSV** - Tab-separated values
- **JSON** - Single object or array of objects
- **Excel (.xlsx, .xls)** - Spreadsheet files
- **Pipe-separated** - Using `|` delimiter
- **Semicolon-separated** - Using `;` delimiter
- **Key-value format** - For simple structured data

#### How to Import Files

**Frontend (UI Method):**
1. Go to **Data Page**
2. Click **"Import File"** button
3. Select your data file
4. Choose target schema (or auto-detect)
5. Select asset type (optional)
6. Toggle "Auto-adapt schema" if you want new fields added automatically
7. Review the preview
8. Click **"Confirm & Import"**

**Backend API:**

```bash
# Step 1: Upload file and get preview
curl -X POST http://localhost:5000/api/uploads/import-file \
  -H "Authorization: Bearer <token>" \
  -F "file=@data.csv" \
  -F "schema_id=1" \
  -F "auto_adapt_schema=true"

# Response includes:
# - format_detected: Detected file format
# - record_count: Number of records found
# - preview: First 10 records
# - suggested_fields: Auto-detected field types
# - fields_added: Whether schema was updated

# Step 2: Confirm import
curl -X POST http://localhost:5000/api/uploads/import-file-confirm \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "records": [array of records from preview],
    "schema_id": 1,
    "asset_type_id": 2,
    "tag": "Batch1"
  }'
```

### 2. Automatic Schema Adaptation

When importing data with new fields, the system can automatically:

1. **Detect Field Types** - Analyzes sample data to infer types:
   - `string` - Text values
   - `integer` - Whole numbers
   - `float` - Decimal numbers
   - `boolean` - True/False values
   - `date` - Date values
   - `json` - Complex structures

2. **Add New Fields** - Creates schema fields for data fields not in the schema

3. **Preserve Existing Schema** - Doesn't modify existing fields

#### Enable/Disable Auto-Adaptation

```typescript
// In FileImportDialog
const [autoAdapt, setAutoAdapt] = useState(true);

// In API call
formData.append('auto_adapt_schema', String(autoAdapt));
```

#### Example: CSV Import with Schema Adaptation

**Input CSV:**
```csv
name,age,email,active,tags
John,30,john@example.com,true,"[""admin""]"
Jane,28,jane@example.com,false,"[""user""]"
```

**Auto-Detected Fields:**
- `name` → string
- `age` → integer
- `email` → string
- `active` → boolean
- `tags` → json

**Result:** All new fields automatically added to schema

### 3. Display Asset Type Names

Changed all UI displays to show asset type names instead of IDs.

#### Before:
```
Asset Type ID: 5
```

#### After:
```
Asset Type: Image
```

#### Implementation in DataPage:

```typescript
<TableCell>
  {record.asset_type_id
    ? assetTypes.find((at) => at.id === record.asset_type_id)?.name 
    : '-'}
</TableCell>
```

### 4. Update Records & Schemas

#### Update Record (in Detail Drawer)

1. Click a record in the table to open detail drawer
2. Click **"Edit"** button
3. Modify fields:
   - Record name
   - Tag
   - Data values
4. Click **"✅ Save Changes"**

#### Update via API

```bash
# Update a metadata record
curl -X PUT http://localhost:5000/api/metadata/<record_id> \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "tag": "newtag",
    "asset_type_id": 2,
    "values": {
      "field1": "new_value",
      "field2": 100
    }
  }'
```

#### Add New Fields to Record (with Schema Adaptation)

```bash
curl -X POST http://localhost:5000/api/metadata/<record_id>/add-fields \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "new_fields": {
      "new_field1": "value1",
      "new_field2": 42
    },
    "add_to_schema": true
  }'
```

This will:
1. Add new fields to the record
2. Infer field types from values
3. Create new schema fields if `add_to_schema` is true

### 5. Field Type Inference

The system automatically infers field types from data:

```python
# Boolean detection
value in ['true', 'false', '1', '0', 'yes', 'no', 'y', 'n']

# Integer detection
try: int(value) → field_type = 'integer'

# Float detection
try: float(value) → field_type = 'float'

# Date detection
datetime.fromisoformat(value) → field_type = 'date'

# JSON detection
isinstance(value, dict) or isinstance(value, list) → field_type = 'json'

# Default
field_type = 'string'
```

## API Endpoints

### File Import

**POST** `/api/uploads/import-file`
- Upload file and get preview
- Multipart form data
- Returns: Format, record count, preview, suggested fields

**POST** `/api/uploads/import-file-confirm`
- Confirm and import records
- JSON body with records array
- Returns: Number of records created, record IDs

### Record Management

**PUT** `/api/metadata/<record_id>`
- Update record fields
- JSON body
- Returns: Success message

**POST** `/api/metadata/<record_id>/add-fields`
- Add new fields to record with schema adaptation
- JSON body
- Returns: Count of fields added

## UI Components

### FileImportDialog (`src/components/FileImportDialog.tsx`)
- File selection
- Format auto-detection
- Preview display
- Schema mapping
- Confirmation

### DataPage Updates
- "Import File" button
- File import dialog integration
- Edit mode in detail drawer
- Asset type name display
- Record update functionality

## Example Workflows

### Workflow 1: Import CSV with Auto-Schema

1. Prepare CSV file:
   ```csv
   product_name,quantity,price,in_stock
   Widget A,100,29.99,true
   Widget B,50,19.99,false
   ```

2. Click "Import File"
3. Select file
4. Enable "Auto-adapt schema"
5. Confirm import
6. Schema automatically has: product_name, quantity, price, in_stock fields

### Workflow 2: Import & Update

1. Import initial data
2. Click record to open detail drawer
3. Click "Edit"
4. Modify values
5. Click "✅ Save Changes"
6. Record updated in database

### Workflow 3: Add Fields to Record

1. Open record detail
2. Click "Edit"
3. Add new field values
4. Depending on implementation, new fields added to schema

## Error Handling

The system handles:
- Invalid file formats
- Missing required fields
- Type conversion errors
- Schema not found
- Permission errors (admin/editor only)

All errors are logged and returned in JSON responses.

## Installation

Ensure openpyxl is installed for Excel support:

```bash
pip install openpyxl
```

## Performance Considerations

- Large files (>10MB) may take time to process
- Preview limited to first 10 records for performance
- Batch imports recommended for >1000 records
- Database indexes on schema_id and asset_type_id recommended

## Security

- File uploads validated for type and size
- SQL injection prevention via ORM
- Authentication required for all endpoints
- Role-based access control (admin/editor for create/update)

## Future Enhancements

- [ ] Batch processing for large files
- [ ] Progress tracking for imports
- [ ] Data validation rules per field
- [ ] Import templates and profiles
- [ ] Field mapping editor
- [ ] Data transformation during import
- [ ] Rollback functionality for failed imports
