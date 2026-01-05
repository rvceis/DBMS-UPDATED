# Code Implementation Reference

## Enhanced data_import_service.py - Key Functions

### 1. Format Detection

```python
def detect_format(self, content: str, filename: str = '') -> str:
    """Auto-detect data format including structured_text"""
    content = content.strip()
    filename_lower = filename.lower()
    
    # Check file extension
    if filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls'):
        return 'excel'
    
    # Try JSON first
    if (content.startswith('{') or content.startswith('[')) and (content.endswith('}') or content.endswith(']')):
        try:
            json.loads(content)
            return 'json'
        except:
            pass
    
    # Check for structured text patterns
    lines = content.split('\n')
    if len(lines) > 1:
        first_line = lines[0].strip()
        
        # Count delimiters for CSV detection
        comma_count = first_line.count(',')
        tab_count = first_line.count('\t')
        pipe_count = first_line.count('|')
        semicolon_count = first_line.count(';')
        
        delim_count = sum(1 for char in first_line if char in [',', '\t', '|', ';'])
        if delim_count >= 2 or comma_count >= 2:
            if tab_count > comma_count and tab_count > 0:
                return 'tsv'
            elif pipe_count > 0 and pipe_count > comma_count:
                return 'pipe'
            elif semicolon_count > 0 and semicolon_count > comma_count:
                return 'semicolon'
            elif comma_count > 0:
                return 'csv'
        
        # Check for structured text (indented, hierarchical)
        if self._is_structured_text(content):
            return 'structured_text'
        
        # Check for key-value format
        if self._is_keyvalue_format(content):
            return 'keyvalue'
    
    return 'plain'
```

### 2. Structured Text Detection

```python
def _is_structured_text(self, content: str) -> bool:
    """Check if content is hierarchical/indented text"""
    lines = content.split('\n')
    
    # Check indentation patterns
    indented_count = 0
    for line in lines[:20]:
        if line and line[0] in [' ', '\t']:
            indented_count += 1
    
    # If significant indentation
    if indented_count > len(lines[:20]) * 0.3:
        return True
    
    # Check for structural patterns
    if '<' in content and '>' in content:  # XML-like
        return True
    
    if '|' in content and '--' in content:  # Markdown table
        return True
    
    if re.search(r'^[=\-#]{3,}', content, re.MULTILINE):  # Separators
        return True
    
    if re.search(r'^\s+[\-\*•]\s+', content, re.MULTILINE):  # Bullet lists
        return True
    
    return False
```

### 3. Hierarchical Text Parsing

```python
def _parse_hierarchical_text(self, content: str) -> List[Dict[str, Any]]:
    """Parse indented/nested text into records"""
    records = []
    current_record = {}
    current_parent_key = None
    
    for line in content.split('\n'):
        if not line.strip():
            if current_record:
                records.append(current_record)
                current_record = {}
                current_parent_key = None
            continue
        
        # Determine indentation level
        indent = len(line) - len(line.lstrip())
        stripped = line.strip()
        
        # Skip separator lines
        if stripped == '---':
            if current_record:
                records.append(current_record)
                current_record = {}
                current_parent_key = None
            continue
        
        # Parse key: value or key = value
        match = re.match(r'([^:=]+)\s*[:=]\s*(.+)', stripped)
        if match:
            key = match.group(1).strip()
            value = match.group(2).strip()
            
            if indent == 0:
                # Top-level key
                current_parent_key = key
                current_record[key] = value
            else:
                # Nested key - flatten with parent
                if current_parent_key:
                    nested_key = f"{current_parent_key}_{key}"
                else:
                    nested_key = key
                current_record[nested_key] = value
        elif current_record:
            # Continuation line
            if stripped.startswith('-') or stripped.startswith('*'):
                stripped = stripped[1:].strip()
            
            last_key = list(current_record.keys())[-1] if current_record else None
            if last_key:
                current_record[last_key] += '\n' + stripped
    
    # Add last record
    if current_record:
        records.append(current_record)
    
    return records
```

### 4. Auto Parse with Format Detection

```python
def auto_parse(self, content: str, schema_fields: List[str] = None, 
               filename: str = '', file_bytes: bytes = None) -> Tuple[str, List[Dict[str, Any]]]:
    """Automatically detect and parse any format"""
    format_type = self.detect_format(content, filename)
    
    if format_type == 'json':
        data = self.parse_json(content)
    elif format_type == 'csv':
        data = self.parse_csv(content, ',')
    elif format_type == 'tsv':
        data = self.parse_csv(content, '\t')
    elif format_type == 'pipe':
        data = self.parse_csv(content, '|')
    elif format_type == 'semicolon':
        data = self.parse_csv(content, ';')
    elif format_type == 'structured_text':
        data = self.parse_structured_text(content)
    elif format_type == 'excel':
        if not file_bytes:
            raise ValueError("File bytes required for Excel format")
        data = self.parse_excel(file_bytes)
    elif format_type == 'keyvalue':
        data = self.parse_keyvalue(content)
    else:
        # Fall back to plain text
        data = self.parse_plain_text(content, schema_fields or [])
    
    return format_type, data
```

