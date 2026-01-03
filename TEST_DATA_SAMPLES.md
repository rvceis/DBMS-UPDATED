# Test Data Samples for Dynamic Schema Implementation

This document provides sample data in various formats to test the dynamic schema features of the MetaDB system.

---

## 📋 Table of Contents
1. [JSON Format Examples](#json-format-examples)
2. [CSV Format Examples](#csv-format-examples)
3. [Key-Value Format Examples](#key-value-format-examples)
4. [Testing Scenarios](#testing-scenarios)

---

## JSON Format Examples

### Example 1: Book Record (Will create new "Book" schema)
```json
{
  "title": "The Great Gatsby",
  "author": "F. Scott Fitzgerald",
  "isbn": "978-0-7432-7356-5",
  "pages": 180,
  "published_year": 1925,
  "genre": "Classic Fiction",
  "available": true,
  "rating": 4.5
}
```

### Example 2: Customer Record (Will create new "Customer" schema)
```json
{
  "customer_name": "Alice Johnson",
  "email": "alice.johnson@example.com",
  "phone": "+1-555-0123",
  "age": 28,
  "membership_level": "Gold",
  "active": true,
  "total_purchases": 1250.50,
  "join_date": "2024-03-15"
}
```

### Example 3: Employee Record (Should match existing "Employee" schema)
```json
{
  "first_name": "Carlos",
  "last_name": "Rodriguez",
  "email": "carlos.rodriguez@company.com",
  "department": "Engineering",
  "salary": 95000,
  "hire_date": "2024-01-10",
  "active": true
}
```

### Example 4: Product Record (Should match existing "Product" schema)
```json
{
  "product_name": "Wireless Headphones",
  "sku": "AUDIO-WH-001",
  "category": "Electronics",
  "price": 79.99,
  "quantity_in_stock": 150,
  "in_stock": true,
  "supplier": "Audio Tech Inc"
}
```

### Example 5: Task Record (Will create new "Task" schema)
```json
{
  "task_name": "Complete API Documentation",
  "description": "Write comprehensive API documentation for all endpoints",
  "assigned_to": "Development Team",
  "priority": "High",
  "status": "In Progress",
  "due_date": "2026-01-15",
  "estimated_hours": 16,
  "completed": false
}
```

---

## CSV Format Examples

### Example 6: Book Data (CSV - single line header + data)
```
title,author,pages,published_year,genre,rating,available
Pride and Prejudice,Jane Austen,432,1813,Romance,4.8,true
```

### Example 7: Customer Data (CSV)
```
customer_name,email,phone,age,membership_level,total_purchases,active
Bob Smith,bob.smith@email.com,555-0199,35,Silver,850.25,true
```

### Example 8: Course Data (CSV - will create new schema)
```
course_name,instructor,duration_weeks,price,enrollment_limit,online,difficulty
Advanced Python Programming,Dr. Sarah Chen,12,599.99,30,true,Intermediate
```

### Example 9: Inventory Item (TSV - tab separated)
```
item_name	category	quantity	unit_price	location	reorder_point
Laptop Stand	Office Supplies	45	29.99	Warehouse A	10
```

---

## Key-Value Format Examples

### Example 10: Server Configuration (Key-Value pairs)
```
server_name: WebServer-01
ip_address: 192.168.1.100
cpu_cores: 8
ram_gb: 32
disk_space_tb: 2
operating_system: Ubuntu 22.04
status: Active
```

### Example 11: Vehicle Record (Key-Value pairs)
```
make: Toyota
model: Camry
year: 2024
color: Silver
mileage: 15000
price: 28500
condition: Excellent
```

---

## Testing Scenarios

### 🧪 Scenario 1: Create Record with New Schema
**Objective:** Test automatic schema creation

**Steps:**
1. Go to Data → Click "Create Record"
2. Enter Name: "Book 1"
3. Select Format: JSON
4. Paste Example 1 (Book Record)
5. Leave "Auto-detect or create" selected
6. Click "Create Record"

**Expected Result:**
- System shows: "No matching schemas found"
- System creates new "Book" schema automatically
- Record created successfully
- New schema visible in Schemas page

---

### 🧪 Scenario 2: Match Existing Schema
**Objective:** Test schema matching for Employee

**Steps:**
1. Click "Create Record"
2. Enter Name: "Employee 6"
3. Select Format: JSON
4. Paste Example 3 (Employee Record)
5. Don't select a schema
6. Click "Create Record"

**Expected Result:**
- System detects matching "Employee" schema
- Shows dialog: "Found 1 matching schema"
- User can select "Employee" schema or create new
- Record created with existing Employee schema

---

### 🧪 Scenario 3: CSV Import
**Objective:** Test CSV parsing

**Steps:**
1. Click "Create Record"
2. Enter Name: "Course 1"
3. Select Format: CSV (comma-separated)
4. Paste Example 8 (Course Data)
5. Click "Create Record"

**Expected Result:**
- System parses CSV correctly
- Creates "Course" schema with 7 fields
- All field types inferred correctly (string, integer, float, boolean)

---

### 🧪 Scenario 4: Key-Value Format
**Objective:** Test key-value parsing

**Steps:**
1. Click "Create Record"
2. Enter Name: "Server Config 1"
3. Select Format: Key-Value (key: value)
4. Paste Example 10 (Server Configuration)
5. Click "Create Record"

**Expected Result:**
- System parses key-value pairs
- Creates schema with appropriate field types
- Record created successfully

---

### 🧪 Scenario 5: File Import (Excel/CSV)
**Objective:** Test file import feature

**Steps:**
1. Go to Data → Click "Import File"
2. Upload `sample_products.xlsx` or `sample_employees.csv`
3. Preview shows detected format and fields
4. Select or auto-detect schema
5. Click "Confirm & Import"

**Expected Result:**
- File parsed correctly
- Format detected (Excel/CSV)
- All records imported
- Schema auto-adapted if needed

---

### 🧪 Scenario 6: Product Record Matching
**Objective:** Test matching existing Product schema

**Steps:**
1. Click "Create Record"
2. Enter Name: "Product 6"
3. Select Format: JSON
4. Paste Example 4 (Product Record)
5. Click "Create Record"

**Expected Result:**
- System finds existing "Product" schema
- Shows matching schema dialog
- User selects Product schema
- Record created successfully

---

### 🧪 Scenario 7: Multiple Format Test
**Objective:** Test switching between formats

**Steps:**
1. Click "Create Record"
2. Try each format dropdown:
   - JSON → See JSON placeholder
   - CSV → See CSV placeholder
   - TSV → See TSV placeholder
   - Key-Value → See key-value placeholder
3. Paste appropriate data for each format
4. Verify parsing works

**Expected Result:**
- Format selector changes placeholder text
- Each format parses correctly
- No errors switching formats

---

## 🎯 Quick Test Checklist

- [ ] Create record with JSON format → New schema auto-created
- [ ] Create record matching Employee schema → Dialog shown with match
- [ ] Create record matching Product schema → Dialog shown with match
- [ ] Parse CSV format correctly
- [ ] Parse TSV format correctly
- [ ] Parse Key-Value format correctly
- [ ] Import Excel file → All records imported
- [ ] Import CSV file → All records imported
- [ ] View created records in Data table
- [ ] Edit existing record → Values update
- [ ] View record details → All fields shown
- [ ] Delete record → Record removed
- [ ] Check Schemas page → New schemas visible

---

## 📊 Expected Database State After Tests

After running all examples, you should have:

**Schemas Created:**
- Employee (existing + 1 new record)
- Product (existing + 1 new record)
- Project (existing)
- Book (NEW)
- Customer (NEW)
- Task (NEW)
- Course (NEW)
- Server Configuration (NEW)
- Vehicle (NEW)

**Total Records:** 14 (existing) + 9 (new) = 23 records

**Field Types Demonstrated:**
- ✅ String fields
- ✅ Integer fields
- ✅ Float fields
- ✅ Boolean fields
- ✅ Date fields

---

## 🔧 Troubleshooting

### Issue: "No matching schema found" error
**Solution:** Ensure `create_new_schema=true` is being sent in request

### Issue: CSV not parsing correctly
**Solution:** Check delimiter (comma, tab, pipe, semicolon)

### Issue: Field types incorrect
**Solution:** System auto-infers types from data values

### Issue: Schema dialog not showing
**Solution:** Ensure schemas are loaded (check Network tab)

---

## 💡 Advanced Testing

### Test Schema Evolution
1. Create record with fields: `name, age, email`
2. Create another record with: `name, age, email, phone`
3. System should auto-add `phone` field to schema

### Test Field Type Inference
Create records with different data types and verify correct inference:
- `"123"` → string
- `123` → integer
- `123.45` → float
- `true/false` → boolean
- `"2026-01-02"` → date (if in YYYY-MM-DD format)

---

## 📝 Notes

- All existing sample data (Employees, Products, Projects) is already seeded
- System supports dynamic schema creation and matching
- Field types are automatically inferred from data
- Schemas can evolve by adding new fields
- Multi-format support: JSON, CSV, TSV, Excel, Key-Value

**Database Connection:** PostgreSQL (dbms_db)  
**Backend:** Flask on localhost:5000  
**Frontend:** React on localhost:5173  
**Auth:** admin@test.com / password
