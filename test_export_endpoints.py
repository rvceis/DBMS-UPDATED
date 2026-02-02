#!/usr/bin/env python3
"""
Test Schema Export - Verify export endpoints are working correctly
"""

import requests
import json
import sys

def test_export_endpoints(backend_url: str = "http://localhost:5000"):
    """Test the fixed export endpoints"""
    
    print("\n" + "=" * 70)
    print("SCHEMA EXPORT TEST")
    print("=" * 70)
    
    # Get auth token
    print("\n🔐 Getting authentication token...")
    
    login_data = {
        "email": "admin@admin.com",
        "password": "admin123"
    }
    
    try:
        auth_response = requests.post(f"{backend_url}/api/auth/login", json=login_data)
        if auth_response.status_code != 200:
            print(f"❌ Login failed: {auth_response.text}")
            return
        
        auth_data = auth_response.json()
        token = auth_data.get('token')
        print(f"✅ Got token: {token[:20]}...")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get first schema
    print("\n📋 Getting first schema...")
    
    try:
        schemas_response = requests.get(f"{backend_url}/api/schemas", headers=headers)
        if schemas_response.status_code != 200:
            print(f"❌ Failed to get schemas: {schemas_response.text}")
            return
        
        schemas = schemas_response.json()
        if not schemas:
            print("❌ No schemas found")
            return
        
        schema_id = schemas[0]['id']
        schema_name = schemas[0]['name']
        print(f"✅ Found schema: {schema_name} (ID: {schema_id})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Test JSON export
    print(f"\n📥 Testing JSON export for schema {schema_id}...")
    
    try:
        json_response = requests.get(
            f"{backend_url}/api/schemas/{schema_id}/export/json",
            headers=headers
        )
        
        if json_response.status_code == 200:
            json_data = json_response.json()
            fields = json_data.get('fields', [])
            print(f"✅ JSON Export successful!")
            print(f"   Schema: {json_data.get('name')}")
            print(f"   Fields: {len(fields)}")
            
            if fields:
                print(f"\n   Field Details:")
                for f in fields[:3]:  # Show first 3
                    print(f"     • {f['field_name']}: {f['field_type']}")
                if len(fields) > 3:
                    print(f"     ... and {len(fields) - 3} more")
            else:
                print("   ⚠️  No fields found in export")
        else:
            print(f"❌ JSON Export failed: {json_response.status_code}")
            print(json_response.text)
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test SQL export
    print(f"\n💾 Testing SQL export for schema {schema_id}...")
    
    try:
        sql_response = requests.get(
            f"{backend_url}/api/schemas/{schema_id}/export/sql",
            headers=headers
        )
        
        if sql_response.status_code == 200:
            sql_data = sql_response.json()
            sql_statement = sql_data.get('sql_statement', '')
            print(f"✅ SQL Export successful!")
            print(f"   Table: {sql_data.get('table_name')}")
            print(f"   Field count: {sql_data.get('field_count', 0)}")
            
            # Show first few lines of SQL
            sql_lines = sql_statement.split('\n')[:8]
            print(f"\n   SQL Preview:")
            for line in sql_lines:
                print(f"   {line}")
            
            if len(sql_statement.split('\n')) > 8:
                print("   ...")
        else:
            print(f"❌ SQL Export failed: {sql_response.status_code}")
            print(sql_response.text)
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test file download
    print(f"\n📝 Testing file download for schema {schema_id}...")
    
    try:
        download_response = requests.get(
            f"{backend_url}/api/schemas/{schema_id}/export/download/json",
            headers=headers
        )
        
        if download_response.status_code == 200:
            content_type = download_response.headers.get('content-type', 'unknown')
            print(f"✅ File download successful!")
            print(f"   Content-Type: {content_type}")
            print(f"   Content Size: {len(download_response.content)} bytes")
            
            # Verify it's valid JSON
            try:
                json.loads(download_response.text)
                print(f"   ✅ Valid JSON format")
            except:
                print(f"   ❌ Invalid JSON format")
        else:
            print(f"❌ Download failed: {download_response.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    backend_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:5000"
    test_export_endpoints(backend_url)
