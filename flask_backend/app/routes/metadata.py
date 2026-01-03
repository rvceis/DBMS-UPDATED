from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import MetadataRecord, SchemaModel, SchemaField, FieldValue
from ..extensions import db
from ..services.schema_matcher import find_best_schema_from_keys, create_schema_from_metadata
from ..services.schema_manager import SchemaManager
from ..services.metadata_catalog import MetadataCatalog
import os
from functools import wraps
from time import time
from datetime import datetime

# Simple rate limiting (in-memory, per-process)
_rate_limit_store = {}

def rate_limit(max_calls=100, period=60):
    """Rate limit decorator: max_calls per period (seconds)"""
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            try:
                user_id = get_jwt_identity()
            except:
                user_id = request.remote_addr
            
            key = f"{f.__name__}:{user_id}"
            now = time()
            
            if key not in _rate_limit_store:
                _rate_limit_store[key] = []
            
            # Clean old entries
            _rate_limit_store[key] = [t for t in _rate_limit_store[key] if now - t < period]
            
            if len(_rate_limit_store[key]) >= max_calls:
                return jsonify({"error": "Rate limit exceeded. Try again later."}), 429
            
            _rate_limit_store[key].append(now)
            return f(*args, **kwargs)
        return wrapped
    return decorator

metadata_bp = Blueprint("metadata", __name__)


@metadata_bp.route("/", methods=["GET"])
@metadata_bp.route("/", methods=["POST"])
@jwt_required()
def create_metadata():
    from flask_jwt_extended import get_jwt
    import json, io, csv, werkzeug
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    # Allow admin, editor, and viewer to create metadata (or change as needed)
    if role not in ("admin", "editor", "viewer"):
        return jsonify({"error": "authentication required"}), 403

    # Accept both JSON and multipart/form-data
    if request.content_type and request.content_type.startswith("multipart/form-data"):
        data = request.form.to_dict()
        file = request.files.get("file")
    else:
        data = request.get_json() or {}
        file = None

    values = data.get("values")
    asset_type_id = data.get("asset_type_id")
    tag = data.get("tag")
    name = data.get("name", "Unnamed Record")
    schema_id = data.get("schema_id")
    create_new_schema = data.get("create_new_schema", False)
    allow_additional = data.get("allow_additional_fields", True)
    metadata_json = data.get("metadata_json")
    raw_data = data.get("raw_data")
    input_format = (data.get("format") or "json").lower()

    # If values not provided but legacy metadata_json exists
    if not values and isinstance(metadata_json, dict):
        values = metadata_json

    # If values missing but raw_data is provided, try to parse based on format
    if (not isinstance(values, dict) or not values) and raw_data:
        try:
            if input_format == 'json':
                parsed = json.loads(raw_data)
                if isinstance(parsed, dict):
                    values = parsed
                elif isinstance(parsed, list) and parsed:
                    values = parsed[0]
                else:
                    return jsonify({"error": "raw_data JSON must be an object or non-empty array"}), 400
            elif input_format == 'ndjson':
                for line in raw_data.splitlines():
                    line = line.strip()
                    if not line:
                        continue
                    values = json.loads(line)
                    break
                if not values:
                    return jsonify({"error": "No JSON objects found in NDJSON raw_data"}), 400
            elif input_format in ('csv', 'tsv'):
                sep = ',' if input_format == 'csv' else '\t'
                f = io.StringIO(raw_data)
                reader = csv.reader(f, delimiter=sep)
                rows = [r for r in reader if any(cell.strip() for cell in r)]
                if len(rows) < 2:
                    return jsonify({"error": "CSV/TSV raw_data must include header and at least one row"}), 400
                headers = [h.strip() for h in rows[0]]
                first = rows[1]
                values = {headers[i]: first[i] if i < len(first) else None for i in range(len(headers))}
            else:
                values = None
        except Exception as e:
            return jsonify({"error": f"Failed to parse raw_data: {str(e)}"}), 400

    # If file is uploaded, save it and set file_path
    file_path = None
    if file and isinstance(file, werkzeug.datastructures.FileStorage):
        upload_dir = os.path.join(os.getcwd(), "uploads")
        os.makedirs(upload_dir, exist_ok=True)
        safe_name = werkzeug.utils.secure_filename(file.filename)
        file_path = os.path.join(upload_dir, safe_name)
        file.save(file_path)

    # Allow record creation if any of: values is a dict, file is uploaded, or raw_data is present
    if not (isinstance(values, dict) and values) and not file_path and not raw_data:
        return jsonify({"error": "values (field map), raw_data, or file upload required"}), 400

    # Resolve schema
    schema: SchemaModel = None
    if schema_id:
        schema = SchemaModel.query.get(schema_id)
        if not schema:
            return jsonify({"error": "schema not found"}), 400
    else:
        keys = list(values.keys()) if values else []
        schema, score = find_best_schema_from_keys(keys, asset_type_id=asset_type_id)
        if not schema:
            if not create_new_schema:
                return jsonify({"error": "no matching schema found; set create_new_schema=true to auto-create"}), 400
            schema = create_schema_from_metadata(
                name=f"AutoSchema-{name}",
                metadata=values or {},
                asset_type_id=asset_type_id,
                user_id=user_id,
                allow_additional_fields=allow_additional,
            )

    # Validate values against schema if present
    if values and schema:
        from ..services.validation_engine import ValidationEngine
        validator = ValidationEngine()
        validation_errors = validator.validate_record_values(schema, values)
        if validation_errors:
            return jsonify({
                "error": "Validation failed",
                "validation_errors": validation_errors
            }), 400

    import json as _json
    r = MetadataRecord(
        name=name,
        schema_id=schema.id,
        asset_type_id=asset_type_id,
        tag=tag,
        created_by=user_id,
        metadata_json=metadata_json,
        raw_data=raw_data if raw_data is not None else (_json.dumps(values) if isinstance(values, dict) else None),
        file_path=file_path
    )
    db.session.add(r)
    db.session.flush()

    # Persist field values if values present
    if values:
        fields = {f.field_name: f for f in SchemaField.query.filter_by(schema_id=schema.id, is_deleted=False).all()}
        for k, v in values.items():
            if k not in fields:
                if schema.allow_additional_fields:
                    continue
                else:
                    db.session.rollback()
                    return jsonify({"error": f"field '{k}' not defined in schema"}), 400
            f = fields[k]
            fv = FieldValue(record_id=r.id, schema_field_id=f.id)
            f_type_backup = f.field_type
            try:
                fv.schema_field = f
                fv.set_value(v)
            finally:
                f.field_type = f_type_backup
            db.session.add(fv)

    db.session.commit()
    return jsonify(r.to_dict(include_values=True)), 201


