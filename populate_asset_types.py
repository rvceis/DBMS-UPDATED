#!/usr/bin/env python3
"""
Asset Type Populator - Initialize diverse asset types in the database
"""

import requests
import json
from typing import List, Dict

class AssetTypePopulator:
    """Populate database with comprehensive asset types"""
    
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
                print(f"✅ Authenticated as {email}")
                return True
            else:
                print(f"❌ Authentication failed: {response.text}")
                return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def create_asset_type(self, name: str, description: str = "") -> bool:
        """Create a new asset type"""
        try:
            response = self.session.post(
                f"{self.backend_url}/asset-types/",
                json={"name": name, "description": description}
            )
            if response.status_code in [201, 200]:
                data = response.json()
                print(f"✅ Created asset type: {name} (ID: {data.get('id')})")
                return True
            else:
                print(f"⚠️  Asset type '{name}' may already exist or error: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Error creating {name}: {e}")
            return False
    
    def create_all_asset_types(self) -> Dict[str, int]:
        """Create all recommended asset types"""
        
        asset_types = [
            # 3D Models
            ("3D Model", "3D model files (GLTF, OBJ, FBX)"),
            ("3D Scene", "Complete 3D scenes with multiple models"),
            ("3D Character", "3D character models for animation"),
            ("3D Building", "Architectural 3D models"),
            ("3D Vehicle", "3D vehicle models"),
            ("3D Environment", "Environmental and terrain models"),
            
            # Images & Media
            ("Image", "Raster image files (PNG, JPG, WebP)"),
            ("Vector Graphics", "Vector graphics (SVG, AI, PDF)"),
            ("Video", "Video files (MP4, WebM, AVI)"),
            ("Audio", "Audio files (MP3, WAV, OGG)"),
            ("Animation", "Animation sequences"),
            
            # Datasets
            ("Dataset", "Data files (CSV, Excel, JSON)"),
            ("Point Cloud", "3D point cloud data (LAS, PLY, PCD)"),
            ("Mesh", "3D mesh data"),
            ("Time Series", "Temporal/time-series data"),
            ("Geospatial Data", "Geographic/GIS data"),
            ("Scientific Data", "Scientific measurement data"),
            
            # Code & Documents
            ("Source Code", "Programming source code"),
            ("Documentation", "Documentation and guides"),
            ("Markdown", "Markdown documentation"),
            ("API Specification", "API specifications (OpenAPI, REST)"),
            ("Configuration", "Configuration files"),
            ("Notebook", "Jupyter notebooks and computational files"),
            
            # Structured Data
            ("Database Record", "Database entries and records"),
            ("Sensor Data", "IoT sensor readings"),
            ("Log File", "System and application logs"),
            ("Report", "Generated reports"),
            ("Form Data", "Form submissions and responses"),
            ("Metadata", "Metadata and annotations"),
            
            # Enterprise
            ("Document", "Enterprise documents"),
            ("Invoice", "Invoice and billing documents"),
            ("Contract", "Legal contracts"),
            ("Design", "Design files (XD, Figma, Sketch)"),
            ("Prototype", "Interactive prototypes"),
            ("Presentation", "Presentation files"),
            
            # Web & Services
            ("Web Page", "HTML web pages"),
            ("REST API", "REST API endpoints"),
            ("GraphQL Schema", "GraphQL schema definitions"),
            ("Webhook", "Webhook configurations"),
            ("Service", "Web services"),
            
            # Physical & Real-World
            ("Physical Object", "Real-world physical object"),
            ("Artifact", "Museum/archive artifacts"),
            ("Equipment", "Equipment and machinery"),
            ("Device", "IoT or computing devices"),
        ]
        
        print("\n" + "=" * 70)
        print("Creating Asset Types")
        print("=" * 70)
        
        created_types = {}
        for name, description in asset_types:
            # For now just create the name (backend may not support description)
            response = self.session.post(
                f"{self.backend_url}/asset-types/",
                json={"name": name}
            )
            if response.status_code in [201, 200]:
                data = response.json()
                asset_id = data.get('id')
                created_types[name] = asset_id
                print(f"✅ {name} (ID: {asset_id})")
            else:
                print(f"⚠️  {name} - {response.status_code}")
        
        return created_types


def main():
    print("\n" + "=" * 70)
    print("Asset Type Manager - Initialize Database")
    print("=" * 70)
    
    populator = AssetTypePopulator()
    
    # Login
    if not populator.login():
        print("❌ Failed to authenticate")
        return
    
    # Create all asset types
    asset_types = populator.create_all_asset_types()
    
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"✅ Created {len(asset_types)} asset types")
    
    print("\nAsset Types Created:")
    for name, asset_id in sorted(asset_types.items()):
        print(f"  • {name}: ID {asset_id}")


if __name__ == "__main__":
    main()
