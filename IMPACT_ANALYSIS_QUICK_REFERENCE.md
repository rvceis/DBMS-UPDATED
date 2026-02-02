# Impact Analysis System - Quick Reference

## Pre-Change Analysis Checklist

### Before ANY Schema Change:

```
□ Affected Records Analysis
  ├─ Total records in schema: COUNT(MetadataRecord)
  ├─ Total field values: COUNT(FieldValue)
  └─ Non-null values: COUNT WHERE value_* IS NOT NULL

□ Data Migration Analysis
  ├─ Type compatibility check: TYPE_COMPATIBILITY[old_type]
  ├─ Sample conversion test: Test 100 sample records
  ├─ Incompatibility estimation: (incompatible/sample) * total
  └─ Migration script generation: SQL with transaction wrapper

□ Validation Conflict Detection
  ├─ Field name validity: [a-z_][a-z0-9_]*
  ├─ Duplicate names: Check all fields
  ├─ Required field + default: Required must have default if records exist
  ├─ Type support: Check SUPPORTED_TYPES list
  ├─ Constraint validity: Format + existing data violations
  └─ Performance warnings: Record count > 100,000

□ Backward Compatibility Review
  ├─ Type reversibility: Is conversion reversible?
  ├─ Soft delete option: Use is_deleted for deprecation
  ├─ Version history: Track schema evolution
  ├─ API stability: Ensure consumers aren't broken
  └─ Rollback capability: Can change be reverted?
```

---

## Impact Analysis API Responses

### Add Field Impact
```json
{
  "operation": "add_field",
  "field_name": "string",
  "field_type": "string",
  "affected_records": 5234,
  "estimated_time_seconds": 5.234,
  "storage_impact_mb": 0.5234,
  "risk_level": "low|medium|high|critical",
  "requires_default": true,
  "recommendations": ["..."]
}
```

### Remove Field Impact
```json
{
  "operation": "remove_field",
  "field_name": "string",
  "field_type": "string",
  "affected_values": 3000,
  "non_null_values": 2850,
  "data_loss": true,
  "risk_level": "low|medium|high|critical",
  "recommendations": ["..."]
}
```

### Change Type Impact
```json
{
  "operation": "change_type",
  "field_name": "string",
  "old_type": "string",
  "new_type": "string",
  "affected_values": 10000,
  "validation_errors": ["..."],
  "risk_level": "low|medium|high|critical",
  "requires_migration": true,
  "reversible": true,
  "recommendations": ["..."]
}
```

---

## Risk Level Assessment

### Risk Scoring
```
LOW        → No existing data affected / Optional field / Safe conversion
MEDIUM     → Some data affected / Required field / Type conversion
HIGH       → Many records affected / Data loss possible / Validation errors
CRITICAL   → Data loss imminent / >100 records with non-null values / Incompatible conversion
```

---

## Type Compatibility Matrix

```
FROM STRING  → to: string, json, array, object
FROM INTEGER → to: integer, float, string, json, array, object
FROM FLOAT   → to: float, string, json, array, object
FROM BOOLEAN → to: boolean, string, json, array, object
FROM DATE    → to: date, string, json, array, object
FROM JSON    → to: json, string, array, object
FROM ARRAY   → to: array, string, json, object
FROM OBJECT  → to: object, string, json, array
```

---

## Validation Rules

### Field Definitions
- **Name**: Must match `[a-z_][a-z0-9_]*` (alphanumeric + underscore, starts with letter)
- **Type**: Must be in SUPPORTED_TYPES list
- **Required + Existing Records**: Must have default value
- **Constraints**: Must match field type and not violate existing data

### Adding Fields
- **Required + Existing Records**: Must specify default
- **Performance**: Warn if >100,000 records

### Removing Fields
- **Data Loss**: Warn if non-null values exist
- **Alternative**: Use soft delete (is_deleted=True)

### Changing Types
- **Compatibility**: Must be in TYPE_COMPATIBILITY matrix
- **Sample Testing**: Test on 100 records first
- **Conversion Errors**: Report estimated total incompatible values

### Constraint Changes
- **Format Validation**: Check constraint definition syntax
- **Data Validation**: Check all existing values against new constraints
- **Violation Report**: List records that violate constraints

---

## Code Locations

