from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..models import SchemaModel
from ..extensions import db

schemas_bp = Blueprint("schemas", __name__)


@schemas_bp.route("/", methods=["GET"])
def list_schemas():
    from ..models import User
    schemas = SchemaModel.query.order_by(SchemaModel.version.desc()).all()
    result = []
    for s in schemas:
        user_name = None
        if s.created_by:
            user = User.query.get(s.created_by)
            user_name = user.username if user else f"User #{s.created_by}"
        result.append({
            "id": s.id,
            "version": s.version,
            "schema_json": s.schema_json,
            "created_by": s.created_by,
            "created_by_name": user_name,
        })
    return jsonify(result)


@schemas_bp.route("/", methods=["POST"])
@jwt_required()
def create_schema():
    from flask_jwt_extended import get_jwt, get_jwt_identity
    from ..models import ChangeLog
    claims = get_jwt()
    user_id = get_jwt_identity()
    if claims.get("role") not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403
    data = request.get_json() or {}
    schema_json = data.get("schema_json")
    if not schema_json:
        return jsonify({"error": "schema_json required"}), 400
    # compute next version
    latest = SchemaModel.query.order_by(SchemaModel.version.desc()).first()
    version = (latest.version + 1) if latest else 1
    s = SchemaModel(version=version, schema_json=schema_json, created_by=int(user_id))
    db.session.add(s)
    db.session.flush()  # Get the schema ID before committing
    
    # Create change log entry
    log = ChangeLog(
        schema_id=s.id,
        change_type="created",
        description=f"Schema v{version} created",
        changed_by=int(user_id)
    )
    db.session.add(log)
    db.session.commit()
    return jsonify({"id": s.id, "version": s.version}), 201


@schemas_bp.route("/<int:schema_id>/logs", methods=["GET"])
def get_schema_logs(schema_id):
    """Get change log history for a specific schema"""
    from ..models import ChangeLog, User
    
    schema = SchemaModel.query.get(schema_id)
    if not schema:
        return jsonify({"error": "schema not found"}), 404
    
    logs = ChangeLog.query.filter_by(schema_id=schema_id).order_by(ChangeLog.timestamp.desc()).all()
    result = []
    for log in logs:
        user_name = None
        if log.changed_by:
            user = User.query.get(log.changed_by)
            user_name = user.username if user else f"User #{log.changed_by}"
        result.append({
            "id": log.id,
            "change_type": log.change_type,
            "description": log.description,
            "changed_by": log.changed_by,
            "changed_by_name": user_name,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        })
    return jsonify(result)


@schemas_bp.route("/logs", methods=["GET"])
def get_all_logs():
    """Get all schema change logs (admin view)"""
    from ..models import ChangeLog, User
    
    logs = ChangeLog.query.order_by(ChangeLog.timestamp.desc()).limit(100).all()
    result = []
    for log in logs:
        user_name = None
        if log.changed_by:
            user = User.query.get(log.changed_by)
            user_name = user.username if user else f"User #{log.changed_by}"
        
        schema = SchemaModel.query.get(log.schema_id) if log.schema_id else None
        result.append({
            "id": log.id,
            "schema_id": log.schema_id,
            "schema_version": schema.version if schema else None,
            "change_type": log.change_type,
            "description": log.description,
            "changed_by": log.changed_by,
            "changed_by_name": user_name,
            "timestamp": log.timestamp.isoformat() if log.timestamp else None
        })
    return jsonify(result)


@schemas_bp.route("/<int:schema_id>", methods=["DELETE"])
@jwt_required()
def delete_schema(schema_id):
    """Delete schema and all related records (CASCADE)"""
    from flask_jwt_extended import get_jwt
    from ..models import MetadataRecord
    
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    user_role = claims.get("role")
    
    schema = SchemaModel.query.get(schema_id)
    if not schema:
        return jsonify({"error": "schema not found"}), 404
    
    # Check permissions: Only admin can delete any schema, editor can only delete their own
    if user_role == "admin":
        # Admin can delete any schema
        pass
    elif user_role == "editor":
        # Editor can only delete their own schemas
        if schema.created_by != user_id:
            return jsonify({
                "error": "You can only delete schemas you created",
                "reason": "unauthorized",
                "created_by": schema.created_by,
                "your_user_id": user_id
            }), 403
    else:
        # Viewer and others cannot delete
        return jsonify({
            "error": "Permission denied. Only admin and schema creator can delete schemas",
            "reason": "insufficient_permissions"
        }), 403
    
    # Save schema name before deletion
    schema_name = schema.name
    
    # Count related records
    record_count = MetadataRecord.query.filter_by(schema_id=schema_id).count()
    
    try:
        # Delete schema (CASCADE will delete all related records, fields, logs)
        db.session.delete(schema)
        db.session.commit()
        
        return jsonify({
            "success": True,
            "message": f"Schema '{schema_name}' deleted",
            "records_deleted": record_count
        }), 200
    except Exception as e:
        db.session.rollback()
        import traceback
        print(f"\n❌ ERROR DELETING SCHEMA {schema_id}:")
        traceback.print_exc()
        print(f"Exception type: {type(e).__name__}")
        print(f"Exception message: {str(e)}\n")
        return jsonify({"error": f"Failed to delete schema: {str(e)}"}), 500

