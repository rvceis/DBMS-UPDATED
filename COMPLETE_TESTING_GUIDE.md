# Dynamic Schema Testing - Complete Content Guide

## Files Created for You

### 1. **Sample Data Files** (5 different domains with relational/dynamic data)

#### File 1: sample_data_v1_IoT_devices.txt
- **Domain**: Internet of Things
- **Records**: 3 sensor devices with hierarchical readings
- **Structure**: Device → Sensor Readings (nested arrays)
- **Relational Feature**: Device references → multiple readings
- **Dynamic Fields**: Different sensor types have different reading types

```
device_id: SENSOR-001
device_name: Temperature Sensor Unit A
location: Building 1, Floor 3
device_type: TemperatureSensor
status: active

sensor_readings:
  - timestamp: 2025-01-01T08:00:00Z
    temperature_celsius: 22.5
    humidity_percent: 45
  
  - timestamp: 2025-01-01T09:00:00Z
    temperature_celsius: 23.1
    humidity_percent: 44

---
[3 devices total, each with multiple sensor readings]
```

#### File 2: sample_data_v2_employee_hierarchy.txt
- **Domain**: HR / Organizational Management
- **Records**: 3 employees with manager relationships and projects
- **Structure**: Employee → Manager (many-to-one), Employee → Team (one-to-many), Employee → Projects
- **Relational Feature**: Manager references, Team member arrays
- **Dynamic Fields**: Performance metrics vary, projects vary

```
employee_id: EMP-0001
first_name: John
email: john.smith@company.com
department: Engineering

manager_info:
  manager_id: MGR-001
  manager_name: Alice Johnson

team_members:
  - member_id: EMP-0002
    member_name: Bob Williams

projects_assigned:
  - project_id: PROJ-101
    project_name: Database Migration
    role: Lead Developer

performance_metrics:
  - review_period: 2024-Q4
    rating: 4.5

---
[3 employees with complex relationships]
```

#### File 3: sample_data_v3_supply_chain.txt
- **Domain**: Logistics / Supply Chain
- **Records**: 3 shipments with items and tracking events
- **Structure**: Shipment → Items (one-to-many), Shipment → TrackingEvents (one-to-many), Shipment → Vendor (many-to-one)
- **Relational Feature**: Multiple items per shipment, tracking event timeline
- **Dynamic Fields**: Different shipments have different item types and event statuses

```
shipment_id: SHIP-2025-001
order_id: ORD-001
status: In Transit
origin_location: Warehouse A, Mumbai

items_shipped:
  - item_code: ITEM-SKU-001
    product_name: Widget A
    quantity: 500
    weight_kg: 1500

tracking_events:
  - event_type: Pickup
    timestamp: 2025-01-01T10:30:00Z
    location: Warehouse A

  - event_type: In Transit
    timestamp: 2025-01-02T14:00:00Z
    location: Highway junction

vendor_info:
  vendor_id: VEN-101
  vendor_name: ABC Suppliers Ltd

---
[3 shipments with multiple items and events each]
```

#### File 4: sample_data_v4_hospital_patients.txt
- **Domain**: Healthcare / Hospital Management
- **Records**: 3 patients with medical history, vital signs, tests, medications
- **Structure**: Patient → Admission, Admission → Vital Signs (time-series), Admission → Tests, Patient → Medical History
- **Relational Feature**: Multiple vital sign readings, test results tracking
- **Dynamic Fields**: Different patients have different medical history, different tests conducted

```
patient_id: PAT-1001
patient_name: Ramesh Kumar
age: 45
blood_group: O+

medical_history:
  - condition: Hypertension
    diagnosed_date: 2020-05-10
    medication: Lisinopril 10mg

current_admission:
  room_number: 302
  attending_doctor: Dr. Vikram Patel

vital_signs:
  - recorded_at: 2025-01-01T11:00:00Z
    temperature_celsius: 37.2
    blood_pressure: 140/90

tests_conducted:
  - test_name: ECG
    conducted_date: 2025-01-01T12:00:00Z
    result: Normal

medications_prescribed:
  - medicine_name: Aspirin
    dosage: 100mg
    frequency: Daily

---
[3 patients with varying medical histories and test results]
```

#### File 5: sample_data_v5_education_courses.txt
- **Domain**: Education / Course Management
- **Records**: 3 courses with enrolled students, schedules, assignments, assessments
- **Structure**: Course → Students (many-to-many), Course → Schedule, Course → Assignments, Course → Assessments
- **Relational Feature**: Multiple students per course, multiple sessions per course
- **Dynamic Fields**: Different courses have different assignment types, different assessment structures

```
course_id: COURSE-CS101
course_name: Data Structures and Algorithms
instructor_name: Dr. Amit Saxena
credits: 4
status: Active

enrolled_students:
  - student_id: STU-001
    student_name: Rohan Singh
    status: Active

course_schedule:
  - session_number: 1
    date: 2025-01-06
    topic: Introduction to Big O Notation
    session_type: Lecture

assignments:
  - assignment_id: ASG-001
    title: Analyze Big O Complexity
    due_date: 2025-01-15
    weight_percent: 10

assessments:
  - assessment_name: Mid Semester Exam
    date: 2025-03-01
    weight_percent: 30

---
[3 courses with varying structures and student enrollments]
```