@metadata_bp.route("/<int:record_id>", methods=["GET"])
@jwt_required()
def get_metadata(record_id):
    from ..models import User
    
    user_id = int(get_jwt_identity())
    
    r = MetadataRecord.query.get(record_id)
    if not r:
        return jsonify({"error": "not found"}), 404
    
    user = User.query.get(user_id)
    # Users can only see their own records, admins see all
    if user.role != "admin" and r.created_by != user_id:
        return jsonify({"error": "forbidden"}), 403
    
    return jsonify(r.to_dict(include_values=True))


@metadata_bp.route("/<int:record_id>/data", methods=["GET", "POST"])
def handle_record_data(record_id):
    """Get paginated data rows OR add new row - uses data_rows table"""
    from flask import request
    
    if request.method == "POST":
        # Add new row
        from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
        jwt_required()(lambda: None)()
        from ..models import User, DataRow
        
        user_id = int(get_jwt_identity())
        user = User.query.get(user_id)
        
        r = MetadataRecord.query.get(record_id)
        if not r:
            return jsonify({"error": "record not found"}), 404
        
        if user.role != "admin" and r.created_by != user_id:
            return jsonify({"error": "forbidden"}), 403
        
        data = request.get_json()
        if not data or "data" not in data:
            return jsonify({"error": "data field required"}), 400
        
        # Get max row_index
        max_row = DataRow.query.filter_by(record_id=record_id).order_by(DataRow.row_index.desc()).first()
        next_index = (max_row.row_index + 1) if max_row else 1
        
        new_row = DataRow(
            record_id=record_id,
            row_index=next_index,
            data=data["data"]
        )
        db.session.add(new_row)
        db.session.commit()
        
        return jsonify({"message": "row added", "row": new_row.to_dict()}), 201
    
    # GET request - paginated data
    from flask_jwt_extended import jwt_required, get_jwt_identity
    jwt_required()(lambda: None)()
    
    from ..models import User, DataRow
    import json
    
    user_id = int(get_jwt_identity())
    
    # Pagination params
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 100, type=int), 5000)  # Max 5000 rows per request
    
    # Filtering params (optional)
    filter_field = request.args.get('filter_field')
    filter_value = request.args.get('filter_value')
    sort_field = request.args.get('sort_field')
    sort_order = request.args.get('sort_order', 'asc')
    
    r = MetadataRecord.query.get(record_id)
    if not r:
        return jsonify({"error": "not found"}), 404
    
    user = User.query.get(user_id)
    if user.role != "admin" and r.created_by != user_id:
        return jsonify({"error": "forbidden"}), 403
    
    # AUTO-MIGRATE: Check if old JSON data exists but no data_rows yet
    from ..models import DataRow
    existing_rows = DataRow.query.filter_by(record_id=record_id).count()
    
    print(f"\n🔍 DEBUG record_id={record_id}: existing_data_rows={existing_rows}")
    print(f"   raw_data type={type(r.raw_data)}, metadata_json type={type(r.metadata_json)}")
    print(f"   raw_data exists={bool(r.raw_data)}, metadata_json exists={bool(r.metadata_json)}")
    
    if existing_rows == 0 and (r.raw_data or r.metadata_json):
        # Need to migrate old data to data_rows table
        import json
        old_data = r.raw_data or r.metadata_json
        
        print(f"   Found old data, attempting migration...")
        
        if isinstance(old_data, str):
            try:
                old_data = json.loads(old_data)
                print(f"   Parsed JSON string")
            except Exception as e:
                print(f"   Failed to parse JSON: {e}")
                old_data = None
        
        if old_data:
            print(f"   Old data type: {type(old_data)}")
            
            # If it's a dict (single record), convert to list
            if isinstance(old_data, dict):
                old_data = [old_data]
                print(f"   Converted dict to list")
            
            # If it's a list of records, migrate each one
            if isinstance(old_data, list):
                print(f"   Migrating {len(old_data)} records...")
                for idx, row_data in enumerate(old_data, 1):
                    if isinstance(row_data, dict):
                        new_row = DataRow(
                            record_id=record_id,
                            row_index=idx,
                            data=row_data
                        )
                        db.session.add(new_row)
                
                try:
                    db.session.commit()
                    print(f"✓ Auto-migrated {len(old_data)} rows from JSON to data_rows table for record {record_id}")
                except Exception as e:
                    db.session.rollback()
                    print(f"✗ Migration error: {str(e)}")
    else:
        print(f"   No migration needed (existing_rows={existing_rows})")
    
    # Query data_rows table (NEW APPROACH)
    query = DataRow.query.filter_by(record_id=record_id)
    
    # Apply filtering using JSONB operators
    if filter_field and filter_value:
        # PostgreSQL JSONB query: data->>'field_name' = 'value'
        from sqlalchemy import cast, String
        query = query.filter(cast(DataRow.data[filter_field], String) == filter_value)
    
    # Count total BEFORE applying sort (so we get accurate total)
    total_rows = query.count()
    
    # Apply sorting
    if sort_field:
        from sqlalchemy import cast, String
        if sort_order == 'desc':
            query = query.order_by(cast(DataRow.data[sort_field], String).desc())
        else:
            query = query.order_by(cast(DataRow.data[sort_field], String).asc())
    else:
        query = query.order_by(DataRow.row_index.asc())
    
    # Paginate
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    
    # Calculate total pages accurately
    import math
    total_pages = math.ceil(total_rows / per_page) if total_rows > 0 else 0
    
    return jsonify({
        "record_id": record_id,
        "record_name": r.name,
        "storage_type": "table",
        "total_rows": total_rows,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "has_next": paginated.has_next,
        "has_prev": paginated.has_prev,
        "data": [row.to_dict() for row in paginated.items]
    }), 200


