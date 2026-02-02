# Impact Analysis System - Visual Diagrams

## 1. System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                      USER REQUEST                                    │
│              (Schema Change Request)                                 │
└────────────────────────┬────────────────────────────────────────────┘
                         │
                         ▼
        ┌────────────────────────────────────┐
        │  IMPACT ANALYSIS LAYER             │
        │  (Pre-flight checks)               │
        └────────────┬───────────────────────┘
                     │
        ┌────────────┴──────────────────────────────────────┐
        │                                                    │
        ▼                                                    ▼
┌──────────────────────┐                    ┌───────────────────────┐
│ AFFECTED RECORDS     │                    │ DATA MIGRATION        │
│ ANALYSIS             │                    │ ANALYSIS              │
│                      │                    │                       │
│ • Record count       │                    │ • Type compatibility  │
│ • Value count        │                    │ • Sample testing      │
│ • Non-null count     │                    │ • Incompatibility est │
│ • Data loss risk     │                    │ • Migration script    │
└─────────────┬────────┘                    └───────────┬───────────┘
              │                                         │
              └──────────────────┬──────────────────────┘
                                 │
                    ┌────────────┴──────────────┐
                    │                           │
                    ▼                           ▼
        ┌───────────────────────┐   ┌───────────────────────┐
        │ VALIDATION CONFLICT   │   │ BACKWARD COMPATIBILITY│
        │ DETECTION             │   │ ANALYSIS              │
        │                       │   │                       │
        │ • Field format        │   │ • Type reversibility  │
        │ • Type support        │   │ • Soft delete option  │
        │ • Constraint format   │   │ • Version tracking    │
        │ • Data violations     │   │ • Rollback capability │
        │ • Required defaults   │   │                       │
        └───────────┬───────────┘   └───────────┬───────────┘
                    │                           │
                    └──────────────┬────────────┘
                                   │
                                   ▼
                    ┌──────────────────────────┐
                    │  IMPACT ANALYSIS REPORT  │
                    │                          │
                    │ • Affected count         │
                    │ • Data loss warning      │
                    │ • Validation errors      │
                    │ • Risk level (L/M/H/C)   │
                    │ • Recommendations        │
                    └──────────────┬───────────┘
                                   │
                    ┌──────────────┴──────────────┐
                    │                             │
                    ▼                             ▼
            ┌──────────────┐            ┌──────────────┐
            │   REJECT     │            │  APPROVE     │
            │   CHANGE     │            │  CHANGE      │
            └──────────────┘            └──────────┬───┘
                                                   │
                                                   ▼
                        ┌──────────────────────────────────────┐
                        │  SCHEMA MODIFICATION LAYER           │
                        │  (Apply changes)                     │
                        │                                      │
                        │ • Update schema definition           │
                        │ • Execute migrations                 │
                        │ • Maintain version history           │
                        │ • Log all changes                    │
                        └──────────────────────────────────────┘
```

---

## 2. Impact Analysis Decision Tree

```
                      Schema Change Request
                              │
                              ▼
                    ┌─────────────────────┐
                    │ What operation?     │
                    └────┬────────┬───┬───┘
                         │        │   │
          ┌──────────────┘        │   └──────────────┐
          ▼                        ▼                  ▼
      ADD FIELD              MODIFY FIELD         REMOVE FIELD
          │                        │                  │
          ▼                        ▼                  ▼
    Check field def       Check type change   Analyze data loss
    · Name format         · Compatibility     · Non-null count
    · Type valid          · Sample test       · Risk level
    · Constraints         · Errors            · Soft vs hard
          │                        │                  │
          ▼                        ▼                  ▼
    Count affected        Count affected     Count affected
    records               values             values
          │                        │                  │
          ▼                        ▼                  ▼
    Risk = Low/Medium     Risk = Medium/High  Risk = Low/High/Critical
    (unless required)     (if errors)         (if non-null > 0)
          │                        │                  │
          ▼                        ▼                  ▼
    Recommend:            Recommend:         Recommend:
    · Default value       · Backup first     · Soft delete
    · Off-peak time       · Test first       · Export data
    · Migration steps     · Reversibility    · Backup first
          │                        │                  │
          └────────────┬───────────┴──────────────────┘
                       │
                       ▼
              ┌─────────────────────┐
              │ User Reviews        │
              │ & Approves          │
              └────────────┬────────┘
                           │
              ┌────────────┴────────────┐
              ▼                         ▼
          APPROVE                   REJECT
              │                         │
              ▼                         ▼
         Apply Change         Return to user
         Update Schema
         Log Version
         Notify User
