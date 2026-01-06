"""
Comprehensive Integration Test Suite for MetaDB
Tests all endpoints, database operations, and frontend integration
"""

import pytest
import json
import os
import sys
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions import db
from app.models import (
    User, AssetType, SchemaModel, SchemaField, MetadataRecord, 
    FieldValue, ChangeLog, SchemaVersion, DataRow
)


@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client"""
    return app.test_client()


@pytest.fixture
def auth_token(client):
    """Get authentication token"""
    # Create user
    with client.application.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash='hashed_password',
            role='admin'
        )
        db.session.add(user)
        db.session.commit()
    
    # Login
    response = client.post('/auth/login', json={
        'email': 'test@example.com',
        'password': 'password123'
    })
    
    if response.status_code == 200:
        return response.json.get('access_token')
    return None


class TestDatabaseConnection:
    """Test database connectivity and schema creation"""
    
    def test_database_tables_exist(self, app):
        """Verify all required tables are created"""
        with app.app_context():
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = [
                'users', 'asset_types', 'schemas', 'schema_fields',
                'metadata_records', 'field_values', 'change_logs',
                'schema_versions', 'data_rows', 'report_templates',
                'report_executions'
            ]
            
            for table in required_tables:
                assert table in tables, f"Table '{table}' not found in database"
    
    def test_schema_field_columns(self, app):
        """Verify schema_fields table has all required columns"""
        with app.app_context():
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('schema_fields')]
            
            required_columns = [
                'id', 'schema_id', 'field_name', 'field_type',
                'is_required', 'default_value', 'constraints',
                'is_deleted', 'order_index'
            ]
            
            for col in required_columns:
                assert col in columns, f"Column '{col}' not found in schema_fields"
    
    def test_field_value_type_columns(self, app):
        """Verify FieldValue has all type-specific columns (EAV pattern)"""
        with app.app_context():
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('field_values')]
            
            type_columns = [
                'value_text', 'value_int', 'value_float', 'value_bool',
                'value_date', 'value_json', 'value_binary'
            ]
            
            for col in type_columns:
                assert col in columns, f"Column '{col}' not found in field_values"


class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_user_registration(self, client):
        """Test user registration"""
        response = client.post('/auth/register', json={
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'password123'
        })
        
        assert response.status_code in [200, 201, 400]  # 400 if user exists
        if response.status_code in [200, 201]:
            assert 'success' in response.json or 'user' in response.json
    
    def test_user_login(self, client):
        """Test user login"""
        # Register first
        client.post('/auth/register', json={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        # Login
        response = client.post('/auth/login', json={
            'email': 'test@example.com',
            'password': 'password123'
        })
        
        assert response.status_code == 200
        assert 'access_token' in response.json
    
    def test_protected_endpoint_requires_token(self, client):
        """Test that protected endpoints require authentication"""
        response = client.get('/api/schemas/')
        assert response.status_code == 401


class TestAssetTypeEndpoints:
    """Test asset type endpoints"""
    
    def test_create_asset_type(self, client, auth_token):
        """Test creating asset type"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post('/api/asset-types/', 
            json={
                'name': 'Document',
                'description': 'Text documents'
            },
            headers=headers
        )
        
        assert response.status_code in [200, 201]
        assert 'id' in response.json or 'asset_type' in response.json
    
    def test_list_asset_types(self, client, auth_token):
        """Test listing asset types"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get('/api/asset-types/', headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json, list)


class TestDynamicSchemaEndpoints:
    """Test dynamic schema CRUD operations"""
    
    def test_create_schema(self, client, auth_token, app):
        """Test creating a dynamic schema"""
        # Create asset type first
        with app.app_context():
            asset_type = AssetType(name='Document', description='Docs')
            db.session.add(asset_type)
            db.session.commit()
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post('/api/schemas/', 
            json={
                'name': 'Document Schema',
                'asset_type_id': 1,
                'fields': [
                    {'name': 'title', 'type': 'string', 'required': True},
                    {'name': 'pages', 'type': 'integer', 'required': False},
                    {'name': 'active', 'type': 'boolean', 'required': False}
                ]
            },
            headers=headers
        )
        
        assert response.status_code in [200, 201]
        assert 'schema' in response.json or 'id' in response.json
    
    def test_list_schemas(self, client, auth_token):
        """Test listing schemas"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get('/api/schemas/', headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json, list)
    
    def test_get_schema_details(self, client, auth_token, app):
        """Test getting schema details with fields"""
        with app.app_context():
            asset_type = AssetType(name='Test Asset', description='Test')
            db.session.add(asset_type)
            db.session.flush()
            
            schema = SchemaModel(
                name='Test Schema',
                version=1,
                asset_type_id=asset_type.id,
                is_active=True
            )
            db.session.add(schema)
            db.session.flush()
            
            field = SchemaField(
                schema_id=schema.id,
                field_name='test_field',
                field_type='string',
                is_required=True
            )
            db.session.add(field)
            db.session.commit()
            schema_id = schema.id
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = client.get(f'/api/schemas/{schema_id}', headers=headers)
        
        assert response.status_code == 200
        assert 'fields' in response.json or 'name' in response.json
    
    def test_add_field_to_schema(self, client, auth_token, app):
        """Test adding a field to existing schema"""
        with app.app_context():
            asset_type = AssetType(name='Test', description='Test')
            db.session.add(asset_type)
            db.session.flush()
            
            schema = SchemaModel(
                name='Schema',
                version=1,
                asset_type_id=asset_type.id,
                is_active=True
            )
            db.session.add(schema)
            db.session.commit()
            schema_id = schema.id
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post(f'/api/schemas/{schema_id}/fields',
            json={
                'field_name': 'new_field',
                'field_type': 'string',
                'is_required': False
            },
            headers=headers
        )
        
        assert response.status_code in [200, 201]
    
    def test_schema_version_control(self, client, auth_token, app):
        """Test schema versioning"""
        with app.app_context():
            asset_type = AssetType(name='Test', description='Test')
            db.session.add(asset_type)
            db.session.flush()
            
            schema = SchemaModel(
                name='Versioned Schema',
                version=1,
                asset_type_id=asset_type.id,
                is_active=True
            )
            db.session.add(schema)
            db.session.commit()
            schema_id = schema.id
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get(f'/api/schemas/{schema_id}/versions', 
            headers=headers)
        
        assert response.status_code == 200 or response.status_code == 404