@metadata_bp.route("/<int:record_id>/debug-data", methods=["GET"])
@jwt_required()
def debug_record_data(record_id):
    """Debug endpoint - see what data actually exists in database"""
    from flask_jwt_extended import get_jwt
    import json
    
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "admin only"}), 403
    
    from ..models import DataRow, User
    
    r = MetadataRecord.query.get(record_id)
    if not r:
        return jsonify({"error": "record not found"}), 404
    
    # Count data_rows
    data_rows_count = DataRow.query.filter_by(record_id=record_id).count()
    
    # Get first row from data_rows (if exists)
    first_data_row = DataRow.query.filter_by(record_id=record_id).first()
    
    # Check what's in metadata_json
    metadata_json_content = r.metadata_json
    metadata_json_length = 0
    metadata_json_keys = []
    
    if isinstance(metadata_json_content, dict):
        metadata_json_length = len(metadata_json_content)
        metadata_json_keys = list(metadata_json_content.keys())
        # If dict has 'data' key with list inside, that's the record count
        if 'data' in metadata_json_content and isinstance(metadata_json_content['data'], list):
            metadata_json_length = len(metadata_json_content['data'])
    elif isinstance(metadata_json_content, str):
        try:
            parsed = json.loads(metadata_json_content)
            if isinstance(parsed, dict):
                metadata_json_length = len(parsed)
                metadata_json_keys = list(parsed.keys())
        except:
            metadata_json_length = 0
    
    return jsonify({
        "record_id": record_id,
        "record_name": r.name,
        "data_rows_table_count": data_rows_count,
        "metadata_json_exists": bool(r.metadata_json),
        "metadata_json_type": str(type(r.metadata_json).__name__),
        "metadata_json_length_or_item_count": metadata_json_length,
        "metadata_json_keys_sample": metadata_json_keys[:10] if metadata_json_keys else [],
        "metadata_json_sample": str(metadata_json_content)[:500] if metadata_json_content else "",
        "first_data_row": first_data_row.to_dict() if first_data_row else None,
    }), 200


