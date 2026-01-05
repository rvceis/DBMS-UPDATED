# Dynamic Schema System - Complete Explanation

## Overview

This DBMS system supports **completely dynamic schemas** with relational data capabilities. Unlike traditional fixed-schema databases, this system allows schemas to evolve while maintaining data integrity and ACID compliance.

---

## 1. Core Architecture

### Three-Layer Data Storage Strategy

```
┌─────────────────────────────────────────────────┐
│         APPLICATION LAYER                       │
│  (Dynamic Schema Management)                    │
└─────────────────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
    ┌───▼──┐      ┌──▼───┐     ┌──▼────┐
    │ EAV  │      │ JSONB│     │Table  │
    │Model │      │Model │     │Model  │
    └──────┘      └──────┘     └───────┘
```

**Layer 1: JSONB Storage (PostgreSQL)**
- Stores entire records as JSON documents
- Supports nested objects and arrays
- GIN indexes for fast querying
- Best for: Dynamic, unstructured data

**Layer 2: EAV Pattern (Entity-Attribute-Value)**
- Normalized storage for relational queries
- Supports type-specific value columns
- Best for: Querying and filtering

**Layer 3: Table-Based Storage (DataRow)**
- Individual rows stored separately
- ACID compliant operations
- Best for: Bulk imports and large datasets

---

## 2. Dynamic Schema Models

### SchemaModel - Flexible Schema Definition

```python
class SchemaModel(db.Model):
    id              # Unique identifier
    name            # Schema name (e.g., "Phase1 Schema")
    version         # Schema version (1, 2, 3, ...)
    asset_type_id   # Link to asset type
    parent_schema_id # Previous version (for history tracking)
    allow_additional_fields  # Boolean - allow fields not in schema
    is_active       # Boolean - active/inactive
    schema_json     # Full schema as JSON (backup)
    created_by      # User who created it
    created_at      # Creation timestamp
```

**Key Features:**
- ✅ Versioning support (schema v1, v2, v3...)
- ✅ Parent-child relationships for tracking evolution
- ✅ Additional fields allowed (flexible beyond schema)
- ✅ Full audit trail

### SchemaField - Individual Field Definitions

```python
class SchemaField(db.Model):
    schema_id           # Which schema this field belongs to
    field_name          # Field name (e.g., "temperature")
    field_type          # string, integer, float, boolean, date, json, array
    is_required         # Required or optional
    default_value       # Default if not provided
    constraints         # JSON: {min, max, regex, enum, pattern}
    description         # Field description
    is_deleted          # Soft delete for rollback
    order_index         # Display order
```

**Supported Field Types:**
```
- string        → Text data
- integer       → Whole numbers
- float         → Decimal numbers
- boolean       → True/False
- date          → ISO date/datetime
- json          → Objects and nested structures
- array         → Lists of values
- object        → Nested objects
```

---

## 3. Data Storage Models

### MetadataRecord - Container for All Data

```python
class MetadataRecord(db.Model):
    id              # Record ID
    name            # Record name (e.g., "phase5")
    schema_id       # Associated schema
    asset_type_id   # Asset type
    
    # Multiple storage options for flexibility
    metadata_json   # Full JSON document
    raw_data        # Raw import data
    
    # Relationships
    field_values    # EAV entries (related records)
    data_rows       # Table rows (bulk data)
    
    created_at, updated_at
```

### DataRow - Actual Data Storage

```python
class DataRow(db.Model):
    """For bulk imports and large datasets"""
    record_id       # Which metadata record
    row_index       # Order in dataset
    data            # JSONB - actual row data
    created_at, updated_at
```

**Example - Storing 100 sensor readings:**
```
record_id=1  (name="phase5")
  ├─ data_row[0]: {device_id: "sensor_001", temperature: 28.5, humidity: 60, ...}
  ├─ data_row[1]: {device_id: "sensor_002", temperature: 29.0, humidity: 62, ...}
  ├─ data_row[2]: {device_id: "sensor_003", temperature: 27.8, humidity: 58, ...}
  └─ ...
```

### FieldValue - EAV Storage

```python
class FieldValue(db.Model):
    """For normalized relational queries"""
    record_id       # Which record
    schema_field_id # Which field
    
    # Type-specific columns (for performance)
    value_text      # For string fields
    value_int       # For integer fields
    value_float     # For float fields
    value_bool      # For boolean fields
    value_date      # For date fields
    value_json      # For complex types
```

---

## 4. How Dynamic Schemas Support Relational Data

### Scenario: Evolving Sensor Data

**File 1 (Phase 1):**
```csv
device_id, timestamp, temperature
sensor_001, 2025-12-31, 28.5
sensor_002, 2025-12-31, 29.0
```
✅ Creates: Schema v1 with 3 fields

**File 2 (Phase 2):**
```csv
device_id, timestamp, temperature, humidity
sensor_001, 2025-12-31, 28.5, 60
sensor_002, 2025-12-31, 29.0, 62
```

**System Detects:**
- Same device_id and timestamp
- humidity field is NEW
- temperature field still exists

