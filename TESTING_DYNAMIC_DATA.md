# Testing Dynamic Schema & Relational Data Features

## Sample Data Files Created

You have 5 truly dynamic & relational datasets. Each shows different data structures:

### 1. **sample_data_v1_IoT_devices.txt**
- **Domain**: Internet of Things / Smart Sensors
- **Dynamic Features**: 
  - Different sensor types (Temperature, Pressure, Motion)
  - Variable sensor readings fields
  - Nested arrays of readings
- **Relational**: Devices → Sensors → Readings (hierarchical)
- **Evolution**: V1 has basic sensors; V2 could add GPS/Location tracking, V3 could add battery info

### 2. **sample_data_v2_employee_hierarchy.txt**
- **Domain**: HR / Organizational Hierarchy
- **Dynamic Features**:
  - Manager relationships (self-referential)
  - Team members arrays
  - Performance metrics with varying review periods
  - Projects with different roles
- **Relational**: Employee → Manager → Team (many-to-many), Employee → Projects
- **Evolution**: V1 basic; V2 adds skills matrix; V3 adds certifications

### 3. **sample_data_v3_supply_chain.txt**
- **Domain**: Logistics / Supply Chain
- **Dynamic Features**:
  - Shipment → Items (one-to-many)
  - Tracking events with varied event types
  - Vendor references
  - Items with different properties
- **Relational**: Shipment → Items, Shipment → TrackingEvents, Order → Shipment
- **Evolution**: V1 basic; V2 adds insurance info; V3 adds customs data

### 4. **sample_data_v4_hospital_patients.txt**
- **Domain**: Healthcare / Hospital Management
- **Dynamic Features**:
  - Patient with multiple nested sections
  - Medical history array with varying conditions
  - Vital signs time-series data
  - Tests with different statuses
  - Medications list
  - Post-operative care (specific to surgical patients)
- **Relational**: Patient → Doctors, Patient → Admissions → Tests → Results
- **Evolution**: V1 basic patient; V2 adds lab results; V3 adds imaging reports; V4 adds insurance

### 5. **sample_data_v5_education_courses.txt**
- **Domain**: Education / Course Management
- **Dynamic Features**:
  - Course with enrolled students
  - Schedule with varying session types
  - Assignments with weights
  - Assessments with prerequisites
  - Projects (some courses have projects, others assignments)
- **Relational**: Course → Students (many-to-many), Course → Assessments, Course → Prerequisites
- **Evolution**: V1 basic; V2 adds student grades; V3 adds prerequisite chains; V4 adds peer reviews

---

## How to Test These

### Step 1: Upload First Dataset
```
1. Go to Frontend UI → Data Import/Upload
2. Select "sample_data_v1_IoT_devices.txt"
3. System will auto-detect as "structured_text"
4. Click "Preview" → See hierarchical structure recognized
5. Click "Import" → Creates Schema v1 with auto-detected fields:
   - device_id (string)
   - device_name (string)
   - location (string)
   - device_type (string)
   - status (string)
   - sensor_readings (array of objects with timestamp, temperature_celsius, humidity_percent)
```

### Step 2: Upload Second Dataset (Different Domain)
```
1. Select "sample_data_v2_employee_hierarchy.txt"
2. System detects it's NOT related to IoT sensors
3. Creates NEW Schema v1 (Employee schema)
   - Different fields: employee_id, manager_info, team_members
4. Now you have 2 independent schemas
```

### Step 3: Upload Related Dataset (Same Domain)
```
1. Select "sample_data_v3_supply_chain.txt"
2. System analyzes: Not a great match to Employee or IoT
3. Creates NEW Schema v1 (Shipment schema)
   - shipment_id, order_id, vendor_info, items_shipped
```

### Step 4: Upload Evolving Dataset (Extended Schema)
```
1. Wait - we need to simulate version evolution
2. Create sample_data_v1_extended_IoT.txt with:
   - All v1 fields PLUS
   - New fields: battery_level, last_maintenance, gps_coordinates
3. Upload it
4. System matches >50% to existing IoT schema
5. Creates Schema v2 (new version) with added fields
6. Now can query across v1 and v2 data simultaneously
```