@metadata_bp.route("/<int:record_id>/migrate-now", methods=["POST"])
@jwt_required()
def manual_migrate_data(record_id):
    """Manually trigger migration from old JSON format to data_rows"""
    from flask_jwt_extended import get_jwt
    
    claims = get_jwt()
    if claims.get("role") != "admin":
        return jsonify({"error": "admin only"}), 403
    
    from ..models import DataRow
    import json
    
    r = MetadataRecord.query.get(record_id)
    if not r:
        return jsonify({"error": "record not found"}), 404
    
    # Delete existing data_rows first (reset)
    DataRow.query.filter_by(record_id=record_id).delete()
    db.session.commit()
    
    # Get old data
    old_data = r.raw_data or r.metadata_json
    
    if not old_data:
        return jsonify({"error": "No old data found"}), 400
    
    # Parse if string
    if isinstance(old_data, str):
        try:
            old_data = json.loads(old_data)
        except:
            return jsonify({"error": "Failed to parse JSON"}), 400
    
    # Convert to list
    if isinstance(old_data, dict):
        old_data = [old_data]
    
    if not isinstance(old_data, list):
        return jsonify({"error": "Data format not supported"}), 400
    
    # Migrate
    migrated_count = 0
    for idx, row_data in enumerate(old_data, 1):
        if isinstance(row_data, dict):
            new_row = DataRow(
                record_id=record_id,
                row_index=idx,
                data=row_data
            )
            db.session.add(new_row)
            migrated_count += 1
    
    db.session.commit()
    
    return jsonify({
        "success": True,
        "message": f"Migrated {migrated_count} rows",
        "migrated_count": migrated_count
    }), 200


