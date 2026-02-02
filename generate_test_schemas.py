#!/usr/bin/env python3
"""
Schema Test Generator - Creates test schemas with various configurations
Not integrated into backend - standalone utility for testing
"""

import json
import random
from typing import List, Dict, Any
from datetime import datetime, timedelta
import requests


class SchemaTestGenerator:
    """Generate test schemas and data for demonstration"""
    
    def __init__(self, backend_url: str = "http://localhost:5000", token: str = None):
        self.backend_url = backend_url
        self.token = token
        self.session = requests.Session()
        if token:
            self.session.headers.update({"Authorization": f"Bearer {token}"})
    
    @staticmethod
    def generate_random_value(field_type: str) -> Any:
        """Generate random value for field type"""
        generators = {
            'integer': lambda: random.randint(1, 10000),
            'float': lambda: round(random.uniform(1.0, 1000.0), 2),
            'string': lambda: ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=10)),
            'boolean': lambda: random.choice([True, False]),
            'date': lambda: (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d'),
            'datetime': lambda: (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            'array': lambda: [random.randint(1, 100) for _ in range(random.randint(1, 5))],
            'object': lambda: {f"key_{i}": random.randint(1, 100) for i in range(random.randint(1, 3))},
        }
        return generators.get(field_type, lambda: 'unknown')()
    
    @staticmethod
    def generate_test_records(schema_fields: List[Dict], count: int = 10) -> List[Dict]:
        """Generate random test records based on schema"""
        records = []
        for _ in range(count):
            record = {}
            for field in schema_fields:
                field_type = field.get('field_type', 'string')
                record[field['field_name']] = SchemaTestGenerator.generate_random_value(field_type)
            records.append(record)
        return records
    
    @staticmethod
    def create_flexible_schema() -> Dict:
        """Create a schema with many different field types to test flexibility"""
        return {
            "name": "Flexible Test Schema",
            "fields": [
                {"field_name": "id", "field_type": "integer", "constraints": {"unique": True, "required": True}},
                {"field_name": "name", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "description", "field_type": "text", "constraints": {}},
                {"field_name": "price", "field_type": "float", "constraints": {}},
                {"field_name": "is_active", "field_type": "boolean", "constraints": {}},
                {"field_name": "created_at", "field_type": "date", "constraints": {}},
                {"field_name": "last_updated", "field_type": "datetime", "constraints": {}},
                {"field_name": "tags", "field_type": "array", "constraints": {}},
                {"field_name": "metadata", "field_type": "object", "constraints": {}},
                {"field_name": "email", "field_type": "string", "constraints": {}},
            ]
        }
    
    @staticmethod
    def create_complex_hierarchical_schema() -> Dict:
        """Create hierarchical schema with relationships"""
        return {
            "name": "Complex Hierarchical Data",
            "fields": [
                {"field_name": "id", "field_type": "integer", "constraints": {"unique": True, "required": True}},
                {"field_name": "parent_id", "field_type": "integer", "constraints": {}},
                {"field_name": "level", "field_type": "integer", "constraints": {}},
                {"field_name": "title", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "category", "field_type": "string", "constraints": {}},
                {"field_name": "status", "field_type": "string", "constraints": {}},
                {"field_name": "owner_info", "field_type": "object", "constraints": {}},
                {"field_name": "child_count", "field_type": "integer", "constraints": {}},
                {"field_name": "metrics", "field_type": "object", "constraints": {}},
            ]
        }
    
    @staticmethod
    def create_sparse_schema() -> Dict:
        """Create schema with optional fields (sparse data)"""
        return {
            "name": "Sparse Optional Data",
            "fields": [
                {"field_name": "required_id", "field_type": "string", "constraints": {"unique": True, "required": True}},
                {"field_name": "optional_field_1", "field_type": "string", "constraints": {}},
                {"field_name": "optional_field_2", "field_type": "float", "constraints": {}},
                {"field_name": "optional_field_3", "field_type": "date", "constraints": {}},
                {"field_name": "optional_field_4", "field_type": "boolean", "constraints": {}},
                {"field_name": "optional_field_5", "field_type": "array", "constraints": {}},
                {"field_name": "optional_field_6", "field_type": "object", "constraints": {}},
                {"field_name": "optional_field_7", "field_type": "text", "constraints": {}},
                {"field_name": "optional_field_8", "field_type": "integer", "constraints": {}},
            ]
        }
    
    @staticmethod
    def create_time_series_schema() -> Dict:
        """Create time-series data schema"""
        return {
            "name": "Time Series Metrics",
            "fields": [
                {"field_name": "metric_id", "field_type": "string", "constraints": {"unique": True, "required": True}},
                {"field_name": "timestamp", "field_type": "datetime", "constraints": {"required": True}},
                {"field_name": "metric_name", "field_type": "string", "constraints": {}},
                {"field_name": "value", "field_type": "float", "constraints": {}},
                {"field_name": "unit", "field_type": "string", "constraints": {}},
                {"field_name": "min_value", "field_type": "float", "constraints": {}},
                {"field_name": "max_value", "field_type": "float", "constraints": {}},
                {"field_name": "avg_value", "field_type": "float", "constraints": {}},
                {"field_name": "status", "field_type": "string", "constraints": {}},
                {"field_name": "tags", "field_type": "array", "constraints": {}},
            ]
        }


def generate_test_data(schema_name: str) -> List[Dict]:
    """Generate diverse test data based on schema name"""
    generators = {
        "ecommerce": lambda: [
            {
                "order_id": f"ORD-{random.randint(10000, 99999)}",
                "amount": round(random.uniform(10, 1000), 2),
                "status": random.choice(["pending", "processing", "shipped", "delivered"]),
                "items": [{"name": f"item_{i}", "qty": random.randint(1, 10)} for i in range(random.randint(1, 5))],
            }
            for _ in range(10)
        ],
        "users": lambda: [
            {
                "user_id": f"U{random.randint(10000, 99999)}",
                "username": f"user_{random.randint(1000, 9999)}",
                "email": f"user{random.randint(1, 9999)}@example.com",
                "age": random.randint(18, 80),
                "active": random.choice([True, False]),
                "roles": random.sample(["admin", "editor", "viewer", "contributor"], k=random.randint(1, 3)),
                "profile": {"bio": f"Bio {random.randint(1, 1000)}", "avatar": f"avatar_{random.randint(1, 100)}.jpg"},
            }
            for _ in range(10)
        ],
        "products": lambda: [
            {
                "sku": f"SKU-{random.randint(100000, 999999)}",
                "name": f"Product {random.randint(1, 10000)}",
                "price": round(random.uniform(1, 10000), 2),
                "stock": random.randint(0, 1000),
                "category": random.choice(["Electronics", "Clothing", "Food", "Books", "Toys"]),
                "rating": round(random.uniform(1, 5), 1),
                "reviews": random.randint(0, 10000),
                "specs": {"color": random.choice(["Red", "Blue", "Green", "Black", "White"]), "size": random.choice(["S", "M", "L", "XL"])},
            }
            for _ in range(10)
        ],
    }
    return generators.get(schema_name.lower(), lambda: [])()


def main():
    print("=" * 60)
    print("Schema Test Generator")
    print("=" * 60)
    
    print("\n📊 Available Test Schemas:")
    print("1. Flexible Test Schema (many field types)")
    print("2. Complex Hierarchical Data (relationships)")
    print("3. Sparse Optional Data (flexible fields)")
    print("4. Time Series Metrics (temporal data)")
    
    choice = input("\nSelect schema (1-4): ").strip()
    
    schemas = {
        "1": SchemaTestGenerator.create_flexible_schema,
        "2": SchemaTestGenerator.create_complex_hierarchical_schema,
        "3": SchemaTestGenerator.create_sparse_schema,
        "4": SchemaTestGenerator.create_time_series_schema,
    }
    
    if choice not in schemas:
        print("❌ Invalid choice")
        return
    
    schema_def = schemas[choice]()
    record_count = int(input("Number of test records to generate: ") or "10")
    
    print(f"\n📝 Generated Schema: {schema_def['name']}")
    print(f"   Fields: {len(schema_def['fields'])}")
    print(f"   Records: {record_count}")
    
    records = SchemaTestGenerator.generate_test_records(schema_def['fields'], record_count)
    
    output_file = f"test_data_{schema_def['name'].lower().replace(' ', '_')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "schema": schema_def,
            "records": records,
            "generated_at": datetime.now().isoformat()
        }, f, indent=2)
    
    print(f"\n✅ Generated {output_file}")
    print("\nSample record:")
    print(json.dumps(records[0], indent=2))


if __name__ == "__main__":
    main()