---

## How to Test

### Quick Start Test (5 minutes)

1. **Start Backend**
```bash
cd /home/akash/Desktop/DBMS_PROJECT/DBMS_LAB_PROJECT/flask_backend
source ./venv/bin/activate
python main.py
```

2. **Start Frontend** (new terminal)
```bash
cd /home/akash/Desktop/DBMS_PROJECT/DBMS_LAB_PROJECT/Frontend
npm run dev
```

3. **Upload First File**
- Go to UI → Data Management → Upload
- Select: `sample_data_v1_IoT_devices.txt`
- System auto-detects: "structured_text"
- Click Preview → See hierarchical data
- Click Import → Watch schema created automatically

4. **Verify Auto-Detection**
```
Expected Output:
✅ Format detected: structured_text
✅ Hierarchical indentation: YES
✅ Records parsed: 3
✅ Fields extracted: 6 (string, array)
✅ Schema created: IoT_Devices_v1
```

5. **Upload Second File**
- Select: `sample_data_v2_employee_hierarchy.txt`
- System detects: Different domain, creates NEW schema
- Expected: "Employee_Hierarchy_v1" (separate from IoT schema)

6. **Generate Report**
- Go to Reports → Generate Now
- Query: Select all devices with their sensor readings
- See nested data properly organized

---

## Testing Each Dynamic Feature

### Feature 1: Hierarchical Data Recognition

**File**: sample_data_v1_IoT_devices.txt

**Test**:
1. Upload file
2. Check if system recognizes indentation
3. Verify nested sensor_readings array is preserved

**Expected**:
```
device_id: SENSOR-001
sensor_readings: [
  { timestamp: "2025-01-01T08:00:00Z", temperature_celsius: 22.5, humidity_percent: 45 },
  { timestamp: "2025-01-01T09:00:00Z", temperature_celsius: 23.1, humidity_percent: 44 },
  ...
]
```

**Success Indicator**: Nested structure preserved, not flattened

---

### Feature 2: Relationship Preservation

**File**: sample_data_v2_employee_hierarchy.txt

**Test**:
1. Upload file
2. Query: "Get employees and their managers"
3. Query: "Get employees and their team members"

**Expected**:
```
employee_id: EMP-0001
manager_info:
  manager_id: MGR-001
  manager_name: Alice Johnson

team_members: [
  { member_id: EMP-0002, member_name: Bob Williams },
  { member_id: EMP-0003, member_name: Carol Davis }
]
```

**Success Indicator**: Relationships queryable across nested objects

---

### Feature 3: One-to-Many Arrays

**File**: sample_data_v3_supply_chain.txt

**Test**:
1. Upload file
2. Generate report showing shipments with all items
3. Generate report showing shipments with all tracking events

**Expected**:
```
shipment_id: SHIP-2025-001
items_shipped: [
  { item_code: "ITEM-SKU-001", product_name: "Widget A", quantity: 500 },
  { item_code: "ITEM-SKU-002", product_name: "Widget B", quantity: 300 }
]

tracking_events: [
  { event_type: "Pickup", timestamp: "2025-01-01T10:30:00Z" },
  { event_type: "In Transit", timestamp: "2025-01-02T14:00:00Z" },
  { event_type: "At Gateway", timestamp: "2025-01-04T08:00:00Z" }
]
```

**Success Indicator**: Arrays with multiple items properly expanded in reports

---

### Feature 4: Time-Series Data

**File**: sample_data_v4_hospital_patients.txt

**Test**:
1. Upload file
2. Query vital signs for a patient
3. See multiple readings over time

**Expected**:
```
patient_id: PAT-1001
vital_signs: [
  { recorded_at: "2025-01-01T11:00:00Z", temperature: 37.2, bp: "140/90" },
  { recorded_at: "2025-01-01T15:00:00Z", temperature: 36.9, bp: "138/88" }
]
```

**Success Indicator**: Time-series data queryable chronologically

---

### Feature 5: Complex Nested Structures

**File**: sample_data_v5_education_courses.txt

**Test**:
1. Upload file
2. Generate report with students enrolled in course
3. Show course schedule with all sessions
4. Show assessments with weights

**Expected**:
```
course_id: COURSE-CS101
enrolled_students: [
  { student_id: "STU-001", student_name: "Rohan Singh" },
  { student_id: "STU-002", student_name: "Neha Patel" }
]

course_schedule: [
  { session_number: 1, topic: "Big O Notation", session_type: "Lecture" },
  { session_number: 2, topic: "Arrays", session_type: "Lecture and Lab" }
]

assessments: [
  { assessment_name: "Mid Exam", weight_percent: 30 },
  { assessment_name: "Final Project", weight_percent: 25 }
]
```

**Success Indicator**: Multiple nested arrays handled correctly

---

## Console Debugging Output

When you upload a file, check the backend console for:

