#!/usr/bin/env python3
"""
Database Population Utility - Quick data loader for demo/testing
Not integrated into backend - standalone utility
"""

import json
import csv
import requests
import sys
from typing import List, Dict, Any
from datetime import datetime

class DatabasePopulator:
    """Populates MetaDB with sample data from various file formats"""
    
    def __init__(self, backend_url: str = "http://localhost:5000", token: str = None):
        self.backend_url = backend_url
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    def login(self, email: str, password: str) -> bool:
        """Login and get token"""
        try:
            response = self.session.post(
                f"{self.backend_url}/auth/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print(f"✅ Logged in as {email}")
                return True
            else:
                print(f"❌ Login failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False
    
    def create_schema(self, schema_name: str, fields_definition: List[Dict], asset_type_id: int = 1) -> int:
        """Create a schema with specified fields"""
        try:
            response = self.session.post(
                f"{self.backend_url}/schemas",
                json={
                    "name": schema_name,
                    "asset_type_id": asset_type_id,
                    "fields": fields_definition,
                    "allow_additional_fields": True
                }
            )
            
            if response.status_code == 201:
                schema_id = response.json().get("id")
                print(f"✅ Created schema '{schema_name}' (ID: {schema_id})")
                return schema_id
            else:
                print(f"❌ Schema creation failed: {response.text}")
                return None
        except Exception as e:
            print(f"❌ Schema creation error: {e}")
            return None
    
    def insert_records(self, schema_id: int, records: List[Dict]) -> int:
        """Insert records into a schema"""
        try:
            success_count = 0
            for record in records:
                response = self.session.post(
                    f"{self.backend_url}/metadata",
                    json={
                        "schema_id": schema_id,
                        "values": record
                    }
                )
                
                if response.status_code in [200, 201]:
                    success_count += 1
                    print(f"  ✓ Record inserted")
                else:
                    print(f"  ✗ Record insert failed: {response.status_code}")
            
            print(f"✅ Inserted {success_count}/{len(records)} records")
            return success_count
        except Exception as e:
            print(f"❌ Insert records error: {e}")
            return 0
    
    def load_json_file(self, filepath: str) -> List[Dict]:
        """Load records from JSON file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
                elif isinstance(data, dict):
                    return [data]
                else:
                    print(f"❌ Invalid JSON format in {filepath}")
                    return []
        except Exception as e:
            print(f"❌ Error loading JSON: {e}")
            return []
    
    def load_csv_file(self, filepath: str) -> List[Dict]:
        """Load records from CSV file"""
        try:
            records = []
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Convert string values to appropriate types
                    converted_row = {}
                    for key, value in row.items():
                        converted_row[key] = self._convert_value(value)
                    records.append(converted_row)
            return records
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return []
    
    def load_ndjson_file(self, filepath: str) -> List[Dict]:
        """Load records from NDJSON file (newline-delimited JSON)"""
        try:
            records = []
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
            return records
        except Exception as e:
            print(f"❌ Error loading NDJSON: {e}")
            return []
    
    @staticmethod
    def _convert_value(value: str) -> Any:
        """Convert string values to appropriate Python types"""
        if value is None or value == '' or value == 'null' or value == 'None':
            return None
        if value.lower() in ('true', 'yes'):
            return True
        if value.lower() in ('false', 'no'):
            return False
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except ValueError:
            return value


def populate_ecommerce_orders(populator: DatabasePopulator):
    """Populate e-commerce orders data"""
    print("\n📦 Loading E-Commerce Orders...")
    
    fields = [
        {"field_name": "order_id", "field_type": "string", "constraints": {"unique": True, "required": True}},
        {"field_name": "customer_name", "field_type": "string", "constraints": {"required": True}},
        {"field_name": "email", "field_type": "string", "constraints": {}},
        {"field_name": "phone", "field_type": "string", "constraints": {}},
        {"field_name": "order_date", "field_type": "date", "constraints": {}},
        {"field_name": "total_amount", "field_type": "float", "constraints": {}},
        {"field_name": "currency", "field_type": "string", "constraints": {}},
        {"field_name": "items_count", "field_type": "integer", "constraints": {}},
        {"field_name": "status", "field_type": "string", "constraints": {"enum": ["pending", "processing", "shipped", "delivered", "cancelled"]}},
        {"field_name": "shipping_address", "field_type": "string", "constraints": {}},
        {"field_name": "payment_method", "field_type": "string", "constraints": {}},
        {"field_name": "notes", "field_type": "text", "constraints": {}},
        {"field_name": "tags", "field_type": "array", "constraints": {}},
        {"field_name": "metadata", "field_type": "object", "constraints": {}},
    ]
    
    schema_id = populator.create_schema("E-Commerce Orders", fields)
    if schema_id:
        records = populator.load_json_file("data/sample_ecommerce_orders.json")
        populator.insert_records(schema_id, records)


def populate_employees(populator: DatabasePopulator):
    """Populate employee data"""
    print("\n👥 Loading Employees...")
    
    fields = [
        {"field_name": "employee_id", "field_type": "string", "constraints": {"unique": True, "required": True}},
        {"field_name": "first_name", "field_type": "string", "constraints": {"required": True}},
        {"field_name": "last_name", "field_type": "string", "constraints": {"required": True}},
        {"field_name": "email", "field_type": "string", "constraints": {}},
        {"field_name": "department", "field_type": "string", "constraints": {}},
        {"field_name": "job_title", "field_type": "string", "constraints": {}},
        {"field_name": "salary", "field_type": "float", "constraints": {}},
        {"field_name": "hire_date", "field_type": "date", "constraints": {}},
        {"field_name": "manager_id", "field_type": "string", "constraints": {}},
        {"field_name": "location", "field_type": "string", "constraints": {}},
        {"field_name": "phone", "field_type": "string", "constraints": {}},
        {"field_name": "skill_level", "field_type": "string", "constraints": {}},
        {"field_name": "certification", "field_type": "string", "constraints": {}},
        {"field_name": "is_active", "field_type": "boolean", "constraints": {}},
        {"field_name": "performance_score", "field_type": "float", "constraints": {}},
        {"field_name": "project_count", "field_type": "integer", "constraints": {}},
    ]
    
    schema_id = populator.create_schema("Employees", fields)
    if schema_id:
        records = populator.load_csv_file("data/sample_employees.csv")
        populator.insert_records(schema_id, records)


def populate_iot_sensors(populator: DatabasePopulator):
    """Populate IoT sensor data"""
    print("\n📡 Loading IoT Sensors...")
    
    fields = [
        {"field_name": "sensor_id", "field_type": "string", "constraints": {"unique": True, "required": True}},
        {"field_name": "sensor_name", "field_type": "string", "constraints": {"required": True}},
        {"field_name": "location", "field_type": "string", "constraints": {}},
        {"field_name": "reading_date", "field_type": "datetime", "constraints": {}},
        {"field_name": "temperature_celsius", "field_type": "float", "constraints": {}},
        {"field_name": "humidity_percent", "field_type": "float", "constraints": {}},
        {"field_name": "pressure_mb", "field_type": "float", "constraints": {}},
        {"field_name": "status", "field_type": "string", "constraints": {"enum": ["normal", "warning", "critical"]}},
        {"field_name": "battery_level", "field_type": "integer", "constraints": {}},
        {"field_name": "last_maintenance", "field_type": "date", "constraints": {}},
        {"field_name": "calibration_due", "field_type": "date", "constraints": {}},
    ]
    
    schema_id = populator.create_schema("IoT Sensors", fields)
    if schema_id:
        records = populator.load_ndjson_file("data/sample_iot_sensors.ndjson")
        populator.insert_records(schema_id, records)


def populate_inventory(populator: DatabasePopulator):
    """Populate inventory/products data"""
    print("\n📦 Loading Inventory Products...")
    
    fields = [
        {"field_name": "product_id", "field_type": "string", "constraints": {"unique": True, "required": True}},
        {"field_name": "product_name", "field_type": "string", "constraints": {"required": True}},
        {"field_name": "category", "field_type": "string", "constraints": {}},
        {"field_name": "price", "field_type": "float", "constraints": {}},
        {"field_name": "currency", "field_type": "string", "constraints": {}},
        {"field_name": "stock_quantity", "field_type": "integer", "constraints": {}},
        {"field_name": "reorder_level", "field_type": "integer", "constraints": {}},
        {"field_name": "supplier_id", "field_type": "string", "constraints": {}},
        {"field_name": "supplier_name", "field_type": "string", "constraints": {}},
        {"field_name": "warehouse_location", "field_type": "string", "constraints": {}},
        {"field_name": "last_restock", "field_type": "date", "constraints": {}},
        {"field_name": "sku", "field_type": "string", "constraints": {"unique": True}},
        {"field_name": "barcode", "field_type": "string", "constraints": {}},
        {"field_name": "is_active", "field_type": "boolean", "constraints": {}},
        {"field_name": "description", "field_type": "text", "constraints": {}},
        {"field_name": "rating", "field_type": "float", "constraints": {}},
        {"field_name": "reviews_count", "field_type": "integer", "constraints": {}},
        {"field_name": "dimensions", "field_type": "object", "constraints": {}},
    ]
    
    schema_id = populator.create_schema("Inventory Products", fields)
    if schema_id:
        records = populator.load_json_file("data/sample_inventory_products.json")
        populator.insert_records(schema_id, records)


def populate_hospital_patients(populator: DatabasePopulator):
    """Populate hospital patient data"""
    print("\n🏥 Loading Hospital Patients...")
    
    fields = [
        {"field_name": "patient_id", "field_type": "string", "constraints": {"unique": True, "required": True}},
        {"field_name": "first_name", "field_type": "string", "constraints": {"required": True}},
        {"field_name": "last_name", "field_type": "string", "constraints": {"required": True}},
        {"field_name": "date_of_birth", "field_type": "date", "constraints": {}},
        {"field_name": "gender", "field_type": "string", "constraints": {}},
        {"field_name": "blood_type", "field_type": "string", "constraints": {}},
        {"field_name": "contact_number", "field_type": "string", "constraints": {}},
        {"field_name": "email", "field_type": "string", "constraints": {}},
        {"field_name": "address", "field_type": "string", "constraints": {}},
        {"field_name": "insurance_id", "field_type": "string", "constraints": {}},
        {"field_name": "admission_date", "field_type": "date", "constraints": {}},
        {"field_name": "discharge_date", "field_type": "date", "constraints": {}},
        {"field_name": "diagnosis", "field_type": "string", "constraints": {}},
        {"field_name": "treatment", "field_type": "string", "constraints": {}},
        {"field_name": "doctor_assigned", "field_type": "string", "constraints": {}},
        {"field_name": "room_number", "field_type": "string", "constraints": {}},
        {"field_name": "bed_number", "field_type": "string", "constraints": {}},
        {"field_name": "severity", "field_type": "string", "constraints": {"enum": ["mild", "moderate", "severe"]}},
        {"field_name": "age_group", "field_type": "string", "constraints": {}},
        {"field_name": "payment_status", "field_type": "string", "constraints": {}},
    ]
    
    schema_id = populator.create_schema("Hospital Patients", fields)
    if schema_id:
        records = populator.load_csv_file("data/sample_hospital_patients.csv")
        populator.insert_records(schema_id, records)


def populate_real_estate(populator: DatabasePopulator):
    """Populate real estate building data"""
    print("\n🏢 Loading Real Estate Buildings...")
    
    fields = [
        {"field_name": "building_id", "field_type": "string", "constraints": {"unique": True, "required": True}},
        {"field_name": "building_name", "field_type": "string", "constraints": {"required": True}},
        {"field_name": "address", "field_type": "string", "constraints": {}},
        {"field_name": "total_floors", "field_type": "integer", "constraints": {}},
        {"field_name": "year_built", "field_type": "integer", "constraints": {}},
        {"field_name": "total_area_sqm", "field_type": "float", "constraints": {}},
        {"field_name": "occupancy_percent", "field_type": "float", "constraints": {}},
        {"field_name": "manager_name", "field_type": "string", "constraints": {}},
        {"field_name": "manager_email", "field_type": "string", "constraints": {}},
        {"field_name": "phone", "field_type": "string", "constraints": {}},
        {"field_name": "facilities", "field_type": "array", "constraints": {}},
        {"field_name": "parking_spaces", "field_type": "integer", "constraints": {}},
        {"field_name": "accessibility_features", "field_type": "array", "constraints": {}},
        {"field_name": "energy_rating", "field_type": "string", "constraints": {}},
        {"field_name": "last_inspection", "field_type": "date", "constraints": {}},
        {"field_name": "maintenance_status", "field_type": "string", "constraints": {}},
        {"field_name": "primary_tenants", "field_type": "array", "constraints": {}},
        {"field_name": "rental_price_per_sqm_annual", "field_type": "float", "constraints": {}},
        {"field_name": "available_floors", "field_type": "integer", "constraints": {}},
        {"field_name": "emergency_contacts", "field_type": "object", "constraints": {}},
    ]
    
    schema_id = populator.create_schema("Real Estate Buildings", fields)
    if schema_id:
        records = populator.load_json_file("data/sample_real_estate_buildings.json")
        populator.insert_records(schema_id, records)


def main():
    print("=" * 60)
    print("MetaDB Population Utility")
    print("=" * 60)
    
    # Get login credentials
    email = input("📧 Enter email: ").strip()
    password = input("🔐 Enter password: ").strip()
    
    # Initialize populator
    populator = DatabasePopulator()
    
    # Login
    if not populator.login(email, password):
        print("❌ Failed to login. Exiting.")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Starting Data Population")
    print("=" * 60)
    
    # Populate different datasets
    try:
        populate_ecommerce_orders(populator)
        populate_employees(populator)
        populate_iot_sensors(populator)
        populate_inventory(populator)
        populate_hospital_patients(populator)
        populate_real_estate(populator)
        
        print("\n" + "=" * 60)
        print("✅ Population Complete!")
        print("=" * 60)
        print("\nThe database now contains:")
        print("  • E-Commerce Orders (with various statuses)")
        print("  • Employees (across departments and locations)")
        print("  • IoT Sensors (with real-time readings)")
        print("  • Inventory Products (electronics & accessories)")
        print("  • Hospital Patients (with medical data)")
        print("  • Real Estate Buildings (properties & facilities)")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Population interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Population error: {e}")


if __name__ == "__main__":
    main()
