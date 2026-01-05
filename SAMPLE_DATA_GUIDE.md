# 5 Sample Datasets for Dynamic + Relational Schema Testing

## Overview
These 5 datasets demonstrate true dynamic and relational data evolution. Each version builds on the previous one by adding new fields, relationships, and hierarchical connections - NOT just adding columns, but evolving the entire data model.

**Files:**
- `sample_data_v1_sensors_basic.txt` - Initial schema
- `sample_data_v2_with_maintenance.txt` - Add maintenance relationships
- `sample_data_v3_with_alerts_anomalies.txt` - Add monitoring & quality metrics
- `sample_data_v4_timeseries_hierarchies.txt` - Add time-series + device hierarchies
- `sample_data_v5_full_relational.txt` - Complete relational model + events + performance

---

## Version 1: Basic Sensor Data (5 sensors)

**Scenario:** Building HVAC monitoring system starts

**Fields (7):**
- sensor_id, location, timestamp, temperature, status
- Basic monitoring only

**Relational Aspects:**
- sensor_id linking to physical locations
- Status tracking (active/inactive)

**Records:** 5 sensors (TEMP_001, TEMP_002, HUMID_001, TEMP_003, HUMID_002)

---

## Version 2: Add Maintenance Relationships

**Scenario:** Maintenance system integrated

**New Fields Added (6):**
- maintenance_schedule: quarterly/semi-annual
- maintenance_last_date: 2024-12-15
- maintenance_next_date: 2025-03-15
- equipment_model: Equipment type identifier
- equipment_serial: Unique serial for equipment traceability
- failure_reason: For inactive sensors

**Relational Aspects:**
- Sensors → Equipment (many-to-one): Multiple sensors can be same model
- Maintenance schedule tracking
- Failure tracking and diagnostics

**Schema Evolution:**
- +6 new fields (simple addition of maintenance attributes)
- Establishes equipment→sensor relationship
- NO data loss - all v1 records still queryable

---

## Version 3: Add Alerts + Anomalies + Data Quality

**Scenario:** Anomaly detection and quality monitoring activated

**New Fields Added (11):**
- building_ref_id, floor_number: Location hierarchy
- alert_threshold_high/low: Dynamic thresholds
- current_alert_status: normal/warning/critical
- anomaly_detected: Boolean flag
- anomaly_type: Type of anomaly
- anomaly_severity: Severity level
- data_quality_score: 0.0-1.0
- last_calibration: Timestamp
- battery_level: 0-100

**Relational Aspects:**
- Building → Floor hierarchy
- Building references (BLDG_A, BLDG_B)
- Alerts have status and severity (relational quality)
- Quality scores link to device health
- Anomalies linked to sensor readings

**Schema Evolution:**
- +11 new fields
- Introduces hierarchical building structure
- Adds quality/health metrics dimension
- Still backward compatible - v1 & v2 data intact

**Dynamic Feature:** Data quality scores vary per sensor even for same model

---

## Version 4: Add Time-Series + Device Hierarchies

**Scenario:** System upgraded for advanced analytics

**New Fields Added (6):**
- zone_id: Zone grouping within floor
- parent_controller_id: Device hierarchy (parent-child)
- hourly_readings_08/09/10: Array of hourly values (comma-separated)
- connected_humidity_sensors: Linked devices (CSV list)
- connected_pressure_sensors: Linked devices (CSV list)
- linked_temperature_sensor: Cross-device relationship

**Relational Aspects:**
- Hierarchical: Building → Floor → Zone → Sensor
- Device graph: Sensors can be connected/linked
- Parent-child controller relationships
- Time-series data as arrays
- Linked measurement sensors

**Schema Evolution:**
- +6 new fields
- HIERARCHICAL relationships introduced
- Arrays/lists for time-series
- Cross-references between sensors (relational graph)
- v1, v2, v3 data still queryable

**Dynamic Feature:** Some sensors have linked devices (HUMID_001 linked to TEMP_001), others don't (HUMID_002 linked to NULL)

---

## Version 5: Complete Relational Model with Events & Performance

**Scenario:** Enterprise-grade monitoring with full telemetry

**New Fields Added (22):**
- device_uuid: Global unique identifier
- maintenance_technician: Person responsible
- maintenance_notes: Free-form text
- equipment_manufacturer: Supply chain
- equipment_manufacturing_date: Traceability
- battery_voltage: Hardware detail
- firmware_version/firmware_last_update: Software version tracking
- recent_events: Event log (pipe-delimited events with timestamps)
- performance_uptime_percent: Availability metric
- performance_data_loss_percent: Quality metric
- performance_last_error: Error log
- performance_error_count_24h: Error tracking
- owner_department: Organizational hierarchy
- owner_contact: Contact information
- cost_center: Financial tracking
- warranty_expiry: Lifecycle tracking
- escalation_level: Alert routing
- repair_priority: Maintenance prioritization
- failure_detected_time: Incident tracking
- estimated_repair_time: Scheduling
- repair_status: Workflow state

**Relational Aspects:**
- Global device UUID for cross-system integration
- Event log: One device → many events (1-to-many)
- Organizational hierarchy: Department → Contact
- Supply chain: Manufacturer → Equipment → Serial
- Lifecycle tracking: Manufacturing date → Warranty expiry
- Performance metrics: Device → multiple quality indicators
- Incident management: Failure → repair ticket → technician
- Maintenance workflow: Status tracking

