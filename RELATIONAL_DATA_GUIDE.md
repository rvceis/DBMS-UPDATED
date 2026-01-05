# Quick Guide: Adding Relational Data to Your System

## What is Relational Data?

Data that connects to other data through relationships:
- **One-to-One**: User ↔ Profile
- **One-to-Many**: Device ↔ Readings
- **Many-to-Many**: Students ↔ Courses

Your system handles all of these!

---

## Method 1: Foreign Key Fields

### Define Relationship in Schema

```
1. Go to Schemas
2. Click on schema (e.g., "Temperature Schema v1")
3. Click "Add Field"
4. Field Name: location_id
5. Field Type: integer
6. Constraints: {
     "foreign_key": "locations.id",
     "cascade_delete": true
   }
7. Save
```

### Use in Data

```csv
device_id, timestamp, temperature, location_id
sensor_001, 2025-01-01, 28.5, 1
sensor_002, 2025-01-01, 29.0, 2
sensor_003, 2025-01-01, 27.8, 1
```

**When you query:**
```
→ Can filter by location_id
→ Can join with locations table
→ Deleting location cascades to readings
```

---

## Method 2: Referenced Lookups

### Store Reference Data Separately

**Create "Locations" Schema:**
```
- location_id (primary)
- location_name
- address
- coordinates
```

**Create "Readings" Schema:**
```
- device_id
- temperature
- location_id  ← Reference to Locations
- timestamp
```

### Query Across Schemas

```
1. Import reading data (with location_id)
2. Import location data (separate)
3. System tracks the relationship
4. Query: "All readings from location 1"
   → Returns: All readings with location_id=1
```

---

## Method 3: Array/List Fields

### Store Multiple Related Items

**Schema Field Type: array**

```json
{
  "device_id": "sensor_001",
  "timestamp": "2025-01-01",
  "readings": [
    {
      "temperature": 28.5,
      "humidity": 60,
      "timestamp": "10:00:00"
    },
    {
      "temperature": 28.6,
      "humidity": 61,
      "timestamp": "10:01:00"
    }
  ],
  "quality_flags": ["valid", "calibrated"]
}
```

**Benefits:**
- Keep related data together
- Nested relationships
- Queryable with JSON operators

---

## Method 4: Nested JSON Objects

### Complex Relationships

```json
{
  "device_id": "sensor_001",
  "location": {
    "id": 1,
    "name": "Room A",
    "building": "Building 1",
    "coordinates": {
      "latitude": 40.7128,
      "longitude": -74.0060
    }
  },
  "readings": {
    "current": {
      "temperature": 28.5,
      "humidity": 60
    },
    "previous": {
      "temperature": 28.4,
      "humidity": 59
    }
  }
}
```

**Best For:**
- Denormalized data
- Self-contained records
- Avoiding multiple queries

---

## Method 5: Many-to-Many Relationships

### Using Bridge Records

**Scenario:** Sensors can be in multiple locations, locations have multiple sensors

**Solution:**

**Schema 1: Sensors**
```
- sensor_id
- name
- type
```

**Schema 2: Locations**
```
- location_id
- name
- building
```

**Schema 3: Sensor_Locations (Junction)**
```
- id
- sensor_id  ← Reference to Sensors
- location_id  ← Reference to Locations
- active_from
- active_to
```

**Data Example:**
```
sensor_001 → Location 1 (Jan 2025 - Present)
sensor_001 → Location 2 (Oct 2024 - Dec 2024)
sensor_002 → Location 1 (Jan 2025 - Present)
```

---

## Real Example: Building HVAC System

### Scenario
Track temperature readings from sensors placed in multiple locations, with relational data about:
- Buildings
- Rooms
- Sensors
- Readings

### Implementation

**Step 1: Create Schemas**

```
1. Buildings Schema
   - building_id
   - building_name
   - address

2. Rooms Schema
   - room_id
   - room_name
   - building_id  ← Foreign Key to Buildings
   - floor
   - area_sqft

3. Sensors Schema
   - sensor_id
   - sensor_name
   - room_id  ← Foreign Key to Rooms
   - sensor_type
   - calibration_date

4. Readings Schema
   - reading_id
   - sensor_id  ← Foreign Key to Sensors
   - timestamp
   - temperature
   - humidity
```

**Step 2: Import Data**

```
buildings.csv → Buildings Schema
rooms.csv → Rooms Schema  (includes building_id)
sensors.csv → Sensors Schema  (includes room_id)
readings.csv → Readings Schema  (includes sensor_id)
```

