"""
Report Export Service
Handles CSV and PDF generation
"""
import os
import csv
import io
from typing import List, Dict
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT


class ReportExportService:
    """Export reports to CSV and PDF formats"""
    
    def __init__(self, reports_dir: str):
        self.reports_dir = reports_dir
        os.makedirs(reports_dir, exist_ok=True)
    
    def export_csv(self, data: List[Dict], fields: List[str], filename: str) -> str:
        """
        Generate CSV file
        
        Args:
            data: List of record dictionaries
            fields: List of field names to include
            filename: Output filename
        
        Returns:
            Full file path
        """
        filepath = os.path.join(self.reports_dir, filename)
        
        # Use all fields if none specified
        if not fields and data:
            fields = list(data[0].keys())
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()
            for row in data:
                # Convert None to empty string and ensure all values are serializable
                clean_row = {}
                for key in fields:
                    value = row.get(key)
                    if value is None:
                        clean_row[key] = ''
                    elif isinstance(value, (dict, list)):
                        clean_row[key] = str(value)
                    else:
                        clean_row[key] = value
                writer.writerow(clean_row)
        
        return filepath
    
    def export_pdf(self, data: List[Dict], fields: List[str], pdf_config: dict, filename: str) -> str:
        """
        Generate PDF file with formatting
        
        Args:
            data: List of record dictionaries
            fields: List of field names to include
            pdf_config: {
                "title": "Report Title",
                "orientation": "portrait|landscape",
                "page_size": "A4|Letter",
                "show_metadata": True,
                "column_labels": {"field1": "Label 1", ...}
            }
            filename: Output filename
        
        Returns:
            Full file path
        """
        filepath = os.path.join(self.reports_dir, filename)
        
        # PDF setup
        page_size_name = pdf_config.get('page_size', 'A4')
        page_size = A4 if page_size_name == 'A4' else letter
        
        orientation = pdf_config.get('orientation', 'portrait')
        if orientation == 'landscape':
            page_size = landscape(page_size)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=page_size,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.5*inch
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=30,
            alignment=TA_CENTER
        )

        # Prepare table data
        if not fields and data:
            fields = list(data[0].keys())

        num_cols = len(fields)
        # Helper function to wrap text intelligently
        def wrap_text(text, max_words=4):
            if not text or text is None:
                return ''
            text = str(text).strip()
            if not text:
                return ''
            # First try word-based wrapping
            words = text.split()
            if len(words) <= max_words:
                return text
            
            # For very long text, wrap at character level too
            lines = []
            chars_per_line = 80 if max_words >= 4 else 60
            current_line = ""
            for word in words:
                if len(current_line) + len(word) + 1 <= chars_per_line:
                    current_line = current_line + " " + word if current_line else word
                else:
                    if current_line:
                        lines.append(current_line)
                    # Split very long words
                    if len(word) > chars_per_line:
                        for i in range(0, len(word), chars_per_line):
                            lines.append(word[i:i+chars_per_line])
                    else:
                        current_line = word
            if current_line:
                lines.append(current_line)
            return '\n'.join(lines)

        # Get column labels
        column_labels = pdf_config.get('column_labels', {})
        headers = [column_labels.get(f, f.replace('_', ' ').title()) for f in fields]

        # Drop columns that are completely empty to avoid blank grids in PDF output
        def _has_value(row: Dict, field: str) -> bool:
            val = row.get(field)
            if val is None and isinstance(row.get('values'), dict):
                val = row['values'].get(field)
            if val is None:
                return False
            if isinstance(val, (list, dict)):
                return len(val) > 0
            return str(val).strip() != ''

        filtered_fields = [f for f in fields if any(_has_value(r, f) for r in data)] or fields
        filtered_headers = [column_labels.get(f, f.replace('_', ' ').title()) for f in filtered_fields]
        num_cols = len(filtered_fields)

        # Check if force vertical layout is requested
        force_vertical = pdf_config.get('force_vertical_layout', False)

        if force_vertical or num_cols > 8:
            # Vertical table layout: each record as a 2-column table (Field, Value)
            for idx, row in enumerate(data):
                record_table_data = []
                for i, field in enumerate(filtered_fields):
                    label = filtered_headers[i]
                    # Try direct, then nested under 'values', then ''
                    value = row.get(field, None)
                    if value is None and isinstance(row.get('values'), dict):
                        value = row['values'].get(field, '')
                    if value is None:
                        value = ''
                    elif isinstance(value, (dict, list)):
                        value = wrap_text(str(value), max_words=3)
                    else:
                        value = wrap_text(str(value), max_words=4)
                    record_table_data.append([label, value])
                record_table = Table(record_table_data, colWidths=[1.8*inch, doc.width-1.8*inch])
                record_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1976d2')),
                    ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                    ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (0, -1), 10),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('BACKGROUND', (1, 0), (1, -1), colors.white),
                    ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
                    ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                    ('FONTSIZE', (1, 0), (1, -1), 10),
                    ('TOPPADDING', (0, 0), (-1, -1), 6),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
                ]))
                elements.append(Paragraph(f"<b>Record {idx+1}</b>", styles['Heading4']))
                elements.append(record_table)
                elements.append(Spacer(1, 0.18*inch))
        else:
            # Normal horizontal table layout
            table_data = [filtered_headers]
            for row in data:
                table_row = []
                for field in filtered_fields:
                    value = row.get(field, None)
                    if value is None and isinstance(row.get('values'), dict):
                        value = row['values'].get(field, '')
                    if value is None:
                        value = ''
                    elif isinstance(value, (dict, list)):
                        value = wrap_text(str(value), max_words=3)
                    else:
                        value = wrap_text(str(value), max_words=4)
                    table_row.append(value)
                table_data.append(table_row)
            available_width = doc.width
            min_col_width = 0.8 * inch
            ideal_col_width = available_width / num_cols
            if ideal_col_width < min_col_width:
                ideal_col_width = min_col_width
            col_widths = [ideal_col_width] * num_cols
            table = Table(table_data, colWidths=col_widths, repeatRows=1)
            header_fontsize = 11 if num_cols <= 6 else 10 if num_cols <= 8 else 9 if num_cols <= 10 else 8
            data_fontsize = 10 if num_cols <= 6 else 9 if num_cols <= 8 else 8 if num_cols <= 10 else 7
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), header_fontsize),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                ('TOPPADDING', (0, 0), (-1, 0), 10),
                ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                ('WORDWRAP', (0, 0), (-1, 0), 'LR'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), data_fontsize),
                ('TOPPADDING', (0, 1), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 1), (-1, -1), 'TOP'),
                ('WORDWRAP', (0, 1), (-1, -1), 'LR'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ]))
            elements.append(table)

        # Footer
        elements.append(Spacer(1, 0.2*inch))
        footer_text = f"<i>End of report - {len(data)} records, {num_cols} fields</i>"
        footer_para = Paragraph(footer_text, styles['Normal'])
        elements.append(footer_para)
        # Build PDF
        doc.build(elements)
        return filepath

    def export_pdf_multi_schema(self, schema_data_list: List[Dict], pdf_config: dict, filename: str) -> str:
        """
        Generate PDF with multiple tables (one per schema)
        
        Args:
            schema_data_list: List of {"schema_name": str, "fields": List[str], "data": List[Dict]}
            pdf_config: PDF configuration
            filename: Output filename
        
        Returns:
            Full file path
        """
        filepath = os.path.join(self.reports_dir, filename)
        
        # PDF setup
        page_size_name = pdf_config.get('page_size', 'A4')
        page_size = A4 if page_size_name == 'A4' else letter
        
        orientation = pdf_config.get('orientation', 'portrait')
        if orientation == 'landscape':
            page_size = landscape(page_size)
        
        doc = SimpleDocTemplate(
            filepath,
            pagesize=page_size,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.5*inch
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        section_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=12,
            spaceBefore=12,
        )
        
        # Main title
        title = pdf_config.get('title', 'Report')
        title_para = Paragraph(f"<b>{title}</b>", title_style)
        elements.append(title_para)
        
        # Metadata section
        if pdf_config.get('show_metadata', True):
            total_records = sum(len(s.get('data', [])) for s in schema_data_list)
            meta_text = f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>"
            meta_text += f"<b>Total Records:</b> {total_records}<br/>"
            meta_text += f"<b>Schemas:</b> {len(schema_data_list)}<br/>"
            
            meta_para = Paragraph(meta_text, styles['Normal'])
            elements.append(meta_para)
            elements.append(Spacer(1, 0.3*inch))
        
        # Generate table for each schema
        for schema_info in schema_data_list:
            schema_name = schema_info.get('schema_name', 'Unknown Schema')
            fields = schema_info.get('fields', [])
            data = schema_info.get('data', [])
            
            # Schema section title
            section_para = Paragraph(f"<b>{schema_name}</b> ({len(data)} records)", section_style)
            elements.append(section_para)
            
            if not data:
                elements.append(Paragraph("No records", styles['Normal']))
                elements.append(Spacer(1, 0.2*inch))
                continue
            
            # Helper function to wrap text
            def wrap_text_multi(text, max_words=3):
                """Break text into multiple lines after max_words words"""
                if not text or text is None:
                    return ''
                text = str(text).strip()
                if not text:
                    return ''
                words = text.split()
                if len(words) <= max_words:
                    return text
                lines = []
                for i in range(0, len(words), max_words):
                    lines.append(' '.join(words[i:i+max_words]))
                return '\n'.join(lines)
            
            column_labels = pdf_config.get('column_labels', {})
            
            # Detect format: bulk import (record_id, row_index) vs single records (id, name)
            is_bulk_format = data and 'row_index' in data[0]
            
            if is_bulk_format:
                headers = ['Record Name', 'Row #', 'Created'] + [column_labels.get(f, f.replace('_', ' ').title()) for f in fields]
            else:
                headers = ['ID', 'Name', 'Created'] + [column_labels.get(f, f.replace('_', ' ').title()) for f in fields]
            
            num_cols = len(headers)
            if num_cols > 15:
                # Vertical table layout for each record (only for very wide tables)
                for idx, row in enumerate(data):
                    record_table_data = []
                    if is_bulk_format:
                        record_table_data.append(['Record Name', str(row.get('record_name', ''))])
                        record_table_data.append(['Row #', str(row.get('row_index', ''))])
                    else:
                        record_table_data.append(['ID', str(row.get('id', ''))])
                        record_table_data.append(['Name', str(row.get('name', ''))])
                    record_table_data.append(['Created', str(row.get('created_at', ''))[:10]])
                    for i, field in enumerate(fields):
                        label = headers[i+2]  # offset by 2 for Name, Row #, Created
                        value = row.get(field, None)
                        if value is None and isinstance(row.get('values'), dict):
                            value = row['values'].get(field, '')
                        if value is None:
                            value = ''
                        elif isinstance(value, (dict, list)):
                            value = wrap_text_multi(str(value), max_words=2)
                        else:
                            value = wrap_text_multi(str(value), max_words=3)
                        record_table_data.append([label, value])
                    record_table = Table(record_table_data, colWidths=[1.8*inch, doc.width-1.8*inch])
                    record_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#1976d2')),
                        ('TEXTCOLOR', (0, 0), (0, -1), colors.whitesmoke),
                        ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
                        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (0, -1), 9),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('BACKGROUND', (1, 0), (1, -1), colors.white),
                        ('TEXTCOLOR', (1, 0), (1, -1), colors.black),
                        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                        ('FONTSIZE', (1, 0), (1, -1), 8),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                        ('GRID', (0, 0), (-1, -1), 0.4, colors.grey),
                    ]))
                    elements.append(Paragraph(f"<b>Record {idx+1}</b>", styles['Heading4']))
                    elements.append(record_table)
                    elements.append(Spacer(1, 0.18*inch))
                elements.append(PageBreak())
            else:
                # Normal horizontal table layout
                table_data = [headers]
                for row in data:
                    if is_bulk_format:
                        table_row = [
                            wrap_text_multi(str(row.get('record_name', '')), max_words=2),
                            str(row.get('row_index', '')),
                            str(row.get('created_at', ''))[:10]
                        ]
                    else:
                        table_row = [
                            str(row.get('id', '')),
                            wrap_text_multi(str(row.get('name', '')), max_words=2),
                            str(row.get('created_at', ''))[:10]
                        ]
                    for field in fields:
                        value = row.get(field, None)
                        if value is None and isinstance(row.get('values'), dict):
                            value = row['values'].get(field, '')
                        if value is None:
                            value = ''
                        elif isinstance(value, (dict, list)):
                            value = wrap_text_multi(str(value), max_words=2)
                        else:
                            value = wrap_text_multi(str(value), max_words=3)
                        table_row.append(value)
                    table_data.append(table_row)
                available_width = doc.width
                min_col_width = 0.7 * inch
                ideal_col_width = available_width / num_cols
                if ideal_col_width < min_col_width:
                    ideal_col_width = min_col_width
                col_widths = [ideal_col_width] * num_cols
                table = Table(table_data, colWidths=col_widths, repeatRows=1)
                header_fontsize = 8 if num_cols > 8 else 9
                data_fontsize = 6 if num_cols > 8 else 7
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), header_fontsize),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                    ('TOPPADDING', (0, 0), (-1, 0), 6),
                    ('VALIGN', (0, 0), (-1, 0), 'MIDDLE'),
                    ('WORDWRAP', (0, 0), (-1, 0), 'LR'),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('ALIGN', (0, 1), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), data_fontsize),
                    ('TOPPADDING', (0, 1), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 1), (-1, -1), 5),
                    ('VALIGN', (0, 1), (-1, -1), 'TOP'),
                    ('WORDWRAP', (0, 1), (-1, -1), 'LR'),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                elements.append(table)
                elements.append(Spacer(1, 0.4*inch))
                elements.append(PageBreak())
        
        # Build PDF
        doc.build(elements)
        
        return filepath    
    def export_multitable_csv(self, report_data: Dict, filename: str) -> str:
        """
        Generate CSV file with multiple tables (one per section)
        
        Args:
            report_data: Report data with multiple tables
            filename: Output filename
        
        Returns:
            Full file path
        """
        filepath = os.path.join(self.reports_dir, filename)
        
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
            writer = csv.writer(csvfile)
            
            # Write report header
            writer.writerow([f"Report: {report_data.get('title', 'Multi-Table Report')}"])
            writer.writerow([f"Generated: {report_data.get('generated_at', 'N/A')}"])
            writer.writerow([])
            
            # Write each table
            for table_idx, table in enumerate(report_data.get('tables', [])):
                if table_idx > 0:
                    writer.writerow([])
                    writer.writerow([])
                
                # Table header
                writer.writerow([f"Table: {table.get('schema_name', f'Table {table_idx + 1}')}"])
                if table.get('schema_description'):
                    writer.writerow([f"Description: {table.get('schema_description')}"])
                writer.writerow([])
                
                # Get all data items for this table
                items = table.get('data', [])
                current_section = None
                
                for item in items:
                    item_type = item.get('type')
                    
                    # Write section headers
                    if item_type == 'schema_info':
                        writer.writerow(['SCHEMA INFORMATION'])
                        writer.writerow(['Schema Name', item.get('schema_name', '')])
                        writer.writerow(['Description', item.get('schema_description', '')])
                        writer.writerow(['Created', item.get('created_at', '')])
                        writer.writerow(['Updated', item.get('updated_at', '')])
                        writer.writerow([])
                    
                    elif item_type == 'field_metadata':
                        if current_section != 'metadata':
                            writer.writerow(['FIELD METADATA'])
                            writer.writerow(['Field Name', 'Type', 'Searchable', 'Required', 'Description'])
                            current_section = 'metadata'
                        writer.writerow([
                            item.get('field_name', ''),
                            item.get('field_type', ''),
                            item.get('is_searchable', False),
                            item.get('is_required', False),
                            item.get('description', ''),
                        ])
                    
                    elif item_type == 'summary':
                        if current_section != 'summary':
                            writer.writerow([])
                            writer.writerow(['SUMMARY'])
                            current_section = 'summary'
                        writer.writerow(['Total Records', item.get('total_records', 0)])
                        writer.writerow(['Total Fields', item.get('total_fields', 0)])
                        writer.writerow([])
                    
                    elif item_type == 'record':
                        if current_section != 'records':
                            writer.writerow([])
                            writer.writerow(['RECORDS'])
                            # Write column headers from first record
                            content = item.get('content', {})
                            headers = ['ID', 'Name'] + list(content.keys())
                            writer.writerow(headers)
                            current_section = 'records'
                        
                        content = item.get('content', {})
                        row_data = [item.get('record_id', ''), item.get('record_name', '')]
                        row_data.extend([str(v) if v is not None else '' for v in content.values()])
                        writer.writerow(row_data)
        
        return filepath
    
    def export_multitable_pdf(self, report_data: Dict, pdf_config: Dict, filename: str) -> str:
        """
        Generate PDF file with multiple tables
        
        Args:
            report_data: Report data with multiple tables
            pdf_config: PDF configuration options
            filename: Output filename
        
        Returns:
            Full file path
        """
        filepath = os.path.join(self.reports_dir, filename)
        
        # Parse PDF config
        orientation = pdf_config.get('orientation', 'portrait')
        page_size_name = pdf_config.get('page_size', 'A4')
        
        if page_size_name == 'letter':
            page_size = letter
        else:
            page_size = A4
        
        if orientation == 'landscape':
            page_size = landscape(page_size)
        
        # Create document
        doc = SimpleDocTemplate(
            filepath,
            pagesize=page_size,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Add title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1976d2'),
            spaceAfter=12,
            alignment=TA_CENTER,
        )
        elements.append(Paragraph(pdf_config.get('title', 'Report'), title_style))
        elements.append(Paragraph(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Spacer(1, 0.3*inch))
        
        # Add each table
        for table_idx, table in enumerate(report_data.get('tables', [])):
            if table_idx > 0:
                elements.append(PageBreak())
            
            # Table heading
            heading_style = ParagraphStyle(
                f'Heading{table_idx}',
                parent=styles['Heading2'],
                fontSize=14,
                textColor=colors.HexColor('#424242'),
                spaceAfter=10,
                spaceBefore=10,
            )
            elements.append(Paragraph(f"Table: {table.get('schema_name', f'Table {table_idx + 1}')}", heading_style))
            
            if table.get('schema_description'):
                elements.append(Paragraph(f"<i>{table.get('schema_description')}</i>", styles['Normal']))
            
            elements.append(Spacer(1, 0.2*inch))
            
            # Build sections (schema info, metadata, summary, records)
            items = table.get('data', [])
            
            # Group items by type
            sections = {'schema_info': [], 'metadata': [], 'summary': [], 'records': []}
            for item in items:
                item_type = item.get('type')
                if item_type in sections:
                    sections[item_type].append(item)
            
            # Schema Info Section
            if sections['schema_info']:
                elements.append(Paragraph("<b>Schema Information</b>", styles['Heading3']))
                for item in sections['schema_info']:
                    schema_table_data = [
                        ['Property', 'Value'],
                        ['Schema Name', item.get('schema_name', '')],
                        ['Description', item.get('schema_description', '')],
                        ['Created', item.get('created_at', '')],
                        ['Updated', item.get('updated_at', '')],
                    ]
                    schema_table = Table(schema_table_data, colWidths=[2*inch, 4*inch])
                    schema_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e3f2fd')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 9),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ]))
                    elements.append(schema_table)
                    elements.append(Spacer(1, 0.2*inch))
            
            # Field Metadata Section
            if sections['metadata']:
                elements.append(Paragraph("<b>Field Metadata</b>", styles['Heading3']))
                metadata_data = [
                    ['Field Name', 'Type', 'Searchable', 'Required', 'Description']
                ]
                for item in sections['metadata']:
                    metadata_data.append([
                        item.get('field_name', ''),
                        item.get('field_type', ''),
                        'Yes' if item.get('is_searchable') else 'No',
                        'Yes' if item.get('is_required') else 'No',
                        item.get('description', '')[:50],  # Truncate long descriptions
                    ])
                
                metadata_table = Table(metadata_data, colWidths=[1.2*inch, 1*inch, 0.8*inch, 0.8*inch, 1.7*inch])
                metadata_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e3f2fd')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                ]))
                elements.append(metadata_table)
                elements.append(Spacer(1, 0.2*inch))
            
            # Summary Section
            if sections['summary']:
                elements.append(Paragraph("<b>Summary</b>", styles['Heading3']))
                for item in sections['summary']:
                    summary_data = [
                        ['Metric', 'Value'],
                        ['Total Records', str(item.get('total_records', 0))],
                        ['Total Fields', str(item.get('total_fields', 0))],
                    ]
                    summary_table = Table(summary_data, colWidths=[2*inch, 2*inch])
                    summary_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e3f2fd')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
                        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 10),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ]))
                    elements.append(summary_table)
                elements.append(Spacer(1, 0.2*inch))
            
            # Records Section (limited rows for PDF readability)
            if sections['records']:
                elements.append(Paragraph("<b>Records</b>", styles['Heading3']))
                
                # Limit to first 50 records for PDF readability
                record_items = sections['records'][:50]
                
                if record_items:
                    # Get all column names from first record
                    first_record = record_items[0].get('content', {})
                    columns = ['ID', 'Name'] + list(first_record.keys())
                    
                    # Build table data
                    records_data = [columns]
                    for item in record_items:
                        content = item.get('content', {})
                        row = [
                            str(item.get('record_id', '')),
                            str(item.get('record_name', ''))[:30],  # Truncate long names
                        ]
                        row.extend([str(v)[:20] if v is not None else '' for v in content.values()])  # Truncate values
                        records_data.append(row)
                    
                    # Calculate column widths (adapt to number of columns)
                    total_width = 7.5 * inch
                    col_width = total_width / len(columns)
                    
                    records_table = Table(records_data, colWidths=[col_width] * len(columns))
                    records_table.setStyle(TableStyle([
                        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e3f2fd')),
                        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1976d2')),
                        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                        ('FONTSIZE', (0, 0), (-1, -1), 8),
                        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                        ('TOPPADDING', (0, 0), (-1, -1), 4),
                        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
                        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                        ('WORDWRAP', (0, 1), (-1, -1), 'LR'),
                        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
                        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ]))
                    elements.append(records_table)
                    
                    if len(sections['records']) > 50:
                        elements.append(Spacer(1, 0.1*inch))
                        elements.append(Paragraph(f"<i>Showing 50 of {len(sections['records'])} records</i>", styles['Normal']))
        
        # Build PDF
        doc.build(elements)
        
        return filepath