**Schema Evolution:**
- +22 new fields
- Complex relational model with multiple hierarchies
- Event log demonstrates time-series + relational fusion
- Performance dashboard data
- Incident/repair workflow data
- Supply chain traceability data
- v1, v2, v3, v4 data still accessible via versioned queries

**Dynamic Feature:** 
- TEMP_003 is OFFLINE - has NULL values and failure indicators
- Different sensors have different event logs
- Complex nested relationships (owner dept → contact)
- Multi-dimensional performance tracking

---

## How to Test Dynamic Schema Feature

### Test 1: Schema Auto-Detection (50% threshold)
1. Upload v1 data → Creates "Sensors_v1" schema (7 fields)
2. Upload v2 data → System detects 50%+ match, suggests adding to v1
3. Choose "Create new version" → Creates v2 with maintenance fields

### Test 2: True Dynamic Evolution
1. After v1: Query reports 7 fields
2. After v2: Same schema now has 13 fields (added 6)
3. After v3: Same schema now has 24 fields (added 11 more)
4. Reports can show:
   - "Show only v1 fields" (7)
   - "Show v1+v2 fields" (13)
   - "Show all fields" (24+)

### Test 3: Relational Data Queries
1. Query sensors in "Building_A" → Get cross-floor results
2. Query linked sensors (connected_humidity_sensors) → Find related devices
3. Query events → Get flattened event timeline
4. Query by maintenance schedule → Cross-version query

### Test 4: Complex Aggregation
- Average temperature by floor (uses building_ref_id + floor_number hierarchy)
- Sensor health by equipment_model (performance metrics + status)
- Maintenance cost by department (owner_department + warranty tracking)
- Event frequency by sensor_id (recent_events array flattening)

---

## Data Format: Key-Value Hierarchical Text

**Format:**
```
field_name: value
nested_field: nested_value

---

field_name: value2
nested_field: nested_value2
```

**Why This Format:**
- ✅ More readable than CSV for complex data
- ✅ Natural for hierarchical/nested data
- ✅ Easy to see relationships
- ✅ Comments supported (#)
- ✅ Self-documenting
- ✅ Less prone to parsing errors than CSV

---

## Key Dynamic Features Demonstrated

### 1. Additive Schema Evolution
- Fields added without breaking existing records
- Backward compatibility across all versions
- Auto-detection algorithm matches different versions

### 2. Relational Hierarchies
- Building → Floor → Zone → Sensor
- Department → Contact
- Manufacturer → Equipment → Sensor
- Parent device → Child devices

### 3. Cross-Device Relationships
- Sensors linked to each other
- Controller hierarchy (parent_controller_id)
- Device graph (connected_humidity_sensors)

### 4. Time-Series Integration
- Hourly readings as arrays
- Event logs with timestamps
- Performance metrics over time

### 5. Multi-Dimensional Data
- Location hierarchy
- Equipment lifecycle
- Supply chain
- Maintenance workflow
- Performance metrics
- Incident management

### 6. Complex Relationships
- One sensor → Many events (1-N)
- Many sensors → Same equipment model (N-1)
- Sensors → Cross-device links (N-N)
- Sensors → Organizational dept → Contact (1-N-1)

---

## How System Handles This

### Schema Detection
```
v1 fields: {sensor_id, location, timestamp, temperature, status}
v2 fields: {sensor_id, location, timestamp, temperature, status, maintenance_schedule, ...}

Similarity = 5/7 = 71% > 50% threshold
→ Suggests: Add to existing schema
→ User confirms → Creates v2
```

### Data Storage
- **Layer 1 (JSONB):** Raw data stored as-is
- **Layer 2 (EAV):** Each field-value pair indexed
- **Layer 3 (Relational):** Foreign keys created for hierarchies

### Querying
```sql
-- Query all versions
SELECT * FROM data_rows WHERE schema_id IN (1,2,3,4,5)

-- Query specific version
SELECT * FROM data_rows WHERE schema_version = 3

-- Hierarchical query
SELECT * WHERE building_ref_id = 'BLDG_A' AND floor_number = 1

-- Event extraction
SELECT data->>'sensor_id', data->>'recent_events' FROM data_rows
```

---

## Testing Workflow

1. **Create Asset Type:** "IoT Sensors"
2. **Upload v1:** Creates schema v1 (7 fields)
3. **Upload v2:** System suggests version → Creates v2 (13 fields)
4. **Generate Report:** Shows all fields from all versions
5. **Upload v3:** Auto-detects, creates v3 (24 fields)
6. **Multi-Version Query:** Reports can combine v1+v2+v3+v4+v5
7. **Relational Queries:** Filter by building, floor, department
8. **Anomaly Detection:** Query by alert_status, anomaly_detected
9. **Performance Analysis:** Group by equipment_model, show stats

---

## Real-World Value

This demonstrates how your system solves real problems:

✅ **Legacy data integration** - v1 data from old system coexists with v5
✅ **Schema evolution** - Fields can be added without migration
✅ **Hierarchical data** - Buildings → Floors → Zones → Sensors
✅ **Relational links** - Devices can reference each other
✅ **Time-series** - Arrays and event logs supported
✅ **Analytics** - Complex cross-dimensional queries
✅ **Compliance** - Full audit trail of who maintains what
✅ **Enterprise** - Organizational hierarchies, cost centers
✅ **Incident management** - Failure tracking, repair workflow
✅ **Supply chain** - Manufacturer → Equipment → Sensor traceability