**Step 3: Query Relationships**

```
"Get average temperature in Building A"
↓
1. Find building_id = "Building A"
2. Get rooms in that building
3. Get sensors in those rooms
4. Get readings from those sensors
5. Calculate average

System handles all joins automatically!
```

---

## Step-by-Step: Add Your Relational Data

### For Time-Series Data (Like Sensors)

1. **Create Main Schema**
   ```
   device_id, timestamp, value1, value2, ...
   ```

2. **Create Metadata Schema** (if needed)
   ```
   device_id, device_name, location, device_type, ...
   ```

3. **Add Foreign Key**
   - Add `device_id` field to both schemas
   - System recognizes the relationship

4. **Import Data**
   - Upload metadata CSV first
   - Upload readings CSV
   - System auto-links by device_id

5. **Query** (System Example)
   ```
   POST /api/data/query
   {
     "schema_id": 1,
     "filters": [
       {"field": "device_id", "operator": "eq", "value": "sensor_001"}
     ]
   }
   ```

### For Hierarchical Data

1. **Create Parent Schema** (Buildings)
   ```
   building_id, name, address
   ```

2. **Create Child Schema** (Rooms)
   ```
   room_id, building_id, name, floor
   ```

3. **Create Grandchild Schema** (Sensors)
   ```
   sensor_id, room_id, name, type
   ```

4. **Add Foreign Keys**
   - rooms.building_id → buildings.building_id
   - sensors.room_id → rooms.room_id

5. **Data Structure:**
   ```
   Building 1
   ├─ Room 1
   │  ├─ Sensor 1
   │  ├─ Sensor 2
   │  └─ Sensor 3
   ├─ Room 2
   │  ├─ Sensor 4
   │  └─ Sensor 5
   └─ Room 3
      └─ Sensor 6
   ```

---

## Features for Relational Data

### Constraints
```python
constraints = {
    "foreign_key": "table_name.column_name",
    "cascade_delete": True,
    "on_update": "cascade"
}
```

### Field Types for Relationships
- `integer` - IDs, foreign keys
- `string` - Reference codes
- `array` - Multiple references
- `json` - Complex relationships

### Querying Relationships

**Filter by related field:**
```
POST /api/data/query
{
  "schema_id": 1,
  "filters": [
    {
      "field": "location_id",
      "operator": "eq",
      "value": 1
    }
  ]
}
```

**Join across schemas:**
```
Query readings with location name:
← System joins automatically
← Returns: readings + location_name
```

---

## Important Notes

1. **Flexible Beyond Schema**
   - If you add extra relational fields not in schema, they're stored
   - System captures them for next schema version

2. **Version Handling**
   - If schema v1 has no location_id, v2 adds it
   - Old records show location_id = NULL
   - Queries work across all versions

3. **Cascading Operations**
   - Delete a location → all readings from that location deleted (if cascade_delete=true)
   - Or keep readings orphaned (cascade_delete=false)

4. **Performance**
   - JSONB indexed for fast queries
   - Foreign keys indexed automatically
   - Array fields queryable with JSON operators

5. **Data Integrity**
   - Foreign key constraints enforced
   - Type validation for each field
   - Automatic timestamp tracking

---

## Try It Now!

### Quick Test: Add Location Data

1. **Go to Schemas** → Create new schema
   ```
   Name: Locations
   Fields:
   - location_id (integer, required)
   - location_name (string, required)
   - address (string)
   - building (string)
   ```

2. **Go to Data** → Create new record
   ```
   Select: Locations schema
   Add:
   - location_id: 1
   - location_name: Room A
   - address: Building 1, Floor 2
   - building: Main Building
   ```

3. **Go to Data** → Create another record
   ```
   For Readings/Sensors:
   - location_id: 1  ← References location above
   - temperature: 28.5
   ```

4. **Generate Report**
   - Reports automatically show location data with readings
   - Relationship is maintained!

---

## Summary

Your system supports relational data through:

✅ **Foreign Keys** - Direct references
✅ **Arrays** - Multiple related items
✅ **JSON Objects** - Complex structures
✅ **Schema Versioning** - Evolving relationships
✅ **Auto-Detection** - Smart matching (50% threshold)
✅ **Constraints** - Data validation
✅ **Cascading Operations** - Data integrity

**You can mix:**
- Structured relational data (traditional SQL)
- Semi-structured JSON data (flexible)
- Bulk time-series data (fast storage)

All in one system! 🚀
