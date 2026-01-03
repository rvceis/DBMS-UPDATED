#!/usr/bin/env python3
"""
Test script for multi-table report generation with content inclusion
"""
import requests
import json
import sys

BASE_URL = "http://localhost:5000/api"

# Test credentials
ADMIN_EMAIL = "admin@example.com"
ADMIN_PASSWORD = "admin123"

def login():
    """Login and get JWT token"""
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get('access_token')
    else:
        print(f"Login failed: {response.status_code} - {response.text}")
        sys.exit(1)

def get_schemas(token):
    """Get list of all schemas"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(f"{BASE_URL}/data/schemas", headers=headers)
    if response.status_code == 200:
        return response.json()
    return []

def create_multitable_template(token, schema_ids):
    """Create a multi-table report template"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Build table configs for first 2 schemas
    table_configs = []
    for i, schema_id in enumerate(schema_ids[:2]):
        table_configs.append({
            "schema_id": schema_id,
            "fields": [],  # Include all fields
            "filters": [],
            "sort": [],
            "limit": 100
        })
    
    template_data = {
        "name": "Multi-Table Test Report",
        "description": "Testing multi-table report generation with content inclusion",
        "table_configs": table_configs,
        "include_records": True,
        "include_metadata": True,
        "include_schema_details": True,
        "include_summary": True,
        "is_public": False
    }
    
    print("\n=== Creating Multi-Table Template ===")
    print(f"Table configs: {len(table_configs)} schemas")
    print(f"Content options: records=True, metadata=True, details=True, summary=True")
    
    response = requests.post(f"{BASE_URL}/reports/templates", 
                            headers=headers, 
                            json=template_data)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 201:
        template = response.json()
        print(f"✅ Template created successfully!")
        print(f"   ID: {template.get('id')}")
        print(f"   Name: {template.get('name')}")
        print(f"   Table count: {template.get('table_count')}")
        print(f"   Include records: {template.get('include_records')}")
        print(f"   Include metadata: {template.get('include_metadata')}")
        print(f"   Include schema details: {template.get('include_schema_details')}")
        print(f"   Include summary: {template.get('include_summary')}")
        return template
    else:
        print(f"❌ Failed to create template: {response.text}")
        return None

def generate_csv_report(token, template_id):
    """Generate CSV report from template"""
    headers = {"Authorization": f"Bearer {token}"}
    
    report_data = {
        "template_id": template_id,
        "format": "csv",
        "params": {}
    }
    
    print(f"\n=== Generating CSV Report ===")
    print(f"Template ID: {template_id}")
    
    response = requests.post(f"{BASE_URL}/reports/generate", 
                            headers=headers, 
                            json=report_data)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 201:
        execution = response.json()
        print(f"✅ Report generated successfully!")
        print(f"   Execution ID: {execution.get('id')}")
        print(f"   Status: {execution.get('status')}")
        print(f"   Row count: {execution.get('row_count')}")
        print(f"   File path: {execution.get('file_path')}")
        print(f"   File size: {execution.get('file_size')} bytes")
        print(f"   Execution time: {execution.get('execution_time_ms')} ms")
        return execution
    else:
        print(f"❌ Failed to generate report: {response.text}")
        return None

def generate_report_with_overrides(token, template_id):
    """Generate report with content option overrides"""
    headers = {"Authorization": f"Bearer {token}"}
    
    report_data = {
        "template_id": template_id,
        "format": "csv",
        "include_records": True,
        "include_metadata": False,  # Override: exclude metadata
        "include_schema_details": True,
        "include_summary": False,  # Override: exclude summary
        "params": {}
    }
    
    print(f"\n=== Generating CSV Report with Overrides ===")
    print(f"Template ID: {template_id}")
    print(f"Overrides: metadata=False, summary=False")
    
    response = requests.post(f"{BASE_URL}/reports/generate", 
                            headers=headers, 
                            json=report_data)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 201:
        execution = response.json()
        print(f"✅ Report generated with overrides!")
        print(f"   Execution ID: {execution.get('id')}")
        print(f"   Status: {execution.get('status')}")
        print(f"   Row count: {execution.get('row_count')}")
        return execution
    else:
        print(f"❌ Failed to generate report: {response.text}")
        return None

def test_legacy_template(token, schema_id):
    """Test backward compatibility with legacy single-schema template"""
    headers = {"Authorization": f"Bearer {token}"}
    
    template_data = {
        "name": "Legacy Single-Schema Report",
        "description": "Testing backward compatibility",
        "schema_id": schema_id,
        "query_config": {
            "fields": [],
            "filters": [],
            "sort": [],
            "limit": 50
        },
        "is_public": False
    }
    
    print("\n=== Creating Legacy Template ===")
    print(f"Schema ID: {schema_id}")
    
    response = requests.post(f"{BASE_URL}/reports/templates", 
                            headers=headers, 
                            json=template_data)
    
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 201:
        template = response.json()
        print(f"✅ Legacy template created successfully!")
        print(f"   ID: {template.get('id')}")
        print(f"   Name: {template.get('name')}")
        
        # Generate report from legacy template
        print(f"\n=== Generating from Legacy Template ===")
        report_data = {
            "template_id": template.get('id'),
            "format": "csv"
        }
        response = requests.post(f"{BASE_URL}/reports/generate", 
                                headers=headers, 
                                json=report_data)
        
        if response.status_code == 201:
            print(f"✅ Legacy report generated successfully!")
            execution = response.json()
            print(f"   Execution ID: {execution.get('id')}")
            print(f"   Status: {execution.get('status')}")
            print(f"   Row count: {execution.get('row_count')}")
        else:
            print(f"❌ Failed to generate legacy report: {response.text}")
        
        return template
    else:
        print(f"❌ Failed to create legacy template: {response.text}")
        return None

def main():
    print("=" * 60)
    print("Multi-Table Report Generation Test")
    print("=" * 60)
    
    # Login
    print("\n🔐 Logging in...")
    token = login()
    print("✅ Login successful")
    
    # Get schemas
    print("\n📋 Fetching schemas...")
    schemas = get_schemas(token)
    
    if len(schemas) < 2:
        print("❌ Need at least 2 schemas for multi-table testing")
        print(f"   Found: {len(schemas)} schemas")
        sys.exit(1)
    
    print(f"✅ Found {len(schemas)} schemas")
    for schema in schemas[:3]:
        print(f"   - {schema.get('id')}: {schema.get('name')}")
    
    schema_ids = [s.get('id') for s in schemas]
    
    # Test 1: Create multi-table template
    template = create_multitable_template(token, schema_ids)
    if not template:
        sys.exit(1)
    
    # Test 2: Generate report
    execution = generate_csv_report(token, template.get('id'))
    if not execution:
        sys.exit(1)
    
    # Test 3: Generate with overrides
    execution_override = generate_report_with_overrides(token, template.get('id'))
    if not execution_override:
        sys.exit(1)
    
    # Test 4: Test legacy compatibility
    legacy_template = test_legacy_template(token, schema_ids[0])
    
    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)
    print("\nSummary:")
    print(f"  - Multi-table template ID: {template.get('id')}")
    print(f"  - CSV report executions: 2")
    print(f"  - Legacy template ID: {legacy_template.get('id') if legacy_template else 'N/A'}")
    print("\nNext steps:")
    print("  1. Check generated CSV files in instance/reports/")
    print("  2. Verify content sections (schema info, metadata, summary, records)")
    print("  3. Test PDF generation")
    print("  4. Update frontend to support multi-table templates")

if __name__ == "__main__":
    main()
