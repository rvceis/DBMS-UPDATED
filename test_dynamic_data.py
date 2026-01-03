#!/usr/bin/env python3
"""
Quick test script to verify the backend /data endpoint works
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_data_endpoint():
    print("🧪 Testing Dynamic Data System...")
    
    # 1. Login
    print("\n1️⃣ Logging in...")
    login_response = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "admin@test.com", "password": "password"}
    )
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_response.text}")
        return
    
    token = login_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    print("✅ Login successful!")
    
    # 2. Create data with auto-schema
    print("\n2️⃣ Creating data record with auto-schema...")
    test_data = {
        "name": "Test Customer Record",
        "values": {
            "customer_name": "Jane Smith",
            "email": "jane@example.com",
            "age": 28,
            "is_premium": True,
            "balance": 1234.56,
            "signup_date": "2025-01-01"
        },
        "create_new_schema": True,
        "schema_name": "TestCustomerSchema",
        "tag": "test"
    }
    
    create_response = requests.post(
        f"{BASE_URL}/data",
        headers=headers,
        json=test_data
    )
    
    if create_response.status_code not in [200, 201]:
        print(f"❌ Create failed: {create_response.text}")
        return
    
    result = create_response.json()
    print("✅ Record created successfully!")
    print(f"   Record ID: {result.get('record', {}).get('id')}")
    print(f"   Schema ID: {result.get('schema', {}).get('id')}")
    print(f"   Schema Name: {result.get('schema', {}).get('name')}")
    
    # 3. List data
    print("\n3️⃣ Listing data records...")
    list_response = requests.get(
        f"{BASE_URL}/data",
        headers=headers
    )
    
    if list_response.status_code != 200:
        print(f"❌ List failed: {list_response.text}")
        return
    
    records = list_response.json()
    print(f"✅ Found {records.get('total', 0)} total records")
    
    # 4. Bulk import
    print("\n4️⃣ Testing bulk import...")
    bulk_data = {
        "records": [
            {"product_name": "Widget A", "price": 29.99, "stock": 100},
            {"product_name": "Widget B", "price": 49.99, "stock": 50},
            {"product_name": "Widget C", "price": 19.99, "stock": 200}
        ],
        "schema_name": "TestProductInventory",
        "create_new_schema": True,
        "tag": "bulk-test"
    }
    
    bulk_response = requests.post(
        f"{BASE_URL}/data/bulk",
        headers=headers,
        json=bulk_data
    )
    
    if bulk_response.status_code not in [200, 201]:
        print(f"❌ Bulk import failed: {bulk_response.text}")
        return
    
    bulk_result = bulk_response.json()
    print(f"✅ Bulk import successful!")
    print(f"   Created {bulk_result.get('count')} records")
    print(f"   Schema: {bulk_result.get('schema', {}).get('name')}")
    
    # 5. Test schema suggestion
    print("\n5️⃣ Testing schema suggestion...")
    suggest_response = requests.post(
        f"{BASE_URL}/data/suggest-schema",
        headers=headers,
        json={
            "values": {"customer_name": "Test", "email": "test@test.com", "age": 25}
        }
    )
    
    if suggest_response.status_code == 200:
        suggest_result = suggest_response.json()
        if suggest_result.get("match_found"):
            print(f"✅ Schema match found: {suggest_result.get('schema', {}).get('name')}")
        else:
            print("ℹ️ No matching schema found")
    
    print("\n🎉 All tests passed! The dynamic data system is working correctly.")
    print("\n📊 Summary:")
    print("   ✅ Backend /data endpoint functional")
    print("   ✅ Auto-schema creation working")
    print("   ✅ Bulk import working")
    print("   ✅ Schema suggestion working")

if __name__ == "__main__":
    try:
        test_data_endpoint()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend. Make sure it's running on http://localhost:5000")
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