@schemas_bp.route("/export/json", methods=["GET"])
@jwt_required()
def export_schemas_json():
    """Export all schemas as JSON - Available to all authenticated roles"""
    from ..models import User
    import json
    
    schemas = SchemaModel.query.order_by(SchemaModel.version.desc()).all()
    result = []
    
    for s in schemas:
        user_name = None
        if s.created_by:
            user = User.query.get(s.created_by)
            user_name = user.username if user else f"User #{s.created_by}"
        
        result.append({
            "id": s.id,
            "version": s.version,
            "schema_json": s.schema_json,
            "created_by": s.created_by,
            "created_by_name": user_name,
        })
    
    return jsonify({
        "export_type": "schemas_json",
        "export_date": __import__('datetime').datetime.now().isoformat(),
        "total_schemas": len(result),
        "schemas": result
    }), 200


@schemas_bp.route("/export/sql", methods=["GET"])
@jwt_required()
def export_schemas_sql():
    """Export all schemas as SQL CREATE TABLE statements - Available to all authenticated roles"""
    from ..models import User
    import json
    
    schemas = SchemaModel.query.order_by(SchemaModel.id.asc()).all()
    sql_statements = []
    
    for s in schemas:
        user_name = None
        if s.created_by:
            user = User.query.get(s.created_by)
            user_name = user.username if user else f"User #{s.created_by}"
        
        # Parse schema_json to get fields
        schema_def = s.schema_json if isinstance(s.schema_json, dict) else json.loads(s.schema_json) if isinstance(s.schema_json, str) else {}
        table_name = schema_def.get('name', f'schema_{s.id}').lower().replace(' ', '_')
        
        # Build CREATE TABLE statement
        sql_lines = [
            f"-- Schema ID: {s.id}, Version: {s.version}",
            f"-- Created by: {user_name}",
            f"CREATE TABLE IF NOT EXISTS {table_name} (",
            "    id SERIAL PRIMARY KEY,"
        ]
        
        # Add fields as columns
        fields = schema_def.get('fields', [])
        for i, field in enumerate(fields):
            field_name = field.get('field_name', f'field_{i}').lower().replace(' ', '_')
            field_type = field.get('field_type', 'TEXT').upper()
            
            # Map data types
            sql_type = map_to_sql_type(field_type)
            
            # Add constraints
            constraints = field.get('constraints', {})
            sql_constraint = ""
            if constraints.get('required'):
                sql_constraint += " NOT NULL"
            if constraints.get('unique'):
                sql_constraint += " UNIQUE"
            
            comma = "," if i < len(fields) - 1 else ""
            sql_lines.append(f"    {field_name} {sql_type}{sql_constraint}{comma}")
        
        sql_lines.append(");")
        sql_statements.append("\n".join(sql_lines))
    
    return jsonify({
        "export_type": "schemas_sql",
        "export_date": __import__('datetime').datetime.now().isoformat(),
        "total_schemas": len(schemas),
        "database_type": "postgresql",
        "sql_statements": sql_statements,
        "combined_sql": "\n\n".join(sql_statements)
    }), 200


@schemas_bp.route("/<int:schema_id>/export/json", methods=["GET"])
@jwt_required()
def export_schema_json(schema_id):
    """Export a single schema as JSON - Available to all authenticated roles"""
    from ..models import User
    
    schema = SchemaModel.query.get(schema_id)
    if not schema:
        return jsonify({"error": "schema not found"}), 404
    
    user_name = None
    if schema.created_by:
        user = User.query.get(schema.created_by)
        user_name = user.username if user else f"User #{schema.created_by}"
    
    return jsonify({
        "export_type": "schema_json",
        "export_date": __import__('datetime').datetime.now().isoformat(),
        "id": schema.id,
        "version": schema.version,
        "schema_json": schema.schema_json,
        "created_by": schema.created_by,
        "created_by_name": user_name,
    }), 200