| Function | File | Purpose |
|----------|------|---------|
| `analyze_field_addition()` | migration_generator.py | Count affected records, estimate impact |
| `analyze_field_removal()` | migration_generator.py | Count data loss risk |
| `analyze_type_change()` | migration_generator.py | Test conversion, estimate incompatibilities |
| `validate_type_change()` | validation_engine.py | Sample data testing |
| `validate_fields()` | validation_engine.py | Field definition validation |
| `validate_add_field()` | validation_engine.py | Add field to existing schema |
| `validate_constraints()` | validation_engine.py | Constraint validation & data testing |
| `modify_field()` | schema_manager.py | Execute field modification with validation |
| `generate_migration()` | migration_generator.py | Generate SQL migration script |

---

## API Endpoints

### Impact Analysis Endpoints
```
POST   /schemas/<id>/impact/add-field
       Body: {field: {name, type, required, default?, constraints?}}
       Returns: Impact analysis with affected_records, risk_level, recommendations

GET    /schemas/<id>/impact/remove-field/<field_name>
       Returns: Impact analysis with affected_values, non_null_values, data_loss warning

POST   /schemas/<id>/impact/change-type/<field_name>
       Body: {new_type: string}
       Returns: Impact analysis with validation_errors, reversibility, recommendations
```

### Schema Modification Endpoints
```
POST   /schemas/<id>/fields
       Body: {field definition}
       First calls impact analysis, then applies if valid

PUT    /schemas/<id>/fields/<field_name>
       Body: {type?, required?, constraints?, description?}
       First validates changes, then applies if valid

DELETE /schemas/<id>/fields/<field_name>
       Query: soft=true (default) or soft=false (hard delete)
       First analyzes impact, then applies soft/hard delete
```

---

## Best Practices

1. **Always Review Impact Analysis**
   - Check affected_records count
   - Review data_loss warnings
   - Read recommendations carefully

2. **Test Large Migrations**
   - Sample data testing (100 records) gives good estimate
   - Test on staging environment first
   - Monitor conversion errors

3. **Use Soft Deletes**
   - Instead of removing fields, mark as `is_deleted=True`
   - Preserves data for recovery
   - Maintains backward compatibility
   - Version history tracks deprecation

4. **Provide Defaults**
   - Required fields added to existing schema need defaults
   - Apply to all existing records automatically
   - Recommended for optional fields too

5. **Monitor Performance**
   - Large schema modifications (>100,000 records) warned
   - Schedule during low-traffic periods
   - Use transactions to ensure atomicity

6. **Maintain Version History**
   - Schema versions track all changes
   - Allows rollback if needed
   - Documents migration history

---

## Example Workflows

### Scenario 1: Safe Field Addition
```
Request: Add "created_at" field (type: date, not required)

Impact Analysis:
  ├─ affected_records: 5000
  ├─ risk_level: "low"
  ├─ requires_default: false
  └─ recommendations: ["Add during low-traffic period"]

Action: Apply immediately (low risk)
```

### Scenario 2: Risky Field Removal
```
Request: Remove "email" field

Impact Analysis:
  ├─ affected_values: 3000
  ├─ non_null_values: 2987
  ├─ data_loss: true
  ├─ risk_level: "high"
  └─ recommendations: ["Use soft delete", "Export data"]

Decision: Use soft delete instead
  └─ is_deleted = true
  └─ Data preserved, API can filter it out
```

### Scenario 3: Type Migration
```
Request: Change "price" from string to float

Impact Analysis:
  ├─ affected_values: 10000
  ├─ validation_errors: [] (empty, all convertible)
  ├─ risk_level: "medium"
  ├─ reversible: true
  └─ recommendations: ["Backup before conversion"]

Action: Proceed with migration script
  └─ BEGIN TRANSACTION
  └─ ALTER COLUMN price TYPE float USING price::float
  └─ COMMIT
```

### Scenario 4: Constraint Violation
```
Request: Add constraint "price > 0" to numeric field

Impact Analysis:
  ├─ validation_errors: ["5 records have price <= 0"]
  ├─ risk_level: "high"
  └─ recommendations: ["Clean data before adding constraint"]

Decision: Fix data first
  └─ UPDATE records WHERE price <= 0
  └─ Then add constraint
```
