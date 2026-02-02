#!/usr/bin/env python3
"""
Asset Schema Creator - Create schemas for different asset types
Automatically generates appropriate fields for each asset type
"""

import requests
import json
from typing import Dict, List, Any
from datetime import datetime


class AssetSchemaCreator:
    """Create schemas for different asset types"""
    
    def __init__(self, backend_url: str = "http://localhost:5000"):
        self.backend_url = backend_url
        self.token = None
        self.session = requests.Session()
    
    def login(self, email: str = "admin@admin.com", password: str = "admin123") -> bool:
        """Authenticate with backend"""
        try:
            response = self.session.post(
                f"{self.backend_url}/auth/login",
                json={"email": email, "password": password}
            )
            if response.status_code == 200:
                data = response.json()
                self.token = data.get('access_token') or data.get('token')
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                return True
            return False
        except:
            return False
    
    def create_schema(self, schema_name: str, fields: List[Dict], 
                     asset_type_id: int = 1) -> Dict[str, Any]:
        """Create a schema with fields"""
        try:
            response = self.session.post(
                f"{self.backend_url}/schemas",
                json={
                    "name": schema_name,
                    "asset_type_id": asset_type_id,
                    "fields": fields
                }
            )
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"❌ Error creating schema: {response.text}")
                return {}
        except Exception as e:
            print(f"❌ Error: {e}")
            return {}
    
    def get_schema_templates(self) -> Dict[str, List[Dict]]:
        """Return predefined schema templates for different asset types"""
        
        return {
            "3D Model": [
                {"field_name": "filename", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "format", "field_type": "string", "constraints": {"enum": ["GLTF", "OBJ", "FBX", "BLEND", "3DS"]}},
                {"field_name": "file_size_mb", "field_type": "float", "constraints": {}},
                {"field_name": "polygon_count", "field_type": "integer", "constraints": {}},
                {"field_name": "texture_count", "field_type": "integer", "constraints": {}},
                {"field_name": "author", "field_type": "string", "constraints": {}},
                {"field_name": "license", "field_type": "string", "constraints": {"enum": ["CC0", "CC-BY", "CC-BY-SA", "Free", "Proprietary"]}},
                {"field_name": "url", "field_type": "string", "constraints": {}},
                {"field_name": "tags", "field_type": "array", "constraints": {}},
            ],
            
            "Dataset": [
                {"field_name": "filename", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "format", "field_type": "string", "constraints": {"enum": ["CSV", "JSON", "XLSX", "Parquet", "SQL"]}},
                {"field_name": "row_count", "field_type": "integer", "constraints": {}},
                {"field_name": "column_count", "field_type": "integer", "constraints": {}},
                {"field_name": "file_size_mb", "field_type": "float", "constraints": {}},
                {"field_name": "description", "field_type": "text", "constraints": {}},
                {"field_name": "source", "field_type": "string", "constraints": {}},
                {"field_name": "license", "field_type": "string", "constraints": {}},
                {"field_name": "columns_info", "field_type": "json", "constraints": {}},
            ],
            
            "Source Code": [
                {"field_name": "filename", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "language", "field_type": "string", "constraints": {"enum": ["Python", "JavaScript", "Java", "C++", "Go", "Rust", "PHP", "C#", "Ruby"]}},
                {"field_name": "lines_of_code", "field_type": "integer", "constraints": {}},
                {"field_name": "file_size_kb", "field_type": "float", "constraints": {}},
                {"field_name": "repository", "field_type": "string", "constraints": {}},
                {"field_name": "license", "field_type": "string", "constraints": {}},
                {"field_name": "last_updated", "field_type": "date", "constraints": {}},
                {"field_name": "description", "field_type": "text", "constraints": {}},
                {"field_name": "dependencies", "field_type": "array", "constraints": {}},
            ],
            
            "Image": [
                {"field_name": "filename", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "format", "field_type": "string", "constraints": {"enum": ["JPEG", "PNG", "WebP", "SVG", "GIF", "BMP"]}},
                {"field_name": "width", "field_type": "integer", "constraints": {}},
                {"field_name": "height", "field_type": "integer", "constraints": {}},
                {"field_name": "file_size_kb", "field_type": "float", "constraints": {}},
                {"field_name": "dpi", "field_type": "integer", "constraints": {}},
                {"field_name": "color_space", "field_type": "string", "constraints": {"enum": ["RGB", "RGBA", "CMYK", "Grayscale"]}},
                {"field_name": "description", "field_type": "text", "constraints": {}},
                {"field_name": "tags", "field_type": "array", "constraints": {}},
            ],
            
            "Video": [
                {"field_name": "filename", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "format", "field_type": "string", "constraints": {"enum": ["MP4", "WebM", "AVI", "MOV", "MKV"]}},
                {"field_name": "duration_seconds", "field_type": "integer", "constraints": {}},
                {"field_name": "resolution", "field_type": "string", "constraints": {"enum": ["480p", "720p", "1080p", "2K", "4K"]}},
                {"field_name": "framerate", "field_type": "float", "constraints": {}},
                {"field_name": "file_size_mb", "field_type": "float", "constraints": {}},
                {"field_name": "codec", "field_type": "string", "constraints": {}},
                {"field_name": "description", "field_type": "text", "constraints": {}},
            ],
            
            "Point Cloud": [
                {"field_name": "filename", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "format", "field_type": "string", "constraints": {"enum": ["LAS", "PLY", "PCD", "XYZ"]}},
                {"field_name": "point_count", "field_type": "integer", "constraints": {}},
                {"field_name": "file_size_mb", "field_type": "float", "constraints": {}},
                {"field_name": "has_colors", "field_type": "boolean", "constraints": {}},
                {"field_name": "has_normals", "field_type": "boolean", "constraints": {}},
                {"field_name": "bounds_min", "field_type": "json", "constraints": {}},
                {"field_name": "bounds_max", "field_type": "json", "constraints": {}},
                {"field_name": "source", "field_type": "string", "constraints": {}},
            ],
            
            "Sensor Data": [
                {"field_name": "sensor_id", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "sensor_type", "field_type": "string", "constraints": {}},
                {"field_name": "timestamp", "field_type": "datetime", "constraints": {"required": True}},
                {"field_name": "value", "field_type": "float", "constraints": {}},
                {"field_name": "unit", "field_type": "string", "constraints": {}},
                {"field_name": "location", "field_type": "string", "constraints": {}},
                {"field_name": "status", "field_type": "string", "constraints": {"enum": ["Normal", "Warning", "Critical"]}},
                {"field_name": "metadata", "field_type": "json", "constraints": {}},
            ],
            
            "API Specification": [
                {"field_name": "api_name", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "format", "field_type": "string", "constraints": {"enum": ["OpenAPI", "GraphQL", "RAML", "AsyncAPI"]}},
                {"field_name": "version", "field_type": "string", "constraints": {}},
                {"field_name": "base_url", "field_type": "string", "constraints": {}},
                {"field_name": "endpoint_count", "field_type": "integer", "constraints": {}},
                {"field_name": "authentication", "field_type": "string", "constraints": {"enum": ["None", "API Key", "OAuth", "JWT", "Basic"]}},
                {"field_name": "description", "field_type": "text", "constraints": {}},
                {"field_name": "documentation_url", "field_type": "string", "constraints": {}},
            ],
            
            "Document": [
                {"field_name": "title", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "format", "field_type": "string", "constraints": {"enum": ["PDF", "DOCX", "XLSX", "PPTX", "TXT", "MD"]}},
                {"field_name": "author", "field_type": "string", "constraints": {}},
                {"field_name": "file_size_mb", "field_type": "float", "constraints": {}},
                {"field_name": "page_count", "field_type": "integer", "constraints": {}},
                {"field_name": "created_date", "field_type": "date", "constraints": {}},
                {"field_name": "modified_date", "field_type": "date", "constraints": {}},
                {"field_name": "description", "field_type": "text", "constraints": {}},
                {"field_name": "tags", "field_type": "array", "constraints": {}},
            ],
            
            "Report": [
                {"field_name": "report_title", "field_type": "string", "constraints": {"required": True}},
                {"field_name": "format", "field_type": "string", "constraints": {"enum": ["PDF", "HTML", "Excel", "PowerPoint"]}},
                {"field_name": "report_type", "field_type": "string", "constraints": {}},
                {"field_name": "generated_date", "field_type": "date", "constraints": {}},
                {"field_name": "period_start", "field_type": "date", "constraints": {}},
                {"field_name": "period_end", "field_type": "date", "constraints": {}},
                {"field_name": "data_rows", "field_type": "integer", "constraints": {}},
                {"field_name": "summary", "field_type": "text", "constraints": {}},
                {"field_name": "metrics", "field_type": "json", "constraints": {}},
            ],
        }
    
    def create_all_templates(self) -> Dict[str, Dict]:
        """Create all predefined schemas"""
        
        print("\n" + "=" * 70)
        print("Creating Asset Type Schemas")
        print("=" * 70)
        
        templates = self.get_schema_templates()
        created_schemas = {}
        
        for asset_type, fields in templates.items():
            print(f"\n📊 Creating schema for: {asset_type}")
            
            result = self.create_schema(f"{asset_type} Schema", fields)
            
            if result and 'id' in result:
                created_schemas[asset_type] = result['id']
                print(f"  ✅ Schema ID: {result['id']}")
            else:
                print(f"  ⚠️  Failed to create schema")
        
        return created_schemas


def main():
    print("\n" + "=" * 70)
    print("Asset Schema Creator")
    print("=" * 70)
    
    creator = AssetSchemaCreator()
    
    if not creator.login():
        print("❌ Failed to authenticate")
        return
    
    print("✅ Authenticated successfully")
    
    # Create all templates
    schemas = creator.create_all_templates()
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"✅ Created {len(schemas)} schemas:")
    for asset_type, schema_id in schemas.items():
        print(f"  • {asset_type}: ID {schema_id}")


if __name__ == "__main__":
    main()
