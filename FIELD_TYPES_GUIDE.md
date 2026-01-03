# Field Type Support & Validation Guide

## Current Supported Field Types

The dynamic schema system supports the following field types:

```
✅ string          - Text fields
✅ integer         - Whole numbers
✅ float           - Decimal numbers
✅ boolean         - True/False values
✅ date            - Date values (YYYY-MM-DD format)
✅ json            - JSON objects/arrays
✅ array           - Generic arrays (can contain any supported type)
✅ object          - JSON objects
```

## Unsupported Type Patterns

The following type patterns are **NOT currently supported**:

```
❌ array<string>       - Specific array of strings (not supported)
❌ array<integer>      - Specific array of integers (not supported)
❌ object<key:value>   - Typed objects (not supported)
```

## Solution for Array Fields

If you need to store arrays of strings or other types, use one of these approaches:

### Option 1: Use `json` type (RECOMMENDED)
Store arrays as JSON:

```python
{
    "tags": {
        "type": "json",
        "required": True,
        "description": "Array of tags stored as JSON"
    }
}
```

Usage:
```json
{
    "tags": ["nodejs", "python", "javascript"]
}
```

### Option 2: Use `array` type
Use generic array type:

```python
{
    "tags": {
        "type": "array",
        "required": True,
        "description": "Array of tags"
    }
}
```

Usage:
```json
{
    "tags": ["nodejs", "python", "javascript"]
}
```

### Option 3: Store as comma-separated string
Simple approach using string field:

```python
{
    "tags": {
        "type": "string",
        "required": True,
        "description": "Tags separated by comma"
    }
}
```

Usage:
```json
{
    "tags": "nodejs,python,javascript"
}
```

---

## Fixing the Test Data Script

To fix the failing Blog Posts and Social Media records in `generate_test_data.py`:

### Before (FAILS)
```python
blog_schema = {
    "name": "BlogPostSchema",
    "fields": [
        {"name": "title", "type": "string", "required": True},
        {"name": "content", "type": "string", "required": True},
        {"name": "tags", "type": "array<string>", "required": False},  # ❌ NOT SUPPORTED
    ]
}
```

### After (WORKS)
```python
blog_schema = {
    "name": "BlogPostSchema",
    "fields": [
        {"name": "title", "type": "string", "required": True},
        {"name": "content", "type": "string", "required": True},
        {"name": "tags", "type": "json", "required": False},  # ✅ USE json OR array
    ]
}
```

---

## Adding New Field Types (For Future Development)

To add support for new field types, modify the validation engine:

**File**: `flask_backend/app/services/metadata_extractor.py`

```python
SUPPORTED_TYPES = {
    'string': str,
    'integer': int,
    'float': float,
    'boolean': bool,
    'date': 'date',
    'json': dict,
    'array': list,
    'object': dict,
    # ADD NEW TYPES HERE:
    'array<string>': list,  # Specific array type
    'email': str,           # Email validation
    'url': str,             # URL validation
    'phone': str,           # Phone number
}
```

Then update the validation logic to handle the new type:

```python
def validate_field(field_name, field_type, value):
    if field_type == 'array<string>':
        if not isinstance(value, list):
            raise ValueError(f"Field '{field_name}' must be an array")
        if not all(isinstance(v, str) for v in value):
            raise ValueError(f"Field '{field_name}' must contain only strings")
    # ... more validation
```

---

## Current Test Data Results

### ✅ Successfully Created (14 records)
- CustomerSchema: 2 records
- ProductInventory: 3 records
- EmployeeSchema: 2 records
- SensorDataSchema: 3 records
- ProjectSchema: 2 records
- FlexibleSchema: 2 records

### ❌ Failed Due to Type Validation (2 records)
- BlogPostSchema: Used `array<string>` for tags field
- SocialMediaSchema: Used `array<string>` for hashtags field

### 📝 To Fix

Edit `generate_test_data.py` and change:
1. Line ~120: Change `"type": "array<string>"` to `"type": "json"` in blog schema
2. Line ~140: Change `"type": "array<string>"` to `"type": "json"` in social media schema

Then rerun:
```bash
python3 generate_test_data.py
```

Expected result: **18/18 records successfully created (100%)**

---

## Implementation Notes

The field type validation is performed in:
- **Backend**: `flask_backend/app/services/metadata_extractor.py` (validate_field_type())
- **Database**: SQLAlchemy model constraints in `flask_backend/app/models.py`
- **Frontend**: TypeScript types in `Frontend/src/types/` (if added)

All validation happens before inserting into database, providing immediate feedback on invalid field types.