**Decision Options:**
```
Option 1: Add Fields to Same Schema
  → Schema v1 becomes: v2 with humidity added
  → Both phase1 and phase2 data use v2
  → Data from phase1 gets humidity=NULL

Option 2: Create New Schema Version
  → Schema v1 (phase1 data)
  → Schema v2 (phase2 data)
  → Parent: v1
  → Relationship: "Added humidity field"

Option 3: Keep Separate Schemas
  → Schema A: Phase 1 (3 fields)
  → Schema B: Phase 2 (4 fields)
  → Both active, independent
```

### Relational Capability: Query Across Versions

**Query: Get all temperature readings from all versions**
```python
# Works because system tracks:
# - device_id (common field)
# - timestamp (common field)
# - temperature (exists in v1, v2, v3)

result = MetadataRecord.query.filter_by(asset_type_id=1)
# Returns data from ALL schema versions
# Automatically handles missing fields (NULL)
```

---

## 5. Schema Evolution & Versioning

### ChangeLog - Track All Changes

```python
class ChangeLog(db.Model):
    schema_id       # Which schema
    change_type     # "add_fields", "new_version", "update", etc.
    description     # Human-readable description
    change_details  # JSON details
        {
            "action": "add_fields",
            "fields_added": ["humidity", "pressure"],
            "from_schema": 1,
            "to_schema": 2
        }
    schema_snapshot # Complete state after change
    changed_by      # User who made change
    timestamp       # When change occurred
```

### SchemaVersion - Snapshot for Rollback

```python
class SchemaVersion(db.Model):
    schema_id
    version_number      # v1, v2, v3, ...
    schema_snapshot     # Complete schema definition
    change_summary      # What changed from previous
    created_by
    created_at
```

**Allows:**
- ✅ View schema at any point in history
- ✅ Rollback to previous schema
- ✅ Compare versions
- ✅ Audit trail

---

## 6. Adding Dynamic Data

### Example 1: Add a New CSV File

**Process:**
```
1. Upload CSV file
2. System auto-detects field names and types
3. Compares with existing schemas (50% field match threshold)
4. Shows options:
   ├─ Add missing fields to existing schema
   ├─ Create new schema version
   └─ Create completely new schema
5. User selects option
6. Data imported with relationship maintained
```

**System automatically:**
- Creates SchemaField entries for new fields
- Records ChangeLog of what changed
- Creates SchemaVersion snapshot
- Stores data in DataRow (JSONB)

### Example 2: Add Single Record Manually

**Process:**
```python
# Create record matching schema
record = MetadataRecord(
    name="sensor_reading_001",
    schema_id=1,
    asset_type_id=1
)

# Add data using multiple methods:

# Method 1: JSONB (simple, fast)
record.raw_data = {
    "device_id": "sensor_001",
    "temperature": 28.5,
    "humidity": 60
}

# Method 2: EAV (relational, queryable)
FieldValue.create(record, field="temperature", value=28.5)
FieldValue.create(record, field="humidity", value=60)

# Method 3: DataRow (for bulk)
DataRow.create(record, row_index=0, data={...})
```

### Example 3: Add Relational Field

```python
# Add relationship to another entity
add_field(
    schema_id=1,
    field_name="location_id",
    field_type="integer",
    constraints={"foreign_key": "locations.id"}
)

# Now data can be queried with joins
```

---

## 7. Relational Data Support

### Foreign Keys

```python
# Schema supports constraints
field = SchemaField(
    schema_id=1,
    field_name="sensor_id",
    field_type="integer",
    constraints={
        "foreign_key": "sensors.id",
        "cascade_delete": True
    }
)
```

### Referenced Lookups

```python
# Data can reference other tables
sensor_reading = {
    "device_id": "sensor_001",        # Reference
    "location": "Room A",             # Reference
    "temperature": 28.5,
    "readings_count": 1024,           # Aggregate
    "last_calibration": "2025-01-01"  # Historical
}
```

### Queries Across Schemas

```python
# Schema v1: device_id, temperature
# Schema v2: device_id, temperature, humidity
# Schema v3: device_id, temperature, humidity, pressure

# Query all readings where temperature > 28
readings = MetadataRecord.query\
    .filter(MetadataRecord.raw_data['temperature'].astext.cast(Float) > 28)\
    .all()

# Returns data from ALL versions that have the field
```

---

## 8. Advanced Features

### Auto-Detection Algorithm

```
When importing new data:

1. Extract field names and types
2. Compare with existing schemas:
   a. Calculate field coverage: (matching_fields / schema_fields) * 100
   b. Prioritize schemas with > 50% coverage
   c. Flag new fields not in schema
3. Show user options:
   ├─ Use existing schema (coverage: 75%)
   ├─ Add fields to existing (coverage: 75%)
   ├─ Create new version
   └─ Create new schema
```

### Flexible Schema Definition

```python
# Schema allows additional fields beyond definition
allow_additional_fields = True

# User can add data with extra fields
data = {
    "defined_field_1": "value",
    "defined_field_2": 123,
    "extra_field_x": "bonus data",  # ← Allowed!
    "extra_field_y": {"nested": "data"}
}

# Extra fields stored in JSONB, not validated
# But tracked for future schema updates
```

