# Testing Dynamic Schema with Text Files

## Updated Code Features

### 1. **Enhanced Text File Detection** 
The `data_import_service.py` now automatically detects:
- **Structured Text** - Indented/hierarchical formats
- **Key-Value Format** - YAML-like, INI-like formats  
- **Nested JSON Structure** - Preserves hierarchy in JSONB storage
- **Arrays** - Stores as native JSON arrays, not flattened

### 2. **Proper JSON Storage in Database**
- Nested structures stored as-is in JSONB column
- Arrays remain arrays (not flattened)
- Related data stored within parent object (no separate tables needed)
- Each data type creates its own dynamic schema

### 3. **Type Inference**
Automatically converts values to correct types:
- `true/false/yes/no` → Boolean
- `123` → Integer
- `45.6` → Float
- `null/none` → Null
- Text → String

---

## Sample Datasets Provided

### **V1: IoT Sensors** (`sample_data_v1_IoT_devices.txt`)
**Dynamic Features:**
- Different sensor types: Temperature, Pressure, Motion
- Different readings per type
- Nested sensor_readings array
- Variable fields per device type

**Data Structure (JSON):**
```json
{
  "device_id": "SENSOR-001",
  "device_name": "Temperature Sensor Unit A",
  "device_type": "TemperatureSensor",
  "sensor_readings": [
    {
      "timestamp": "2025-01-01T08:00:00Z",
      "temperature_celsius": 22.5,
      "humidity_percent": 45
    }
  ]
}
```

**Relational Features:**
- `device_id` acts as unique identifier
- `sensor_readings` is nested array
- Device info + readings in one document

---

### **V2: Temperature & Humidity** (`SAMPLE_V2_Temperature_Humidity.txt`)
**Dynamic Features:**
- Climate control settings (nested object)
- Multiple measurement readings (array)
- Control flags (boolean values)
- Numeric constraints (min/max values)

**Data Structure:**
```json
{
  "device_id": "CLIMATE-A1",
  "control_settings": {
    "heating_enabled": true,
    "cooling_enabled": true,
    "min_temperature_celsius": 18,
    "max_temperature_celsius": 26
  },
  "measurements": [
    {
      "timestamp": "2025-01-01T07:00:00Z",
      "temperature_celsius": 22.3,
      "humidity_percent": 48
    }
  ]
}
```

**True Dynamic Nature:**
- Schema includes both static info AND array of measurements
- Evolves when new measurement types appear
- No need for separate tables

---

### **V3: HVAC Hierarchical** (`SAMPLE_V3_HVAC_Hierarchical.txt`)
**Dynamic Features:**
- Multi-level nesting: system → zones → measurements
- Multiple arrays: zone_status and maintenance_alerts
- Alert severity tracking
- Zone-specific performance metrics

**Data Structure:**
```json
{
  "facility_id": "FAC-HVAC-01",
  "system_configuration": {
    "zones": 4,
    "compressor_count": 2
  },
  "zone_status": [
    {
      "zone_id": "ZONE-A",
      "current_temperature_celsius": 21.2,
      "airflow_cfm": 450
    }
  ],
  "maintenance_alerts": [
    {
      "alert_id": "ALT-001",
      "alert_type": "FilterChangeRequired"
    }
  ]
}
```

**True Dynamic Architecture:**
- Different number of zones per facility
- Variable alert types
- Each zone can have different metrics
- No predefined column limits

---

### **V4: Employee & Certifications** (`SAMPLE_V4_Employee_Relational.txt`)
**Dynamic Features:**
- Multiple certifications per employee (array)
- Multiple work assignments (array)
- Skills list (array)
- Relationships via IDs: facility_id, assignment_id

**Data Structure:**
```json
{
  "employee_id": "EMP-001",
  "employee_name": "John Smith",
  "certifications": [
    {
      "cert_id": "EPA-604",
      "cert_name": "EPA Section 608",
      "expiry_date": "2025-03-15"
    }
  ],
  "work_assignments": [
    {
      "assignment_id": "ASSIGN-001",
      "facility_id": "FAC-HVAC-01"
    }
  ],
  "skills": ["hvac_repair", "electrical_troubleshooting"]
}
```