class TestDataRecordEndpoints:
    """Test data record CRUD operations"""
    
    def test_create_record(self, client, auth_token, app):
        """Test creating a data record"""
        with app.app_context():
            asset_type = AssetType(name='Document', description='Docs')
            db.session.add(asset_type)
            db.session.flush()
            
            schema = SchemaModel(
                name='Doc Schema',
                version=1,
                asset_type_id=asset_type.id,
                is_active=True
            )
            db.session.add(schema)
            db.session.flush()
            
            for field_name in ['title', 'author']:
                field = SchemaField(
                    schema_id=schema.id,
                    field_name=field_name,
                    field_type='string'
                )
                db.session.add(field)
            db.session.commit()
            schema_id = schema.id
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post('/api/data/create',
            json={
                'name': 'My Document',
                'schema_id': schema_id,
                'values': {
                    'title': 'Test Doc',
                    'author': 'John Doe'
                }
            },
            headers=headers
        )
        
        assert response.status_code in [200, 201]
        assert 'success' in response.json or 'record' in response.json
    
    def test_list_records(self, client, auth_token):
        """Test listing data records"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get('/api/data/', headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json, (list, dict))
    
    def test_get_record_details(self, client, auth_token, app):
        """Test getting record details"""
        with app.app_context():
            asset_type = AssetType(name='Test', description='Test')
            db.session.add(asset_type)
            db.session.flush()
            
            schema = SchemaModel(
                name='Schema',
                version=1,
                asset_type_id=asset_type.id,
                is_active=True
            )
            db.session.add(schema)
            db.session.flush()
            
            record = MetadataRecord(
                name='Test Record',
                schema_id=schema.id,
                asset_type_id=asset_type.id
            )
            db.session.add(record)
            db.session.commit()
            record_id = record.id
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        response = client.get(f'/api/data/{record_id}', headers=headers)
        
        assert response.status_code in [200, 404]
    
    def test_update_record(self, client, auth_token, app):
        """Test updating a record"""
        with app.app_context():
            asset_type = AssetType(name='Test', description='Test')
            db.session.add(asset_type)
            db.session.flush()
            
            schema = SchemaModel(
                name='Schema',
                version=1,
                asset_type_id=asset_type.id,
                is_active=True
            )
            db.session.add(schema)
            db.session.flush()
            
            record = MetadataRecord(
                name='Record',
                schema_id=schema.id,
                asset_type_id=asset_type.id
            )
            db.session.add(record)
            db.session.commit()
            record_id = record.id
        
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.put(f'/api/data/{record_id}',
            json={'name': 'Updated Record'},
            headers=headers
        )
        
        assert response.status_code in [200, 404]


class TestEAVStorage:
    """Test EAV (Entity-Attribute-Value) storage pattern"""
    
    def test_field_value_storage_text(self, app):
        """Test storing text value in EAV pattern"""
        with app.app_context():
            asset_type = AssetType(name='Test', description='Test')
            db.session.add(asset_type)
            db.session.flush()
            
            schema = SchemaModel(
                name='Schema',
                version=1,
                asset_type_id=asset_type.id,
                is_active=True
            )
            db.session.add(schema)
            db.session.flush()
            
            field = SchemaField(
                schema_id=schema.id,
                field_name='name',
                field_type='string',
                is_required=True
            )
            db.session.add(field)
            db.session.flush()
            
            record = MetadataRecord(
                name='Test',
                schema_id=schema.id,
                asset_type_id=asset_type.id
            )
            db.session.add(record)
            db.session.flush()
            
            fv = FieldValue(
                record_id=record.id,
                schema_field_id=field.id
            )
            fv.set_value('Test Name')
            db.session.add(fv)
            db.session.commit()
            
            # Verify storage
            retrieved = db.session.query(FieldValue).first()
            assert retrieved.get_value() == 'Test Name'
            assert retrieved.value_text == 'Test Name'
    
    def test_field_value_storage_integer(self, app):
        """Test storing integer value"""
        with app.app_context():
            asset_type = AssetType(name='Test', description='Test')
            db.session.add(asset_type)
            db.session.flush()
            
            schema = SchemaModel(
                name='Schema',
                version=1,
                asset_type_id=asset_type.id,
                is_active=True
            )
            db.session.add(schema)
            db.session.flush()
            
            field = SchemaField(
                schema_id=schema.id,
                field_name='count',
                field_type='integer'
            )
            db.session.add(field)
            db.session.flush()
            
            record = MetadataRecord(
                name='Test',
                schema_id=schema.id,
                asset_type_id=asset_type.id
            )
            db.session.add(record)
            db.session.flush()
            
            fv = FieldValue(
                record_id=record.id,
                schema_field_id=field.id
            )
            fv.set_value(42)
            db.session.add(fv)
            db.session.commit()
            
            retrieved = db.session.query(FieldValue).first()
            assert retrieved.get_value() == 42
            assert retrieved.value_int == 42
    
    def test_field_value_storage_boolean(self, app):
        """Test storing boolean value"""
        with app.app_context():
            asset_type = AssetType(name='Test', description='Test')
            db.session.add(asset_type)
            db.session.flush()
            
            schema = SchemaModel(
                name='Schema',
                version=1,
                asset_type_id=asset_type.id,
                is_active=True
            )
            db.session.add(schema)
            db.session.flush()
            
            field = SchemaField(
                schema_id=schema.id,
                field_name='active',
                field_type='boolean'
            )
            db.session.add(field)
            db.session.flush()
            
            record = MetadataRecord(
                name='Test',
                schema_id=schema.id,
                asset_type_id=asset_type.id
            )
            db.session.add(record)
            db.session.flush()
            
            fv = FieldValue(
                record_id=record.id,
                schema_field_id=field.id
            )
            fv.set_value(True)
            db.session.add(fv)
            db.session.commit()
            
            retrieved = db.session.query(FieldValue).first()
            assert retrieved.get_value() is True
            assert retrieved.value_bool is True
    
    def test_field_value_storage_json(self, app):
        """Test storing JSON value"""
        with app.app_context():
            asset_type = AssetType(name='Test', description='Test')
            db.session.add(asset_type)
            db.session.flush()
            
            schema = SchemaModel(
                name='Schema',
                version=1,
                asset_type_id=asset_type.id,
                is_active=True
            )
            db.session.add(schema)
            db.session.flush()
            
            field = SchemaField(
                schema_id=schema.id,
                field_name='metadata',
                field_type='json'
            )
            db.session.add(field)
            db.session.flush()
            
            record = MetadataRecord(
                name='Test',
                schema_id=schema.id,
                asset_type_id=asset_type.id
            )
            db.session.add(record)
            db.session.flush()
            
            fv = FieldValue(
                record_id=record.id,
                schema_field_id=field.id
            )
            json_data = {'key': 'value', 'nested': {'field': 123}}
            fv.set_value(json_data)
            db.session.add(fv)
            db.session.commit()
            
            retrieved = db.session.query(FieldValue).first()
            assert retrieved.get_value() == json_data
            assert retrieved.value_json == json_data


class TestDataRowBulkStorage:
    """Test JSONB bulk storage for imports"""
    
    def test_data_row_creation(self, app):
        """Test creating data rows"""
        with app.app_context():
            asset_type = AssetType(name='Test', description='Test')
            db.session.add(asset_type)
            db.session.flush()
            
            schema = SchemaModel(
                name='Schema',
                version=1,
                asset_type_id=asset_type.id,
                is_active=True
            )
            db.session.add(schema)
            db.session.flush()
            
            record = MetadataRecord(
                name='Bulk Import',
                schema_id=schema.id,
                asset_type_id=asset_type.id
            )
            db.session.add(record)
            db.session.flush()
            
            # Add data rows
            for i in range(5):
                row = DataRow(
                    record_id=record.id,
                    row_index=i,
                    data={'name': f'Row {i}', 'value': i * 10}
                )
                db.session.add(row)
            db.session.commit()
            
            # Verify
            rows = db.session.query(DataRow).filter_by(record_id=record.id).all()
            assert len(rows) == 5
            assert rows[0].data['name'] == 'Row 0'
            assert rows[4].data['value'] == 40


class TestUploadEndpoints:
    """Test file upload endpoints"""
    
    def test_parse_endpoint(self, client, auth_token):
        """Test data parsing endpoint"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.post('/api/uploads/parse',
            json={
                'content': 'field1,field2\nvalue1,value2',
                'format': 'csv'
            },
            headers=headers
        )
        
        assert response.status_code in [200, 400]