@metadata_bp.route("/<int:record_id>/data/<int:row_id>", methods=["PUT"])
@jwt_required()
def update_data_row(record_id, row_id):
    """Update a single data row - ACID compliant"""
    from flask import request
    from flask_jwt_extended import get_jwt
    from ..models import User, DataRow
    
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    
    if claims.get("role") not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403
    
    r = MetadataRecord.query.get(record_id)
    if not r:
        return jsonify({"error": "Record not found"}), 404
    
    row = DataRow.query.filter_by(id=row_id, record_id=record_id).first()
    if not row:
        return jsonify({"error": "Row not found"}), 404
    
    data = request.get_json() or {}
    new_data = data.get('data')
    
    if not isinstance(new_data, dict):
        return jsonify({"error": "data must be an object"}), 400
    
    try:
        row.data = new_data
        row.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Row updated successfully",
            "row": row.to_dict()
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@metadata_bp.route("/<int:record_id>/data/<int:row_id>", methods=["DELETE"])
def delete_data_row(record_id, row_id):
    from flask import request
    
    from flask_jwt_extended import jwt_required
    jwt_required()(lambda: None)()
    """Delete a single data row - ACID compliant"""
    from ..models import User, DataRow
    from flask_jwt_extended import get_jwt
    
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    
    if claims.get("role") not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403
    
    r = MetadataRecord.query.get(record_id)
    if not r:
        return jsonify({"error": "Record not found"}), 404
    
    row = DataRow.query.filter_by(id=row_id, record_id=record_id).first()
    if not row:
        return jsonify({"error": "Row not found"}), 404
    
    try:
        db.session.delete(row)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Row deleted successfully"
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@metadata_bp.route("/<int:record_id>", methods=["PUT"])
@jwt_required()
def update_metadata(record_id):
    from flask_jwt_extended import get_jwt, get_jwt_identity
    from ..models import User
    
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    
    if role not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403
    
    r = MetadataRecord.query.get(record_id)
    if not r:
        return jsonify({"error": "not found"}), 404
    
    user = User.query.get(user_id)
    # Users can only edit their own records, admins can edit all
    if user.role != "admin" and r.created_by != user_id:
        return jsonify({"error": "forbidden"}), 403
    
    data = request.get_json() or {}
    if "name" in data:
        r.name = data["name"]
    # Update dynamic values if provided
    values = data.get("values")
    if isinstance(values, dict):
        fields = {f.field_name: f for f in SchemaField.query.filter_by(schema_id=r.schema_id, is_deleted=False).all()}
        for k, v in values.items():
            if k not in fields:
                if r.schema.allow_additional_fields:
                    continue
                else:
                    return jsonify({"error": f"field '{k}' not defined in schema"}), 400
            f = fields[k]
            fv = FieldValue.query.filter_by(record_id=r.id, schema_field_id=f.id).first()
            if not fv:
                fv = FieldValue(record_id=r.id, schema_field_id=f.id)
                db.session.add(fv)
            # For set_value convenience
            f_type_backup = f.field_type
            try:
                fv.schema_field = f
                fv.set_value(v)
            finally:
                f.field_type = f_type_backup
    if "tag" in data:
        r.tag = data["tag"]
    if "schema_id" in data:
        r.schema_id = data["schema_id"]
    if "asset_type_id" in data:
        r.asset_type_id = data["asset_type_id"]
    db.session.commit()
    return jsonify(r.to_dict(include_values=True))


