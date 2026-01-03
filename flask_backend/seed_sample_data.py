#!/usr/bin/env python3
"""
Seed sample data into PostgreSQL database
Creates: Schemas, Metadata Records, Field Values
"""

import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import (
    SchemaModel, SchemaField, MetadataRecord, FieldValue,
    AssetType, User
)

def set_field_value(fv, value, field_type):
    """Set field value based on field type"""
    if value is None:
        return
    
    if field_type == 'string':
        fv.value_text = str(value)
    elif field_type == 'integer':
        try:
            fv.value_int = int(value) if value != '' else None
        except:
            fv.value_int = None
    elif field_type == 'float':
        try:
            fv.value_float = float(value) if value != '' else None
        except:
            fv.value_float = None
    elif field_type == 'boolean':
        if isinstance(value, bool):
            fv.value_bool = value
        else:
            fv.value_bool = str(value).lower() in ['true', '1', 'yes', 'on']
    elif field_type == 'date':
        if isinstance(value, str):
            try:
                fv.value_date = datetime.strptime(value, '%Y-%m-%d')
            except:
                pass
    elif field_type in ('json', 'array', 'object'):
        fv.value_json = value if isinstance(value, (dict, list)) else str(value)

def get_user():
    """Get admin user"""
    return User.query.filter_by(email='admin@test.com').first()

def create_employee_schema():
    """Create Employee schema"""
    user = get_user()
    asset_type = AssetType.query.filter_by(name='Document').first()
    
    schema = SchemaModel(
        name='Employee',
        asset_type_id=asset_type.id,
        allow_additional_fields=True,
        created_by=user.id
    )
    db.session.add(schema)
    db.session.flush()
    
    # Add fields
    fields_data = [
        ('first_name', 'string', 'First name'),
        ('last_name', 'string', 'Last name'),
        ('email', 'string', 'Email address'),
        ('phone', 'string', 'Phone number'),
        ('department', 'string', 'Department'),
        ('salary', 'integer', 'Annual salary'),
        ('hire_date', 'date', 'Hire date'),
        ('active', 'boolean', 'Is active'),
    ]
    
    for field_name, field_type, description in fields_data:
        field = SchemaField(
            schema_id=schema.id,
            field_name=field_name,
            field_type=field_type,
            is_required=(field_name in ['first_name', 'last_name', 'email']),
            description=description
        )
        db.session.add(field)
    
    db.session.commit()
    print(f"✅ Created Employee schema with 8 fields")
    return schema

def create_product_schema():
    """Create Product schema"""
    user = get_user()
    asset_type = AssetType.query.filter_by(name='Document').first()
    
    schema = SchemaModel(
        name='Product',
        asset_type_id=asset_type.id,
        allow_additional_fields=True,
        created_by=user.id
    )
    db.session.add(schema)
    db.session.flush()
    
    # Add fields
    fields_data = [
        ('product_name', 'string', 'Product name'),
        ('sku', 'string', 'Stock keeping unit'),
        ('category', 'string', 'Product category'),
        ('price', 'float', 'Price in USD'),
        ('quantity_in_stock', 'integer', 'Quantity available'),
        ('in_stock', 'boolean', 'Available for sale'),
        ('supplier', 'string', 'Supplier name'),
    ]
    
    for field_name, field_type, description in fields_data:
        field = SchemaField(
            schema_id=schema.id,
            field_name=field_name,
            field_type=field_type,
            is_required=(field_name in ['product_name', 'sku']),
            description=description
        )
        db.session.add(field)
    
    db.session.commit()
    print(f"✅ Created Product schema with 7 fields")
    return schema

def create_project_schema():
    """Create Project schema"""
    user = get_user()
    asset_type = AssetType.query.filter_by(name='Document').first()
    
    schema = SchemaModel(
        name='Project',
        asset_type_id=asset_type.id,
        allow_additional_fields=True,
        created_by=user.id
    )
    db.session.add(schema)
    db.session.flush()
    
    # Add fields
    fields_data = [
        ('project_name', 'string', 'Project name'),
        ('status', 'string', 'Current status'),
        ('budget', 'float', 'Project budget'),
        ('start_date', 'date', 'Start date'),
        ('end_date', 'date', 'End date'),
        ('team_lead', 'string', 'Lead team member'),
        ('team_size', 'integer', 'Number of team members'),
        ('priority', 'string', 'Priority level'),
    ]
    
    for field_name, field_type, description in fields_data:
        field = SchemaField(
            schema_id=schema.id,
            field_name=field_name,
            field_type=field_type,
            is_required=(field_name in ['project_name', 'status']),
            description=description
        )
        db.session.add(field)
    
    db.session.commit()
    print(f"✅ Created Project schema with 8 fields")
    return schema