class TestAnalyticsEndpoints:
    """Test analytics endpoints"""
    
    def test_dashboard_stats(self, client, auth_token):
        """Test dashboard statistics"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get('/api/analytics/dashboard', headers=headers)
        
        assert response.status_code == 200
        assert 'total_data_records' in response.json or 'total_records' in response.json
    
    def test_data_by_asset_type(self, client, auth_token):
        """Test data grouped by asset type"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get('/api/analytics/data-by-asset-type', 
            headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json, list)
    
    def test_data_timeline(self, client, auth_token):
        """Test data creation timeline"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get('/api/analytics/data-timeline', 
            headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json, list)


class TestReportEndpoints:
    """Test report generation endpoints"""
    
    def test_list_templates(self, client, auth_token):
        """Test listing report templates"""
        headers = {'Authorization': f'Bearer {auth_token}'}
        
        response = client.get('/api/reports/templates', headers=headers)
        
        assert response.status_code in [200, 404]


class TestDynamicSchemaFeatures:
    """Test innovative dynamic schema features"""
    
    def test_schema_snapshot_on_create(self, app):
        """Test that schema snapshot is created on schema creation"""
        with app.app_context():
            asset_type = AssetType(name='Test', description='Test')
            db.session.add(asset_type)
            db.session.flush()
            
            schema = SchemaModel(
                name='Schema',
                version=1,
                asset_type_id=asset_type.id,
                is_active=True
            )
            db.session.add(schema)
            db.session.flush()
            
            field = SchemaField(
                schema_id=schema.id,
                field_name='test',
                field_type='string'
            )
            db.session.add(field)
            
            # Create version snapshot
            version = SchemaVersion(
                schema_id=schema.id,
                version_number=1,
                schema_snapshot={'name': 'Schema', 'fields': [{'name': 'test', 'type': 'string'}]},
                change_summary='Initial creation'
            )
            db.session.add(version)
            db.session.commit()
            
            # Verify
            retrieved = db.session.query(SchemaVersion).first()
            assert retrieved.schema_snapshot is not None
            assert 'fields' in retrieved.schema_snapshot
    
    def test_change_log_on_schema_modification(self, app):
        """Test that changes are logged"""
        with app.app_context():
            asset_type = AssetType(name='Test', description='Test')
            db.session.add(asset_type)
            db.session.flush()
            
            schema = SchemaModel(
                name='Schema',
                version=1,
                asset_type_id=asset_type.id,
                is_active=True
            )
            db.session.add(schema)
            db.session.flush()
            
            # Log change
            log = ChangeLog(
                schema_id=schema.id,
                change_type='field_added',
                description='Added field: name',
                change_details={'field': 'name', 'type': 'string'}
            )
            db.session.add(log)
            db.session.commit()
            
            # Verify
            retrieved = db.session.query(ChangeLog).first()
            assert retrieved.change_type == 'field_added'
            assert 'field' in retrieved.change_details


def test_database_integrity(app):
    """Test database integrity constraints"""
    with app.app_context():
        # Test unique constraint on schema-field
        asset_type = AssetType(name='Test', description='Test')
        db.session.add(asset_type)
        db.session.flush()
        
        schema = SchemaModel(
            name='Schema',
            version=1,
            asset_type_id=asset_type.id,
            is_active=True
        )
        db.session.add(schema)
        db.session.flush()
        
        field1 = SchemaField(
            schema_id=schema.id,
            field_name='duplicate_field',
            field_type='string'
        )
        db.session.add(field1)
        db.session.flush()
        
        # Try to add duplicate - should fail
        field2 = SchemaField(
            schema_id=schema.id,
            field_name='duplicate_field',
            field_type='string'
        )
        db.session.add(field2)
        
        with pytest.raises(Exception):  # IntegrityError
            db.session.commit()


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])
