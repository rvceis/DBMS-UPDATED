"""
Generic Data Routes - Handle ANY relational data with dynamic schemas
This replaces the metadata-specific approach with a fully generic data management system
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from ..models import MetadataRecord, SchemaModel, SchemaField, FieldValue, AssetType
from ..extensions import db
from ..services.schema_matcher import find_best_schema_from_keys, create_schema_from_metadata
from ..services.validation_engine import ValidationEngine
from datetime import datetime
import os
import json

data_bp = Blueprint("data", __name__)


@data_bp.route("/", methods=["GET"])
@jwt_required()
def list_data():
    """List all data records with filters"""
    schema_id = request.args.get("schema_id", type=int)
    asset_type_id = request.args.get("asset_type_id", type=int)
    tag = request.args.get("tag")
    search = request.args.get("search")
    limit = request.args.get("limit", default=100, type=int)
    offset = request.args.get("offset", default=0, type=int)

    query = MetadataRecord.query
    
    if schema_id:
        query = query.filter_by(schema_id=schema_id)
    if asset_type_id:
        query = query.filter_by(asset_type_id=asset_type_id)
    if tag:
        query = query.filter_by(tag=tag)
    if search:
        query = query.filter(MetadataRecord.name.ilike(f"%{search}%"))
    
    total = query.count()
    records = query.order_by(MetadataRecord.created_at.desc()).limit(limit).offset(offset).all()
    
    return jsonify({
        "records": [r.to_dict(include_values=True) for r in records],
        "total": total,
        "limit": limit,
        "offset": offset
    })


@data_bp.route("/", methods=["POST"])
@jwt_required()
def create_data():
    """
    Create a new data record with dynamic schema support.
    Accepts any JSON data and automatically creates/matches schemas.
    """
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    
    if role not in ("admin", "editor", "viewer"):
        return jsonify({"error": "authentication required"}), 403

    data = request.get_json() or {}
    
    # Extract metadata
    name = data.get("name", "Unnamed Record")
    schema_id = data.get("schema_id")
    asset_type_id = data.get("asset_type_id")
    tag = data.get("tag")
    values = data.get("values") or data.get("data") or {}
    create_new_schema = data.get("create_new_schema", False)
    allow_additional = data.get("allow_additional_fields", True)
    
    if not isinstance(values, dict) or not values:
        return jsonify({"error": "values (dict) required"}), 400

    # Resolve or create schema
    schema = None
    if schema_id:
        schema = SchemaModel.query.get(schema_id)
        if not schema:
            return jsonify({"error": "schema not found"}), 400
    else:
        # Try to find matching schema
        keys = list(values.keys())
        schema, score = find_best_schema_from_keys(keys, asset_type_id=asset_type_id)
        
        if not schema:
            if not create_new_schema:
                return jsonify({
                    "error": "no matching schema found",
                    "hint": "set create_new_schema=true to auto-create"
                }), 400
            
            # Generate schema name if not provided or empty
            schema_name = data.get("schema_name", "").strip()
            if not schema_name:
                # Use record name as base for schema name
                record_name = name.strip() if name else "Record"
                # Remove special characters and spaces
                clean_name = ''.join(c if c.isalnum() else '_' for c in record_name)
                schema_name = f"{clean_name}_schema"
            
            # Ensure asset_type_id is valid (default to 'Other' if not provided)
            final_asset_type_id = asset_type_id
            if not final_asset_type_id:
                from ..models import AssetType
                default_asset_type = AssetType.query.filter_by(name='Other').first()
                if not default_asset_type:
                    # If 'Other' doesn't exist, use the first available
                    default_asset_type = AssetType.query.first()
                if default_asset_type:
                    final_asset_type_id = default_asset_type.id
                else:
                    return jsonify({"error": "No asset types available. Please create at least one asset type."}), 400
            
            # Check if schema with same name and asset type already exists
            existing_schema = SchemaModel.query.filter_by(
                name=schema_name,
                asset_type_id=final_asset_type_id,
                is_active=True
            ).first()
            
            if existing_schema:
                # Use existing schema instead of creating duplicate
                schema = existing_schema
            else:
                # Auto-create schema from data
                schema = create_schema_from_metadata(
                    name=schema_name,
                    metadata=values,
                    asset_type_id=final_asset_type_id,
                    user_id=user_id,
                    allow_additional_fields=allow_additional,
                )

    # Validate values against schema
    validator = ValidationEngine()
    validation_errors = validator.validate_record_values(schema, values)
    if validation_errors:
        return jsonify({
            "error": "Validation failed",
            "validation_errors": validation_errors
        }), 400

    # Create record
    record = MetadataRecord(
        name=name,
        schema_id=schema.id,
        asset_type_id=asset_type_id,
        tag=tag,
        created_by=user_id,
        raw_data=json.dumps(values)
    )
    db.session.add(record)
    db.session.flush()

    # Persist field values using EAV pattern
    fields = {f.field_name: f for f in SchemaField.query.filter_by(
        schema_id=schema.id, is_deleted=False
    ).all()}
    
    for field_name, value in values.items():
        if field_name not in fields:
            if schema.allow_additional_fields:
                continue
            else:
                db.session.rollback()
                return jsonify({"error": f"field '{field_name}' not defined in schema"}), 400
        
        field = fields[field_name]
        field_value = FieldValue(record_id=record.id, schema_field_id=field.id)
        field_value.schema_field = field
        field_value.set_value(value)
        db.session.add(field_value)

    db.session.commit()
    
    return jsonify({
        "message": "Record created successfully",
        "record": record.to_dict(include_values=True),
        "schema": schema.to_dict(include_fields=True)
    }), 201


@data_bp.route("/<int:record_id>", methods=["GET"])
@jwt_required()
def get_data(record_id):
    """Get a single data record"""
    from ..models import User
    
    user_id = int(get_jwt_identity())
    record = MetadataRecord.query.get(record_id)
    
    if not record:
        return jsonify({"error": "not found"}), 404
    
    user = User.query.get(user_id)
    # Users can only see their own records, admins see all
    if user.role != "admin" and record.created_by != user_id:
        return jsonify({"error": "forbidden"}), 403
    
    return jsonify(record.to_dict(include_values=True))


@data_bp.route("/<int:record_id>", methods=["PUT"])
@jwt_required()
def update_data(record_id):
    """Update a data record"""
    from ..models import User
    
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    
    if role not in ("admin", "editor"):
        return jsonify({"error": "admin or editor required"}), 403
    
    record = MetadataRecord.query.get(record_id)
    if not record:
        return jsonify({"error": "not found"}), 404
    
    user = User.query.get(user_id)
    if user.role != "admin" and record.created_by != user_id:
        return jsonify({"error": "forbidden"}), 403
    
    data = request.get_json() or {}
    
    # Update basic fields
    if "name" in data:
        record.name = data["name"]
    if "tag" in data:
        record.tag = data["tag"]
    if "schema_id" in data:
        record.schema_id = data["schema_id"]
    if "asset_type_id" in data:
        record.asset_type_id = data["asset_type_id"]
    
    # Update field values
    values = data.get("values") or data.get("data")
    if isinstance(values, dict):
        # Update raw_data
        record.raw_data = json.dumps(values)
        
        fields = {f.field_name: f for f in SchemaField.query.filter_by(
            schema_id=record.schema_id, is_deleted=False
        ).all()}
        
        for field_name, value in values.items():
            if field_name not in fields:
                if record.schema.allow_additional_fields:
                    continue
                else:
                    return jsonify({"error": f"field '{field_name}' not defined in schema"}), 400
            
            field = fields[field_name]
            field_value = FieldValue.query.filter_by(
                record_id=record.id, schema_field_id=field.id
            ).first()
            
            if not field_value:
                field_value = FieldValue(record_id=record.id, schema_field_id=field.id)
                db.session.add(field_value)
            
            field_value.schema_field = field
            field_value.set_value(value)
    
    db.session.commit()
    return jsonify({
        "message": "Record updated successfully",
        "record": record.to_dict(include_values=True)
    })


@data_bp.route("/<int:record_id>", methods=["DELETE"])
@jwt_required()
def delete_data(record_id):
    """Delete a data record"""
    from ..models import User
    
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    
    record = MetadataRecord.query.get(record_id)
    if not record:
        return jsonify({"error": "not found"}), 404
    
    user = User.query.get(user_id)
    if role != "admin" and record.created_by != user_id:
        return jsonify({"error": "forbidden"}), 403
    
    if role not in ("admin", "editor", "viewer"):
        return jsonify({"error": "authentication required"}), 403
    
    db.session.delete(record)
    db.session.commit()
    
    return jsonify({"message": "Record deleted successfully"})


@data_bp.route("/bulk-preview", methods=["POST"])
@jwt_required()
def bulk_preview_data():
    """
    Preview bulk import and detect similar schemas
    Returns potential matching schemas without creating anything
    """
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    
    if role not in ("admin", "editor", "viewer"):
        return jsonify({"error": "authentication required"}), 403
    
    data = request.get_json() or {}
    records_data = data.get("records") or data.get("data") or []
    asset_type_id = data.get("asset_type_id")
    
    if not isinstance(records_data, list) or not records_data:
        return jsonify({"error": "records (array) required"}), 400

    # Use first record to find similar schemas
    first_record = records_data[0]
    if not isinstance(first_record, dict):
        return jsonify({"error": "each record must be a dict"}), 400

    keys = set(first_record.keys())
    
    # Find schemas with similar fields
    similar_schemas = []
    
    from ..models import SchemaModel, SchemaField
    schemas_to_check = SchemaModel.query.filter_by(is_active=True)
    if asset_type_id:
        schemas_to_check = schemas_to_check.filter_by(asset_type_id=asset_type_id)
    
    for schema in schemas_to_check.all():
        schema_fields = {f.field_name for f in schema.fields if not f.is_deleted}
        
        if not schema_fields:
            continue
        
        # Calculate similarity using improved metrics
        matching_fields = keys & schema_fields
        new_fields_in_data = keys - schema_fields
        missing_fields_in_data = schema_fields - keys
        
        # Primary metric: how much of the data fields exist in schema
        fields_in_schema_percent = (len(matching_fields) / len(keys)) * 100 if len(keys) > 0 else 0
        
        # Secondary metric: penalize if schema has extra fields (but not much)
        extra_field_penalty = (len(missing_fields_in_data) / max(len(schema_fields), 1)) * 20  # Max 20% penalty
        
        similarity = max(0, fields_in_schema_percent - extra_field_penalty)
        
        # Include if there is any overlap; UI will sort by similarity
        if len(matching_fields) >= 1:
            new_fields = list(new_fields_in_data)
            missing_fields = list(missing_fields_in_data)
            
            similar_schemas.append({
                'schema_id': schema.id,
                'schema_name': schema.name,
                'similarity': similarity,
                'new_fields': new_fields,
                'missing_fields': missing_fields,
            })
    
    # Sort by similarity descending
    similar_schemas.sort(key=lambda x: x['similarity'], reverse=True)
    
    return jsonify({
        'record_count': len(records_data),
        'fields_detected': list(keys),
        'similar_schemas': similar_schemas[:5],  # Top 5 similar schemas
        'preview': records_data[:5]  # Show first 5 records
    }), 200


@data_bp.route("/bulk", methods=["POST"])
@jwt_required()
def bulk_create_data():
    """
    Bulk create data records from array of objects.
    Automatically infers schema from first record.
    """
    claims = get_jwt()
    user_id = int(get_jwt_identity())
    role = claims.get("role")
    
    if role not in ("admin", "editor", "viewer"):
        return jsonify({"error": "authentication required"}), 403
    
    data = request.get_json() or {}
    records_data = data.get("records") or data.get("data") or []
    schema_name = data.get("schema_name", "BulkImport")
    asset_type_id = data.get("asset_type_id")
    create_new_schema = data.get("create_new_schema", True)
    schema_choice = data.get("schema_choice")  # NEW: Handle schema choice
    
    if not isinstance(records_data, list) or not records_data:
        return jsonify({"error": "records (array) required"}), 400

    # Use first record to infer/match schema
    first_record = records_data[0]
    if not isinstance(first_record, dict):
        return jsonify({"error": "each record must be a dict"}), 400

    keys = list(first_record.keys())
    
    # Handle schema choice if provided
    schema = None
    if schema_choice:
        choice_action = schema_choice.get('action')
        choice_schema_id = schema_choice.get('schema_id')
        
        # Ensure schema_id is an integer
        if choice_schema_id:
            choice_schema_id = int(choice_schema_id)
        
        if choice_action == 'reuse':
            # Reuse existing schema
            schema = SchemaModel.query.get(choice_schema_id)
            if not schema:
                print(f"❌ Schema not found: ID {choice_schema_id}, Type: {type(choice_schema_id)}")
                return jsonify({"error": f"Selected schema not found (ID: {choice_schema_id})"}), 404
            print(f"✓ BULK IMPORT: REUSING SCHEMA {schema.name} (ID: {schema.id})")
        
        elif choice_action == 'add_fields':
            # Add new fields to existing schema
            schema = SchemaModel.query.get(choice_schema_id)
            if not schema:
                return jsonify({"error": "Selected schema not found"}), 404
            
            from ..models import SchemaField
            existing_fields = {f.field_name for f in schema.fields if not f.is_deleted}
            max_order = max([f.order_index for f in schema.fields if f.order_index] + [0])
            
            # Add missing fields
            for idx, key in enumerate([k for k in keys if k not in existing_fields]):
                field_type = 'string'
                if isinstance(first_record.get(key), bool):
                    field_type = 'boolean'
                elif isinstance(first_record.get(key), int):
                    field_type = 'integer'
                elif isinstance(first_record.get(key), float):
                    field_type = 'float'
                
                new_field = SchemaField(
                    schema_id=schema.id,
                    field_name=key,
                    field_type=field_type,
                    is_required=False,
                    description='Added during bulk import',
                    order_index=max_order + idx + 1
                )
                db.session.add(new_field)
            
            db.session.commit()
            print(f"✓ BULK IMPORT: ADDED FIELDS TO SCHEMA {schema.name} (ID: {schema.id})")
        
        elif choice_action == 'new_version':
            # Create new version of schema
            original_schema = SchemaModel.query.get(choice_schema_id)
            if not original_schema:
                return jsonify({"error": "Selected schema not found"}), 404
            
            from ..models import SchemaField
            new_version = original_schema.version + 1
            schema = SchemaModel(
                name=f"{original_schema.name} (v{new_version})",
                version=new_version,
                asset_type_id=original_schema.asset_type_id,
                schema_json={},
                created_by=user_id,
                parent_schema_id=original_schema.id,
                allow_additional_fields=True
            )
            db.session.add(schema)
            db.session.flush()
            
            # Copy fields from original
            for field in original_schema.fields:
                if not field.is_deleted:
                    new_field = SchemaField(
                        schema_id=schema.id,
                        field_name=field.field_name,
                        field_type=field.field_type,
                        is_required=field.is_required,
                        description=field.description,
                        order_index=field.order_index
                    )
                    db.session.add(new_field)
            
            # Add new fields from data
            existing_fields = {f.field_name for f in original_schema.fields if not f.is_deleted}
            max_order = max([f.order_index for f in original_schema.fields if f.order_index] + [0])
            
            for idx, key in enumerate([k for k in keys if k not in existing_fields]):
                field_type = 'string'
                if isinstance(first_record.get(key), bool):
                    field_type = 'boolean'
                elif isinstance(first_record.get(key), int):
                    field_type = 'integer'
                elif isinstance(first_record.get(key), float):
                    field_type = 'float'
                
                new_field = SchemaField(
                    schema_id=schema.id,
                    field_name=key,
                    field_type=field_type,
                    is_required=False,
                    description='Added in new version',
                    order_index=max_order + idx + 1
                )
                db.session.add(new_field)
            
            db.session.commit()
            print(f"✓ BULK IMPORT: CREATED NEW VERSION {schema.name} (ID: {schema.id})")
        
        elif choice_action == 'create_new':
            # Create completely new schema
            schema = None  # Will be created below
            create_new_schema = True
            print(f"✓ BULK IMPORT: CREATING NEW SCHEMA")
    
    # If no schema yet, create one
    if not schema:
        schema, score = find_best_schema_from_keys(keys, asset_type_id=asset_type_id) if not schema_choice else (None, 0)
        
        if not schema and create_new_schema:
            # Ensure schema name is not empty
            if schema_name and schema_name.strip():
                final_schema_name = schema_name.strip()
            else:
                # Use first record's values to generate meaningful name
                if first_record:
                    # Try to find a name field
                    name_field = first_record.get('name') or first_record.get('title') or first_record.get('product_name') or 'BulkImport'
                    clean_name = ''.join(c if c.isalnum() else '_' for c in str(name_field)[:30])
                    final_schema_name = f"{clean_name}_schema"
                else:
                    final_schema_name = f"BulkImport_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Ensure asset_type_id is valid (default to 'Other' if not provided)
            final_asset_type_id = asset_type_id
            if not final_asset_type_id:
                from ..models import AssetType
                default_asset_type = AssetType.query.filter_by(name='Other').first()
                if not default_asset_type:
                    default_asset_type = AssetType.query.first()
                if default_asset_type:
                    final_asset_type_id = default_asset_type.id
                else:
                    return jsonify({"error": "No asset types available. Please create at least one asset type."}), 400
            
            # Check if schema with same name already exists
            existing_schema = SchemaModel.query.filter_by(
                name=final_schema_name,
                asset_type_id=final_asset_type_id,
                is_active=True
            ).first()
            
            if existing_schema:
                schema = existing_schema
            else:
                schema = create_schema_from_metadata(
                    name=final_schema_name,
                    metadata=first_record,
                    asset_type_id=final_asset_type_id,
                    user_id=user_id,
                    allow_additional_fields=True,
                )
        elif not schema:
            return jsonify({"error": "no matching schema found"}), 400

    # Create all records
    created_records = []
    validator = ValidationEngine()
    
    for idx, record_values in enumerate(records_data):
        if not isinstance(record_values, dict):
            continue
            
        # Validate
        validation_errors = validator.validate_record_values(schema, record_values)
        if validation_errors:
            return jsonify({
                "error": f"Validation failed for record {idx}",
                "validation_errors": validation_errors
            }), 400
        
        # Create record
        record = MetadataRecord(
            name=record_values.get("name", f"Record {idx + 1}"),
            schema_id=schema.id,
            asset_type_id=asset_type_id,
            tag=data.get("tag"),
            created_by=user_id,
            raw_data=json.dumps(record_values)
        )
        db.session.add(record)
        db.session.flush()
        
        # Add field values
        fields = {f.field_name: f for f in SchemaField.query.filter_by(
            schema_id=schema.id, is_deleted=False
        ).all()}
        
        for field_name, value in record_values.items():
            if field_name not in fields:
                continue
            
            field = fields[field_name]
            field_value = FieldValue(record_id=record.id, schema_field_id=field.id)
            field_value.schema_field = field
            field_value.set_value(value)
            db.session.add(field_value)
        
        created_records.append(record)
    
    db.session.commit()
    
    return jsonify({
        "message": f"Created {len(created_records)} records",
        "count": len(created_records),
        "schema": schema.to_dict(include_fields=True),
        "records": [r.to_dict(include_values=True) for r in created_records]
    }), 201


@data_bp.route("/suggest-schema", methods=["POST"])
@jwt_required()
def suggest_schema():
    """Suggest matching schemas for given data"""
    data = request.get_json() or {}
    values = data.get("values") or data.get("data") or {}
    asset_type_id = data.get("asset_type_id")
    
    if not isinstance(values, dict):
        return jsonify({"error": "values (dict) required"}), 400
    
    keys = list(values.keys())
    schema, score = find_best_schema_from_keys(keys, asset_type_id=asset_type_id)
    
    if schema:
        return jsonify({
            "match_found": True,
            "schema": schema.to_dict(include_fields=True),
            "match_score": score
        })
    else:
        return jsonify({
            "match_found": False,
            "message": "No matching schema found. Consider creating a new schema."
        })


@data_bp.route("/schema/<int:schema_id>/records", methods=["GET"])
@jwt_required()
def get_schema_records(schema_id):
    """Get all records in a schema with optional filtering"""
    limit = request.args.get("limit", default=100, type=int)
    offset = request.args.get("offset", default=0, type=int)
    search = request.args.get("search")
    tag = request.args.get("tag")
    
    # Verify schema exists
    schema = SchemaModel.query.get(schema_id)
    if not schema:
        return jsonify({"error": "Schema not found"}), 404
    
    query = MetadataRecord.query.filter_by(schema_id=schema_id)
    
    if search:
        query = query.filter(MetadataRecord.name.ilike(f"%{search}%"))
    if tag:
        query = query.filter_by(tag=tag)
    
    total = query.count()
    records = query.order_by(MetadataRecord.created_at.desc()).limit(limit).offset(offset).all()
    
    return jsonify({
        "schema": schema.to_dict(include_fields=True),
        "records": [r.to_dict(include_values=True) for r in records],
        "total": total,
        "limit": limit,
        "offset": offset
    })


@data_bp.route("/schema/<int:schema_id>/content", methods=["GET"])
@jwt_required()
def get_schema_content_summary(schema_id):
    """Get schema content summary with record count and field info"""
    schema = SchemaModel.query.get(schema_id)
    if not schema:
        return jsonify({"error": "Schema not found"}), 404
    
    # Count records
    record_count = MetadataRecord.query.filter_by(schema_id=schema_id).count()
    
    # Get field information
    fields = SchemaField.query.filter_by(schema_id=schema_id, is_deleted=False).all()
    field_info = [
        {
            "name": f.field_name,
            "type": f.field_type,
            "required": f.is_required,
            "description": f.description
        }
        for f in fields
    ]
    
    # Get unique tags
    tags = db.session.query(MetadataRecord.tag).filter(
        MetadataRecord.schema_id == schema_id,
        MetadataRecord.tag.isnot(None)
    ).distinct().all()
    
    # Get asset types used
    asset_types_used = db.session.query(MetadataRecord.asset_type_id).filter(
        MetadataRecord.schema_id == schema_id,
        MetadataRecord.asset_type_id.isnot(None)
    ).distinct().all()
    
    asset_types_info = []
    for (at_id,) in asset_types_used:
        if at_id:
            at = AssetType.query.get(at_id)
            if at:
                asset_types_info.append({"id": at.id, "name": at.name})
    
    return jsonify({
        "schema": schema.to_dict(include_fields=False),
        "summary": {
            "record_count": record_count,
            "field_count": len(fields),
            "fields": field_info,
            "tags": [tag[0] for tag in tags if tag[0]],
            "asset_types": asset_types_info
        }
    })
