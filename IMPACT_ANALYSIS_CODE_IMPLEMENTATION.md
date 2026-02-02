# Impact Analysis - Code Implementation Details

## Table of Contents
1. [Affected Records Analysis - Implementation](#1-affected-records-analysis---implementation)
2. [Data Migration Analysis - Implementation](#2-data-migration-analysis---implementation)
3. [Validation Conflict Detection - Implementation](#3-validation-conflict-detection---implementation)
4. [Backward Compatibility - Implementation](#4-backward-compatibility---implementation)

---

## 1. Affected Records Analysis - Implementation

### 1.1 Get Total Affected Records

**File**: `flask_backend/app/services/migration_generator.py`

```python
class ImpactAnalyzer:
    def analyze_field_addition(self, schema_id: int, field_def: Dict) -> Dict[str, Any]:
        """
        Analyze how many records will be affected by adding a field
        """
        from ..models import MetadataRecord
        
        # ✅ QUERY 1: Count all records in schema
        record_count = MetadataRecord.query.filter_by(
            schema_id=schema_id
        ).count()
        
        # Calculate performance impact
        estimated_time = record_count * 0.001  # ~1ms per record
        storage_impact = record_count * 0.0001  # ~0.1KB per record
        
        # Determine risk based on record count and field properties
        risk_level = 'low' if not field_def.get('required') else 'medium'
        if record_count > 100000:
            risk_level = 'high' if field_def.get('required') else 'medium'
        
        return {
            'operation': 'add_field',
            'field_name': field_def['name'],
            'field_type': field_def['type'],
            'affected_records': record_count,  # ✅ TOTAL AFFECTED
            'estimated_time_seconds': estimated_time,
            'storage_impact_mb': storage_impact,
            'risk_level': risk_level,
            'requires_default': field_def.get('required', False) and record_count > 0,
        }
```

### 1.2 Get Field Values Count (Removal Analysis)

**File**: `flask_backend/app/services/migration_generator.py`

```python
class ImpactAnalyzer:
    def analyze_field_removal(self, schema_id: int, field_name: str) -> Dict[str, Any]:
        """
        Analyze impact of removing a field:
        - How many values will be lost?
        - How many records have non-null values?
        """
        from ..models import FieldValue
        
        # Find the field
        field = SchemaField.query.filter_by(
            schema_id=schema_id,
            field_name=field_name,
            is_deleted=False
        ).first()
        
        if not field:
            return {'error': 'Field not found'}
        
        # ✅ QUERY 1: Count ALL values stored for this field
        value_count = FieldValue.query.filter_by(
            schema_field_id=field.id
        ).count()
        
        # ✅ QUERY 2: Count NON-NULL values (actual data)
        # Use database-level aggregation for efficiency
        non_null_count = db.session.query(
            db.func.count(FieldValue.id)
        ).filter(
            FieldValue.schema_field_id == field.id,
            db.or_(
                FieldValue.value_text.isnot(None),
                FieldValue.value_int.isnot(None),
                FieldValue.value_float.isnot(None),
                FieldValue.value_bool.isnot(None),
                FieldValue.value_date.isnot(None),
                FieldValue.value_json.isnot(None)
            )
        ).scalar()
        
        # Determine risk level based on data loss
        if non_null_count > 100:
            risk_level = 'critical'  # Large data loss
        elif non_null_count > 0:
            risk_level = 'high'       # Some data loss
        else:
            risk_level = 'low'        # No data loss
        
        return {
            'operation': 'remove_field',
            'field_name': field_name,
            'field_type': field.field_type,
            'affected_values': value_count,      # ✅ TOTAL VALUES
            'non_null_values': non_null_count,   # ✅ DATA VALUES
            'data_loss': non_null_count > 0,
            'risk_level': risk_level,
            'recommendations': [
                '⚠️  CRITICAL: Will lose data!' if non_null_count > 0 else None,
                'Use soft delete instead of hard delete' if non_null_count > 0 else None,
                'Export data before deletion' if non_null_count > 100 else None
            ]
        }
```

### 1.3 API Endpoint for Affected Records

**File**: `flask_backend/app/routes/schemas_dynamic.py`

```python
@schemas_bp.route("/<int:schema_id>/impact/add-field", methods=["POST"])
@jwt_required()
def analyze_add_field_impact(schema_id):
    """
    Analyze impact of adding a field BEFORE applying it
    """
    data = request.get_json() or {}
    field_def = data.get("field")
    
    if not field_def:
        return jsonify({"error": "field definition required"}), 400
    
    # Get impact analysis
    analysis = impact_analyzer.analyze_field_addition(schema_id, field_def)
    
    return jsonify(analysis)


@schemas_bp.route("/<int:schema_id>/impact/remove-field/<field_name>", methods=["GET"])
@jwt_required()
def analyze_remove_field_impact(schema_id, field_name):
    """
    Analyze impact of removing a field BEFORE applying it
    """
    analysis = impact_analyzer.analyze_field_removal(schema_id, field_name)
    return jsonify(analysis)
```

### 1.4 Python Usage Example

```python
# Analyze before making changes
import requests

# Analyze adding a field
response = requests.post(
    'http://localhost:5000/schemas/1/impact/add-field',
    json={
        "field": {
            "name": "new_field",
            "type": "string",
            "required": False
        }
    },
    headers={"Authorization": "Bearer token"}
)

impact = response.json()
print(f"Will affect {impact['affected_records']} records")
print(f"Estimated time: {impact['estimated_time_seconds']:.2f} seconds")
print(f"Risk level: {impact['risk_level']}")

# Analyze removing a field
response = requests.get(
    'http://localhost:5000/schemas/1/impact/remove-field/old_field',
    headers={"Authorization": "Bearer token"}
)

impact = response.json()
print(f"Will lose {impact['non_null_values']} values")
print(f"Data loss: {impact['data_loss']}")
```

---

## 2. Data Migration Analysis - Implementation

### 2.1 Type Compatibility Checking

**File**: `flask_backend/app/services/validation_engine.py`

```python
class ValidationEngine:
    """
    Defines which type conversions are safe
    """
    
    # Type compatibility matrix - what types CAN be converted to
    TYPE_COMPATIBILITY = {
        'string': ['string', 'json', 'array', 'object'],
        'integer': ['integer', 'float', 'string', 'json', 'array', 'object'],
        'float': ['float', 'string', 'json', 'array', 'object'],
        'boolean': ['boolean', 'string', 'json', 'array', 'object'],
        'date': ['date', 'string', 'json', 'array', 'object'],
        'json': ['json', 'string', 'array', 'object'],
        'array': ['array', 'string', 'json', 'object'],
        'object': ['object', 'string', 'json', 'array']
    }
    
    def validate_type_change(
        self,
        field_id: int,
        old_type: str,
        new_type: str
    ) -> List[str]:
        """
        Validate if a type change is safe
        """
        errors = []
        
        # ✅ STEP 1: Check type compatibility matrix
        if new_type not in self.TYPE_COMPATIBILITY.get(old_type, []):
            errors.append(
                f"Cannot convert from '{old_type}' to '{new_type}'. "
                f"Allowed conversions: {', '.join(self.TYPE_COMPATIBILITY.get(old_type, []))}"
            )
            return errors  # Stop here if incompatible
        
        # ✅ STEP 2: Get the field from database
        field = SchemaField.query.get(field_id)
        if not field:
            errors.append(f"Field {field_id} not found")
            return errors
        
        # ✅ STEP 3: Sample conversion testing
        # Test on 100 records to find incompatibilities
        sample_values = FieldValue.query.filter_by(
            schema_field_id=field_id
        ).limit(100).all()  # Test on sample
        
        incompatible_count = 0
        incompatible_examples = []
        
        for value in sample_values:
            current_value = value.get_value()
            if current_value is not None:  # Skip NULL values
                try:
                    # Try to convert the value
                    self._test_conversion(current_value, old_type, new_type)
                except (ValueError, TypeError) as e:
                    incompatible_count += 1
                    if len(incompatible_examples) < 3:  # Collect first 3 examples
                        incompatible_examples.append({
                            'value': str(current_value),
                            'error': str(e)
                        })
        
        # ✅ STEP 4: Extrapolate to total data
        if incompatible_count > 0:
            total_values = FieldValue.query.filter_by(
                schema_field_id=field_id
            ).count()
            
            # Estimate incompatible values in full dataset
            estimated_incompatible = int(
                (incompatible_count / len(sample_values)) * total_values
            )
            
            errors.append(
                f"Found {incompatible_count} incompatible values in sample of {len(sample_values)}. "
                f"Estimated {estimated_incompatible} out of {total_values} total values "
                f"will not convert successfully. Examples: {incompatible_examples}"
            )
        
        return errors
    
    def _test_conversion(self, value: Any, old_type: str, new_type: str):
        """
        Test if a specific value can be converted
        """
        if new_type == 'integer':
            return int(value)
        elif new_type == 'float':
            return float(value)
        elif new_type == 'boolean':
            if isinstance(value, bool):
                return value
            return value.lower() in ('true', '1', 'yes')
        elif new_type == 'date':
            from datetime import datetime
            if isinstance(value, str):
                return datetime.fromisoformat(value)
            return value
        elif new_type in ['json', 'array', 'object', 'string']:
            return str(value)  # Can always convert to string/json
        else:
            return value
```

### 2.2 Migration Script Generation

**File**: `flask_backend/app/services/migration_generator.py`

```python
class MigrationGenerator:
    """
    Generates SQL migration scripts for schema changes
    """
    
    def generate_migration(
        self,
        schema_id: int,
        from_version: int,
        to_version: int,
        dialect: str = 'postgresql'
    ) -> str:
        """
        Generate SQL migration script with data migration steps
        """
        # Get version snapshots
        from_snap = SchemaVersion.query.filter_by(
            schema_id=schema_id,
            version=from_version
        ).first()
        
        to_snap = SchemaVersion.query.filter_by(
            schema_id=schema_id,
            version=to_version
        ).first()
        
        if not from_snap or not to_snap:
            raise ValueError("Version snapshots not found")
        
        # Calculate differences
        diff = self._calculate_diff(from_snap, to_snap)
        
        # Generate script header with comments
        script = self._generate_script_header(
            schema_id, from_version, to_version, diff
        )
        
        # ✅ WRAP IN TRANSACTION for atomicity
        script += "\nBEGIN TRANSACTION;\n\n"
        
        # ✅ Add new fields
        for field_name in diff['added_fields']:
            field_def = next(
                (f for f in to_snap['schema_snapshot']['fields'] 
                 if f['name'] == field_name),
                None
            )
            if field_def:
                script += self._generate_add_field_sql(
                    f"metadata_record_{schema_id}",
                    field_def,
                    dialect
                )
                script += "\n"
        
        # ✅ Modify existing fields (type changes, constraints)
        for field_name, changes in diff['modified_fields'].items():
            if 'type' in changes:  # Type change
                script += self._generate_type_change_sql(
                    f"metadata_record_{schema_id}",
                    field_name,
                    changes['old_type'],
                    changes['new_type'],
                    dialect
                )
                script += "\n"
        
        # ✅ Remove fields (soft delete)
        for field_name in diff['removed_fields']:
            script += f"-- Soft delete field '{field_name}'\n"
            script += f"UPDATE schema_field SET is_deleted = TRUE "
            script += f"WHERE schema_id = {schema_id} AND field_name = '{field_name}';\n\n"
        
        # ✅ Commit transaction
        script += "COMMIT;\n"
        
        return script
    
    def _generate_add_field_sql(self, table_name: str, field_def: Dict, dialect: str) -> str:
        """Generate ADD COLUMN statement"""
        field_name = field_def['name']
        field_type = self._get_sql_type(field_def['type'], dialect)
        default = field_def.get('default')
        
        sql = f"ALTER TABLE {table_name}\n"
        sql += f"ADD COLUMN {field_name} {field_type}"
        
        if default is not None:
            sql += f" DEFAULT {self._format_default(default, field_def['type'])}"
        
        if field_def.get('required'):
            sql += " NOT NULL"
        
        sql += ";\n"
        return sql
    
    def _generate_type_change_sql(
        self,
        table_name: str,
        field_name: str,
        old_type: str,
        new_type: str,
        dialect: str
    ) -> str:
        """Generate type change with data migration"""
        old_sql_type = self._get_sql_type(old_type, dialect)
        new_sql_type = self._get_sql_type(new_type, dialect)
        
        # PostgreSQL syntax
        if dialect == 'postgresql':
            return (
                f"-- Type change: {field_name} {old_type} → {new_type}\n"
                f"ALTER TABLE {table_name}\n"
                f"ALTER COLUMN {field_name} TYPE {new_sql_type}\n"
                f"USING {field_name}::{new_sql_type};\n"
            )
        # MySQL syntax
        elif dialect == 'mysql':
            return (
                f"-- Type change: {field_name} {old_type} → {new_type}\n"
                f"ALTER TABLE {table_name}\n"
                f"MODIFY COLUMN {field_name} {new_sql_type};\n"
            )
        else:
            raise ValueError(f"Unsupported dialect: {dialect}")
    
    def _get_sql_type(self, field_type: str, dialect: str) -> str:
        """Map application types to SQL types"""
        type_map = {
            'string': 'VARCHAR(255)',
            'integer': 'INTEGER',
            'float': 'DOUBLE PRECISION' if dialect == 'postgresql' else 'FLOAT',
            'boolean': 'BOOLEAN',
            'date': 'DATE',
            'json': 'JSONB' if dialect == 'postgresql' else 'JSON',
            'array': 'TEXT[]' if dialect == 'postgresql' else 'JSON',
            'object': 'JSONB' if dialect == 'postgresql' else 'JSON'
        }
        return type_map.get(field_type, 'TEXT')
```

### 2.3 Type Change Impact Analysis

**File**: `flask_backend/app/services/migration_generator.py`

```python
class ImpactAnalyzer:
    def analyze_type_change(
        self,
        schema_id: int,
        field_name: str,
        new_type: str
    ) -> Dict[str, Any]:
        """
        Analyze impact of changing a field's type
        """
        # ✅ STEP 1: Find the field
        field = SchemaField.query.filter_by(
            schema_id=schema_id,
            field_name=field_name,
            is_deleted=False
        ).first()
        
        if not field:
            return {'error': 'Field not found'}
        
        # ✅ STEP 2: Validate type change compatibility
        validator = ValidationEngine()
        validation_errors = validator.validate_type_change(
            field.id, field.field_type, new_type
        )
        
        # ✅ STEP 3: Count affected values
        value_count = FieldValue.query.filter_by(
            schema_field_id=field.id
        ).count()
        
        # ✅ STEP 4: Determine reversibility
        # String type is "reversible" - data can be converted back
        reversible = new_type == 'string'
        
        # ✅ STEP 5: Assess risk
        if validation_errors:
            risk_level = 'high'  # Conversion errors found
        elif value_count > 1000:
            risk_level = 'medium'  # Large dataset
        else:
            risk_level = 'medium'  # Even small conversions need testing
        
        return {
            'operation': 'change_type',
            'field_name': field_name,
            'old_type': field.field_type,
            'new_type': new_type,
            'affected_values': value_count,
            'validation_errors': validation_errors,  # Conversion issues
            'risk_level': risk_level,
            'requires_migration': True,
            'reversible': reversible,
            'recommendations': [
                'Test conversion on sample data first',
                'Backup data before conversion' if value_count > 1000 else None,
                'Consider creating new field instead' if validation_errors else None,
                'Schedule during low-traffic period' if value_count > 10000 else None
            ]
        }
```

---

## 3. Validation Conflict Detection - Implementation

### 3.1 Field Definition Validation

**File**: `flask_backend/app/services/validation_engine.py`

```python
class ValidationEngine:
    SUPPORTED_TYPES = [
        'string', 'integer', 'float', 'boolean', 'date', 'json', 'array', 'object'
    ]
    
    def validate_fields(self, fields: List[Dict[str, Any]]) -> List[str]:
        """
        Validate field definitions BEFORE creating schema
        """
        errors = []
        field_names = set()
        
        for idx, field in enumerate(fields):
            # ✅ CHECK 1: Required 'name' key
            if 'name' not in field:
                errors.append(f"Field {idx}: Missing 'name'")
                continue
            
            field_name = field['name']
            
            # ✅ CHECK 2: Duplicate field names
            if field_name in field_names:
                errors.append(f"Field '{field_name}': Duplicate field name")
            field_names.add(field_name)
            
            # ✅ CHECK 3: Valid field name format
            if not self._is_valid_identifier(field_name):
                errors.append(
                    f"Field '{field_name}': Invalid name. Must be alphanumeric "
                    f"with underscores, starting with letter"
                )
            
            # ✅ CHECK 4: Supported type
            field_type = field.get('type', 'string')
            if field_type not in self.SUPPORTED_TYPES:
                errors.append(
                    f"Field '{field_name}': Unsupported type '{field_type}'. "
                    f"Supported: {', '.join(self.SUPPORTED_TYPES)}"
                )
            
            # ✅ CHECK 5: Constraint format validation
            if 'constraints' in field and field['constraints']:
                constraint_errors = self._validate_constraints(
                    field_name, field_type, field['constraints']
                )
                errors.extend(constraint_errors)
            
            # ✅ CHECK 6: Required field must have default
            if field.get('required', False) and 'default' not in field:
                errors.append(
                    f"Field '{field_name}': Required fields must have a default value "
                    f"for existing records"
                )
        
        return errors
    
    def _is_valid_identifier(self, name: str) -> bool:
        """Check if name is valid (alphanumeric + underscore, starts with letter)"""
        if not name:
            return False
        if not name[0].isalpha() and name[0] != '_':
            return False
        return all(c.isalnum() or c == '_' for c in name)
```

### 3.2 Add Field Validation

**File**: `flask_backend/app/services/validation_engine.py`

```python
class ValidationEngine:
    def validate_add_field(
        self,
        schema_id: int,
        field_def: Dict[str, Any],
        record_count: int
    ) -> List[str]:
        """
        Validate adding a field to schema with existing records
        """
        errors = []
        
        # ✅ STEP 1: Basic field definition validation
        errors.extend(self.validate_fields([field_def]))
        
        if errors:  # Stop if basic validation fails
            return errors
        
        # ✅ STEP 2: Check required field + no default conflict
        if record_count > 0 and field_def.get('required', False):
            if 'default' not in field_def or field_def['default'] is None:
                errors.append(
                    f"Cannot add required field '{field_def['name']}' without default "
                    f"value to schema with {record_count} existing records"
                )
        
        # ✅ STEP 3: Performance warning for large tables
        if record_count > 100000:
            errors.append(
                f"WARNING: Adding field to large schema ({record_count} records). "
                f"This may take time and impact performance. "
                f"Schedule during low-traffic period."
            )
        
        return errors
```

### 3.3 Constraint Validation

**File**: `flask_backend/app/services/validation_engine.py`

```python
class ValidationEngine:
    def validate_constraints(
        self,
        field_id: int,
        constraints: Dict[str, Any]
    ) -> List[str]:
        """
        Validate constraint definitions and check against existing data
        """
        errors = []
        
        # ✅ STEP 1: Find the field
        field = SchemaField.query.get(field_id)
        if not field:
            errors.append(f"Field {field_id} not found")
            return errors
        
        # ✅ STEP 2: Validate constraint format
        constraint_errors = self._validate_constraints(
            field.field_name, field.field_type, constraints
        )
        errors.extend(constraint_errors)
        
        if errors:
            return errors  # Stop if format is invalid
        
        # ✅ STEP 3: Check existing data against constraints
        values = FieldValue.query.filter_by(schema_field_id=field_id).all()
        violations = []
        
        for value in values:
            current_value = value.get_value()
            if current_value is not None:  # Skip NULL values
                violation = self._check_constraint_violation(
                    current_value, field.field_type, constraints
                )
                if violation:
                    violations.append(f"Record {value.record_id}: {violation}")
        
        # ✅ STEP 4: Report violations
        if violations:
            errors.append(
                f"{len(violations)} records violate new constraints. "
                f"First violations: {', '.join(violations[:5])}"
            )
        
        return errors
    
    def _validate_constraints(
        self,
        field_name: str,
        field_type: str,
        constraints: Dict[str, Any]
    ) -> List[str]:
        """Validate constraint definition format"""
        errors = []
        
        for constraint_type, constraint_value in constraints.items():
            # Min/Max only for numeric types
            if constraint_type in ['min', 'max']:
                if field_type not in ['integer', 'float']:
                    errors.append(
                        f"Field '{field_name}': {constraint_type} constraint "
                        f"only valid for numeric types"
                    )
            
            # Length only for string types
            elif constraint_type == 'length':
                if field_type not in ['string', 'array']:
                    errors.append(
                        f"Field '{field_name}': length constraint "
                        f"only valid for string/array types"
                    )
            
            # Pattern only for string types
            elif constraint_type == 'pattern':
                if field_type != 'string':
                    errors.append(
                        f"Field '{field_name}': pattern constraint "
                        f"only valid for string types"
                    )
                # Validate regex
                try:
                    import re
                    re.compile(constraint_value)
                except re.error:
                    errors.append(
                        f"Field '{field_name}': Invalid regex pattern"
                    )
        
        return errors
    
    def _check_constraint_violation(
        self,
        value: Any,
        field_type: str,
        constraints: Dict[str, Any]
    ) -> Optional[str]:
        """Check if a value violates constraints"""
        
        # Min constraint
        if 'min' in constraints:
            if value < constraints['min']:
                return f"Value {value} violates min constraint {constraints['min']}"
        
        # Max constraint
        if 'max' in constraints:
            if value > constraints['max']:
                return f"Value {value} violates max constraint {constraints['max']}"
        
        # Length constraint
        if 'length' in constraints:
            if len(str(value)) > constraints['length']:
                return f"Length {len(str(value))} exceeds constraint {constraints['length']}"
        
        # Pattern constraint
        if 'pattern' in constraints:
            import re
            if not re.match(constraints['pattern'], str(value)):
                return f"Value '{value}' doesn't match pattern {constraints['pattern']}"
        
        return None
```

---

## 4. Backward Compatibility - Implementation

### 4.1 Type Reversibility

**File**: `flask_backend/app/services/migration_generator.py`

```python
class ImpactAnalyzer:
    def analyze_type_change(self, schema_id: int, field_name: str, new_type: str):
        # ...
        
        # ✅ Type is reversible if it can be converted back
        reversible = new_type == 'string'
        
        # String type is reversible because:
        # - All types can be converted TO string
        # - You can always parse strings back to original types
        # - No information is lost in string representation
        
        return {
            'reversible': reversible,
            'recommendations': [
                'Change is reversible - can undo if needed' if reversible 
                else 'Change may not be reversible',
                'Backup data before conversion'
            ]
        }
```

### 4.2 Soft Delete Support

**File**: `flask_backend/app/models.py`

```python
class SchemaField(db.Model):
    """Schema field with soft delete support"""
    __tablename__ = 'schema_field'
    
    id = db.Column(db.Integer, primary_key=True)
    schema_id = db.Column(db.Integer, db.ForeignKey('schema_model.id'))
    field_name = db.Column(db.String(255), nullable=False)
    field_type = db.Column(db.String(50), nullable=False)
    is_deleted = db.Column(db.Boolean, default=False)  # ✅ SOFT DELETE
    is_required = db.Column(db.Boolean, default=False)
    description = db.Column(db.Text)
    constraints = db.Column(db.JSON, nullable=True)
    order_index = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())


# Usage:
def remove_field_soft(schema_id: int, field_name: str):
    """Remove field by soft delete"""
    field = SchemaField.query.filter_by(
        schema_id=schema_id,
        field_name=field_name
    ).first()
    
    field.is_deleted = True  # Mark as deleted, don't remove
    db.session.commit()
    
    # Benefits:
    # - Data is preserved for recovery
    # - Legacy code still sees the field
    # - Can be undeleted later
    # - Backward compatible
```

### 4.3 Schema Versioning

**File**: `flask_backend/app/models.py`

```python
class SchemaVersion(db.Model):
    """Track schema evolution"""
    __tablename__ = 'schema_version'
    
    id = db.Column(db.Integer, primary_key=True)
    schema_id = db.Column(db.Integer, db.ForeignKey('schema_model.id'))
    version = db.Column(db.Integer)  # Version number
    schema_snapshot = db.Column(db.JSON)  # Complete schema at this version
    change_description = db.Column(db.Text)
    changed_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=db.func.now())
    
    # Benefits:
    # - Track what changed and when
    # - Know who made the change
    # - Can rollback to previous versions
    # - Backward compatibility reference
```

### 4.4 Version Comparison

**File**: `flask_backend/app/services/schema_version_control.py`

```python
class SchemaVersionControl:
    def compare_versions(self, version1: SchemaVersion, version2: SchemaVersion) -> Dict:
        """
        Compare two schema versions to understand changes
        Helps identify backward compatibility issues
        """
        snap1 = version1.schema_snapshot
        snap2 = version2.schema_snapshot
        
        fields1 = {f['name']: f for f in snap1['fields']}
        fields2 = {f['name']: f for f in snap2['fields']}
        
        # Find changes
        added_fields = set(fields2.keys()) - set(fields1.keys())
        removed_fields = set(fields1.keys()) - set(fields2.keys())
        modified_fields = {}
        
        for field_name in set(fields1.keys()) & set(fields2.keys()):
            if fields1[field_name] != fields2[field_name]:
                modified_fields[field_name] = {
                    'old': fields1[field_name],
                    'new': fields2[field_name]
                }
        
        return {
            'added_fields': list(added_fields),
            'removed_fields': list(removed_fields),
            'modified_fields': modified_fields,
            'backward_compatible': (
                len(removed_fields) == 0 and  # No removals
                not any(  # No required changes
                    m['new'].get('required', False) 
                    for m in modified_fields.values()
                )
            )
        }
```

---

## Summary Table

| Condition | Key Implementation | Database Queries |
|-----------|------------------|------------------|
| **Affected Records** | Count MetadataRecord by schema_id | `COUNT(MetadataRecord) WHERE schema_id = ?` |
| **Field Values** | Count FieldValue by field_id, separate null/non-null | `COUNT(FieldValue)` with null checks |
| **Type Compatibility** | TYPE_COMPATIBILITY matrix with sample testing | Sample 100 records, extrapolate |
| **Validation Conflicts** | Pre-flight validation against schema definition | Multiple validation functions |
| **Backward Compatibility** | Soft delete + versioning + type reversibility | is_deleted flag, SchemaVersion table |
| **Data Migration** | SQL generation with transaction wrapping | Generated migration scripts |
