# Quick Testing Guide - Dynamic Schema & Relational Data

## Files Available for Testing

Located in `/home/akash/Desktop/DBMS_PROJECT/DBMS_LAB_PROJECT/`:

```
sample_data_v1_sensors_basic.txt           (5 sensors, 7 fields - basic)
sample_data_v2_with_maintenance.txt        (5 sensors, 13 fields - +maintenance)
sample_data_v3_with_alerts_anomalies.txt   (5 sensors, 24 fields - +monitoring)
sample_data_v4_timeseries_hierarchies.txt  (5 sensors, 30 fields - +time-series)
sample_data_v5_full_relational.txt         (5 sensors, 52 fields - +events/performance)
```

---

## Step-by-Step Testing

### Step 1: Create Asset Type
```
POST /api/asset_types
{
  "name": "IoT_Sensors",
  "description": "Temperature and humidity sensors from building HVAC system"
}
```

**Response:** `asset_type_id: 1`

---

### Step 2: Upload Version 1 (Basic)

**Upload:** `sample_data_v1_sensors_basic.txt`

```
POST /api/uploads/file
Form Data:
  - file: sample_data_v1_sensors_basic.txt
  - schema_id: (will auto-detect since no schema exists)
  - asset_type_id: 1
```

**Expected Response:**
```json
{
  "filename": "sample_data_v1_sensors_basic.txt",
  "format_detected": "keyvalue",
  "record_count": 5,
  "preview": [...],
  "data_fields": [
    "sensor_id",
    "location", 
    "timestamp",
    "temperature",
    "status"
  ]
}
```

**System Action:**
- Detects key-value format ✓
- Auto-creates Schema v1 with these 5 fields
- Stores 5 sensor records

**Records Created:**
- TEMP_001 (Building A, Floor 1) - Active
- TEMP_002 (Building A, Floor 2) - Active
- HUMID_001 (Building A, Floor 1) - Active
- TEMP_003 (Building B, Floor 1) - Inactive
- HUMID_002 (Building B, Floor 1) - Active

---

### Step 3: Upload Version 2 (Add Maintenance)

**Upload:** `sample_data_v2_with_maintenance.txt`

```
POST /api/uploads/file
Form Data:
  - file: sample_data_v2_with_maintenance.txt
  - schema_id: 1  (same as v1)
  - asset_type_id: 1
```

**Expected Response:**
```json
{
  "format_detected": "keyvalue",
  "record_count": 5,
  "data_fields": [
    "sensor_id",
    "location",
    "timestamp", 
    "temperature",
    "status",
    "maintenance_schedule",
    "maintenance_last_date",
    "maintenance_next_date",
    "equipment_model",
    "equipment_serial",
    "failure_reason"  // only for TEMP_003
  ]
}
```

**System Action:**
- Detects 50%+ field overlap (5 common fields / 10 new fields = 50%)
- Suggests: "Add as new version of existing schema"
- User confirms → Creates Schema v2
- New fields added: maintenance_schedule, maintenance_last_date, etc.
- v1 data is still queryable (backward compatible)

**Key Difference from v1:**
- Same 5 sensors
- Same sensor_id, location, temperature, status
- NEW: maintenance info, equipment details, failure tracking

---

### Step 4: Upload Version 3 (Add Monitoring)

**Upload:** `sample_data_v3_with_alerts_anomalies.txt`

```
POST /api/uploads/file
Form Data:
  - file: sample_data_v3_with_alerts_anomalies.txt
  - schema_id: 1
  - asset_type_id: 1
```

**System Action:**
- Detects overlap with v2 (13 common fields / 24 total)
- Creates Schema v3
- Adds: building_ref_id, alert_threshold, current_alert_status, anomaly_detected, etc.

**Dynamic Feature Test:**
- TEMP_002 now shows: `anomaly_detected: true`
- TEMP_003 shows: `current_alert_status: critical`
- System now tracking data quality, anomalies, building hierarchy

