"""
Data Import Service
Handles parsing and importing data from multiple formats (JSON, CSV, Excel, etc.)
"""
import csv
import json
import io
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
import re
import openpyxl
from openpyxl import load_workbook


class DataImportService:
    """Parse and import data from various formats"""
    
    def detect_format(self, content: str, filename: str = '') -> str:
        """
        Auto-detect data format
        
        Returns: 'json', 'csv', 'tsv', 'plain', 'excel', 'keyvalue', 'structured_text', or 'unknown'
        """
        content = content.strip()
        
        # Check file extension first
        filename_lower = filename.lower()
        if filename_lower.endswith('.xlsx') or filename_lower.endswith('.xls'):
            return 'excel'
        
        # Try JSON first
        if (content.startswith('{') or content.startswith('[')) and (content.endswith('}') or content.endswith(']')):
            try:
                json.loads(content)
                return 'json'
            except:
                pass
        
        # Check for CSV/TSV/Delimited patterns
        lines = content.split('\n')
        if len(lines) > 1:
            first_line = lines[0].strip()
            
            # Count delimiters
            comma_count = first_line.count(',')
            tab_count = first_line.count('\t')
            pipe_count = first_line.count('|')
            semicolon_count = first_line.count(';')
            
            # Require multiple delimiters for CSV detection
            delim_count = sum(1 for char in first_line if char in [',', '\t', '|', ';'])
            if delim_count >= 2 or comma_count >= 2:
                # Determine delimiter
                if tab_count > comma_count and tab_count > 0:
                    return 'tsv'
                elif pipe_count > 0 and pipe_count > comma_count:
                    return 'pipe'
                elif semicolon_count > 0 and semicolon_count > comma_count:
                    return 'semicolon'
                elif comma_count > 0:
                    return 'csv'
            
            # Check for structured text patterns (indented, hierarchical, formatted)
            if self._is_structured_text(content):
                return 'structured_text'
            
            # Check for key-value pairs (YAML-like, INI-like)
            if self._is_keyvalue_format(content):
                return 'keyvalue'
        
        # Default to plain text for simple lists/data
        return 'plain'
    
    def _is_structured_text(self, content: str) -> bool:
        """Check if content is structured text (indented blocks, nested, hierarchical)"""
        lines = content.split('\n')
        
        # Check for indentation patterns (common in structured text)
        indented_count = 0
        total_non_empty = 0
        for line in lines:  # Check ALL lines, not just first 20
            if not line.strip():
                continue
            total_non_empty += 1
            if line and len(line) > 0 and line[0] in [' ', '\t']:
                indented_count += 1
        
        # If ANY significant indentation exists (>10% of lines), it's structured
        if total_non_empty > 0 and indented_count > 0:
            ratio = indented_count / total_non_empty
            if ratio >= 0.1:  # Lowered from 0.3 to 0.1 (10%)
                return True
        
        # Check for array-like patterns (- item)
        if re.search(r'^\s+-\s+\w+:', content, re.MULTILINE):
            return True
        
        # Check for YAML-style arrays (- key: value under a parent)
        if re.search(r':\s*\n\s+-\s+\w+:', content, re.MULTILINE):
            return True
        
        # Check for record separators with key-value pairs (--- separator)
        if '---' in content and re.search(r'^\w+:\s*.+', content, re.MULTILINE):
            # Check if there's ANY indentation anywhere
            if re.search(r'^\s+', content, re.MULTILINE):
                return True
        
        # Check for common structured patterns
        # XML-like
        if '<' in content and '>' in content:
            return True
        
        # Markdown table
        if '|' in content and '--' in content:
            return True
        
        # Hierarchical (===, ---, ##, etc.)
        if re.search(r'^[=\-#]{3,}', content, re.MULTILINE):
            return True
        
        # Indented lists with bullets/numbers
        if re.search(r'^\s+[\-\*•]\s+', content, re.MULTILINE):
            return True
        
        return False
    
    def _is_keyvalue_format(self, content: str) -> bool:
        """Check if content is key-value format (YAML-like, INI-like)"""
        lines = content.split('\n')
        keyvalue_count = 0
        
        for line in lines[:20]:  # Check first 20 lines
            line = line.strip()
            if not line or line.startswith('#') or line.startswith(';'):
                continue
            # Match patterns like: key: value, key=value, key := value
            if re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*\s*[:=]\s*.+', line):
                keyvalue_count += 1
        
        # If >30% of lines are key-value, it's likely the format
        total_content_lines = sum(1 for line in lines if line.strip() and not line.strip().startswith('#'))
        if total_content_lines > 0 and keyvalue_count / total_content_lines > 0.3:
            return True
        
        return False
    
    def parse_excel(self, file_content: bytes, sheet_name: str = 0) -> List[Dict[str, Any]]:
        """Parse Excel file (XLSX/XLS)"""
        try:
            wb = load_workbook(io.BytesIO(file_content))
            ws = wb[wb.sheetnames[sheet_name]] if isinstance(sheet_name, int) else wb[sheet_name]
            
            # Get headers from first row
            headers = []
            for cell in ws[1]:
                headers.append(cell.value if cell.value else '')
            
            # Get data rows
            records = []
            for row in ws.iter_rows(min_row=2, values_only=True):
                if any(row):  # Skip empty rows
                    record = {}
                    for idx, value in enumerate(row):
                        if idx < len(headers):
                            record[headers[idx]] = value
                    records.append(record)
            
            return records
        except Exception as e:
            raise ValueError(f"Failed to parse Excel file: {str(e)}")
    
    def parse_json(self, content: str) -> List[Dict[str, Any]]:
        """Parse JSON data"""
        data = json.loads(content)
        
        # If single object, wrap in array
        if isinstance(data, dict):
            return [data]
        elif isinstance(data, list):
            return data
        else:
            raise ValueError("JSON must be object or array")
    
    def parse_csv(self, content: str, delimiter: str = ',') -> List[Dict[str, Any]]:
        """Parse CSV/TSV/delimited data"""
        if delimiter == 'tab':
            delimiter = '\t'
        elif delimiter == 'pipe':
            delimiter = '|'
        elif delimiter == 'semicolon':
            delimiter = ';'
        
        print(f"\n🔍 CSV PARSE DEBUG:")
        print(f"   Input content length: {len(content)} chars")
        print(f"   Line count: {content.count(chr(10)) + 1}")
        print(f"   Delimiter: '{delimiter}'")
        
        reader = csv.DictReader(io.StringIO(content), delimiter=delimiter)
        records = list(reader)
        
        print(f"   Records parsed: {len(records)}")
        if records:
            print(f"   Fields: {list(records[0].keys())}")
            print(f"   First record: {records[0]}")
        print()
        
        return records
    
    def parse_keyvalue(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse key-value format like:
        name: John
        age: 30
        email: john@example.com
        ---
        name: Jane
        age: 25
        """
        records = []
        current_record = {}
        
        for line in content.split('\n'):
            line = line.strip()
            
            # Empty line or separator - save current record
            if not line or line == '---':
                if current_record:
                    records.append(current_record)
                    current_record = {}
                continue
            
            # Parse key: value or key = value
            match = re.match(r'([^:=]+)\s*[:=]\s*(.+)', line)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                current_record[key] = value
        
        # Add last record
        if current_record:
            records.append(current_record)
        
        return records
    
    def parse_structured_text(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse structured text formats (indented blocks, hierarchical data, markdown tables)
        Supports:
        - Markdown tables
        - Indented hierarchical data
        - Multi-line records separated by blank lines
        """
        records = []
        
        # Check for markdown table format (| header | header |)
        if '|' in content and re.search(r'\|\s*-+\s*\|', content):
            return self._parse_markdown_table(content)
        
        # Check for hierarchical/indented format
        if re.search(r'^\s+', content, re.MULTILINE):
            return self._parse_hierarchical_text(content)
        
        # Default: treat as key-value blocks separated by blank lines
        return self.parse_keyvalue(content)
    
    def _parse_markdown_table(self, content: str) -> List[Dict[str, Any]]:
        """Parse markdown table format"""
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        records = []
        
        # Find header row
        header_idx = -1
        for idx, line in enumerate(lines):
            if '|' in line and idx + 1 < len(lines) and '-' in lines[idx + 1]:
                header_idx = idx
                break
        
        if header_idx < 0:
            return records
        
        # Parse headers
        header_line = lines[header_idx]
        headers = [h.strip() for h in header_line.split('|') if h.strip()]
        
        # Parse data rows (skip separator row)
        for idx in range(header_idx + 2, len(lines)):
            line = lines[idx]
            if not line or '|' not in line:
                continue
            
            values = [v.strip() for v in line.split('|') if v.strip()]
            if len(values) > 0:
                record = {}
                for i, header in enumerate(headers):
                    record[header] = values[i] if i < len(values) else ''
                records.append(record)
        
        return records
    
    def _parse_hierarchical_text(self, content: str) -> List[Dict[str, Any]]:
        """Parse indented/hierarchical text format with proper nesting (JSON structure)
        
        Handles:
        - Key: value pairs at root level
        - Nested objects via indentation
        - Arrays with - prefix
        - Repeated keys merge into arrays
        - Record separators: --- only (not blank lines)
        """
        records = []
        current_record = {}
        current_parent_key = None
        current_array = None
        in_array_context = False
        
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()
            
            # Check for explicit record separator (ONLY ---)
            if stripped == '---':
                if current_record:
                    records.append(current_record)
                    current_record = {}
                    current_parent_key = None
                    current_array = None
                    in_array_context = False
                i += 1
                continue
            
            # Skip blank lines entirely (they don't separate records anymore)
            if not stripped:
                i += 1
                continue
            
            # Determine indentation level
            indent = len(line) - len(line.lstrip())
            
            # Check for parent key with no value (indicates nested structure or array)
            parent_match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_\s]*)\s*:\s*$', stripped)
            if parent_match and indent == 0:
                new_parent_key = parent_match.group(1).strip()
                
                # If this key already exists, we'll MERGE the new values
                # (e.g., repeated sensor_readings: blocks)
                if new_parent_key in current_record:
                    # Key exists - continue appending to existing array
                    current_parent_key = new_parent_key
                    # Ensure it's a list
                    if not isinstance(current_record[current_parent_key], list):
                        current_record[current_parent_key] = [current_record[current_parent_key]]
                    current_array = current_record[current_parent_key]
                    in_array_context = True
                else:
                    # New key
                    current_parent_key = new_parent_key
                    current_array = None
                    in_array_context = False
                i += 1
                continue
            
            # PRIORITY 1: Check for array item with key:value FIRST (e.g., "- timestamp: 2025-01-01")
            # This must come before regular key:value to prevent "- key" from matching as key
            array_item_match = re.match(r'^-\s+([^:=]+)\s*[:=]\s*(.+)$', stripped)
            if array_item_match and current_parent_key:
                key = array_item_match.group(1).strip()
                value = array_item_match.group(2).strip()
                
                in_array_context = True
                
                # Initialize array if needed
                if current_parent_key not in current_record:
                    current_record[current_parent_key] = []
                
                if not isinstance(current_record[current_parent_key], list):
                    prev_value = current_record[current_parent_key]
                    current_record[current_parent_key] = [prev_value] if prev_value else []
                
                current_array = current_record[current_parent_key]
                # Start new array item
                current_array.append({key: self._infer_value_type(value)})
                i += 1
                continue
            
            # PRIORITY 2: Check for simple list item (- value or * value) 
            # before general key:value matching
            simple_list_match = re.match(r'^[-\*•]\s+([^:=]+)$', stripped)
            if simple_list_match and current_parent_key:
                item = simple_list_match.group(1).strip()
                in_array_context = True
                
                if current_parent_key not in current_record:
                    current_record[current_parent_key] = []
                
                if not isinstance(current_record[current_parent_key], list):
                    prev_value = current_record[current_parent_key]
                    current_record[current_parent_key] = [prev_value] if prev_value else []
                
                current_record[current_parent_key].append(self._infer_value_type(item))
                i += 1
                continue
            
            # PRIORITY 3: Continuation of array item (indented key: value after - item)
            if indent > 0 and current_array and len(current_array) > 0 and in_array_context:
                cont_match = re.match(r'^([^:=]+)\s*[:=]\s*(.+)$', stripped)
                if cont_match:
                    key = cont_match.group(1).strip()
                    value = cont_match.group(2).strip()
                    # Add to last array item
                    if isinstance(current_array[-1], dict):
                        current_array[-1][key] = self._infer_value_type(value)
                    i += 1
                    continue
            
            # PRIORITY 4: Parse as key: value (top-level or nested object)
            match = re.match(r'^([^:=]+)\s*[:=]\s*(.+)$', stripped)
            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                
                if indent == 0:
                    # Top-level key with value
                    current_parent_key = key
                    current_array = None
                    in_array_context = False
                    current_record[key] = self._infer_value_type(value)
                else:
                    # Nested key - add to parent's structure (object, not array)
                    if current_parent_key and not in_array_context:
                        # Initialize nested structure if needed
                        if current_parent_key not in current_record:
                            current_record[current_parent_key] = {}
                        
                        # If parent is not a dict, convert it
                        if not isinstance(current_record[current_parent_key], dict):
                            if isinstance(current_record[current_parent_key], list):
                                # Add to last array item
                                if current_record[current_parent_key]:
                                    current_record[current_parent_key][-1][key] = self._infer_value_type(value)
                            else:
                                prev_value = current_record[current_parent_key]
                                current_record[current_parent_key] = {"_value": prev_value, key: self._infer_value_type(value)}
                        else:
                            current_record[current_parent_key][key] = self._infer_value_type(value)
                i += 1
                continue
            
            i += 1
        
        # Add last record
        if current_record:
            records.append(current_record)
        
        return records
    
    def _infer_value_type(self, value: str) -> Any:
        """Infer and convert value to appropriate Python type"""
        value = value.strip()
        
        # Boolean
        if value.lower() in ['true', 'yes', '1']:
            return True
        elif value.lower() in ['false', 'no', '0']:
            return False
        
        # Null
        elif value.lower() in ['null', 'none', '']:
            return None
        
        # Integer
        try:
            if '.' not in value:
                return int(value)
        except (ValueError, AttributeError):
            pass
        
        # Float
        try:
            return float(value)
        except (ValueError, AttributeError):
            pass
        
        # String (default)
        return value
    
    def parse_plain_text(self, content: str, schema_fields: List[str]) -> List[Dict[str, Any]]:
        """
        Parse plain text by splitting on newlines and mapping to schema fields
        Useful for simple lists
        """
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if not schema_fields:
            # Create generic field
            return [{'value': line} for line in lines]
        
        # Map to first field
        primary_field = schema_fields[0]
        return [{primary_field: line} for line in lines]
    
    def auto_parse(self, content: str, schema_fields: List[str] = None, filename: str = '', file_bytes: bytes = None) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Automatically detect format and parse data
        
        Returns: (format_detected, parsed_data)
        """
        format_type = self.detect_format(content, filename)
        
        if format_type == 'json':
            data = self.parse_json(content)
        elif format_type == 'csv':
            data = self.parse_csv(content, ',')
        elif format_type == 'tsv':
            data = self.parse_csv(content, '\t')
        elif format_type == 'pipe':
            data = self.parse_csv(content, '|')
        elif format_type == 'semicolon':
            data = self.parse_csv(content, ';')
        elif format_type == 'structured_text':
            data = self.parse_structured_text(content)
        elif format_type == 'excel':
            if not file_bytes:
                raise ValueError("File bytes required for Excel format")
            data = self.parse_excel(file_bytes)
        elif format_type == 'keyvalue':
            data = self.parse_keyvalue(content)
        else:
            # Fall back to plain text
            data = self.parse_plain_text(content, schema_fields or [])
        
        return format_type, data
    
    def validate_against_schema(self, data: List[Dict[str, Any]], schema_fields: List[Dict]) -> Tuple[List[Dict], List[str]]:
        """
        Validate and type-cast data against schema
        
        Returns: (valid_records, errors)
        """
        valid_records = []
        errors = []
        
        for idx, record in enumerate(data):
            validated_record = {}
            record_errors = []
            
            for field in schema_fields:
                field_name = field['field_name']
                field_type = field['field_type']
                is_required = field.get('is_required', False)
                
                # Get value from record
                value = record.get(field_name)
                
                # Check required
                if is_required and (value is None or value == ''):
                    record_errors.append(f"Record {idx + 1}: '{field_name}' is required")
                    continue
                
                # Skip if empty and not required
                if value is None or value == '':
                    validated_record[field_name] = None
                    continue
                
                # Type casting
                try:
                    if field_type == 'integer':
                        validated_record[field_name] = int(value)
                    elif field_type == 'float':
                        validated_record[field_name] = float(value)
                    elif field_type == 'boolean':
                        if isinstance(value, bool):
                            validated_record[field_name] = value
                        else:
                            lower_val = str(value).lower()
                            validated_record[field_name] = lower_val in ('true', '1', 'yes', 'y')
                    elif field_type == 'date':
                        # Try parsing date
                        if isinstance(value, str):
                            validated_record[field_name] = value  # Let backend handle date parsing
                        else:
                            validated_record[field_name] = str(value)
                    elif field_type in ('json', 'array', 'object'):
                        if isinstance(value, str):
                            validated_record[field_name] = json.loads(value)
                        else:
                            validated_record[field_name] = value
                    else:  # string
                        validated_record[field_name] = str(value)
                except Exception as e:
                    record_errors.append(f"Record {idx + 1}: '{field_name}' - {str(e)}")
            
            if record_errors:
                errors.extend(record_errors)
            else:
                valid_records.append(validated_record)
        
        return valid_records, errors
    
    def suggest_field_mapping(self, data: List[Dict[str, Any]], schema_fields: List[Dict]) -> Dict[str, str]:
        """
        Suggest mapping from data fields to schema fields
        
        Returns: {data_field: schema_field}
        """
        if not data:
            return {}
        
        data_fields = list(data[0].keys())
        schema_field_names = [f['field_name'] for f in schema_fields]
        
        mapping = {}
        
        for data_field in data_fields:
            # Exact match
            if data_field in schema_field_names:
                mapping[data_field] = data_field
                continue
            
            # Case-insensitive match
            lower_data = data_field.lower()
            for schema_field in schema_field_names:
                if schema_field.lower() == lower_data:
                    mapping[data_field] = schema_field
                    break
            
            # Fuzzy match (contains)
            if data_field not in mapping:
                for schema_field in schema_field_names:
                    if lower_data in schema_field.lower() or schema_field.lower() in lower_data:
                        mapping[data_field] = schema_field
                        break
        
        return mapping

    def infer_field_type(self, values: List[Any]) -> str:
        """
        Infer field type from sample values
        
        Returns: 'string', 'integer', 'float', 'boolean', 'date', 'json'
        """
        if not values:
            return 'string'
        
        # Filter non-None values
        non_null = [v for v in values if v is not None and v != '']
        if not non_null:
            return 'string'
        
        # Check types
        all_int = True
        all_float = True
        all_bool = True
        all_date = True
        
        for val in non_null:
            val_str = str(val).strip().lower()
            
            # Check if integer
            try:
                int(val)
            except:
                all_int = False
            
            # Check if float
            try:
                float(val)
            except:
                all_float = False
            
            # Check if boolean
            if val_str not in ('true', 'false', '1', '0', 'yes', 'no', 'y', 'n'):
                all_bool = False
            
            # Check if date
            try:
                datetime.fromisoformat(val_str.split(' ')[0])
            except:
                all_date = False
        
        if all_int:
            return 'integer'
        elif all_float:
            return 'float'
        elif all_bool:
            return 'boolean'
        elif all_date:
            return 'date'
        else:
            return 'string'
    
    def suggest_schema_fields(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Suggest schema fields based on data
        
        Returns: List of field definitions
        """
        if not data:
            return []
        
        # Collect all field names and their sample values
        field_samples = {}
        for record in data:
            for field_name, value in record.items():
                if field_name not in field_samples:
                    field_samples[field_name] = []
                field_samples[field_name].append(value)
        
        # Generate field definitions
        suggested_fields = []
        for field_name, values in field_samples.items():
            field_type = self.infer_field_type(values)
            suggested_fields.append({
                'field_name': field_name,
                'field_type': field_type,
                'is_required': False,
                'description': f'Auto-detected {field_type} field'
            })
        
        return suggested_fields

