#!/usr/bin/env python3
"""
Data Validator & Test Runner - Validates schemas and tests data imports
Standalone utility for testing data quality and schema compatibility
"""

import json
import csv
import sys
from typing import Dict, List, Any, Tuple
from datetime import datetime
import traceback


class DataValidator:
    """Validate data against schema definitions"""
    
    FIELD_TYPE_VALIDATORS = {
        'integer': lambda x: isinstance(x, int) and not isinstance(x, bool),
        'float': lambda x: isinstance(x, (int, float)) and not isinstance(x, bool),
        'string': lambda x: isinstance(x, str),
        'text': lambda x: isinstance(x, str),
        'boolean': lambda x: isinstance(x, bool),
        'date': lambda x: isinstance(x, str) and len(x) == 10,  # YYYY-MM-DD
        'datetime': lambda x: isinstance(x, str),
        'timestamp': lambda x: isinstance(x, str),
        'array': lambda x: isinstance(x, list),
        'json': lambda x: isinstance(x, (dict, list)),
        'object': lambda x: isinstance(x, dict),
    }
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.errors = []
        self.warnings = []
    
    def validate_record(self, record: Dict, schema_fields: List[Dict]) -> Tuple[bool, List[str]]:
        """Validate single record against schema"""
        issues = []
        
        for field in schema_fields:
            field_name = field['field_name']
            field_type = field['field_type']
            constraints = field.get('constraints', {})
            value = record.get(field_name)
            
            # Check required constraint
            if constraints.get('required', False) and value is None:
                issues.append(f"Field '{field_name}' is required but missing")
                continue
            
            # Skip validation for None values if not required
            if value is None:
                continue
            
            # Type validation
            validator = self.FIELD_TYPE_VALIDATORS.get(field_type)
            if validator and not validator(value):
                issues.append(f"Field '{field_name}': expected {field_type}, got {type(value).__name__}")
            
            # Unique constraint (would need database to fully validate)
            if constraints.get('unique'):
                pass  # Can only be validated with full dataset
            
            # Min/max constraints
            if isinstance(value, (int, float)):
                if 'min' in constraints and value < constraints['min']:
                    issues.append(f"Field '{field_name}': value {value} < minimum {constraints['min']}")
                if 'max' in constraints and value > constraints['max']:
                    issues.append(f"Field '{field_name}': value {value} > maximum {constraints['max']}")
            
            # Enum constraint
            if 'enum' in constraints and value not in constraints['enum']:
                issues.append(f"Field '{field_name}': value '{value}' not in allowed values {constraints['enum']}")
            
            # Pattern constraint (regex)
            if 'pattern' in constraints:
                import re
                if not re.match(constraints['pattern'], str(value)):
                    issues.append(f"Field '{field_name}': value '{value}' does not match pattern {constraints['pattern']}")
        
        # Check for extra fields
        schema_field_names = {f['field_name'] for f in schema_fields}
        extra_fields = set(record.keys()) - schema_field_names
        if extra_fields:
            issues.append(f"Extra fields not in schema: {extra_fields}")
        
        return len(issues) == 0, issues
    
    def validate_dataset(self, records: List[Dict], schema_fields: List[Dict]) -> Dict[str, Any]:
        """Validate entire dataset"""
        results = {
            "total_records": len(records),
            "valid_records": 0,
            "invalid_records": 0,
            "issues": [],
            "field_statistics": {},
            "data_quality_score": 0.0
        }
        
        for idx, record in enumerate(records):
            is_valid, issues = self.validate_record(record, schema_fields)
            if is_valid:
                results["valid_records"] += 1
            else:
                results["invalid_records"] += 1
                results["issues"].append({
                    "record_index": idx,
                    "errors": issues
                })
        
        # Calculate data quality score
        results["data_quality_score"] = (results["valid_records"] / len(records) * 100) if records else 0
        
        # Collect field statistics
        for field in schema_fields:
            field_name = field['field_name']
            field_type = field['field_type']
            values = [r.get(field_name) for r in records]
            null_count = sum(1 for v in values if v is None)
            
            results["field_statistics"][field_name] = {
                "type": field_type,
                "total": len(records),
                "null_count": null_count,
                "null_percentage": (null_count / len(records) * 100) if records else 0,
                "filled": len(records) - null_count
            }
        
        return results
    
    @staticmethod
    def load_json_data(filepath: str) -> Tuple[List[Dict], bool]:
        """Load JSON data file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
                if isinstance(data, dict) and 'records' in data:
                    return data['records'], True
                elif isinstance(data, list):
                    return data, True
                else:
                    return [], False
        except Exception as e:
            print(f"❌ Error loading JSON: {e}")
            return [], False
    
    @staticmethod
    def load_csv_data(filepath: str) -> Tuple[List[Dict], bool]:
        """Load CSV data file"""
        try:
            with open(filepath, 'r') as f:
                reader = csv.DictReader(f)
                records = list(reader)
                return records, True
        except Exception as e:
            print(f"❌ Error loading CSV: {e}")
            return [], False
    
    @staticmethod
    def load_ndjson_data(filepath: str) -> Tuple[List[Dict], bool]:
        """Load NDJSON (newline-delimited JSON) data file"""
        try:
            records = []
            with open(filepath, 'r') as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))
            return records, True
        except Exception as e:
            print(f"❌ Error loading NDJSON: {e}")
            return [], False


def print_report(validation_result: Dict[str, Any], schema_name: str):
    """Print formatted validation report"""
    print("\n" + "=" * 70)
    print(f"VALIDATION REPORT - {schema_name}")
    print("=" * 70)
    
    print(f"\n📊 Overall Results:")
    print(f"   Total Records: {validation_result['total_records']}")
    print(f"   Valid: {validation_result['valid_records']} ✅")
    print(f"   Invalid: {validation_result['invalid_records']} ❌")
    print(f"   Data Quality Score: {validation_result['data_quality_score']:.1f}%")
    
    if validation_result['issues']:
        print(f"\n⚠️  Issues Found ({len(validation_result['issues'])}):")
        for issue in validation_result['issues'][:10]:  # Show first 10
            print(f"   Record #{issue['record_index']}:")
            for error in issue['errors'][:3]:  # Show first 3 errors per record
                print(f"      - {error}")
        if len(validation_result['issues']) > 10:
            print(f"   ... and {len(validation_result['issues']) - 10} more issues")
    
    print(f"\n📋 Field Statistics:")
    for field_name, stats in validation_result['field_statistics'].items():
        print(f"   {field_name}:")
        print(f"      Type: {stats['type']}")
        print(f"      Filled: {stats['filled']}/{stats['total']} ({100 - stats['null_percentage']:.1f}%)")
        if stats['null_percentage'] > 0:
            print(f"      Nulls: {stats['null_count']} ({stats['null_percentage']:.1f}%)")


def main():
    print("=" * 70)
    print("Data Validator & Schema Tester")
    print("=" * 70)
    
    print("\n📁 Supported File Formats: JSON, CSV, NDJSON")
    print("Usage: python3 data_validator.py <data_file> <schema_file>")
    print("\nExample:")
    print("  python3 data_validator.py data.json schema.json")
    print("  python3 data_validator.py employees.csv employee_schema.json")
    print("  python3 data_validator.py sensors.ndjson sensors_schema.json")
    
    if len(sys.argv) < 3:
        print("\n💡 Interactive Mode:")
        data_file = input("\nData file path: ").strip()
        schema_file = input("Schema file path: ").strip()
    else:
        data_file = sys.argv[1]
        schema_file = sys.argv[2]
    
    # Load schema
    try:
        with open(schema_file, 'r') as f:
            schema_data = json.load(f)
            if isinstance(schema_data, dict) and 'fields' in schema_data:
                schema_fields = schema_data['fields']
                schema_name = schema_data.get('name', 'Unknown')
            else:
                schema_fields = schema_data
                schema_name = "Unknown"
    except Exception as e:
        print(f"❌ Error loading schema: {e}")
        return
    
    # Load data based on file extension
    validator = DataValidator(verbose=True)
    file_ext = data_file.split('.')[-1].lower()
    
    if file_ext == 'json':
        records, success = validator.load_json_data(data_file)
    elif file_ext == 'csv':
        records, success = validator.load_csv_data(data_file)
    elif file_ext == 'ndjson':
        records, success = validator.load_ndjson_data(data_file)
    else:
        print(f"❌ Unsupported file format: {file_ext}")
        return
    
    if not success or not records:
        print(f"❌ Failed to load data from {data_file}")
        return
    
    print(f"\n✅ Loaded {len(records)} records")
    print(f"✅ Schema has {len(schema_fields)} fields")
    
    # Validate dataset
    print("\n🔍 Validating data...")
    result = validator.validate_dataset(records, schema_fields)
    
    # Print report
    print_report(result, schema_name)
    
    # Save report to file
    report_file = f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "schema_name": schema_name,
            "data_file": data_file,
            "validation_result": result
        }, f, indent=2)
    
    print(f"\n💾 Report saved to: {report_file}")


if __name__ == "__main__":
    main()
