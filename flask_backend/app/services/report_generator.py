"""
Report Generator Service
Orchestrates report generation with multi-table and content inclusion support
"""
import os
import time
import json
from datetime import datetime
from typing import Dict, Optional, List
from ..models import ReportTemplate, ReportExecution, SchemaModel, MetadataRecord, SchemaField
from ..extensions import db
from .report_query_builder import ReportQueryBuilder
from .report_export_service import ReportExportService


class ReportGenerator:
    """Main report generation orchestrator"""
    
    def __init__(self, reports_dir: str):
        self.query_builder = ReportQueryBuilder()
        self.exporter = ReportExportService(reports_dir)
        self.reports_dir = reports_dir
    
    def generate_report(
        self,
        template_id: int,
        format: str,
        user_id: int,
        params: Optional[Dict] = None
    ) -> ReportExecution:
        """
        Generate a report from template (supports multi-table and content inclusion)
        
        Args:
            template_id: Report template ID
            format: 'csv' or 'pdf'
            user_id: User requesting the report
            params: Runtime parameters to override config
        
        Returns:
            ReportExecution object
        """
        template = ReportTemplate.query.get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Support both legacy (single schema) and new (multi-table) modes
        if template.table_configs:
            return self._generate_multitable_report(template, format, user_id, params)
        elif template.schema_id:
            return self._generate_single_table_report(template, format, user_id, params)
        else:
            raise ValueError(f"Template '{template.name}' (ID: {template_id}) has no associated schema or table configs. " +
                           f"Please configure the template with either a schema_id or table_configs before generating reports.")
    
    def _generate_multitable_report(
        self,
        template: ReportTemplate,
        format: str,
        user_id: int,
        params: Optional[Dict] = None
    ) -> ReportExecution:
        """Generate report from multiple tables with content inclusion"""
        execution = ReportExecution(
            template_id=template.id,
            user_id=user_id,
            trigger_type='manual',
            format=format,
            status='running',
            query_params=params or {}
        )
        db.session.add(execution)
        db.session.commit()
        
        try:
            start_time = time.time()
            report_data = self._collect_multitable_data(template, params or {})
            
            # Generate filename
            timestamp = int(time.time())
            filename = f"report_{template.id}_{execution.id}_{timestamp}.{format}"
            
            # Export based on format
            if format == 'csv':
                filepath = self.exporter.export_multitable_csv(report_data, filename)
            elif format == 'pdf':
                pdf_config = template.pdf_config or {}
                pdf_config['title'] = template.name
                filepath = self.exporter.export_multitable_pdf(report_data, pdf_config, filename)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Count total rows
            total_rows = sum(1 for table in report_data['tables'] 
                            for item in table.get('data', []) if item.get('type') == 'record')
            
            # Update execution
            execution.completed_at = datetime.utcnow()
            execution.status = 'completed'
            execution.row_count = total_rows
            execution.file_path = filepath
            execution.file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
            execution.execution_time_ms = int((time.time() - start_time) * 1000)
            
        except Exception as e:
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            raise
        finally:
            db.session.commit()
        
        return execution
    
    def _collect_multitable_data(self, template: ReportTemplate, params: Dict) -> Dict:
        """Collect data from multiple tables with content inclusion options"""
        report_data = {
            'title': template.name,
            'description': template.description,
            'generated_at': datetime.utcnow().isoformat(),
            'include_records': template.include_records,
            'include_metadata': template.include_metadata,
            'include_schema_details': template.include_schema_details,
            'include_summary': template.include_summary,
            'tables': []
        }
        
        for table_config in template.table_configs:
            schema_id = table_config.get('schema_id')
            schema = SchemaModel.query.get(schema_id)
            if not schema:
                continue
            
            table_data = {
                'schema_id': schema_id,
                'schema_name': schema.name,
                'schema_description': schema.description,
                'data': []
            }
            
            # Add schema details if requested
            if template.include_schema_details:
                table_data['data'].append({
                    'type': 'schema_info',
                    'schema_name': schema.name,
                    'schema_description': schema.description,
                    'created_at': schema.created_at.isoformat() if schema.created_at else None,
                    'updated_at': schema.updated_at.isoformat() if schema.updated_at else None,
                })
            
            # Add metadata if requested
            if template.include_metadata:
                fields = SchemaField.query.filter_by(schema_id=schema_id).all()
                for field in fields:
                    table_data['data'].append({
                        'type': 'field_metadata',
                        'field_name': field.field_name,
                        'field_type': field.field_type,
                        'is_searchable': field.is_searchable,
                        'is_required': getattr(field, 'is_required', False),
                        'description': getattr(field, 'description', None),
                    })
            
            # Add summary if requested
            if template.include_summary:
                record_count = MetadataRecord.query.filter_by(schema_id=schema_id).count()
                table_data['data'].append({
                    'type': 'summary',
                    'total_records': record_count,
                    'total_fields': len(schema.schema_fields) if hasattr(schema, 'schema_fields') else 0,
                })
            
            # Add actual record content if requested
            if template.include_records:
                # Build query config from table config
                query_config = {
                    'fields': table_config.get('fields', []),
                    'filters': table_config.get('filters', []),
                    'sort': table_config.get('sort', []),
                    'limit': table_config.get('limit', 10000)
                }
                
                # Merge with runtime params
                query_config = self._merge_params(query_config, params)
                
                # Query records
                records = self._query_records(schema, query_config)
                for record in records:
                    table_data['data'].append({
                        'type': 'record',
                        'record_id': record.get('id'),
                        'record_name': record.get('name'),
                        'content': {k: v for k, v in record.items() if k not in ['id', 'name', 'type']},
                    })
            
            report_data['tables'].append(table_data)
        
        return report_data
    
    def _query_records(self, schema: SchemaModel, query_config: Dict) -> List[Dict]:
        """Query records for a schema with field selection and filtering"""
        from ..models import DataRow
        
        query = MetadataRecord.query.filter_by(schema_id=schema.id)
        
        # Apply limit (for records, not expanded rows)
        limit = query_config.get('limit', 10000)
        query = query.limit(limit)
        
        # Get fields to select
        fields = query_config.get('fields', [])
        
        # Execute and format
        records = query.all()
        result = []
        
        for record in records:
            # FIRST: Check DataRow table (new approach for bulk imports)
            data_rows = DataRow.query.filter_by(record_id=record.id).all()
            
            if data_rows:
                # Data stored in separate DataRow table
                for data_row in data_rows:
                    record_dict = {
                        'record_id': record.id,
                        'record_name': record.name,
                        'row_index': data_row.row_index,
                    }
                    row_data = data_row.data or {}
                    if isinstance(row_data, dict):
                        if fields:
                            for field in fields:
                                record_dict[field] = row_data.get(field)
                        else:
                            record_dict.update(row_data)
                    result.append(record_dict)
            else:
                # FALLBACK: Get data from raw_data or metadata_json (legacy)
                record_data = record.raw_data or record.metadata_json or {}
                # Parse if string
                if isinstance(record_data, str):
                    try:
                        record_data = json.loads(record_data)
                    except:
                        record_data = {}
                
                # Handle array format (bulk import) - expand all rows
                if isinstance(record_data, list):
                    for idx, row_data in enumerate(record_data):
                        if isinstance(row_data, dict):
                            record_dict = {
                                'record_id': record.id,
                                'record_name': record.name,
                                'row_index': idx + 1,
                            }
                            # Add selected fields or all fields if none specified
                            if fields:
                                for field in fields:
                                    record_dict[field] = row_data.get(field)
                            else:
                                record_dict.update(row_data)
                            result.append(record_dict)
                elif isinstance(record_data, dict) and record_data:
                    # Single object format with actual data
                    record_dict = {
                        'id': record.id,
                        'name': record.name,
                    }
                    # Add selected fields or all fields if none specified
                    if fields:
                        for field in fields:
                            record_dict[field] = record_data.get(field)
                    else:
                        record_dict.update(record_data)
                    result.append(record_dict)
        
        return result
    
    def _generate_single_table_report(
        self,
        template: ReportTemplate,
        format: str,
        user_id: int,
        params: Optional[Dict] = None
    ) -> ReportExecution:
        """Generate legacy single-table report for backward compatibility"""
        from ..models import DataRow
        
        # Create execution record
        execution = ReportExecution(
            template_id=template.id,
            user_id=user_id,
            trigger_type='manual',
            format=format,
            status='running',
            query_params=params or {}
        )
        db.session.add(execution)
        db.session.commit()
        
        try:
            start_time = time.time()
            
            # Build query config (merge template config with runtime params)
            query_config = self._merge_params(template.query_config or {}, params or {})
            
            # Query all records with their full data
            query = MetadataRecord.query.filter_by(schema_id=template.schema_id)
            
            # Apply limit
            limit = query_config.get('limit', 10000)
            query = query.limit(limit)
            
            # Execute and format data
            records = query.all()
            data = []
            fields = query_config.get('fields', [])
            all_fields = set()
            
            for record in records:
                # FIRST: Check DataRow table (new approach for bulk imports)
                data_rows = DataRow.query.filter_by(record_id=record.id).all()
                
                if data_rows:
                    # Data stored in separate DataRow table
                    for data_row in data_rows:
                        row = {
                            'record_id': record.id,
                            'record_name': record.name,
                            'row_index': data_row.row_index,
                        }
                        row_data = data_row.data or {}
                        if isinstance(row_data, dict):
                            if fields:
                                for field in fields:
                                    row[field] = row_data.get(field)
                            else:
                                row.update(row_data)
                                all_fields.update(row_data.keys())
                        data.append(row)
                else:
                    # FALLBACK: Get data from raw_data or metadata_json (legacy)
                    record_data = record.raw_data or record.metadata_json or {}
                    # Parse if string
                    if isinstance(record_data, str):
                        try:
                            record_data = json.loads(record_data)
                        except:
                            record_data = {}
                    
                    # Handle array format (bulk import)
                    if isinstance(record_data, list):
                        for idx, row_data in enumerate(record_data):
                            if isinstance(row_data, dict):
                                row = {
                                    'record_id': record.id,
                                    'record_name': record.name,
                                    'row_index': idx + 1,
                                }
                                if fields:
                                    for field in fields:
                                        row[field] = row_data.get(field)
                                else:
                                    row.update(row_data)
                                    all_fields.update(row_data.keys())
                                data.append(row)
                    elif isinstance(record_data, dict) and record_data:
                        row = {
                            'id': record.id,
                            'name': record.name,
                            'created_at': record.created_at.isoformat() if record.created_at else None,
                        }
                        if fields:
                            for field in fields:
                                row[field] = record_data.get(field)
                        else:
                            row.update(record_data)
                            all_fields.update(record_data.keys())
                        data.append(row)
            
            # Generate filename
            timestamp = int(time.time())
            filename = f"report_{template.id}_{execution.id}_{timestamp}.{format}"
            
            # Get all field names for export
            if not fields and data:
                fields = list(data[0].keys())
            
            # Export based on format
            if format == 'csv':
                filepath = self.exporter.export_csv(data, fields, filename)
            elif format == 'pdf':
                pdf_config = template.pdf_config or {}
                pdf_config['title'] = template.name
                pdf_config['filters'] = query_config.get('filters', [])
                filepath = self.exporter.export_pdf(data, fields, pdf_config, filename)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Update execution
            execution.completed_at = datetime.utcnow()
            execution.status = 'completed'
            execution.row_count = len(data)
            execution.file_path = filepath
            execution.file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
            execution.execution_time_ms = int((time.time() - start_time) * 1000)
            
        except Exception as e:
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            raise
        finally:
            db.session.commit()
        
        return execution
    
    def generate_adhoc_report(
        self,
        schema_id: int,
        query_config: dict,
        format: str,
        user_id: int,
        report_name: str = "Ad-hoc Report"
    ) -> ReportExecution:
        """
        Generate a report without a saved template
        
        Args:
            schema_id: Schema to query
            query_config: Query configuration
            format: 'csv' or 'pdf'
            user_id: User requesting the report
            report_name: Name for the report
        
        Returns:
            ReportExecution object
        """
        schema = SchemaModel.query.get(schema_id)
        if not schema:
            raise ValueError(f"Schema {schema_id} not found")
        
        # Create execution record (no template)
        execution = ReportExecution(
            template_id=None,
            user_id=user_id,
            trigger_type='adhoc',
            format=format,
            status='running',
            query_params=query_config
        )
        db.session.add(execution)
        db.session.commit()
        
        try:
            start_time = time.time()
            
            # Query all records with their full data
            query = MetadataRecord.query.filter_by(schema_id=schema_id)
            
            # Apply filters if any
            for filter_item in query_config.get('filters', []):
                field_name = filter_item.get('field')
                operator = filter_item.get('operator', 'eq')
                value = filter_item.get('value')
                
                if operator == 'eq':
                    query = query.filter(MetadataRecord.raw_data[field_name].astext == str(value))
                elif operator == 'contains':
                    query = query.filter(MetadataRecord.raw_data[field_name].astext.ilike(f'%{value}%'))
                elif operator == 'gt':
                    query = query.filter(MetadataRecord.raw_data[field_name].astext.cast(db.Float) > float(value))
                elif operator == 'lt':
                    query = query.filter(MetadataRecord.raw_data[field_name].astext.cast(db.Float) < float(value))
            
            # Apply sorting
            for sort_item in query_config.get('sort', []):
                field_name = sort_item.get('field')
                direction = sort_item.get('direction', 'asc')
                if direction == 'asc':
                    query = query.order_by(MetadataRecord.raw_data[field_name].astext.asc())
                else:
                    query = query.order_by(MetadataRecord.raw_data[field_name].astext.desc())
            
            # Apply limit
            limit = query_config.get('limit', 10000)
            query = query.limit(limit)
            
            # Execute and format data
            records = query.all()
            data = []
            fields = query_config.get('fields', [])
            
            # If no fields specified, extract them from the first record's raw_data
            if not fields and records:
                first_record_data = records[0].raw_data or records[0].metadata_json or {}
                if isinstance(first_record_data, dict):
                    fields = list(first_record_data.keys())
            
            for record in records:
                row = {
                    'id': record.id,
                    'name': record.name,
                    'created_at': record.created_at.isoformat() if record.created_at else None,
                }
                
                # Add all data fields from JSON column
                record_data = record.raw_data or record.metadata_json or {}
                # Ensure record_data is a dictionary
                if not isinstance(record_data, dict):
                    record_data = {}
                
                if record_data:
                    if fields:
                        # Only include specified fields
                        for field in fields:
                            row[field] = record_data.get(field)
                    else:
                        # Include all fields
                        row.update(record_data)
                
                data.append(row)
            
            # Generate filename
            timestamp = int(time.time())
            filename = f"adhoc_{execution.id}_{timestamp}.{format}"
            
            # Get all field names for export
            if not fields and data:
                fields = list(data[0].keys())
            
            # Export
            if format == 'csv':
                filepath = self.exporter.export_csv(data, fields, filename)
            elif format == 'pdf':
                pdf_config = query_config.get('pdf_config', {})
                pdf_config['title'] = report_name
                filepath = self.exporter.export_pdf(data, fields, pdf_config, filename)
            else:
                raise ValueError(f"Unsupported format: {format}")
            
            # Update execution
            execution.completed_at = datetime.utcnow()
            execution.status = 'completed'
            execution.row_count = len(data)
            execution.file_path = filepath
            execution.file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0
            execution.execution_time_ms = int((time.time() - start_time) * 1000)
            
        except Exception as e:
            execution.status = 'failed'
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            raise
        finally:
            db.session.commit()
        
        return execution
    
    def _merge_params(self, base_config: dict, params: dict) -> dict:
        """Merge runtime parameters into base query config"""
        config = base_config.copy()
        
        # Override limit if provided
        if 'limit' in params:
            config['limit'] = params['limit']
        
        # Add/override filters
        if 'filters' in params:
            config['filters'] = config.get('filters', []) + params['filters']
        
        # Override fields
        if 'fields' in params:
            config['fields'] = params['fields']
        
        return config