---

### Step 5: Upload Version 4 (Add Time-Series + Hierarchies)

**Upload:** `sample_data_v4_timeseries_hierarchies.txt`

```
POST /api/uploads/file
Form Data:
  - file: sample_data_v4_timeseries_hierarchies.txt
  - schema_id: 1
  - asset_type_id: 1
```

**System Action:**
- Creates Schema v4
- Adds: zone_id, parent_controller_id, hourly readings arrays, cross-device links

**Relational Features Tested:**
- Hierarchies: BLDG_A → Floor 1 → ZONE_A1_WEST → TEMP_001
- Device links: `connected_humidity_sensors: HUMID_001`
- Time-series: `hourly_readings_08: 21.8,22.1,22.3,22.5`
- Parent-child: `parent_controller_id: CTRL_A1`

---

### Step 6: Upload Version 5 (Complete Model)

**Upload:** `sample_data_v5_full_relational.txt`

```
POST /api/uploads/file
Form Data:
  - file: sample_data_v5_full_relational.txt
  - schema_id: 1
  - asset_type_id: 1
```

**System Action:**
- Creates Schema v5 (most comprehensive)
- Adds: device_uuid, events, performance metrics, warranty, cost center, etc.

**Enterprise Features:**
- UUID for global system integration
- Event logs (1-N relationship)
- Performance dashboard metrics
- Organizational hierarchy (department, contact, cost center)
- Supply chain (manufacturer, warranty)
- Incident management (failure, repair status, priority)

---

## Query Examples

### Query 1: Get all sensors in Building A
```
GET /api/data/records?schema_id=1&filter={"building_ref_id":"BLDG_A"}
```
**Result:** TEMP_001, TEMP_002, HUMID_001 (3 records)

### Query 2: Get sensors with anomalies
```
GET /api/data/records?schema_id=1&filter={"anomaly_detected":true}
```
**Result:** TEMP_002 (only if v3 or later)

### Query 3: Cross-version query (all v1, v2, v3)
```
GET /api/reports/generate
{
  "schema_id": 1,
  "include_all_versions": true,
  "fields": ["sensor_id", "location", "temperature", "status", "current_alert_status"]
}
```
**Result:**
- v1 records: temperature, status ✓ (others NULL)
- v2 records: temperature, status, equipment_model ✓
- v3+ records: ALL fields ✓

### Query 4: Hierarchical report
```
{
  "group_by": "building_ref_id",
  "aggregate": {
    "temperature": "avg",
    "status": "count",
    "anomaly_detected": "sum"
  }
}
```
**Result:**
```
BLDG_A: avg_temp=22.5, active=3, anomalies=1
BLDG_B: avg_temp=52.0, active=1, anomalies=0
```

### Query 5: Device relationships
```
{
  "query": "Get sensors linked to TEMP_001"
}
```
**Result:** 
- v4: HUMID_001 (via connected_humidity_sensors)
- v5: HUMID_001 (via multiple link types)

---

## Report Generation Tests

### Report 1: Basic Info Report
```
POST /api/reports/generate
{
  "schema_id": 1,
  "fields": ["sensor_id", "location", "temperature", "status"]
}
```
**Output:** Simple 4-column report, all 5 sensors

### Report 2: Multi-Version Report
```
POST /api/reports/generate
{
  "schema_id": 1,
  "include_all_versions": true,
  "fields": [
    "sensor_id",
    "location",
    "temperature",
    "equipment_model",
    "current_alert_status",
    "anomaly_detected",
    "data_quality_score"
  ]
}
```
**Output:**
- v1 data: only sensor_id, location, temperature ✓
- v2 data: adds equipment_model ✓
- v3+ data: full fields ✓

