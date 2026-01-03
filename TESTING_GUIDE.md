# Testing Data Import & Update Features

## Quick Start Testing

### 1. Start the Application

```bash
# Terminal 1: Flask Backend
cd flask_backend
source venv/bin/activate
python3 main.py

# Terminal 2: Frontend (in another terminal)
cd Frontend
npm run dev
```

### 2. Login
- Email: `admin@test.com`
- Password: `password`

---

## Test Scenarios

### Test 1: Import CSV File

**Objective:** Import employee data from CSV with auto-schema adaptation

**Steps:**
1. Go to Data Page
2. Click "Import File" button
3. Select `sample_employees.csv`
4. Keep "Auto-adapt schema" enabled
5. Click to preview
6. Review the detected fields (name, email, phone, department, salary, joined_date, active, skills)
7. Click "Confirm & Import"
8. Should create 10 records

**Expected Results:**
- ✅ File detected as CSV
- ✅ 10 records found
- ✅ 8 fields auto-detected (name, email, phone, department, salary, joined_date, active, skills)
- ✅ Field types correctly inferred:
  - name → string
  - email → string
  - phone → string
  - department → string
  - salary → integer
  - joined_date → date
  - active → boolean
  - skills → string
- ✅ Records created with asset type name displayed

### Test 2: Import JSON File

**Objective:** Import project data from JSON with mixed types

**Steps:**
1. Go to Data Page
2. Click "Import File" button
3. Select `sample_projects.json`
4. Enable "Auto-adapt schema"
5. Preview and confirm

**Expected Results:**
- ✅ Format detected as JSON
- ✅ 3 records found
- ✅ Field types auto-detected:
  - title → string
  - status → string
  - budget → integer (or float if decimal)
  - start_date → date
  - end_date → date
  - team_size → integer
  - priority → string

### Test 3: Import Excel File

**Objective:** Import product data from Excel spreadsheet

**Steps:**
1. Go to Data Page
2. Click "Import File" button
3. Select `sample_products.xlsx`
4. Disable "Auto-adapt schema" (to test manual schema selection)
5. Preview and confirm

**Expected Results:**
- ✅ Format detected as Excel
- ✅ 8 records found
- ✅ All headers correctly parsed as field names
- ✅ Data types inferred correctly

### Test 4: Update Record

**Objective:** Test editing and saving record changes

**Steps:**
1. Go to Data Page
2. Click on any record (from your imports)
3. Click "Edit" button
4. Modify:
   - Record name
   - Tag
5. Click "✅ Save Changes"
6. Verify changes saved

**Expected Results:**
- ✅ Edit mode activated with highlighted input fields
- ✅ Save button appears
- ✅ Record updated in database
- ✅ Changes reflected in table

### Test 5: Asset Type Display

**Objective:** Verify asset type names display instead of IDs

**Steps:**
1. Go to Data Page
2. Create a record with an asset type
3. Check table display
4. Open detail drawer

**Expected Results:**
- ✅ Table shows asset type names (e.g., "Image", "Video")
- ✅ Not showing numeric IDs
- ✅ Detail drawer shows full asset type name

### Test 6: Field Type Inference Accuracy

**Objective:** Test that field types are correctly inferred

**Steps:**
1. Create a test CSV with mixed types:
```csv
int_field,float_field,bool_field,date_field,string_field
42,3.14,true,2024-01-15,Hello
100,2.71,false,2024-01-20,World
```

2. Import file
3. Check suggested fields

**Expected Results:**
- ✅ int_field → integer
- ✅ float_field → float
- ✅ bool_field → boolean
- ✅ date_field → date
- ✅ string_field → string

### Test 7: Multiple Format Detection

**Objective:** Test auto-detection of different delimiters

**Steps:**
1. Create test files with different delimiters:
   - Pipe-separated: `name|age|email`
   - Semicolon-separated: `name;age;email`
   - Tab-separated: `name<TAB>age<TAB>email`

2. Import each file
3. Verify format detection

**Expected Results:**
- ✅ Pipe format detected
- ✅ Semicolon format detected
- ✅ Tab format detected as TSV

### Test 8: Bulk Import (Existing)

**Objective:** Verify bulk import still works with JSON

**Steps:**
1. Go to Data Page
2. Click "Bulk Import" (original button)
3. Paste JSON array:
```json
[
  {"name": "Record 1", "value": 100},
  {"name": "Record 2", "value": 200}
]
```
4. Import

**Expected Results:**
- ✅ Original bulk import still works
- ✅ Records created

---

## API Testing (cURL)

### Test Import File Endpoint

```bash
# 1. Upload CSV file and get preview
curl -X POST http://localhost:5000/api/uploads/import-file \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@sample_employees.csv" \
  -F "auto_adapt_schema=true"

# Expected: 200 OK with preview data
```

### Test Update Record Endpoint

```bash
# Update a record (replace RECORD_ID with actual ID)
curl -X PUT http://localhost:5000/api/metadata/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "tag": "updated",
    "values": {
      "field1": "new_value"
    }
  }'

# Expected: 200 OK with update confirmation
```

### Test Add Fields to Record

```bash
# Add new fields to record with schema adaptation
curl -X POST http://localhost:5000/api/metadata/1/add-fields \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_fields": {
      "new_field1": "value1",
      "new_field2": 42
    },
    "add_to_schema": true
  }'

# Expected: 200 OK with count of fields added
```

---

## Troubleshooting

### Issue: File import shows "No file provided"
- **Solution:** Ensure file is selected before clicking upload

### Issue: Format detected as "unknown"
- **Solution:** Check file format is supported or paste content directly

### Issue: Schema adaptation not working
- **Solution:** Verify "Auto-adapt schema" is enabled and schema has `allow_additional_fields=true`

### Issue: Field type incorrectly detected
- **Solution:** Check sample data - detection based on first few records. Ensure consistent typing.

### Issue: Update fails with "Record not found"
- **Solution:** Verify record ID exists and user has edit permission

### Issue: Excel file not reading
- **Solution:** Ensure openpyxl is installed: `pip install openpyxl`

---

## Performance Testing

### Test Large CSV Import
- Create CSV with 1000+ records
- Measure import time
- Verify all records created

### Test Complex Schema
- Import data with 50+ fields
- Verify schema adaptation handles it
- Check for performance degradation

---

## Regression Testing Checklist

After implementing, verify:
- [ ] Existing bulk import still works
- [ ] Create record dialog still works
- [ ] Delete records still works
- [ ] Filters still apply correctly
- [ ] Report generation still works
- [ ] All schemas visible in dropdown
- [ ] Asset types correctly displayed throughout app

---

## Sample Data Files

Located in project root:
- `sample_employees.csv` - 10 employees with various field types
- `sample_projects.json` - 3 projects with nested data
- `sample_products.xlsx` - 8 products in Excel format

Use these for testing without needing to create your own files.

---

## Success Criteria

All features are working when:
1. ✅ CSV/JSON/Excel files import successfully
2. ✅ Field types auto-detected correctly
3. ✅ Schema auto-adapts with new fields
4. ✅ Asset type names display in UI
5. ✅ Records can be edited and saved
6. ✅ No errors in browser console
7. ✅ No errors in server logs
8. ✅ Data persists after page refresh