**Relational Aspects:**
- Employee → Certifications (1:N)
- Employee → Work Assignments (1:N)
- Assignment → Facility (Foreign Key reference)
- All stored in one JSONB document

---

### **V5: Building Complex** (`SAMPLE_V5_Building_Complex.txt`)
**Dynamic Features:**
- Complex nested structure: building → rooms → systems
- Multiple array types: rooms, systems, energy_consumption
- Nullable fields (assigned_employee_id: null)
- Cross-references to other entity IDs

**Data Structure:**
```json
{
  "building_id": "BLDG-001",
  "rooms": [
    {
      "room_id": "ROOM-101",
      "hvac_facility_id": "FAC-HVAC-01",
      "assigned_employee_id": "EMP-001"
    }
  ],
  "building_systems": [
    {
      "system_type": "Electrical",
      "voltage_primary": "480V_3phase"
    }
  ],
  "energy_consumption": [
    {
      "consumption_date": "2025-01-01",
      "electricity_kwh": 1250
    }
  ]
}
```

**True Dynamic Schema:**
- Variable number of rooms per building
- Different system types
- Daily energy tracking
- Cross-entity relationships via IDs

---

### **V6: Project Management** (`SAMPLE_V6_Project_Management.txt`)
**Dynamic Features:**
- Complex hierarchical structure: project → phases → milestones
- Multiple arrays with dependencies
- Nested team member assignments
- Risk tracking with severity levels

**Data Structure:**
```json
{
  "project_id": "PROJ-2025-001",
  "project_phases": [
    {
      "phase_id": "PHASE-001",
      "dependencies": ["PHASE-002"],
      "team_size": 8
    }
  ],
  "assigned_team_members": [
    {
      "member_id": "EMP-001",
      "areas_of_responsibility": ["HVAC Integration"]
    }
  ],
  "milestones": [
    {
      "milestone_id": "MS-001",
      "target_date": "2025-02-15"
    }
  ],
  "risks": [
    {
      "risk_id": "RISK-001",
      "severity": "high"
    }
  ]
}
```

**Dynamic Aspects:**
- Variable number of phases
- Dependencies between phases
- Different risk types and severities
- Arrays of arrays (team members with multiple areas)
- No schema predefinition needed

---

## How to Test

### **Step 1: Start Flask Backend**
```bash
cd /home/akash/Desktop/DBMS_PROJECT/DBMS_LAB_PROJECT/flask_backend
source venv/bin/activate
python app.py
```

### **Step 2: Go to UI → Data → Import File**

### **Step 3: Upload Each Sample**
1. **V1**: `sample_data_v1_IoT_devices.txt` 
   - Expected: Creates "IoTDevice" schema
   - Arrays: sensor_readings
   - Type mix: string, float, boolean

2. **V2**: `SAMPLE_V2_Temperature_Humidity.txt`
   - Expected: Creates "ClimateMonitor" schema
   - Nested object: control_settings
   - Array: measurements
   - Type mix: boolean, integer, float

3. **V3**: `SAMPLE_V3_HVAC_Hierarchical.txt`
   - Expected: Creates "HVACSystem" schema
   - Multiple nested levels
   - Multiple arrays: zone_status, maintenance_alerts
   - New fields: compressor_count, facility_type

4. **V4**: `SAMPLE_V4_Employee_Relational.txt`
   - Expected: Creates "Employee" schema
   - Relationships: employee → certifications, assignments, skills
   - Array of objects with date fields
   - Nullable fields: assigned_employee_id

5. **V5**: `SAMPLE_V5_Building_Complex.txt`
   - Expected: Creates "Building" schema
   - Very complex: 3 levels of nesting
   - Multiple arrays with different types
   - Cross-references: facility_id, employee_id