### Report 3: Maintenance Report
```
POST /api/reports/generate
{
  "schema_id": 1,
  "fields": [
    "sensor_id",
    "equipment_serial",
    "maintenance_schedule",
    "maintenance_last_date",
    "maintenance_next_date",
    "maintenance_technician"
  ]
}
```
**Output:** 
- v1: NULL (not stored)
- v2+: Full maintenance info

### Report 4: Incident Report
```
POST /api/reports/generate
{
  "schema_id": 1,
  "fields": [
    "sensor_id",
    "current_alert_status",
    "anomaly_detected",
    "failure_reason",
    "repair_status",
    "estimated_repair_time"
  ]
}
```
**Output:**
- TEMP_003: critical status, failed calibration, repair scheduled ✓
- Others: normal status

---

## CSV Import Test (Alternative Format)

### Create CSV from sample data
```csv
sensor_id,location,timestamp,temperature,status
TEMP_001,Building_A_Floor_1,2025-01-01T08:00:00,22.5,active
TEMP_002,Building_A_Floor_2,2025-01-01T08:00:00,21.8,active
HUMID_001,Building_A_Floor_1,2025-01-01T08:00:00,45.2,active
TEMP_003,Building_B_Floor_1,2025-01-01T08:00:00,23.1,inactive
HUMID_002,Building_B_Floor_1,2025-01-01T08:00:00,52.0,active
```

**Upload:**
```
POST /api/uploads/file
Form Data:
  - file: sample_data.csv
  - schema_id: 1
```

**Expected:**
- Format detected: "csv" ✓
- 5 records parsed ✓
- Same results as text version

---

## Validation Tests

### Test: Text File Detection
- ✅ Detects keyvalue format (field: value)
- ✅ Detects structured hierarchical text
- ✅ Falls back to plain text if needed

### Test: Schema Auto-Detection
- ✅ Calculates 50% field overlap
- ✅ Suggests schema version creation
- ✅ Maintains backward compatibility

### Test: Dynamic Evolution
- ✅ v1 → v2 adds fields
- ✅ v2 → v3 adds more fields
- ✅ v3 → v4 adds hierarchies
- ✅ v4 → v5 adds complex relationships
- ✅ Old data remains intact

### Test: Relational Queries
- ✅ Building → Floor hierarchy works
- ✅ Cross-device links work
- ✅ Event logs are queryable
- ✅ Aggregations work across versions

---

## Expected System Behavior

### After All Uploads:
- ✅ 1 Asset Type created: IoT_Sensors
- ✅ 1 Schema with 5 versions
- ✅ 25 data records (5 sensors × 5 versions)
- ✅ All queryable simultaneously
- ✅ Reports can mix versions
- ✅ Hierarchical queries work
- ✅ Anomaly detection visible in v3+
- ✅ Device relationships in v4+
- ✅ Event logs in v5

### File Format Detection:
- ✅ Text files correctly identified as keyvalue
- ✅ CSV files correctly identified as csv
- ✅ JSON files correctly identified as json
- ✅ Hierarchical text properly parsed
- ✅ No data loss in conversion

---

## Troubleshooting

### Issue: "No matching schema found"
- Solution: First upload to create schema, then upload related data

### Issue: "Text file detected as plain"
- Solution: This is correct - will still parse as key-value pairs

### Issue: "Fields not auto-detected"
- Solution: Ensure field format is: `fieldname: value` (space after colon)

### Issue: "Empty values in report"
- Solution: Use `include_all_versions: true` to see data from older versions

### Issue: "Hierarchies not working"
- Solution: Use v4+ which includes building_ref_id, floor_number, zone_id

---

## Success Criteria

✅ All 5 text files parse without errors  
✅ System detects keyvalue format correctly  
✅ Schema evolution creates 5 versions  
✅ 50% threshold triggers version creation  
✅ Hierarchical queries return correct results  
✅ Cross-version reports work  
✅ Relational links (device→device) work  
✅ Event logs parse and query correctly  
✅ Anomalies detected in v3+  
✅ No data loss across versions