### Type-Safe Storage

```python
# Different types handled properly

field = SchemaField(
    field_name="sensor_data",
    field_type="json"
)

# Stores complex nested data
value = {
    "readings": [
        {"ts": "2025-01-01T10:00:00", "value": 28.5},
        {"ts": "2025-01-01T10:01:00", "value": 29.0}
    ],
    "metadata": {
        "unit": "celsius",
        "sensor_type": "DHT22"
    }
}

# EAV model stores in value_json column
# Can be queried with PostgreSQL JSON operators
```

---

## 9. Real-World Example: Multi-Version Sensor Network

```
Asset Type: "Temperature Sensors"

Year 1 - Schema v1
├─ device_id: string
├─ timestamp: date
└─ temperature: float
Data: 1000 readings

Year 2 - Schema v2 (v1 + add_fields)
├─ device_id: string
├─ timestamp: date
├─ temperature: float
├─ humidity: float        ← NEW
└─ battery_level: integer ← NEW
Data: 1500 readings

Year 3 - Schema v3 (v2 + add_fields)
├─ All v2 fields
├─ pressure: float        ← NEW
├─ air_quality: string    ← NEW
└─ location_id: integer   ← Reference to locations table
Data: 2000 readings

Query: "Get average temperature by location across all 3 years"
→ System automatically:
  1. Handles NULL values for year 1 (no location_id)
  2. Handles NULL values for year 2 (no location_id)
  3. Joins with locations table for v3
  4. Aggregates temperature (exists in all versions)
  5. Returns results
```

---

## 10. Benefits of This Dynamic Schema System

| Feature | Benefit |
|---------|---------|
| **Schema Versioning** | Track evolution, rollback if needed |
| **JSONB Storage** | Flexible, nested data support |
| **EAV Model** | Relational queries, type safety |
| **Auto-Detection** | Intelligent schema matching (50% threshold) |
| **Change Tracking** | Audit trail, understand what changed |
| **Additional Fields** | Store extra data beyond schema |
| **Field Types** | 8+ types (string, number, date, json, etc.) |
| **Constraints** | Validation, foreign keys, defaults |
| **Multiple Imports** | Combine data from different sources |
| **Aggregation** | Query across all versions seamlessly |

---

## 11. How to Add Dynamic Data - Step by Step

### Option A: Upload New File
```
1. Go to Data → Import
2. Select CSV file
3. System detects fields
4. Choose: Add to existing schema OR Create new version
5. Data imported automatically
6. ChangeLog records what happened
```

### Option B: Create Single Record
```
1. Go to Data → Create New Record
2. Select Schema and version
3. Fill in fields (additional fields allowed)
4. Save
5. Data stored in JSONB + optional EAV
```

### Option C: Bulk Import API
```python
POST /api/data/bulk
{
    "schema_id": 1,
    "records": [
        {"device_id": "001", "temperature": 28.5},
        {"device_id": "002", "temperature": 29.0}
    ]
}
```

### Option D: Evolve Schema
```
1. Go to Schemas → View Versions
2. Click "Add Fields" or "Create New Version"
3. Add new fields (type, constraints, etc.)
4. System updates ChangeLog
5. New records use updated schema
6. Old records still queryable (NULL for new fields)
```

---

## 12. Query Examples

### Example 1: Simple Field Query
```python
# Get all records where temperature > 28
records = MetadataRecord.query.filter(
    MetadataRecord.raw_data['temperature'].cast(Float) > 28
).all()
```

### Example 2: Cross-Schema Query
```python
# Get temperature readings from ALL schema versions
query = db.session.query(
    MetadataRecord.name,
    MetadataRecord.schema_id,
    func.json_extract_path_text(
        MetadataRecord.raw_data, 'temperature'
    ).cast(Float)
).filter(
    MetadataRecord.asset_type_id == 1
).order_by(MetadataRecord.created_at)
```

### Example 3: Aggregation
```python
# Average temperature by device across all imports
query = db.session.query(
    func.json_extract_path_text(
        MetadataRecord.raw_data, 'device_id'
    ),
    func.avg(
        func.json_extract_path_text(
            MetadataRecord.raw_data, 'temperature'
        ).cast(Float)
    )
).group_by(
    func.json_extract_path_text(
        MetadataRecord.raw_data, 'device_id'
    )
)
```

---

## Summary

**Your system is a hybrid database that:**

✅ **Supports dynamic schemas** - fields can change over time
✅ **Maintains relationships** - can link to other tables/records
✅ **Tracks evolution** - complete history of schema changes
✅ **Allows flexible data** - extra fields beyond schema definition
✅ **Supports multiple storage models** - JSONB, EAV, Table
✅ **Enables cross-version queries** - transparently handles schema evolution
✅ **Provides audit trail** - who changed what and when
✅ **Auto-detects schema matches** - intelligent import recommendations

**You CAN add relational data in multiple ways:**
1. Add foreign key fields to schema
2. Reference other tables in data values
3. Use arrays to link multiple records
4. Create nested JSON objects for relationships
5. Use separate schema for linked entities

The system intelligently detects when data belongs together and helps you organize it!