def create_employee_records(schema):
    """Create sample employee records"""
    user = get_user()
    
    employees = [
        {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john.doe@company.com',
            'phone': '555-0101',
            'department': 'Engineering',
            'salary': '95000',
            'hire_date': '2020-01-15',
            'active': 'true',
        },
        {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane.smith@company.com',
            'phone': '555-0102',
            'department': 'Marketing',
            'salary': '75000',
            'hire_date': '2019-06-20',
            'active': 'true',
        },
        {
            'first_name': 'Bob',
            'last_name': 'Johnson',
            'email': 'bob.johnson@company.com',
            'phone': '555-0103',
            'department': 'Sales',
            'salary': '70000',
            'hire_date': '2021-03-10',
            'active': 'true',
        },
        {
            'first_name': 'Alice',
            'last_name': 'Williams',
            'email': 'alice.williams@company.com',
            'phone': '555-0104',
            'department': 'Engineering',
            'salary': '105000',
            'hire_date': '2019-01-05',
            'active': 'true',
        },
        {
            'first_name': 'Charlie',
            'last_name': 'Brown',
            'email': 'charlie.brown@company.com',
            'phone': '555-0105',
            'department': 'HR',
            'salary': '65000',
            'hire_date': '2022-05-12',
            'active': 'true',
        },
    ]
    
    count = 0
    for emp in employees:
        record = MetadataRecord(
            name=f"{emp['first_name']} {emp['last_name']}",
            schema_id=schema.id,
            tag='employee',
            created_by=user.id,
            raw_data=str(emp)
        )
        db.session.add(record)
        db.session.flush()
        
        # Add field values
        for field_name, value in emp.items():
            field = SchemaField.query.filter_by(
                schema_id=schema.id,
                field_name=field_name,
                is_deleted=False
            ).first()
            
            if field:
                fv = FieldValue(
                    record_id=record.id,
                    schema_field_id=field.id
                )
                set_field_value(fv, value, field.field_type)
                db.session.add(fv)
        
        count += 1
    
    db.session.commit()
    print(f"✅ Created {count} employee records")

def create_product_records(schema):
    """Create sample product records"""
    user = get_user()
    
    products = [
        {
            'product_name': 'Laptop Pro 15',
            'sku': 'LAPP-001',
            'category': 'Electronics',
            'price': '1299.99',
            'quantity_in_stock': '45',
            'in_stock': 'true',
            'supplier': 'TechCorp',
        },
        {
            'product_name': 'USB-C Cable',
            'sku': 'USBC-001',
            'category': 'Accessories',
            'price': '19.99',
            'quantity_in_stock': '250',
            'in_stock': 'true',
            'supplier': 'Cable Inc',
        },
        {
            'product_name': 'Wireless Mouse',
            'sku': 'MOUSE-001',
            'category': 'Accessories',
            'price': '49.99',
            'quantity_in_stock': '120',
            'in_stock': 'true',
            'supplier': 'Peripherals Plus',
        },
        {
            'product_name': '4K Monitor',
            'sku': 'MON-001',
            'category': 'Electronics',
            'price': '599.99',
            'quantity_in_stock': '30',
            'in_stock': 'true',
            'supplier': 'DisplayTech',
        },
        {
            'product_name': 'Mechanical Keyboard',
            'sku': 'KEY-001',
            'category': 'Accessories',
            'price': '149.99',
            'quantity_in_stock': '80',
            'in_stock': 'true',
            'supplier': 'Key Makers',
        },
    ]
    
    count = 0
    for prod in products:
        record = MetadataRecord(
            name=prod['product_name'],
            schema_id=schema.id,
            tag='product',
            created_by=user.id,
            raw_data=str(prod)
        )
        db.session.add(record)
        db.session.flush()
        
        # Add field values
        for field_name, value in prod.items():
            field = SchemaField.query.filter_by(
                schema_id=schema.id,
                field_name=field_name,
                is_deleted=False
            ).first()
            
            if field:
                fv = FieldValue(
                    record_id=record.id,
                    schema_field_id=field.id
                )
                set_field_value(fv, value, field.field_type)
                db.session.add(fv)
        
        count += 1
    
    db.session.commit()
    print(f"✅ Created {count} product records")