```
🔍 CSV PARSE DEBUG:
   Input content length: 1247 chars
   Detected format: structured_text
   Hierarchical indentation: YES
   Records parsed: 3
   Fields: ['device_id', 'device_name', 'location', 'device_type', 'status', 'sensor_readings']
   First record: {'device_id': 'SENSOR-001', 'device_name': 'Temperature Sensor Unit A', ...}

✅ Schema auto-detected:
   Schema Name: IoT_Devices
   Fields: 7
   Field Types: string (6), array (1)

✅ Data stored in JSONB:
   Records: 3
   Total size: ~2.5 KB
   Indexed: YES (GIN index created)
```

---

## Testing Schema Versioning

### Test: Upload Related Data to Same Domain

1. **Already uploaded**: sample_data_v1_IoT_devices.txt
   - Created: Schema v1 (3 IoT devices)

2. **Create new extended file**: sample_data_v1_extended.txt
   ```
   device_id: SENSOR-001
   device_name: Temperature Sensor Unit A
   location: Building 1, Floor 3
   device_type: TemperatureSensor
   status: active
   battery_level: 85          ← NEW FIELD
   last_maintenance: 2024-12-01  ← NEW FIELD
   gps_coordinates: 19.0760,-72.8777  ← NEW FIELD
   
   sensor_readings:
     - timestamp: 2025-01-01T08:00:00Z
       temperature_celsius: 22.5
   ```

3. **Upload extended file**
   - System matches 70%+ to existing IoT schema
   - Creates: Schema v2 (with 3 new fields)
   - ChangeLog recorded: "Added battery_level, last_maintenance, gps_coordinates"

4. **Test cross-version query**
   - Generate report including all schema versions
   - Should show v1 data + v2 data combined
   - Old fields = NULL in v2 records
   - New fields = NULL in v1 records

**Expected Behavior**:
```
device_id | battery_level | last_maintenance | gps_coordinates
SENSOR-001| 85            | 2024-12-01       | 19.0760,-72.8777
SENSOR-002| NULL          | NULL             | NULL            (v1 data)
SENSOR-003| NULL          | NULL             | NULL            (v1 data)
```

---

## Success Checklist

✅ **Text File Support**
- [ ] Uploaded .txt file successfully
- [ ] System detected format as "structured_text"
- [ ] Hierarchical indentation recognized
- [ ] Data parsed correctly

✅ **Hierarchical Data**
- [ ] Nested objects preserved in JSONB
- [ ] Arrays stored with multiple items
- [ ] Relationships maintained

✅ **Auto-Schema Generation**
- [ ] Fields auto-extracted from data
- [ ] Field types correctly inferred
- [ ] Schema created without manual definition

✅ **Dynamic Schema Evolution**
- [ ] Related files create same schema version
- [ ] New fields create new version
- [ ] Schema versioning tracked in ChangeLog
- [ ] Can query across versions

✅ **Relational Features**
- [ ] Can query nested objects
- [ ] Can expand arrays into reports
- [ ] Foreign key relationships work
- [ ] Can aggregate related data

✅ **Reporting**
- [ ] Reports show nested data structures
- [ ] Arrays expanded properly in CSV export
- [ ] PDF export readable with nested data
- [ ] Filtering works on nested fields

---

## Common Issues & Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| "Unknown format" | Poor formatting | Check indentation consistency |
| Empty records | No "---" separator | Add separators between records |
| Flat data | Indentation not preserved | Use 2-space or 4-space tabs, not mixed |
| Arrays missing | No "- " prefix for items | Mark list items with "- item" |
| Dates not recognized | Format not ISO | Use YYYY-MM-DD or ISO format |
| Nested data lost | Wrong parser selected | Check _is_structured_text() output |
| Schema mismatch | Field names don't match | Check exact field name spelling |

---

## File Locations

All sample files are ready in:
```
/home/akash/Desktop/DBMS_PROJECT/DBMS_LAB_PROJECT/

├── sample_data_v1_IoT_devices.txt              ✓ Created
├── sample_data_v2_employee_hierarchy.txt       ✓ Created
├── sample_data_v3_supply_chain.txt             ✓ Created
├── sample_data_v4_hospital_patients.txt        ✓ Created
├── sample_data_v5_education_courses.txt        ✓ Created
├── TESTING_DYNAMIC_DATA.md                     ✓ Created (detailed test guide)
├── TEXT_FILE_PARSER_GUIDE.md                   ✓ Created (code guide)
└── flask_backend/app/services/data_import_service.py  ✓ Enhanced (text parsing)
```

---

## Summary

**What You Can Now Test**:

1. ✅ Upload structured text files (not just CSV)
2. ✅ Auto-detect hierarchical and indented data
3. ✅ Preserve nested objects and arrays
4. ✅ Auto-generate schemas from data
5. ✅ Track schema evolution with versioning
6. ✅ Query relational/nested data
7. ✅ Generate reports with complex structures
8. ✅ Handle truly dynamic data (not just adding columns)

**Ready to Test**:
- 5 sample datasets with real-world relational structures
- Enhanced text file parser in data_import_service.py
- Complete documentation for each feature
- Console debugging output for validation
