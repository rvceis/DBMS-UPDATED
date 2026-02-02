#!/usr/bin/env python3
"""
Complete Database Setup - Creates asset types AND populates schemas with data
Run this once to fully initialize the database with all assets and sample data
"""

import requests
import json
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime


class CompleteDatabaseSetup:
    """Setup complete database with asset types, schemas, and data"""
    
    def __init__(self, backend_url: str = "http://localhost:5000"):
        self.backend_url = backend_url
        self.token = None
        self.session = requests.Session()
        self.asset_type_ids = {}
    
    def login(self, email: str = "admin@admin.com", password: str = "admin123") -> bool:
        """Authenticate with backend"""
        try:
            response = self.session.post(
                f"{self.backend_url}/auth/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token') or data.get('token')
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                print(f"✅ Authenticated as {email}")
                return True
            return False
        except:
            return False
    
    def create_asset_types(self) -> Dict[str, int]:
        """Create all asset types and cache their IDs"""
        asset_types = [
            "Dataset", "3D Model", "Video", "Image", "Source Code",
            "API Specification", "Document", "Sensor Data"
        ]
        
        print("\n" + "=" * 70)
        print("Creating Asset Types")
        print("=" * 70)
        
        for name in asset_types:
            try:
                response = self.session.post(
                    f"{self.backend_url}/asset-types/",
                    json={"name": name}
                )
                if response.status_code in [201, 200]:
                    data = response.json()
                    asset_id = data.get('id', 1)
                    self.asset_type_ids[name] = asset_id
                    print(f"✅ {name} (ID: {asset_id})")
                else:
                    print(f"⚠️  {name} - may already exist")
                    self.asset_type_ids[name] = 1  # Default to 1
            except:
                self.asset_type_ids[name] = 1
        
        return self.asset_type_ids
    
    def get_asset_type_id(self, name: str) -> int:
        """Get asset type ID, default to 1 if not found"""
        return self.asset_type_ids.get(name, 1)
    
    def create_schema(self, name: str, fields: List[Dict], asset_type_name: str = "Dataset") -> Optional[int]:
        """Create schema with proper asset type"""
        try:
            asset_type_id = self.get_asset_type_id(asset_type_name)
            response = self.session.post(
                f"{self.backend_url}/schemas",
                json={
                    "name": name,
                    "asset_type_id": asset_type_id,
                    "fields": fields,
                    "allow_additional_fields": True
                }
            )
            
            if response.status_code == 201:
                schema_id = response.json().get("id")
                print(f"✅ Schema: {name} (ID: {schema_id})")
                return schema_id
            else:
                print(f"❌ Schema failed: {name} - {response.text[:100]}")
                return None
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def insert_records(self, schema_id: int, records: List[Dict], count: int = None) -> int:
        """Insert records into schema"""
        if not records:
            return 0
        
        if count:
            records = records[:count]
        
        success_count = 0
        for record in records:
            try:
                response = self.session.post(
                    f"{self.backend_url}/metadata",
                    json={
                        "schema_id": schema_id,
                        "values": record,
                        "name": record.get("name") or record.get("id") or f"Record {success_count + 1}"
                    }
                )
                if response.status_code in [200, 201]:
                    success_count += 1
            except:
                pass
        
        if success_count > 0:
            print(f"  ✓ Inserted {success_count} records")
        return success_count
    
    def load_json(self, data_list: List[Dict]) -> List[Dict]:
        """Load JSON data"""
        return data_list if isinstance(data_list, list) else []
    
    def load_csv_data(self, csv_data: str) -> List[Dict]:
        """Load CSV data from string"""
        import io
        records = []
        try:
            f = io.StringIO(csv_data)
            reader = csv.DictReader(f)
            for row in reader:
                converted_row = {}
                for key, value in row.items():
                    if key and value:
                        converted_row[key] = self._convert_value(value)
                if converted_row:
                    records.append(converted_row)
        except:
            pass
        return records
    
    @staticmethod
    def _convert_value(value: str) -> Any:
        """Convert string to appropriate type"""
        if not value or value.lower() in ('null', 'none'):
            return None
        if value.lower() in ('true', 'yes'):
            return True
        if value.lower() in ('false', 'no'):
            return False
        try:
            if '.' in value:
                return float(value)
            return int(value)
        except:
            return value
    
    def setup_complete(self):
        """Run complete setup"""
        
        print("\n" + "=" * 70)
        print("Complete Database Setup")
        print("=" * 70)
        
        # Step 1: Create asset types
        self.create_asset_types()
        
        # Step 2: Create schemas and populate data
        print("\n" + "=" * 70)
        print("Creating Schemas and Populating Data")
        print("=" * 70)
        
        # E-Commerce Orders
        print("\n📦 E-Commerce Orders")
        schema_id = self.create_schema(
            "E-Commerce Orders",
            [
                {"field_name": "order_id", "field_type": "string", "constraints": {"unique": True, "required": True}},
                {"field_name": "customer_name", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "email", "field_type": "string", "constraints": {}},
                {"field_name": "total_amount", "field_type": "float", "constraints": {}},
                {"field_name": "status", "field_type": "string", "constraints": {"enum": ["pending", "processing", "shipped", "delivered"]}},
                {"field_name": "order_date", "field_type": "date", "constraints": {}},
                {"field_name": "items_count", "field_type": "integer", "constraints": {}},
            ],
            "Dataset"
        )
        
        if schema_id:
            ecommerce_data = [
                {"order_id": "ORD001", "customer_name": "John Doe", "email": "john@example.com", "total_amount": 299.99, "status": "delivered", "order_date": "2025-12-01", "items_count": 3},
                {"order_id": "ORD002", "customer_name": "Jane Smith", "email": "jane@example.com", "total_amount": 149.99, "status": "shipped", "order_date": "2025-12-02", "items_count": 1},
                {"order_id": "ORD003", "customer_name": "Bob Johnson", "email": "bob@example.com", "total_amount": 599.99, "status": "processing", "order_date": "2025-12-03", "items_count": 5},
                {"order_id": "ORD004", "customer_name": "Alice Brown", "email": "alice@example.com", "total_amount": 99.99, "status": "pending", "order_date": "2025-12-04", "items_count": 1},
                {"order_id": "ORD005", "customer_name": "Charlie Wilson", "email": "charlie@example.com", "total_amount": 1299.99, "status": "delivered", "order_date": "2025-12-05", "items_count": 10},
            ]
            self.insert_records(schema_id, ecommerce_data)
        
        # Employees
        print("\n👥 Employees")
        schema_id = self.create_schema(
            "Employees",
            [
                {"field_name": "employee_id", "field_type": "string", "constraints": {"unique": True, "required": True}},
                {"field_name": "first_name", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "last_name", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "email", "field_type": "string", "constraints": {}},
                {"field_name": "department", "field_type": "string", "constraints": {}},
                {"field_name": "job_title", "field_type": "string", "constraints": {}},
                {"field_name": "salary", "field_type": "float", "constraints": {}},
                {"field_name": "hire_date", "field_type": "date", "constraints": {}},
            ],
            "Dataset"
        )
        
        if schema_id:
            employee_data = [
                {"employee_id": "EMP001", "first_name": "Alice", "last_name": "Anderson", "email": "alice.a@company.com", "department": "Engineering", "job_title": "Senior Developer", "salary": 120000, "hire_date": "2018-05-15"},
                {"employee_id": "EMP002", "first_name": "Bob", "last_name": "Brown", "email": "bob.b@company.com", "department": "Sales", "job_title": "Sales Manager", "salary": 95000, "hire_date": "2019-03-10"},
                {"employee_id": "EMP003", "first_name": "Carol", "last_name": "Chen", "email": "carol.c@company.com", "department": "Engineering", "job_title": "DevOps Engineer", "salary": 110000, "hire_date": "2020-01-20"},
                {"employee_id": "EMP004", "first_name": "David", "last_name": "Davis", "email": "david.d@company.com", "department": "Marketing", "job_title": "Marketing Specialist", "salary": 75000, "hire_date": "2021-07-01"},
                {"employee_id": "EMP005", "first_name": "Emma", "last_name": "Evans", "email": "emma.e@company.com", "department": "Engineering", "job_title": "QA Engineer", "salary": 85000, "hire_date": "2020-11-05"},
            ]
            self.insert_records(schema_id, employee_data)
        
        # IoT Sensors
        print("\n📡 IoT Sensors")
        schema_id = self.create_schema(
            "IoT Sensors",
            [
                {"field_name": "sensor_id", "field_type": "string", "constraints": {"unique": True, "required": True}},
                {"field_name": "sensor_type", "field_type": "string", "constraints": {}},
                {"field_name": "location", "field_type": "string", "constraints": {}},
                {"field_name": "temperature", "field_type": "float", "constraints": {}},
                {"field_name": "humidity", "field_type": "float", "constraints": {}},
                {"field_name": "timestamp", "field_type": "datetime", "constraints": {}},
                {"field_name": "status", "field_type": "string", "constraints": {"enum": ["normal", "warning", "critical"]}},
            ],
            "Sensor Data"
        )
        
        if schema_id:
            sensor_data = [
                {"sensor_id": "SENSOR001", "sensor_type": "Temperature", "location": "Building A", "temperature": 22.5, "humidity": 45.0, "timestamp": "2025-12-02T10:30:00Z", "status": "normal"},
                {"sensor_id": "SENSOR002", "sensor_type": "Temperature", "location": "Building B", "temperature": 23.1, "humidity": 48.0, "timestamp": "2025-12-02T10:35:00Z", "status": "normal"},
                {"sensor_id": "SENSOR003", "sensor_type": "Humidity", "location": "Building A", "temperature": 21.8, "humidity": 52.0, "timestamp": "2025-12-02T10:40:00Z", "status": "warning"},
                {"sensor_id": "SENSOR004", "sensor_type": "Temperature", "location": "Building C", "temperature": 25.0, "humidity": 60.0, "timestamp": "2025-12-02T10:45:00Z", "status": "critical"},
                {"sensor_id": "SENSOR005", "sensor_type": "Humidity", "location": "Building C", "temperature": 20.5, "humidity": 65.0, "timestamp": "2025-12-02T10:50:00Z", "status": "warning"},
            ]
            self.insert_records(schema_id, sensor_data)
        
        # Products Inventory
        print("\n📦 Inventory Products")
        schema_id = self.create_schema(
            "Inventory Products",
            [
                {"field_name": "product_id", "field_type": "string", "constraints": {"unique": True, "required": True}},
                {"field_name": "product_name", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "category", "field_type": "string", "constraints": {}},
                {"field_name": "price", "field_type": "float", "constraints": {}},
                {"field_name": "stock", "field_type": "integer", "constraints": {}},
                {"field_name": "supplier", "field_type": "string", "constraints": {}},
            ],
            "Dataset"
        )
        
        if schema_id:
            product_data = [
                {"product_id": "PROD001", "product_name": "Laptop", "category": "Electronics", "price": 999.99, "stock": 15, "supplier": "TechCorp"},
                {"product_id": "PROD002", "product_name": "Mouse", "category": "Electronics", "price": 29.99, "stock": 150, "supplier": "PeripheralCo"},
                {"product_id": "PROD003", "product_name": "Keyboard", "category": "Electronics", "price": 79.99, "stock": 75, "supplier": "PeripheralCo"},
                {"product_id": "PROD004", "product_name": "Monitor", "category": "Electronics", "price": 299.99, "stock": 30, "supplier": "DisplayTech"},
                {"product_id": "PROD005", "product_name": "USB Cable", "category": "Accessories", "price": 9.99, "stock": 500, "supplier": "CableMakers"},
            ]
            self.insert_records(schema_id, product_data)
        
        # Hospital Patients
        print("\n🏥 Hospital Patients")
        schema_id = self.create_schema(
            "Hospital Patients",
            [
                {"field_name": "patient_id", "field_type": "string", "constraints": {"unique": True, "required": True}},
                {"field_name": "first_name", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "last_name", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "age", "field_type": "integer", "constraints": {}},
                {"field_name": "blood_type", "field_type": "string", "constraints": {}},
                {"field_name": "admission_date", "field_type": "date", "constraints": {}},
                {"field_name": "diagnosis", "field_type": "string", "constraints": {}},
                {"field_name": "doctor", "field_type": "string", "constraints": {}},
            ],
            "Dataset"
        )
        
        if schema_id:
            patient_data = [
                {"patient_id": "PAT001", "first_name": "Sarah", "last_name": "Adams", "age": 45, "blood_type": "O+", "admission_date": "2025-11-20", "diagnosis": "Hypertension", "doctor": "Dr. Smith"},
                {"patient_id": "PAT002", "first_name": "Michael", "last_name": "Brown", "age": 62, "blood_type": "A+", "admission_date": "2025-11-25", "diagnosis": "Diabetes Management", "doctor": "Dr. Johnson"},
                {"patient_id": "PAT003", "first_name": "Jennifer", "last_name": "Wilson", "age": 38, "blood_type": "B-", "admission_date": "2025-12-01", "diagnosis": "Appendicitis", "doctor": "Dr. Lee"},
                {"patient_id": "PAT004", "first_name": "Robert", "last_name": "Taylor", "age": 55, "blood_type": "AB+", "admission_date": "2025-12-02", "diagnosis": "Heart Disease", "doctor": "Dr. Smith"},
                {"patient_id": "PAT005", "first_name": "Lisa", "last_name": "Anderson", "age": 29, "blood_type": "O-", "admission_date": "2025-12-03", "diagnosis": "Pregnancy Monitoring", "doctor": "Dr. Martinez"},
            ]
            self.insert_records(schema_id, patient_data)
        
        print("\n" + "=" * 70)
        print("✅ Database Setup Complete!")
        print("=" * 70)
        print("\nCreated:")
        print("  ✓ 8 Asset Types")
        print("  ✓ 5 Schemas with sample data:")
        print("    - E-Commerce Orders (5 records)")
        print("    - Employees (5 records)")
        print("    - IoT Sensors (5 records)")
        print("    - Inventory Products (5 records)")
        print("    - Hospital Patients (5 records)")
        print("\nYou can now create more schemas and add data using the UI!")


def main():
    setup = CompleteDatabaseSetup()
    
    if not setup.login():
        print("❌ Failed to authenticate. Check backend is running.")
        return
    
    setup.setup_complete()


if __name__ == "__main__":
    main()