```

---

## 3. Data Flow: Affected Records Analysis

```
┌──────────────────────────────────────────────────┐
│ User: "What happens if I remove this field?"     │
└──────────────┬───────────────────────────────────┘
               │
               ▼
    ┌──────────────────────┐
    │ ImpactAnalyzer       │
    │.analyze_field_removal│
    └──────────┬───────────┘
               │
               ▼
    ┌──────────────────────────────────────────────┐
    │ Query 1: Find field                          │
    │ SELECT * FROM schema_field                   │
    │ WHERE schema_id=? AND field_name=?           │
    └──────────────┬───────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────┐
    │ Query 2: Count ALL field values              │
    │ SELECT COUNT(*) FROM field_value             │
    │ WHERE schema_field_id=?                      │
    │ Result: total_values = 3000                  │
    └──────────────┬───────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────┐
    │ Query 3: Count NON-NULL field values         │
    │ SELECT COUNT(*) FROM field_value             │
    │ WHERE schema_field_id=?                      │
    │   AND (value_text IS NOT NULL                │
    │        OR value_int IS NOT NULL              │
    │        OR value_float IS NOT NULL ...)       │
    │ Result: non_null_values = 2850               │
    └──────────────┬───────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────┐
    │ Calculate Risk Level                         │
    │ if non_null > 100: risk = "critical"         │
    │ elif non_null > 0: risk = "high"             │
    │ else: risk = "low"                           │
    │                                              │
    │ Result: risk_level = "high"                  │
    └──────────────┬───────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────┐
    │ Return Impact Report                         │
    │ {                                            │
    │   "operation": "remove_field",               │
    │   "field_name": "email",                     │
    │   "affected_values": 3000,                   │
    │   "non_null_values": 2850,                   │
    │   "data_loss": true,                         │
    │   "risk_level": "high",                      │
    │   "recommendations": [...]                   │
    │ }                                            │
    └──────────────┬───────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────┐
    │ User receives detailed impact analysis      │
    │ and makes informed decision                 │
    └──────────────────────────────────────────────┘
```

---

## 4. Data Flow: Type Conversion Validation

```
┌────────────────────────────────────────────────────────┐
│ User: "Can I change 'price' from string to float?"     │
└───────────────┬────────────────────────────────────────┘
                │
                ▼
    ┌──────────────────────────────┐
    │ ValidationEngine             │
    │.validate_type_change()       │
    └──────────────┬───────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────────┐
    │ Step 1: Check Type Compatibility Matrix         │
    │                                                   │
    │ 'string' can convert to:                         │
    │   ['string', 'json', 'array', 'object']          │
    │                                                   │
    │ new_type='float' NOT in allowed list             │
    │ ERROR: "Cannot convert string → float"           │
    │                                                   │
    │ Result: validation_errors = [error]              │
    └──────────────┬───────────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────────┐
    │ Step 2: Sample Data Conversion Test              │
    │                                                   │
    │ SELECT * FROM field_value                        │
    │ WHERE schema_field_id=? LIMIT 100;               │
    │ Result: sample_values = [100 records]            │
    └──────────────┬───────────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────────┐
    │ Step 3: Test Each Sample Value                   │
    │                                                   │
    │ For each value in sample:                        │
    │   try:                                           │
    │     converted = float(value)  # Convert          │
    │   except ValueError:                             │
    │     incompatible_count += 1                      │
    │                                                   │
    │ incompatible_count = 3 (out of 100)              │
    └──────────────┬───────────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────────┐
    │ Step 4: Extrapolate to Total Dataset            │
    │                                                   │
    │ total_values = 10000                             │
    │ incompatible_ratio = 3/100 = 0.03                │
    │ estimated_incompatible = 0.03 * 10000 = 300      │
    │                                                   │
    │ Result: "300 out of 10000 values will fail"      │
    └──────────────┬───────────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────────┐
    │ Step 5: Assess Risk                              │
    │                                                   │
    │ if validation_errors: risk_level = "high"        │
    │ Result: risk_level = "high"                      │
    └──────────────┬───────────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────────┐
    │ Return Impact Report                             │
    │ {                                                │
    │   "operation": "change_type",                    │
    │   "field_name": "price",                         │
    │   "old_type": "string",                          │
    │   "new_type": "float",                           │
    │   "affected_values": 10000,                      │
    │   "validation_errors": ["...300 values fail..."],│
    │   "risk_level": "high",                          │
    │   "reversible": false,                           │
    │   "recommendations": [                           │
    │     "Clean data before conversion",              │
    │     "Consider creating new field"                │
    │   ]                                              │
    │ }                                                │
    └──────────────┬───────────────────────────────────┘
                   │
                   ▼
    ┌──────────────────────────────────────────────────┐
    │ User sees: "High risk! 300 values won't convert" │
    │ User can:                                        │
    │   - Clean data first, then retry                 │
    │   - Create new field instead                     │
    │   - Export data before conversion                │
    └──────────────────────────────────────────────────┘