@metadata_bp.route("/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete_metadata(record_id):
    from flask_jwt_extended import get_jwt, get_jwt_identity
    from ..models import User
    
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    
    r = MetadataRecord.query.get(record_id)
    if not r:
        return jsonify({"error": "not found"}), 404
    
    user = User.query.get(user_id)
    # Users can delete their own records, only admins can delete others
    if role != "admin" and r.created_by != user_id:
        return jsonify({"error": "forbidden"}), 403
    
    if role not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403
    
    db.session.delete(r)
    db.session.commit()
    return jsonify({"message": "deleted"})

@metadata_bp.route("/<int:record_id>/add-fields", methods=["POST"])
@jwt_required()
def add_record_fields(record_id):
    """
    Add new fields to a record (with schema adaptation)
    
    Body: {
        "new_fields": {field_name: value, ...},
        "add_to_schema": true/false
    }
    """
    from flask_jwt_extended import get_jwt
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    
    if role not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403
    
    r = MetadataRecord.query.get(record_id)
    if not r:
        return jsonify({"error": "Record not found"}), 404
    
    data = request.get_json() or {}
    new_fields = data.get('new_fields', {})
    add_to_schema = data.get('add_to_schema', True)
    
    if not new_fields:
        return jsonify({"error": "new_fields required"}), 400
    
    try:
        schema = SchemaModel.query.get(r.schema_id)
        existing_fields = {f.field_name: f.id for f in schema.fields if not f.is_deleted}
        
        # Add fields to schema if requested
        if add_to_schema:
            for field_name, value in new_fields.items():
                if field_name not in existing_fields:
                    # Infer field type
                    field_type = 'string'
                    if isinstance(value, bool):
                        field_type = 'boolean'
                    elif isinstance(value, int):
                        field_type = 'integer'
                    elif isinstance(value, float):
                        field_type = 'float'
                    
                    new_field = SchemaField(
                        schema_id=schema.id,
                        field_name=field_name,
                        field_type=field_type,
                        is_required=False,
                        description=f'Added on {datetime.utcnow().isoformat()}'
                    )
                    db.session.add(new_field)
                    db.session.flush()
                    existing_fields[field_name] = new_field.id
        
        # Update record's raw_data
        parsed_data = r.get_parsed_data() or {}
        if isinstance(parsed_data, dict):
            parsed_data.update(new_fields)
            r.raw_data = _json.dumps(parsed_data)
        
        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"Added {len(new_fields)} fields",
            "schema_updated": add_to_schema
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500


@metadata_bp.route("/<int:record_id>/update-advanced", methods=["PUT"])
def update_record_advanced(record_id):
    """
    Advanced record update with multiple input formats and schema validation
    
    Body: {
        "format": "form" | "json" | "csv",
        "data": {...} or "csv string" or [{}, {}],
        "schema_action": "validate" | "adapt" | "create_new" | "keep_current",
        "new_schema_name": "optional for create_new"
    }
    """
    from flask import request
    
    from flask_jwt_extended import jwt_required, get_jwt_identity
    jwt_required()(lambda: None)()
    
    from flask_jwt_extended import get_jwt
    import csv as csv_lib
    import io
    from datetime import datetime
    
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    
    if role not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403
    
    r = MetadataRecord.query.get(record_id)
    if not r:
        return jsonify({"error": "Record not found"}), 404
    
    data = request.get_json() or {}
    input_format = data.get('format', 'form')  # form, json, csv
    input_data = data.get('data')
    schema_action = data.get('schema_action', 'validate')  # validate, adapt, create_new, keep_current
    new_schema_name = data.get('new_schema_name')
    
    if not input_data:
        return jsonify({"error": "data required"}), 400
    
    try:
        # Parse input based on format
        parsed_data = None
        
        if input_format == 'form' or input_format == 'json':
            # Form/JSON - expect dict or array
            if isinstance(input_data, dict):
                parsed_data = input_data
            elif isinstance(input_data, list):
                parsed_data = input_data
            else:
                return jsonify({"error": "Invalid data format"}), 400
                
        elif input_format == 'csv':
            # CSV string - parse it
            if not isinstance(input_data, str):
                return jsonify({"error": "CSV data must be string"}), 400
            f = io.StringIO(input_data)
            reader = csv_lib.DictReader(f)
            parsed_data = list(reader)
            if not parsed_data:
                return jsonify({"error": "No data found in CSV"}), 400
        else:
            return jsonify({"error": f"Unsupported format: {input_format}"}), 400
        
        # Get schema and existing fields
        schema = SchemaModel.query.get(r.schema_id)
        existing_field_names = {f.field_name for f in schema.fields if not f.is_deleted}
        
        # Detect new fields
        if isinstance(parsed_data, dict):
            data_fields = set(parsed_data.keys())
        elif isinstance(parsed_data, list) and parsed_data:
            data_fields = set(parsed_data[0].keys())
        else:
            data_fields = set()
        
        new_fields = data_fields - existing_field_names
        
        # Handle schema action
        if new_fields and schema_action == 'validate':
            return jsonify({
                "validation_error": True,
                "message": f"New fields detected: {', '.join(new_fields)}",
                "new_fields": list(new_fields),
                "suggest_action": "adapt or create_new"
            }), 400
        
        elif new_fields and schema_action == 'adapt':
            # Add new fields to current schema
            for field_name in new_fields:
                # Infer type from first value
                sample_value = parsed_data.get(field_name) if isinstance(parsed_data, dict) else parsed_data[0].get(field_name)
                field_type = 'string'
                if isinstance(sample_value, bool):
                    field_type = 'boolean'
                elif isinstance(sample_value, int):
                    field_type = 'integer'
                elif isinstance(sample_value, float):
                    field_type = 'float'
                
                new_field = SchemaField(
                    schema_id=schema.id,
                    field_name=field_name,
                    field_type=field_type,
                    is_required=False,
                    description=f'Auto-added on update'
                )
                db.session.add(new_field)
            
        elif new_fields and schema_action == 'create_new':
            # Create new schema with all fields
            if not new_schema_name:
                new_schema_name = f"{schema.name} (Updated {datetime.utcnow().strftime('%Y-%m-%d')})"            
            new_schema = SchemaModel(
                name=new_schema_name,
                version=schema.version + 1,
                asset_type_id=schema.asset_type_id,
                schema_json=schema.schema_json,
                created_by=user_id,
                allow_additional_fields=schema.allow_additional_fields,
                parent_schema_id=schema.id
            )
            db.session.add(new_schema)
            db.session.flush()
            
            # Copy existing fields
            for field in schema.fields:
                if not field.is_deleted:
                    new_field = SchemaField(
                        schema_id=new_schema.id,
                        field_name=field.field_name,
                        field_type=field.field_type,
                        is_required=field.is_required,
                        description=field.description,
                        constraints=field.constraints,
                        default_value=field.default_value
                    )
                    db.session.add(new_field)
            
            # Add new fields
            for field_name in new_fields:
                sample_value = parsed_data.get(field_name) if isinstance(parsed_data, dict) else parsed_data[0].get(field_name)
                field_type = 'string'
                if isinstance(sample_value, bool):
                    field_type = 'boolean'
                elif isinstance(sample_value, int):
                    field_type = 'integer'
                elif isinstance(sample_value, float):
                    field_type = 'float'
                
                new_field = SchemaField(
                    schema_id=new_schema.id,
                    field_name=field_name,
                    field_type=field_type,
                    is_required=False,
                    description='Added from update'
                )
                db.session.add(new_field)
            
            # Update record to use new schema
            r.schema_id = new_schema.id
        
        # Update record data
        r.raw_data = _json.dumps(parsed_data)
        r.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": "Record updated successfully",
            "schema_action": schema_action,
            "new_fields_added": list(new_fields) if new_fields else [],
            "record": r.to_dict(include_values=True)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        import traceback
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
        
        added_count = 0
        
        for field_name, value in new_fields.items():
            if field_name not in existing_fields:
                # Add to schema if enabled
                if add_to_schema and schema.allow_additional_fields:
                    # Infer type from value
                    if isinstance(value, bool):
                        field_type = 'boolean'
                    elif isinstance(value, int):
                        field_type = 'integer'
                    elif isinstance(value, float):
                        field_type = 'float'
                    elif isinstance(value, dict) or isinstance(value, list):
                        field_type = 'json'
                    else:
                        field_type = 'string'
                    
                    new_schema_field = SchemaField(
                        schema_id=r.schema_id,
                        field_name=field_name,
                        field_type=field_type,
                        is_required=False,
                        description='Auto-added field'
                    )
                    db.session.add(new_schema_field)
                    db.session.flush()
                    field_id = new_schema_field.id
                else:
                    continue
            else:
                field_id = existing_fields[field_name]
            
            # Add field value to record
            fv = FieldValue(
                record_id=record_id,
                field_id=field_id,
                value=str(value) if value is not None else None
            )
            db.session.add(fv)
            added_count += 1
        
        db.session.commit()
        
        return jsonify({
            "message": "Fields added",
            "fields_added": added_count,
            "record_id": record_id
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500