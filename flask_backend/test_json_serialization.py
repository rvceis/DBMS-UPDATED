#!/usr/bin/env python3
"""
Test script to diagnose JSON serialization errors in the upload endpoints
"""
import sys
import os
import json
import tempfile

sys.path.insert(0, os.getcwd())

from app import create_app
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

def setup_test_user():
    """Create a test user for authentication"""
    app = create_app()
    with app.app_context():
        # Check if test user exists
        user = User.query.filter_by(email='jsontest@test.com').first()
        if user:
            db.session.delete(user)
            db.session.commit()
        
        # Create new test user
        new_user = User(
            username='jsontest',
            email='jsontest@test.com',
            password_hash=generate_password_hash('test123'),
            role='admin'
        )
        db.session.add(new_user)
        db.session.commit()
        print("✅ Test user created: jsontest@test.com / test123")
        return new_user.id

def test_import_file_endpoint():
    """Test the /uploads/import-file endpoint"""
    app = create_app()
    
    with app.test_client() as client:
        # Step 1: Login
        print("\n1️⃣  Testing authentication...")
        login_response = client.post('/auth/login', 
            json={'email': 'jsontest@test.com', 'password': 'test123'},
            content_type='application/json')
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.status_code}")
            print(f"Response: {login_response.data.decode()[:200]}")
            return
        
        token = login_response.json.get('access_token')
        print(f"✅ Authentication successful")
        
        # Step 2: Create test CSV file
        print("\n2️⃣  Creating test file...")
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("name,age,city\nAlice,30,NYC\nBob,25,LA\nCharlie,35,Chicago\n")
            temp_file = f.name
        print(f"✅ Test CSV created: {temp_file}")
        
        # Step 3: Upload file
        print("\n3️⃣  Testing /uploads/import-file endpoint...")
        try:
            with open(temp_file, 'rb') as f:
                upload_response = client.post('/uploads/import-file',
                    headers={'Authorization': f'Bearer {token}'},
                    data={'file': (f, 'test.csv'), 'asset_type_id': '5'},
                    content_type='multipart/form-data')
            
            print(f"Response status: {upload_response.status_code}")
            
            if upload_response.status_code == 200:
                print("✅ Upload endpoint responded with 200 OK")
                try:
                    response_data = upload_response.json
                    print(f"✅ Response is valid JSON")
                    print(f"\nResponse keys: {list(response_data.keys())}")
                    print(f"Format detected: {response_data.get('format_detected')}")
                    print(f"Record count: {response_data.get('record_count')}")
                    print(f"Schema created: {response_data.get('schema_created')}")
                    
                    # Check if schema object is serializable
                    if 'schema' in response_data:
                        schema_obj = response_data['schema']
                        print(f"✅ Schema object present and serialized")
                        print(f"Schema type: {schema_obj.get('name')}")
                    
                except json.JSONDecodeError as e:
                    print(f"❌ Response is NOT valid JSON: {e}")
                    print(f"Raw response: {upload_response.data.decode()[:500]}")
            else:
                print(f"❌ Upload endpoint returned {upload_response.status_code}")
                try:
                    error_data = upload_response.json
                    print(f"Error: {error_data.get('error')}")
                except:
                    print(f"Response: {upload_response.data.decode()[:300]}")
        
        except Exception as e:
            print(f"❌ Error during test: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Cleanup
            os.unlink(temp_file)
            print(f"\n✅ Test file cleaned up")

if __name__ == '__main__':
    print("=" * 60)
    print("JSON SERIALIZATION TEST")
    print("=" * 60)
    
    print("\n🔧 Setting up test environment...")
    setup_test_user()
    
    print("\n🧪 Running endpoint tests...")
    test_import_file_endpoint()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