### Step 5: Test Relational Queries
```
After uploading all datasets:
1. Go to Reports → Generate Now → Adhoc Query
2. Test hierarchical navigation:
   - "Show all employees and their managers"
   - "List shipments and their tracking events"
   - "Get patients and their vital signs history"

3. System uses nested fields to build relationships:
   - JSONB queries on nested objects
   - Array expansion for one-to-many
   - Foreign key matching for cross-schema
```

---

## Expected System Behavior

| Action | Expected Result |
|--------|-----------------|
| Upload IoT file | "Detected: structured_text, Format: Hierarchical, Records: 3" |
| Upload Employee file | "New schema detected (different fields), Created separate schema" |
| Upload Extended IoT data | "70% match to IoT schema v1, Creating schema v2 with 3 new fields" |
| Query all devices with readings | Returns nested structure with all sensor readings |
| Query all employees with managers | Shows manager relationships preserved |
| Generate report across versions | Shows data from both v1 and v2 seamlessly |
| Export to CSV | Flattens nested data into rows/columns intelligently |

---

## Behind The Scenes

### What the system does:

1. **Text File Detection**:
   - Reads hierarchical indentation
   - Recognizes key: value format
   - Parses multi-level nested blocks
   - Handles array indicators (---  separators, indented lists)

2. **Schema Extraction**:
   - Top-level keys → field names
   - Value types → field types
   - Nested objects → json type
   - Arrays → array type
   - Parent_schema tracking → version history

3. **Data Storage**:
   - **Layer 1 (JSONB)**: Full nested structure preserved
   - **Layer 2 (EAV)**: Flattened for queries
   - **Layer 3 (Relationships)**: Foreign keys created

4. **Schema Evolution**:
   - Compares new data fields to existing schemas
   - Calculates field overlap % (target: 50%+)
   - If match: Create new version
   - If no match: Create new schema
   - ChangeLog records: "Added fields: X, Y, Z"

5. **Relational Querying**:
   - Follows nested paths
   - Joins across referenced IDs
   - Expands arrays into rows
   - Returns hierarchical results

---

## Testing Strategy

### For Version 1 (All Same Domain):
```
Upload v1, v2, v3, v4, v5 but from SAME domain:
- v1: Basic sensor structure
- v2: Same sensors + GPS coordinates
- v3: Same sensors + Battery percentage  
- v4: Same sensors + Maintenance history
- v5: Same sensors + Calibration info

Expected: All match >50%, create 5 versions of SAME schema
```

### For Version 2 (Different Domains):
```
Upload v1, v2, v3, v4, v5 in given order (different domains):
Expected: Creates 5 different schemas

Then test cross-schema queries:
- "Show all records from all schemas"
- Filter by domain/type
- Join on common timestamps or IDs
```

### For Version 3 (Relational Queries):
```
After uploading all:
1. Test nested field access:
   SELECT device -> readings[0].temperature
   
2. Test array operations:
   SELECT employee_id, array_length(team_members)
   
3. Test recursive lookups:
   SELECT employee_id, manager_info.manager_name, manager_info.manager_id
```

---

## Files Location

All sample data files are in:
```
/home/akash/Desktop/DBMS_PROJECT/DBMS_LAB_PROJECT/
├── sample_data_v1_IoT_devices.txt
├── sample_data_v2_employee_hierarchy.txt  
├── sample_data_v3_supply_chain.txt
├── sample_data_v4_hospital_patients.txt
└── sample_data_v5_education_courses.txt
```

---

## Quick Start

1. Start backend: `cd flask_backend && python main.py`
2. Start frontend: `cd Frontend && npm run dev`
3. Go to UI → Data Management → Upload File
4. Select one of the sample files
5. Watch it auto-detect as "structured_text"
6. See schema being created automatically
7. Upload another file and watch it create a different schema (or new version)
8. Generate reports showing nested/relational data

---

## Success Indicators

✅ **System is working correctly if**:
- Files detected as "structured_text" (not CSV)
- Hierarchical indentation properly recognized
- Nested objects parsed as JSON fields
- Arrays with multiple items properly stored
- Relationships between data preserved
- Can query nested fields (e.g., manager_info.manager_name)
- Can generate reports showing parent-child relationships
- Schema versions created when new fields appear
- Old data accessible while new data shows in new version

❌ **Problems to watch for**:
- File shows as "unknown" format → May need to enhance detection
- Data flattened incorrectly → May need to adjust parsing
- Nested relationships lost → May need to check JSONB storage
- Can't query nested data → May need to configure EAV indexing