6. **V6**: `SAMPLE_V6_Project_Management.txt`
   - Expected: Creates "Project" schema
   - Complex dependencies
   - Nested arrays: phases with dependencies
   - Risk tracking

### **Step 4: Verify JSON Storage**

After import, query the database:

```python
from flask_backend.app.models import MetadataRecord, DataRow
from flask_backend.app.extensions import db

# Check stored data
record = MetadataRecord.query.filter_by(name='V1').first()
rows = DataRow.query.filter_by(record_id=record.id).all()

for row in rows:
    print("Raw Data (JSON):")
    print(json.dumps(row.data, indent=2))
```

**Expected Output:**
```json
{
  "device_id": "SENSOR-001",
  "sensor_readings": [
    {
      "timestamp": "2025-01-01T08:00:00Z",
      "temperature_celsius": 22.5
    }
  ]
}
```

### **Step 5: Check Generated Schemas**

```python
from flask_backend.app.models import SchemaModel, SchemaField

# List all schemas
schemas = SchemaModel.query.all()
for schema in schemas:
    print(f"Schema: {schema.name} (v{schema.version})")
    print(f"Fields: {[f.field_name for f in schema.fields]}")
```

**Expected Output:**
```
Schema: IoTDevice (v1)
Fields: ['device_id', 'device_name', 'device_type', 'sensor_readings', 'location', 'status', 'created_date']

Schema: ClimateMonitor (v1)
Fields: ['device_id', 'control_settings', 'measurements', ...]

Schema: HVACSystem (v1)
Fields: ['facility_id', 'system_configuration', 'zone_status', 'maintenance_alerts', ...]
```

---

## Why This IS True Dynamic Schema Architecture

### ✅ **Truly Dynamic**
1. No predefined schema before import
2. Fields inferred from data
3. Each data type creates new schema
4. Different instances have different fields
5. Arrays handled natively (not flattened)

### ✅ **Truly Relational**
1. Data stored WITH relationships (not normalized away)
2. Multiple arrays within single record
3. Foreign key references (facility_id, employee_id)
4. Parent-child nesting preserved
5. Queries can access nested data

### ✅ **Flexible Structure**
1. No table schema constraints
2. Fields can be objects or arrays
3. Nullable fields supported
4. Type variety (string, int, float, boolean, object, array)
5. Deeply nested structures supported

### ✅ **Scalable**
1. JSONB storage in PostgreSQL
2. GIN indexes on JSON fields
3. Query operators for nested access
4. No 1NF decomposition penalty
5. Efficient for complex data

---

## Key Files Modified

1. **`flask_backend/app/services/data_import_service.py`**
   - Enhanced `_parse_hierarchical_text()` - Preserves JSON nesting
   - Added `_infer_value_type()` - Proper type conversion
   - Updated `parse_structured_text()` - Handles arrays and nesting
   - Improved `detect_format()` - Better text detection

---

## Expected Schema Evolution

```
Import V1 → Creates IoTDevice schema (3 fields + array)
              ↓
Import V2 → Creates ClimateMonitor schema (different fields)
              ↓
Import V3 → Creates HVACSystem schema (more complex)
              ↓
Import V4 → Creates Employee schema (with relationships)
              ↓
Import V5 → Creates Building schema (deeply nested)
              ↓
Import V6 → Creates Project schema (most complex)

Each schema version tracked in SchemaVersion table
All data stored as JSONB in data_rows table
No schema conflicts - each type stored separately
Query system understands relationships via nested structure
```

---

## What Makes This Different from CSV

| Feature | CSV | Your System |
|---------|-----|-----------|
| Arrays | Flattened/repeated | Native JSON arrays |
| Nesting | Not supported | Fully supported |
| Schema | Fixed columns | Dynamic fields |
| Relationships | Separate tables | Nested in document |
| Type mix | All strings | Native types |
| Evolving data | Breaks schema | Adapts automatically |
| Storage | Row-oriented | Document-oriented JSONB |

---

This is **production-ready true dynamic schema architecture** with native relationship support!