```

---

## 5. Validation Conflict Detection Flow

```
                User Creates Field Definition
                        │
                        ▼
        ┌───────────────────────────────┐
        │ validate_fields()             │
        │ Check each field definition   │
        └────┬─────────────────────┬────┘
             │                     │
             ▼                     ▼
        ┌──────────┐          ┌──────────────┐
        │ Required │          │ Type Support │
        │ Keys?    │          │ Valid?       │
        │ - name   │          │ - string     │
        │ - type   │          │ - integer    │
        │          │          │ - float      │
        └────┬─────┘          │ - boolean    │
             │                │ - date       │
             ▼                │ - json       │
        Pass? ─N→ Error       │ - array      │
        │ Y                   │ - object     │
        │                     │              │
        │                     └────┬─────────┘
        │                          │
        │                          ▼
        │                     Pass? ─N→ Error
        │                     │ Y
        │                     │
        ▼                     ▼
    ┌──────────┐          ┌──────────────┐
    │ Duplicate│          │ Constraints  │
    │ Names?   │          │ Valid Format?│
    └────┬─────┘          └────┬────────┘
         │                     │
         ▼                     ▼
    Pass? ─N→ Error      Pass? ─N→ Error
    │ Y                  │ Y
    │                    │
    ▼                    ▼
    ┌──────────┐          ┌──────────────┐
    │ Valid    │          │ Required +   │
    │ Format?  │          │ Default?     │
    │ [a-z_]   │          │ If required: │
    │ [a-z0-9] │          │ must have def│
    └────┬─────┘          └────┬────────┘
         │                     │
         ▼                     ▼
    Pass? ─N→ Error      Pass? ─N→ Error
    │ Y                  │ Y
    │                    │
    └────────┬───────────┘
             │
             ▼
    ┌──────────────────────┐
    │ All Validations      │
    │ Passed?              │
    └──────┬───────────┬───┘
           │           │
        NO ▼        YES▼
    ┌──────────┐  ┌──────────────┐
    │ Return   │  │ Accept Field │
    │ Errors   │  │ Definition   │
    └──────────┘  └──────────────┘
```

---

## 6. Risk Level Scoring

```
                    Risk Assessment
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
    OPERATION      DATA AFFECTED      CONFLICTS
        │                 │                 │
    ┌───┴──────┐      ┌────┴──────┐    ┌────┴──────┐
    │           │      │           │    │           │
    ADD    MODIFY REMOVE │      NON-NULL │       NONE │MINOR│MAJOR
    FIELD  FIELD  FIELD  │      VALUES   │            │    │    │
    │      │      │      │      │        │            │    │    │
    └──┬──┴──┬───┴──┬────┴──┬───┴────────┴──┬────────┴┬───┴───┬─┘
       │     │      │       │              │         │       │
    LOW │  MED │   MED    ZERO        0-100   100+   NONE │ SOME │ MANY
       │     │      │       │              │         │       │
       └─────┼──────┴───────┴──────────┬───┴─────────┘       │
             │                        │                      │
             └────────┬───────────────┴──────────────────────┘
                      │
        LOW (✓ Safe to apply immediately)
        • No data loss
        • Optional field
        • No validation errors
        • <100K records
                      │
        MEDIUM (⚠ Review recommended)
        • Some data affected
        • Type conversion needed
        • Performance impact (100K-1M records)
        • Requires defaults
                      │
        HIGH (⚠⚠ Requires approval)
        • Data loss possible
        • Validation conflicts detected
        • >1M records affected
        • Incompatible conversions
                      │
        CRITICAL (❌ Prevent by default)
        • Definite data loss
        • >100 non-null values lost
        • Incompatible type conversion
        • Constraint violations
