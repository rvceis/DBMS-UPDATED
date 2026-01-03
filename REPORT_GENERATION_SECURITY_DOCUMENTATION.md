# Report Generation Features & Security Documentation

## Table of Contents
1. [Report Generation Features](#report-generation-features)
2. [Form Validation](#form-validation)
3. [Security Implementation](#security-implementation)
4. [API Documentation](#api-documentation)
5. [Best Practices](#best-practices)

---

## Report Generation Features

### Overview
The system supports comprehensive report generation with multiple features:

### 1. Report Template Management

**Features:**
- Create, read, update, delete (CRUD) report templates
- Public/private template sharing
- Template versioning
- Schema-based template configuration

**File:** `flask_backend/app/routes/reports.py`

**Endpoints:**

#### GET /api/reports/templates
- **Description:** List all accessible report templates
- **Authentication:** JWT required
- **Access Control:**
  - Admin: sees all templates
  - Other roles: see own templates + public templates
- **Response:**
```json
[
  {
    "id": 1,
    "name": "Monthly Sales Report",
    "schema_id": 5,
    "created_by": 1,
    "is_public": true,
    "created_at": "2026-01-02T13:16:00.374786"
  }
]
```

#### GET /api/reports/templates/:id
- **Description:** Get detailed template with configuration
- **Authentication:** JWT required
- **Response:** Includes `query_config`, `display_config`, `pdf_config`

#### POST /api/reports/templates
- **Description:** Create new report template
- **Authentication:** JWT required (editor/admin only)
- **Role Requirement:** `editor` or `admin`
- **Request Body:**
```json
{
  "name": "Quarterly Report",
  "description": "Q1 2026 Sales Analysis",
  "schema_id": 5,
  "asset_type_id": 4,
  "query_config": {
    "fields": ["product_name", "quantity", "price"],
    "filters": [
      {
        "field": "status",
        "operator": "eq",
        "value": "active"
      }
    ],
    "limit": 1000
  },
  "display_config": {
    "format": "table",
    "colors": true,
    "summary": true
  },
  "pdf_config": {
    "orientation": "landscape",
    "page_size": "A4",
    "include_footer": true
  },
  "is_public": false
}
```

#### PUT /api/reports/templates/:id
- **Description:** Update report template
- **Authentication:** JWT required
- **Authorization:** Template owner or admin
- **Request Body:** Same as POST

#### DELETE /api/reports/templates/:id
- **Description:** Delete report template
- **Authentication:** JWT required
- **Authorization:** Template owner or admin

---

### 2. Report Generation Methods

#### A. Template-Based Report Generation

**Endpoint:** `POST /api/reports/generate`

- **Description:** Generate report from saved template
- **Authentication:** JWT required
- **Request Body:**
```json
{
  "template_id": 5,
  "format": "pdf",
  "params": {
    "limit": 500,
    "filters": [
      {
        "field": "date",
        "operator": "gte",
        "value": "2026-01-01"
      }
    ]
  }
}
```

- **Response:**
```json
{
  "id": 1,
  "template_id": 5,
  "status": "completed",
  "format": "pdf",
  "file_path": "instance/reports/report_5_1_1704282000.pdf",
  "file_size": 102400,
  "row_count": 245,
  "execution_time_ms": 1234,
  "completed_at": "2026-01-02T13:20:00.000000"
}
```

**Features:**
- Runtime parameter override
- Dynamic filtering
- Asynchronous execution for large datasets
- File generation and caching

---

#### B. Ad-Hoc Report Generation

**Endpoint:** `POST /api/reports/generate/adhoc`

- **Description:** Generate report without saved template
- **Authentication:** JWT required
- **Request Body:**
```json
{
  "schema_id": 5,
  "name": "Custom Sales Analysis",
  "format": "csv",
  "query_config": {
    "fields": ["product_name", "quantity", "total_sales"],
    "filters": [
      {
        "field": "quantity",
        "operator": "gt",
        "value": 100
      }
    ],
    "sort": [
      {
        "field": "total_sales",
        "order": "DESC"
      }
    ],
    "limit": 500
  }
}
```

**Features:**
- One-time report generation
- No template required
- Full query configuration
- CSV or PDF export

---

#### C. Multi-Schema Records Report

**Endpoint:** `POST /api/reports/generate/records`

- **Description:** Generate report from selected records across multiple schemas
- **Request Body:**
```json
{
  "record_ids": [1, 3, 5, 7],
  "format": "pdf",
  "include_schema_name": true,
  "group_by_schema": true
}
```

**Features:**
- Multi-schema support
- Separate tables per schema
- Record-level granularity
- Dynamic field extraction

---

### 3. Report Export Formats

#### CSV Export
- **Service:** `ReportExportService.export_csv()`
- **Features:**
  - UTF-8 encoding
  - Proper delimiter handling
  - Field selection
  - Row-based export

**File:** `flask_backend/app/services/report_export_service.py`

#### PDF Export
- **Service:** `ReportExportService.export_pdf()`
- **Features:**
  - Configurable orientation (portrait/landscape)
  - Page sizing (A4, letter, etc.)
  - Header and footer support
  - Table formatting with colors
  - Multi-page support

**Configuration Options:**
```json
{
  "title": "Report Title",
  "orientation": "landscape",
  "page_size": "A4",
  "include_header": true,
  "include_footer": true,
  "header_text": "Custom Header",
  "footer_text": "Page {page} of {total}",
  "colors": true,
  "column_widths": [2, 3, 2, 2],
  "filters": [
    {
      "field": "status",
      "operator": "eq",
      "value": "active"
    }
  ]
}
```

---

### 4. Query Building & Filtering

**Service:** `ReportQueryBuilder` (`flask_backend/app/services/report_query_builder.py`)

#### Supported Filters

| Operator | Description | Example |
|----------|-------------|---------|
| `eq` | Equals | `{"field": "status", "operator": "eq", "value": "active"}` |
| `ne` | Not equals | `{"field": "status", "operator": "ne", "value": "inactive"}` |
| `gt` | Greater than | `{"field": "price", "operator": "gt", "value": 100}` |
| `lt` | Less than | `{"field": "price", "operator": "lt", "value": 1000}` |
| `gte` | Greater or equal | `{"field": "date", "operator": "gte", "value": "2026-01-01"}` |
| `lte` | Less or equal | `{"field": "date", "operator": "lte", "value": "2026-12-31"}` |
| `in` | In list | `{"field": "status", "operator": "in", "value": ["active", "pending"]}` |
| `contains` | String contains | `{"field": "name", "operator": "contains", "value": "John"}` |
| `between` | Between range | `{"field": "price", "operator": "between", "value": [100, 1000]}` |

#### Sorting

**Format:**
```json
{
  "sort": [
    {"field": "created_at", "order": "DESC"},
    {"field": "name", "order": "ASC"}
  ]
}
```

**Orders:** `ASC`, `DESC`

#### Field Selection

**Usage:**
```json
{
  "fields": ["name", "email", "created_at", "status"]
}
```

**Default:** All schema fields if not specified

---

### 5. Report Execution Tracking

**Model:** `ReportExecution`

**Fields:**
- `id`: Unique execution ID
- `template_id`: Associated template (nullable for adhoc)
- `user_id`: Requesting user
- `status`: `running | completed | failed`
- `format`: `csv | pdf`
- `file_path`: Generated file location
- `file_size`: Bytes
- `row_count`: Records included
- `execution_time_ms`: Milliseconds to generate
- `error_message`: Error details if failed
- `created_at`: Execution start time
- `completed_at`: Completion time

---

## Form Validation

### Backend Validation

#### Report Template Creation Validation

**File:** `flask_backend/app/routes/reports.py` (lines 47-73)

```python
@reports_bp.route('/templates', methods=['POST'])
@jwt_required()
def create_template():
    data = request.get_json()
    
    # Required field validation
    if not data.get('name'):
        return jsonify({'error': 'name is required'}), 400
    
    if not data.get('schema_id'):
        return jsonify({'error': 'schema_id is required'}), 400
    
    # Schema existence validation
    schema = SchemaModel.query.get(data['schema_id'])
    if not schema:
        return jsonify({'error': 'Schema not found'}), 404
```

**Validation Rules:**

| Field | Rule | Type |
|-------|------|------|
| `name` | Required, non-empty | String |
| `schema_id` | Required, must exist | Integer |
| `description` | Optional | String |
| `asset_type_id` | Optional | Integer |
| `query_config` | Optional, JSON object | Object |
| `display_config` | Optional, JSON object | Object |
| `pdf_config` | Optional, JSON object | Object |
| `is_public` | Optional, default false | Boolean |

---

#### Report Generation Validation

**File:** `flask_backend/app/routes/reports.py` (lines 144-169)

```python
@reports_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_report():
    data = request.get_json()
    
    template_id = data.get('template_id')
    format_type = data.get('format', 'csv')
    
    # Required field validation
    if not template_id:
        return jsonify({'error': 'template_id is required'}), 400
    
    # Format validation
    if format_type not in ['csv', 'pdf']:
        return jsonify({'error': 'format must be csv or pdf'}), 400
    
    # Template existence and access validation
    template = ReportTemplate.query.get(template_id)
    if not template:
        return jsonify({'error': 'Template not found'}), 404
```

**Validation Rules:**

| Field | Rule | Example |
|-------|------|---------|
| `template_id` | Required, must exist | `5` |
| `format` | Must be `csv` or `pdf` | `"pdf"` |
| `params` | Optional, JSON object | `{"limit": 500}` |

---

#### Query Configuration Validation

**File:** `flask_backend/app/services/report_query_builder.py`

**Validation Logic:**

```python
def build_query(self, query_config: dict, schema: SchemaModel):
    # Base query validation
    query = db.session.query(MetadataRecord).filter_by(schema_id=schema.id)
    
    # Filters validation
    for filter_def in query_config.get('filters', []):
        # Field existence check
        field_name = filter_def.get('field')
        field = next((f for f in schema.fields if f.field_name == field_name), None)
        if not field:
            return query  # Skip invalid field
        
        # Operator validation
        operator = filter_def.get('operator', 'eq')
        valid_operators = ['eq', 'ne', 'gt', 'lt', 'gte', 'lte', 'in', 'contains', 'between']
        if operator not in valid_operators:
            continue  # Skip invalid operator
```

**Validations:**
- Field existence in schema
- Operator validity
- Sort field existence
- Limit bounds (max 10000)
- Value type matching

---

### Frontend Validation

#### File Upload Validation

**File:** `Frontend/src/components/FileImportDialog.tsx`

```typescript
const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
  const selectedFile = e.target.files?.[0];
  if (!selectedFile) return;

  // File extension validation
  const allowedExtensions = ['json', 'csv', 'tsv', 'xlsx', 'xls', 'txt'];
  const fileExtension = selectedFile.name.split('.').pop()?.toLowerCase();
  
  if (!fileExtension || !allowedExtensions.includes(fileExtension)) {
    const errMsg = `Invalid file format: .${fileExtension}. Supported formats: JSON, CSV, TSV, Excel, TXT`;
    setError(errMsg);
    toast.error(errMsg);
    return;
  }
  
  // File exists and size check (implicit via File API)
  setFile(selectedFile);
};
```

**Validations:**
- File extension whitelist (`.json`, `.csv`, `.tsv`, `.xlsx`, `.xls`, `.txt`)
- File size (handled by browser)
- File type verification

---

#### Form Input Validation

**Pattern Examples:**

```typescript
// Email validation
const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

// Schema name validation
const schemaNamePattern = /^[a-zA-Z0-9_\-\s]{1,255}$/;

// Field name validation
const fieldNamePattern = /^[a-zA-Z_][a-zA-Z0-9_]{0,254}$/;

// Number validation
const numberPattern = /^-?\d+(\.\d+)?$/;
```

**Material-UI TextField Validation:**

```typescript
<TextField
  fullWidth
  label="Report Name"
  value={formData.name}
  onChange={(e) => setFormData({...formData, name: e.target.value})}
  error={!formData.name}
  helperText={!formData.name ? "Name is required" : ""}
  required
  inputProps={{
    maxLength: 255
  }}
/>
```

---

## Security Implementation

### 1. Authentication

**Method:** JWT (JSON Web Tokens)

**Location:** `flask_backend/app/routes/auth.py`

#### Login Endpoint
```python
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    user = User.query.filter_by(email=email).first()
    
    # Secure password comparison
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Token generation with claims
    token = create_access_token(
        identity=str(user.id),
        additional_claims={"role": user.role, "email": user.email}
    )
    
    return jsonify({'access_token': token})
```

**Security Features:**
- Bcrypt password hashing via `werkzeug.security.generate_password_hash()`
- Constant-time comparison with `check_password_hash()`
- Role-based claims in JWT
- Token expiration (configurable)

---

### 2. Authorization & Access Control

**Pattern:** Role-Based Access Control (RBAC)

**Roles:**
- `admin`: Full system access
- `editor`: Create/edit schemas, data, reports
- `viewer`: Read-only access

#### Backend Authorization

**Decorator Pattern:**
```python
@reports_bp.route('/templates/<int:template_id>', methods=['DELETE'])
@jwt_required()
def delete_template(template_id):
    user_id = int(get_jwt_identity())
    claims = get_jwt()
    role = claims.get('role', 'viewer')
    
    template = ReportTemplate.query.get_or_404(template_id)
    
    # Permission check: owner or admin
    if template.created_by != user_id and role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    db.session.delete(template)
    db.session.commit()
```

**Authorization Rules:**

| Endpoint | Roles | Conditions |
|----------|-------|-----------|
| GET /templates | All authenticated | See own + public templates (non-admin) |
| POST /templates | editor, admin | Create new |
| PUT /templates/:id | editor, admin | Owner or admin |
| DELETE /templates/:id | editor, admin | Owner or admin |
| POST /generate | All authenticated | Template is public OR user is owner OR user is admin |

#### Frontend Authorization

**File:** `Frontend/src/components/layout/Sidebar.tsx`

```typescript
const canAccessItem = (item: NavItem, user: any) => {
  if (!item.requiredRole) return true;
  return user?.role === item.requiredRole || user?.role === 'admin';
};

const navItems: NavItem[] = [
  { label: 'Asset Types', path: '/asset-types', requiredRole: 'admin' },
  { label: 'Users', path: '/users', requiredRole: 'admin' },
  { label: 'Reports', path: '/reports', requiredRole: 'editor' },
];
```

---

### 3. Input Sanitization

#### SQL Injection Prevention

**Method:** SQLAlchemy ORM parameterized queries

```python
# ✅ SAFE: Uses parameterized query
field_value = filter_def.get('value')
query = query.filter(
    self._get_value_column(field_alias, field.field_type) == field_value
)

# ❌ UNSAFE (not used): String concatenation
# query = db.session.execute(f"SELECT * FROM records WHERE name = '{name}'")
```

#### XSS Prevention

**Frontend:**
- React auto-escapes JSX expressions
- No direct `innerHTML` usage
- Content Security Policy headers (server-side)

**Backend:**
- No user input directly rendered to HTML
- JSON responses (not HTML templates with embedded data)

#### CSRF Protection

**Potential:** Can be enabled via Flask-CORS and CSRF tokens
**Current Status:** JWT stateless (cross-origin safe)

---

### 4. Rate Limiting

**Recommendation:** Implement for report generation

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    storage_uri="memory://"
)

@reports_bp.route('/generate', methods=['POST'])
@jwt_required()
@limiter.limit("5 per minute")
def generate_report():
    # ... implementation
```

---

### 5. Secure Headers

**Recommendations:**

```python
# Add to Flask app configuration
app.config.update({
    'SESSION_COOKIE_SECURE': True,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'PERMANENT_SESSION_LIFETIME': 3600,  # 1 hour
    'JWT_SECRET_KEY': os.environ.get('JWT_SECRET_KEY'),
    'CORS_ORIGINS': os.environ.get('CORS_ORIGINS', 'http://localhost:5173').split(',')
})

# Add security headers middleware
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

---

### 6. Data Validation & Type Checking

**File Upload Validation:**

```python
@uploads_bp.route('/import-file', methods=['POST'])
@jwt_required()
def import_file():
    # File extension validation
    allowed_extensions = {'.json', '.csv', '.tsv', '.xlsx', '.xls', '.txt'}
    file_ext = '.' + file.filename.rsplit('.', 1)[-1].lower()
    
    if file_ext not in allowed_extensions:
        return jsonify({'error': f'Unsupported file format: {file_ext}'}), 400
    
    # UTF-8 encoding validation for text files
    if filename.endswith(('.json', '.csv', '.tsv', '.txt')):
        try:
            content = file_content.decode('utf-8')
        except UnicodeDecodeError:
            return jsonify({'error': 'File must be UTF-8 encoded text'}), 400
    
    # File size limits (implicit via Flask)
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
```

---

### 7. Error Handling & Information Disclosure

**Secure Error Responses:**

```python
# ✅ GOOD: Generic error message
@reports_bp.route('/templates/<int:template_id>')
def get_template(template_id):
    try:
        template = ReportTemplate.query.get_or_404(template_id)
        return jsonify(template.to_dict())
    except Exception as e:
        # Log internally
        logger.error(f"Template retrieval failed: {str(e)}")
        # Return generic message
        return jsonify({'error': 'Internal server error'}), 500

# ❌ BAD: Leaks implementation details
return jsonify({'error': f'Database error: {str(e)}'}), 500
```

---

### 8. File Security

**Report File Storage:**

```python
import os
import uuid
from datetime import datetime

def generate_safe_filename(template_id, execution_id, format):
    """Generate secure filename"""
    timestamp = int(time.time())
    # No user input in filename
    filename = f"report_{template_id}_{execution_id}_{timestamp}.{format}"
    return filename

def validate_file_path(filepath):
    """Prevent directory traversal attacks"""
    # Resolve to absolute path
    real_path = os.path.realpath(filepath)
    
    # Ensure within reports directory
    reports_dir = os.path.realpath(REPORTS_DIR)
    if not real_path.startswith(reports_dir):
        raise ValueError("Invalid file path")
    
    return real_path
```

**File Access Control:**

```python
@reports_bp.route('/download/<int:execution_id>')
@jwt_required()
def download_report(execution_id):
    user_id = int(get_jwt_identity())
    execution = ReportExecution.query.get_or_404(execution_id)
    
    # Verify ownership
    if execution.user_id != user_id and role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Validate file path
    filepath = validate_file_path(execution.file_path)
    
    # Return file
    return send_file(filepath)
```

---

## API Documentation

### Summary

| Method | Endpoint | Purpose | Auth | Role |
|--------|----------|---------|------|------|
| GET | /api/reports/templates | List templates | ✓ | All |
| GET | /api/reports/templates/:id | Get template | ✓ | All |
| POST | /api/reports/templates | Create template | ✓ | editor, admin |
| PUT | /api/reports/templates/:id | Update template | ✓ | Owner, admin |
| DELETE | /api/reports/templates/:id | Delete template | ✓ | Owner, admin |
| POST | /api/reports/generate | Generate from template | ✓ | All |
| POST | /api/reports/generate/adhoc | Generate ad-hoc report | ✓ | All |
| POST | /api/reports/generate/records | Generate records report | ✓ | All |
| GET | /api/reports/executions | List report executions | ✓ | Own + admin |
| GET | /api/reports/download/:id | Download report file | ✓ | Owner + admin |

---

## Best Practices

### 1. Performance Optimization

**Query Limits:**
- Default limit: 10,000 records
- Maximum recommended: 50,000 records
- For larger datasets: use pagination or filtering

**Caching Strategies:**
```python
from flask_caching import Cache

cache = Cache(app, config={'CACHE_TYPE': 'redis'})

@reports_bp.route('/templates/<int:template_id>')
@cache.cached(timeout=300)  # Cache for 5 minutes
def get_template(template_id):
    template = ReportTemplate.query.get_or_404(template_id)
    return jsonify(template.to_dict())
```

---

### 2. Report Generation Optimization

**Large Dataset Handling:**
```python
def generate_report_optimized(template_id, format, user_id, params):
    # Use database streaming for large result sets
    query = build_query(params)
    
    # Process in chunks
    chunk_size = 1000
    with open(filepath, 'w') as f:
        for chunk in query.yield_per(chunk_size):
            process_chunk(chunk, f)
    
    return filepath
```

---

### 3. Monitoring & Logging

**Request Logging:**
```python
import logging

logger = logging.getLogger(__name__)

@reports_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_report():
    user_id = int(get_jwt_identity())
    data = request.get_json()
    
    logger.info(f"Report generation requested by user {user_id}, template {data.get('template_id')}")
    
    try:
        execution = report_gen.generate_report(...)
        logger.info(f"Report generated successfully: {execution.id}")
        return jsonify(execution.to_dict())
    except Exception as e:
        logger.error(f"Report generation failed: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to generate report'}), 500
```

---

### 4. Data Privacy

**PII Masking:**
```python
def mask_sensitive_fields(data, sensitive_fields):
    """Mask PII in reports"""
    masked = []
    for record in data:
        masked_record = record.copy()
        for field in sensitive_fields:
            if field in masked_record:
                masked_record[field] = '***REDACTED***'
        masked.append(masked_record)
    return masked
```

---

### 5. Compliance

**Audit Trail:**
```python
class ReportAudit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    template_id = db.Column(db.Integer, db.ForeignKey('report_templates.id'))
    action = db.Column(db.String(50))  # create, generate, download, delete
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    details = db.Column(db.JSON)

def log_audit(user_id, template_id, action, details=None):
    audit = ReportAudit(
        user_id=user_id,
        template_id=template_id,
        action=action,
        details=details
    )
    db.session.add(audit)
    db.session.commit()
```

---

## Security Checklist

- ✅ JWT authentication implemented
- ✅ Role-based access control
- ✅ SQL injection prevention (ORM)
- ✅ XSS prevention (React auto-escape)
- ✅ Password hashing (bcrypt)
- ✅ File upload validation
- ✅ UTF-8 encoding validation
- ✅ Input sanitization
- ✅ Error message sanitization
- ⚠️ CSRF tokens (recommended)
- ⚠️ Rate limiting (recommended)
- ⚠️ HTTPS only (deployment requirement)
- ⚠️ API rate limiting (recommended)
- ⚠️ Audit logging (recommended)
- ⚠️ PII masking (optional)

---

## Related Documentation

- [REPORT_GENERATION_GUIDE.md](REPORT_GENERATION_GUIDE.md)
- [BACKEND_ARCHITECTURE.md](BACKEND_ARCHITECTURE.md)
- [DATA_IMPORT_GUIDE.md](DATA_IMPORT_GUIDE.md)

---

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-02 | 1.0 | Initial documentation |

---

## Support & Contact

For security vulnerabilities, please report to: security@example.com

For feature requests or bugs, use the project issue tracker.