@schemas_bp.route("/<int:schema_id>/export/sql", methods=["GET"])
@jwt_required()
def export_schema_sql(schema_id):
    """Export a single schema as SQL CREATE TABLE statement - Available to all authenticated roles"""
    from ..models import User
    import json
    
    schema = SchemaModel.query.get(schema_id)
    if not schema:
        return jsonify({"error": "schema not found"}), 404
    
    user_name = None
    if schema.created_by:
        user = User.query.get(schema.created_by)
        user_name = user.username if user else f"User #{schema.created_by}"
    
    # Parse schema_json to get fields
    schema_def = schema.schema_json if isinstance(schema.schema_json, dict) else json.loads(schema.schema_json) if isinstance(schema.schema_json, str) else {}
    table_name = schema_def.get('name', f'schema_{schema.id}').lower().replace(' ', '_')
    
    # Build CREATE TABLE statement
    sql_lines = [
        f"-- Schema ID: {schema.id}, Version: {schema.version}",
        f"-- Created by: {user_name}",
        f"CREATE TABLE IF NOT EXISTS {table_name} (",
        "    id SERIAL PRIMARY KEY,"
    ]
    
    # Add fields as columns
    fields = schema_def.get('fields', [])
    for i, field in enumerate(fields):
        field_name = field.get('field_name', f'field_{i}').lower().replace(' ', '_')
        field_type = field.get('field_type', 'TEXT').upper()
        
        # Map data types
        sql_type = map_to_sql_type(field_type)
        
        # Add constraints
        constraints = field.get('constraints', {})
        sql_constraint = ""
        if constraints.get('required'):
            sql_constraint += " NOT NULL"
        if constraints.get('unique'):
            sql_constraint += " UNIQUE"
        
        comma = "," if i < len(fields) - 1 else ""
        sql_lines.append(f"    {field_name} {sql_type}{sql_constraint}{comma}")
    
    sql_lines.append(");")
    sql_statement = "\n".join(sql_lines)
    
    return jsonify({
        "export_type": "schema_sql",
        "export_date": __import__('datetime').datetime.now().isoformat(),
        "id": schema.id,
        "version": schema.version,
        "database_type": "postgresql",
        "table_name": table_name,
        "sql_statement": sql_statement,
        "created_by": schema.created_by,
        "created_by_name": user_name,
    }), 200


@schemas_bp.route("/<int:schema_id>/export/download/<format>", methods=["GET"])
@jwt_required()
def download_schema_export(schema_id, format):
    """Download schema export in specified format (json, sql) - Available to all authenticated roles"""
    from flask import send_file
    from io import BytesIO
    from ..models import User
    import json
    
    if format not in ["json", "sql"]:
        return jsonify({"error": "invalid format. Use 'json' or 'sql'"}), 400
    
    schema = SchemaModel.query.get(schema_id)
    if not schema:
        return jsonify({"error": "schema not found"}), 404
    
    user_name = None
    if schema.created_by:
        user = User.query.get(schema.created_by)
        user_name = user.username if user else f"User #{schema.created_by}"
    
    schema_def = schema.schema_json if isinstance(schema.schema_json, dict) else json.loads(schema.schema_json) if isinstance(schema.schema_json, str) else {}
    schema_name = schema_def.get('name', f'schema_{schema.id}')
    
    if format == "json":
        # Export as JSON
        export_data = {
            "schema_id": schema.id,
            "schema_name": schema_name,
            "version": schema.version,
            "created_by": user_name,
            "schema_definition": schema.schema_json
        }
        content = json.dumps(export_data, indent=2)
        mimetype = "application/json"
        filename = f"{schema_name}_v{schema.version}.json"
    
    else:  # format == "sql"
        # Export as SQL
        table_name = schema_name.lower().replace(' ', '_')
        sql_lines = [
            f"-- Schema: {schema_name}",
            f"-- Version: {schema.version}",
            f"-- Created by: {user_name}",
            f"-- Exported: {__import__('datetime').datetime.now().isoformat()}",
            "",
            f"CREATE TABLE IF NOT EXISTS {table_name} (",
            "    id SERIAL PRIMARY KEY,"
        ]
        
        fields = schema_def.get('fields', [])
        for i, field in enumerate(fields):
            field_name = field.get('field_name', f'field_{i}').lower().replace(' ', '_')
            field_type = field.get('field_type', 'TEXT').upper()
            sql_type = map_to_sql_type(field_type)
            
            constraints = field.get('constraints', {})
            sql_constraint = ""
            if constraints.get('required'):
                sql_constraint += " NOT NULL"
            if constraints.get('unique'):
                sql_constraint += " UNIQUE"
            
            comma = "," if i < len(fields) - 1 else ""
            sql_lines.append(f"    {field_name} {sql_type}{sql_constraint}{comma}")
        
        sql_lines.append(");")
        content = "\n".join(sql_lines)
        mimetype = "text/plain"
        filename = f"{schema_name}_v{schema.version}.sql"
    
    # Create file-like object
    file_obj = BytesIO(content.encode('utf-8'))
    file_obj.seek(0)
    
    return send_file(
        file_obj,
        mimetype=mimetype,
        as_attachment=True,
        download_name=filename
    )


def map_to_sql_type(field_type):
    """Map application field types to SQL types"""
    type_mapping = {
        'integer': 'INTEGER',
        'int': 'INTEGER',
        'float': 'FLOAT',
        'double': 'DOUBLE PRECISION',
        'string': 'VARCHAR(255)',
        'text': 'TEXT',
        'boolean': 'BOOLEAN',
        'bool': 'BOOLEAN',
        'date': 'DATE',
        'datetime': 'TIMESTAMP',
        'timestamp': 'TIMESTAMP',
        'array': 'TEXT[]',
        'json': 'JSONB',
        'object': 'JSONB',
    }
    return type_mapping.get(field_type.lower(), 'TEXT')