```

---

## 7. Backward Compatibility Analysis

```
┌──────────────────────────────┐
│ Schema Change Proposed       │
└──────────────┬───────────────┘
               │
               ▼
    ┌──────────────────────┐
    │ Is field removal?    │
    └────┬────────────────┬┘
         │ YES            │ NO
         │                │
         ▼                ▼
    ┌─────────────┐  ┌──────────────────┐
    │ Soft Delete │  │ Other Operations │
    │ (Preserve)  │  │ - Add field      │
    │             │  │ - Modify field   │
    │ is_deleted= │  └────┬────────┬────┘
    │   TRUE      │       │        │
    │             │   Type  Constraint
    │ ✓ Data kept │   change change
    │ ✓ Can undo  │       │        │
    │ ✓ Compatible│       ▼        ▼
    └─────────────┘  ┌──────────┐ ┌──────────┐
                     │Check Type│ │ Check New │
                     │Compat    │ │ vs Existing
                     │Matrix    │ │ Data
                     └────┬─────┘ └────┬─────┘
                          │            │
                    Safe?  │      Violation? │
                     ▼     │            ▼
                    YES    │          YES
                     │     │            │
                     ▼     ▼            ▼
              ┌────────────────┐ ┌──────────┐
              │Reversible?     │ │ CONFLICT │
              │to string?      │ │ DETECTED │
              └───┬──────────┬─┘ └──────────┘
                  │ YES  NO │
                  │          │
                  ▼          ▼
            ┌──────────┐ ┌──────────┐
            │ ✓ Safe   │ │⚠ Risky   │
            │ to apply │ │Backward  │
            │          │ │incompat  │
            │Reversible│ │Warn user │
            └──────────┘ └──────────┘

BACKWARD COMPATIBILITY FEATURES:
✓ Soft delete (is_deleted=True) preserves data
✓ Schema versions track all changes  
✓ Can rollback to previous versions
✓ Type reversibility to string type
✓ Existing data never lost
✓ Deprecated fields remain queryable
```

---

## 8. Complete Decision Workflow

```
                START: Schema Change Request
                            │
                            ▼
                ┌───────────────────────┐
                │ Extract Operation     │
                │ and Parameters        │
                └────────┬──────────────┘
                         │
        ┌────────────────┼────────────────┐
        ▼                ▼                ▼
    ADD FIELD       MODIFY FIELD      REMOVE FIELD
    │              │                 │
    ▼              ▼                 ▼
    ┌────┐      ┌────┐         ┌────────┐
    │A1  │      │M1  │         │R1      │
    └────┘      └────┘         └────────┘
     │           │              │
     ▼           ▼              ▼
    ┌────┐      ┌────┐         ┌────────┐
    │A2  │      │M2  │         │R2      │
    └────┘      └────┘         └────────┘
     │           │              │
     ▼           ▼              ▼
    ┌────┐      ┌────┐         ┌────────┐
    │A3  │      │M3  │         │R3      │
    └────┘      └────┘         └────────┘
     │           │              │
     └─────┬─────┴──────────────┘
           │
           ▼
    ┌──────────────────────┐
    │ Generate Impact      │
    │ Analysis Report      │
    └──────┬───────────────┘
           │
           ▼
    ┌──────────────────────┐
    │ Assess Risk Level    │
    │ L/M/H/C              │
    └──────┬───────────────┘
           │
           ▼
    ┌──────────────────────┐
    │ Return Report to     │
    │ User for Review      │
    └──────┬───────────────┘
           │
    ┌──────┴──────┐
    ▼             ▼
  REJECT        APPROVE
    │             │
    ▼             ▼
  CANCEL        EXECUTE
  CHANGE        CHANGE
    │             │
    │             ▼
    │         ┌─────────┐
    │         │Update   │
    │         │Database │
    │         └────┬────┘
    │              │
    │              ▼
    │         ┌─────────────┐
    │         │Update       │
    │         │Schema       │
    │         │Version      │
    │         └────┬────────┘
    │              │
    │              ▼
    │         ┌─────────────┐
    │         │Log Change   │
    │         │in Changelog │
    │         └────┬────────┘
    │              │
    └──────┬───────┘
           │
           ▼
        END: Return Status
```

---

## 9. Affected Records Metrics

```
Schema Operations Impact Visualization

ADDING FIELD to 5000-record schema:
┌─────────────────────────┐
│ 5000 Records Affected   │ ← All records get new field
│ 0 Data Loss             │ ← No existing data affected
│ Risk: LOW               │ ← Safe operation
└─────────────────────────┘

REMOVING FIELD with 2850 non-null values:
┌─────────────────────────┐
│ 3000 Total Values       │ ← Total values in field
│ 2850 Non-Null Values    │ ← Values containing data
│ 95% Data Loss          │ ← Percentage of data lost
│ Risk: HIGH              │ ← Dangerous operation
└─────────────────────────┘

TYPE CONVERSION of 10000 values:
┌─────────────────────────┐
│ 10000 Values to Convert │ ← Total values
│ 100 Sample Test         │ ← Test sample size
│ 3 Failures in Sample    │ ← Incompatible values
│ ~300 Estimated Failures │ ← Extrapolated failures
│ Risk: MEDIUM/HIGH       │ ← Significant issues
└─────────────────────────┘
```

---

These diagrams provide visual representation of how the impact analysis system works at different levels of abstraction.
