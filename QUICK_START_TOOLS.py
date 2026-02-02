#!/usr/bin/env python3
"""
DBMS Lab Project - Quick Start Guide
======================================

AVAILABLE TOOLS:

1. populate_database.py
   - Main tool for loading sample data into the backend
   - Creates schemas and inserts records
   - Usage: python3 populate_database.py

2. generate_test_schemas.py
   - Creates test schemas with various field types
   - Generates random test data for each schema
   - Interactive mode for selecting schema types
   - Usage: python3 generate_test_schemas.py

3. generate_nested_data.py
   - Creates realistic nested/relational data
   - 5 different data patterns (Company, E-commerce, IoT, Documents, Medical)
   - Usage: python3 generate_nested_data.py

4. data_validator.py
   - Validates data files against schema definitions
   - Generates quality reports
   - Supports JSON, CSV, NDJSON formats
   - Usage: python3 data_validator.py <data_file> <schema_file>

SAMPLE DATA FILES:

JSON Files (supports nested objects/arrays):
  - sample_ecommerce_orders.json (orders with nested items)
  - sample_inventory_products.json (products with specs)
  - sample_real_estate_buildings.json (buildings with facilities)

CSV Files (tabular data):
  - sample_employees.csv (employee records)
  - sample_hospital_patients.csv (patient records)

NDJSON Files (newline-delimited JSON, one record per line):
  - sample_iot_sensors.ndjson (sensor readings)


QUICK START WORKFLOW:

1. Start Flask Backend:
   cd flask_backend
   python3 app.py

2. Start React Frontend:
   cd Frontend
   npm start

3. Populate Database:
   python3 populate_database.py
   (login with admin account)

4. Generate Additional Test Data:
   python3 generate_nested_data.py
   (select data type, generates JSON file)

5. Validate Data Quality:
   python3 data_validator.py sample_employees.csv employee_schema.json


SCHEMA TYPES AVAILABLE:

Test Schemas:
  - Flexible Test Schema: Multiple data types
  - Complex Hierarchical: Parent-child relationships
  - Sparse Optional Data: Variable fields
  - Time Series Metrics: Temporal data

Nested Data Patterns:
  - Company Hierarchy (employees, departments, skills, contact info)
  - E-Commerce Transactions (orders, items, payment, shipping)
  - Sensor Network (IoT devices, readings, thresholds, maintenance)
  - Document Management (versioning, access control, metadata)
  - Medical Records (patients, encounters, medications, insurance)


KEY FEATURES DEMONSTRATED:

✅ Adaptive Schema System - Handles any data structure
✅ Flexible Field Types - 13+ data types supported
✅ Nested Objects - Complex data structures
✅ Arrays - Multiple values in single field
✅ Optional Fields - Sparse data support
✅ Relationships - Parent-child hierarchies
✅ Heterogeneous Data - Mixed types in one record
✅ Real-world Patterns - E-commerce, IoT, Medical, etc.


EXPORT FEATURES:

Once data is loaded in backend:

1. Export All Schemas (JSON):
   GET /schemas/export/json

2. Export All Schemas (SQL):
   GET /schemas/export/sql

3. Export Single Schema (JSON):
   GET /schemas/{schema_id}/export/json

4. Export Single Schema (SQL):
   GET /schemas/{schema_id}/export/sql

5. Download Schema Export:
   GET /schemas/{schema_id}/export/download/json
   GET /schemas/{schema_id}/export/download/sql


AUTHORIZATION:

Admin:
  - Can create, edit, delete any schema
  - Can delete any records
  - Full system access

Editor:
  - Can create schemas
  - Can only delete their own schemas
  - Can manage own records

Viewer:
  - Read-only access
  - Can view schemas and records
  - Cannot create or delete


TROUBLESHOOTING:

1. Connection Error:
   - Ensure Flask backend is running on port 5000
   - Check: http://localhost:5000/health

2. Authentication Failed:
   - Use admin credentials during populate
   - Check JWT token expiration

3. Data Validation Failed:
   - Use data_validator.py to check data quality
   - Review error messages for field type mismatches

4. Schema Creation Failed:
   - Verify field names are unique
   - Check field types are valid
   - Ensure constraints are properly formatted


SAMPLE DATA CHARACTERISTICS:

E-Commerce Orders:
  - Status variations (pending, processing, shipped, delivered)
  - Multiple currencies (USD, EUR, GBP)
  - Nested items array with discounts
  - Complex payment and shipping objects

Employees:
  - Multiple departments and locations
  - Skill arrays (varies per employee)
  - Contact info (phone, email, office location)
  - Performance ratings and metrics

IoT Sensors:
  - Building/floor/room hierarchy
  - Time-series readings (current, min, max, avg)
  - Status indicators (normal, warning, critical)
  - Maintenance tracking (battery, next service)

Inventory Products:
  - Product SKUs and categories
  - Pricing and stock levels
  - Customer ratings and review counts
  - Nested specifications (color, size)

Hospital Patients:
  - Patient demographics and medical history
  - Multiple encounters with various providers
  - Current medications with dosages
  - Insurance information
  - Allergy tracking

Real Estate Buildings:
  - Building hierarchy (address, city, country)
  - Facility arrays (gym, pool, parking, etc.)
  - Tenant information
  - Emergency contact arrays
  - Accessibility features


PYTHON API (populate_database.py):

from populate_database import DatabasePopulator

# Initialize
populator = DatabasePopulator("http://localhost:5000")
populator.login("admin@example.com", "password")

# Create schema
fields = [
    {"field_name": "id", "field_type": "integer", "constraints": {"unique": True}},
    {"field_name": "name", "field_type": "string", "constraints": {"required": True}},
]
schema_id = populator.create_schema("My Schema", fields)

# Insert records
records = [{"id": 1, "name": "Record 1"}, {"id": 2, "name": "Record 2"}]
populator.insert_records(schema_id, records)

# Load from file
populator.populate_ecommerce_from_json("data.json")


NEXT STEPS:

1. Run populate_database.py to create sample schemas
2. Use frontend to view and interact with data
3. Export schemas using export endpoints
4. Generate more test data with generator scripts
5. Validate data quality with validator
6. Explore analytics and reporting features

"""

if __name__ == "__main__":
    print(__doc__)