def create_project_records(schema):
    """Create sample project records"""
    user = get_user()
    
    today = datetime.now()
    
    projects = [
        {
            'project_name': 'Website Redesign',
            'status': 'In Progress',
            'budget': '50000',
            'start_date': (today - timedelta(days=60)).strftime('%Y-%m-%d'),
            'end_date': (today + timedelta(days=30)).strftime('%Y-%m-%d'),
            'team_lead': 'Jane Smith',
            'team_size': '6',
            'priority': 'High',
        },
        {
            'project_name': 'Mobile App v2',
            'status': 'Planning',
            'budget': '150000',
            'start_date': (today + timedelta(days=10)).strftime('%Y-%m-%d'),
            'end_date': (today + timedelta(days=180)).strftime('%Y-%m-%d'),
            'team_lead': 'John Doe',
            'team_size': '8',
            'priority': 'Critical',
        },
        {
            'project_name': 'Database Migration',
            'status': 'Completed',
            'budget': '35000',
            'start_date': (today - timedelta(days=120)).strftime('%Y-%m-%d'),
            'end_date': (today - timedelta(days=30)).strftime('%Y-%m-%d'),
            'team_lead': 'Alice Williams',
            'team_size': '4',
            'priority': 'High',
        },
        {
            'project_name': 'Security Audit',
            'status': 'In Progress',
            'budget': '25000',
            'start_date': (today - timedelta(days=15)).strftime('%Y-%m-%d'),
            'end_date': (today + timedelta(days=15)).strftime('%Y-%m-%d'),
            'team_lead': 'Charlie Brown',
            'team_size': '3',
            'priority': 'Critical',
        },
    ]
    
    count = 0
    for proj in projects:
        record = MetadataRecord(
            name=proj['project_name'],
            schema_id=schema.id,
            tag='project',
            created_by=user.id,
            raw_data=str(proj)
        )
        db.session.add(record)
        db.session.flush()
        
        # Add field values
        for field_name, value in proj.items():
            field = SchemaField.query.filter_by(
                schema_id=schema.id,
                field_name=field_name,
                is_deleted=False
            ).first()
            
            if field:
                fv = FieldValue(
                    record_id=record.id,
                    schema_field_id=field.id
                )
                set_field_value(fv, value, field.field_type)
                db.session.add(fv)
        
        count += 1
    
    db.session.commit()
    print(f"✅ Created {count} project records")

def main():
    """Main function"""
    print("\n" + "="*70)
    print("🌱 SEEDING SAMPLE DATA INTO POSTGRESQL")
    print("="*70)
    
    try:
        app = create_app()
        
        with app.app_context():
            # Check if user exists
            user = get_user()
            if not user:
                print("❌ Admin user not found. Please run setup_postgres.py first")
                return
            
            print(f"✅ Found admin user: {user.email}\n")
            
            # Create schemas
            print("📋 Creating Schemas...")
            employee_schema = create_employee_schema()
            product_schema = create_product_schema()
            project_schema = create_project_schema()
            
            # Create sample data
            print("\n📊 Creating Sample Records...")
            create_employee_records(employee_schema)
            create_product_records(product_schema)
            create_project_records(project_schema)
            
            print("\n" + "="*70)
            print("✅ SAMPLE DATA SEEDED SUCCESSFULLY!")
            print("="*70)
            print("\n📊 Summary:")
            print("   • 3 Schemas created (Employee, Product, Project)")
            print("   • 5 Employee records created")
            print("   • 5 Product records created")
            print("   • 4 Project records created")
            print("   • Total: 14 sample records")
            print("\n🎉 Database is ready with sample data!")
            print("="*70 + "\n")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