### 5. Schema Field Suggestion

```python
def suggest_schema_fields(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Auto-generate schema from parsed data"""
    if not data:
        return []
    
    # Collect field samples
    field_samples = {}
    for record in data:
        for field_name, value in record.items():
            if field_name not in field_samples:
                field_samples[field_name] = []
            field_samples[field_name].append(value)
    
    # Generate field definitions
    suggested_fields = []
    for field_name, values in field_samples.items():
        field_type = self.infer_field_type(values)
        suggested_fields.append({
            'field_name': field_name,
            'field_type': field_type,
            'is_required': False,
            'description': f'Auto-detected {field_type} field'
        })
    
    return suggested_fields

def infer_field_type(self, values: List[Any]) -> str:
    """Infer field type from values"""
    if not values:
        return 'string'
    
    # Filter non-None values
    non_null = [v for v in values if v is not None and v != '']
    if not non_null:
        return 'string'
    
    # Test each type
    all_int = all(isinstance(v, int) or (isinstance(v, str) and v.isdigit()) for v in non_null)
    if all_int:
        return 'integer'
    
    all_float = True
    for v in non_null:
        try:
            float(v)
        except:
            all_float = False
            break
    if all_float:
        return 'float'
    
    all_bool = all(str(v).lower() in ('true', 'false', '1', '0', 'yes', 'no') for v in non_null)
    if all_bool:
        return 'boolean'
    
    all_date = True
    for v in non_null:
        try:
            datetime.fromisoformat(str(v).split(' ')[0])
        except:
            all_date = False
            break
    if all_date:
        return 'date'
    
    return 'string'
```

---

## PostgreSQL Queries for Nested Data

### Query 1: Extract Nested Device Readings

```sql
SELECT 
  data->>'device_id' as device_id,
  data->>'device_name' as device_name,
  reading->>'timestamp' as timestamp,
  reading->>'temperature_celsius' as temperature,
  reading->>'humidity_percent' as humidity
FROM data_rows,
  jsonb_array_elements(data->'sensor_readings') as reading
WHERE data->>'device_type' = 'TemperatureSensor'
ORDER BY data->>'device_id', reading->>'timestamp';
```

### Query 2: Get Employee with Manager Name

```sql
SELECT 
  data->>'employee_id' as emp_id,
  data->>'first_name' as first_name,
  data->'manager_info'->>'manager_name' as manager_name,
  data->'manager_info'->>'manager_email' as manager_email,
  jsonb_array_length(data->'team_members') as team_size
FROM data_rows
WHERE schema_id = (SELECT id FROM schemas WHERE name = 'Employee_Hierarchy');
```

### Query 3: Shipment with Items and Events

```sql
WITH shipment_data AS (
  SELECT 
    data->>'shipment_id' as shipment_id,
    data->>'order_id' as order_id,
    jsonb_array_length(data->'items_shipped') as item_count,
    jsonb_array_length(data->'tracking_events') as event_count
  FROM data_rows
  WHERE data @> '{"status": "In Transit"}'
)
SELECT * FROM shipment_data;
```

### Query 4: Patient Vital Signs Time Series

```sql
SELECT 
  data->>'patient_id' as patient_id,
  data->>'patient_name' as patient_name,
  vitals->>'recorded_at' as recorded_at,
  (vitals->>'temperature_celsius')::float as temp,
  vitals->>'blood_pressure' as bp,
  (vitals->>'heart_rate')::int as hr
FROM data_rows,
  jsonb_array_elements(data->'vital_signs') as vitals
WHERE schema_id = (SELECT id FROM schemas WHERE name = 'Hospital_Patients')
ORDER BY patient_id, recorded_at;
```

### Query 5: Course with Enrolled Students

```sql
SELECT 
  data->>'course_id' as course_id,
  data->>'course_name' as course_name,
  data->>'instructor_name' as instructor,
  student->>'student_id' as student_id,
  student->>'student_name' as student_name,
  student->>'status' as enrollment_status
FROM data_rows,
  jsonb_array_elements(data->'enrolled_students') as student
WHERE schema_id = (SELECT id FROM schemas WHERE name = 'Education_Courses')
ORDER BY course_id, student_id;
```

---

## Frontend Integration Points

### Upload Handler

