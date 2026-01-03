#!/usr/bin/env python3
"""
Test data generator for the dynamic schema system
Creates various types of records to test different scenarios
"""
import requests
import json

BASE_URL = "http://localhost:5000"

# Test credentials
EMAIL = "admin@test.com"
PASSWORD = "password"

def get_token():
    """Login and get JWT token"""
    response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": EMAIL, "password": PASSWORD}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.text}")
        return None

def create_record(token, name, data, schema_name=None, asset_type_id=None):
    """Create a single record"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "name": name,
        "values": data,
        "create_new_schema": True,
        "schema_name": schema_name or f"Schema_{name}",
        "asset_type_id": asset_type_id
    }
    
    response = requests.post(
        f"{BASE_URL}/data",
        headers=headers,
        json=payload
    )
    
    if response.status_code in [200, 201]:
        print(f"✅ Created: {name}")
        return response.json()
    else:
        print(f"❌ Failed to create {name}: {response.text}")
        return None

def create_bulk_records(token, records, schema_name="BulkSchema"):
    """Bulk import multiple records"""
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {
        "records": records,
        "schema_name": schema_name,
        "create_new_schema": True
    }
    
    response = requests.post(
        f"{BASE_URL}/data/bulk",
        headers=headers,
        json=payload
    )
    
    if response.status_code in [200, 201]:
        count = response.json().get("count", len(records))
        print(f"✅ Bulk imported {count} records for {schema_name}")
        return response.json()
    else:
        print(f"❌ Bulk import failed: {response.text}")
        return None

def main():
    print("🧪 Testing Dynamic Schema System\n")
    
    # Get token
    print("1️⃣ Authenticating...")
    token = get_token()
    if not token:
        return
    print("✅ Authenticated!\n")
    
    # Test 1: Customer Records
    print("2️⃣ Creating Customer Records...")
    customers = [
        {
            "name": "Customer 1",
            "data": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john@example.com",
                "age": 32,
                "phone": "+1-234-567-8900",
                "is_premium": True,
                "signup_date": "2024-01-15",
                "balance": 1500.50
            }
        },
        {
            "name": "Customer 2",
            "data": {
                "first_name": "Jane",
                "last_name": "Smith",
                "email": "jane@example.com",
                "age": 28,
                "phone": "+1-234-567-8901",
                "is_premium": False,
                "signup_date": "2024-06-20",
                "balance": 750.25
            }
        }
    ]
    
    for customer in customers:
        create_record(token, customer["name"], customer["data"], "CustomerSchema")
    
    # Test 2: Product Inventory
    print("\n3️⃣ Creating Product Inventory Records...")
    products = [
        {"product_name": "Laptop", "sku": "LP-001", "price": 999.99, "stock": 15, "category": "Electronics"},
        {"product_name": "Mouse", "sku": "MS-001", "price": 29.99, "stock": 150, "category": "Accessories"},
        {"product_name": "Keyboard", "sku": "KB-001", "price": 79.99, "stock": 80, "category": "Accessories"},
    ]
    create_bulk_records(token, products, "ProductInventory")
    
    # Test 3: Employee Records
    print("\n4️⃣ Creating Employee Records...")
    employees = [
        {
            "name": "Employee 1",
            "data": {
                "employee_id": "EMP001",
                "full_name": "Alice Johnson",
                "department": "Engineering",
                "position": "Senior Developer",
                "salary": 120000,
                "hire_date": "2020-03-10",
                "is_active": True,
                "years_experience": 8
            }
        },
        {
            "name": "Employee 2",
            "data": {
                "employee_id": "EMP002",
                "full_name": "Bob Wilson",
                "department": "Sales",
                "position": "Sales Manager",
                "salary": 95000,
                "hire_date": "2019-07-15",
                "is_active": True,
                "years_experience": 10
            }
        }
    ]
    
    for emp in employees:
        create_record(token, emp["name"], emp["data"], "EmployeeSchema")
    
    # Test 4: Blog Posts
    print("\n5️⃣ Creating Blog Posts...")
    blog_posts = [
        {
            "title": "Getting Started with Python",
            "author": "Tech Writer",
            "content": "This is a comprehensive guide to Python programming...",
            "tags": ["python", "programming", "tutorial"],
            "views": 1523,
            "published": True,
            "publish_date": "2024-01-20"
        },
        {
            "title": "Advanced Database Design",
            "author": "Database Expert",
            "content": "Learn about normalization, indexing, and optimization...",
            "tags": ["database", "sql", "performance"],
            "views": 842,
            "published": True,
            "publish_date": "2024-02-05"
        }
    ]
    create_bulk_records(token, blog_posts, "BlogPostSchema")
    
    # Test 5: IoT Sensor Data
    print("\n6️⃣ Creating IoT Sensor Data...")
    sensor_data = [
        {"sensor_id": "SENS-001", "location": "Room A", "temperature": 22.5, "humidity": 45.2, "timestamp": "2024-01-02T10:30:00"},
        {"sensor_id": "SENS-002", "location": "Room B", "temperature": 21.8, "humidity": 48.7, "timestamp": "2024-01-02T10:31:00"},
        {"sensor_id": "SENS-003", "location": "Warehouse", "temperature": 18.2, "humidity": 52.1, "timestamp": "2024-01-02T10:32:00"},
    ]
    create_bulk_records(token, sensor_data, "SensorDataSchema")
    
    # Test 6: Project Management
    print("\n7️⃣ Creating Project Management Records...")
    projects = [
        {
            "name": "Project Alpha",
            "data": {
                "project_code": "PROJ-001",
                "title": "E-commerce Platform",
                "description": "Build a scalable e-commerce platform",
                "status": "In Progress",
                "start_date": "2024-01-01",
                "end_date": "2024-06-30",
                "team_size": 8,
                "budget": 250000,
                "priority": "High"
            }
        },
        {
            "name": "Project Beta",
            "data": {
                "project_code": "PROJ-002",
                "title": "Mobile App",
                "description": "Develop iOS and Android apps",
                "status": "Planning",
                "start_date": "2024-02-01",
                "end_date": "2024-08-31",
                "team_size": 5,
                "budget": 150000,
                "priority": "Medium"
            }
        }
    ]
    
    for proj in projects:
        create_record(token, proj["name"], proj["data"], "ProjectSchema")
    
    # Test 7: Social Media Posts
    print("\n8️⃣ Creating Social Media Posts...")
    posts = [
        {
            "username": "john_tech",
            "content": "Just launched my new project! Check it out 🚀",
            "likes": 342,
            "comments": 28,
            "shares": 15,
            "timestamp": "2024-01-02T14:30:00",
            "hashtags": ["coding", "webdev", "javascript"]
        },
        {
            "username": "design_pro",
            "content": "UI/UX tips for better user experience",
            "likes": 567,
            "comments": 45,
            "shares": 89,
            "timestamp": "2024-01-02T15:45:00",
            "hashtags": ["design", "ux", "ui"]
        }
    ]
    create_bulk_records(token, posts, "SocialPostSchema")
    
    # Test 8: Mixed/Flexible Schema
    print("\n9️⃣ Creating Mixed Data (Flexible Schema)...")
    mixed_data = [
        {
            "name": "Mixed 1",
            "data": {
                "id": 1,
                "type": "document",
                "title": "Report Q4",
                "pages": 25,
                "format": "PDF"
            }
        },
        {
            "name": "Mixed 2",
            "data": {
                "id": 2,
                "type": "video",
                "title": "Tutorial Video",
                "duration_minutes": 45,
                "resolution": "1080p",
                "views": 1200
            }
        }
    ]
    
    for item in mixed_data:
        create_record(token, item["name"], item["data"], "FlexibleSchema")
    
    print("\n" + "="*50)
    print("✨ Test data creation completed!")
    print("="*50)
    print("\n📊 Summary:")
    print("  ✅ 2 Customer records")
    print("  ✅ 3 Product inventory records")
    print("  ✅ 2 Employee records")
    print("  ✅ 2 Blog posts")
    print("  ✅ 3 IoT sensor records")
    print("  ✅ 2 Project management records")
    print("  ✅ 2 Social media posts")
    print("  ✅ 2 Mixed/flexible data records")
    print("\nTotal: 18 records created with different schemas!")
    print("\n🌐 Visit http://localhost:5173/data to view the records")

if __name__ == "__main__":
    main()