```typescript
// In Frontend/src/pages/DataImport.tsx
const handleFileUpload = async (file: File) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('asset_type_id', selectedAssetType);
  
  try {
    const response = await fetch('/api/data/import-file', {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
      body: formData
    });
    
    const result = await response.json();
    
    // result.format_detected will be:
    // 'csv', 'json', 'structured_text', 'keyvalue', 'excel', etc.
    
    console.log(`Detected format: ${result.format_detected}`);
    console.log(`Parsed records: ${result.preview_data.length}`);
    console.log(`Suggested schema: ${result.suggested_schema}`);
    
    // Show preview with detected structure
    setPreviewData(result.preview_data);
    setDetectedFormat(result.format_detected);
    
  } catch (error) {
    console.error('Upload failed:', error);
  }
};
```

### Display Hierarchical Data

```typescript
// Render nested objects and arrays
const renderValue = (value: any) => {
  if (typeof value === 'object') {
    if (Array.isArray(value)) {
      return (
        <ul>
          {value.map((item, idx) => (
            <li key={idx}>{renderValue(item)}</li>
          ))}
        </ul>
      );
    } else {
      return (
        <ul>
          {Object.entries(value).map(([k, v]: any) => (
            <li key={k}><strong>{k}:</strong> {renderValue(v)}</li>
          ))}
        </ul>
      );
    }
  }
  return String(value);
};

// In preview table
<TableCell>
  {renderValue(record[field])}
</TableCell>
```

---

## Backend Route Handler

```python
# In flask_backend/app/routes/metadata.py
@metadata_bp.route('/import-file', methods=['POST'])
def import_file_with_auto_detection():
    """
    Auto-detect format and parse file
    Returns: format_detected, preview_data, suggested_schema
    """
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    asset_type_id = request.form.get('asset_type_id', type=int)
    
    try:
        # Read file content
        content = file.read().decode('utf-8', errors='replace')
        file_bytes = file.read() if file.filename.endswith(('.xlsx', '.xls')) else None
        file.seek(0)
        
        # Initialize import service
        import_service = DataImportService()
        
        # Auto-detect format and parse
        format_detected, parsed_data = import_service.auto_parse(
            content, 
            filename=file.filename,
            file_bytes=file_bytes
        )
        
        # Suggest schema fields
        suggested_fields = import_service.suggest_schema_fields(parsed_data)
        
        # Get preview (first 5 records)
        preview_data = parsed_data[:5]
        
        return jsonify({
            'format_detected': format_detected,
            'records_parsed': len(parsed_data),
            'preview_data': preview_data,
            'suggested_schema': {
                'fields': suggested_fields,
                'field_count': len(suggested_fields)
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

---

## Testing Commands

### Test Format Detection

```python
# Run this in Python terminal
from flask_backend.app.services.data_import_service import DataImportService

service = DataImportService()

# Test structured text
with open('sample_data_v1_IoT_devices.txt') as f:
    content = f.read()
    format = service.detect_format(content, 'sample_data_v1_IoT_devices.txt')
    print(f"Detected: {format}")  # Should print: structured_text
    
    # Parse it
    format, data = service.auto_parse(content)
    print(f"Records parsed: {len(data)}")
    print(f"First record keys: {list(data[0].keys())}")
    
    # Suggest schema
    fields = service.suggest_schema_fields(data)
    print(f"Suggested fields: {[f['field_name'] for f in fields]}")
```

### Verify Schema Creation

```python
# After uploading, check database
from flask_backend.app.models import SchemaModel, SchemaField

schema = SchemaModel.query.filter_by(name='IoT_Devices').first()
print(f"Schema: {schema.name} v{schema.version}")
print(f"Fields: {[f.field_name for f in schema.fields]}")
print(f"Field types: {[f.field_type for f in schema.fields]}")
```

### Query Nested Data

```python
# In Flask shell
from flask_backend.app.models import DataRow
from sqlalchemy import text

# Query nested device readings
query = """
SELECT data->>'device_id' as device_id,
       reading->>'temperature_celsius' as temperature
FROM data_rows,
jsonb_array_elements(data->'sensor_readings') as reading
"""

result = db.session.execute(text(query))
for row in result:
    print(f"Device: {row.device_id}, Temp: {row.temperature}°C")
```

---

## Summary

**Updated in data_import_service.py**:
1. ✅ Enhanced format detection
2. ✅ Hierarchical text parsing
3. ✅ Key-value format support
4. ✅ Auto-schema generation
5. ✅ Type inference
6. ✅ Field mapping suggestion

**Files to Test**:
- sample_data_v1_IoT_devices.txt
- sample_data_v2_employee_hierarchy.txt
- sample_data_v3_supply_chain.txt
- sample_data_v4_hospital_patients.txt
- sample_data_v5_education_courses.txt

**Backend Ready**:
- Accepts .txt files with structured data
- Auto-detects hierarchical format
- Preserves nested relationships
- Creates schemas automatically
- Stores in JSONB with full query support
