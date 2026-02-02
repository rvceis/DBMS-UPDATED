#!/usr/bin/env python3
"""
BATCH DATA LOADER - Loads all sample data files at once
Useful for rapid schema testing and demonstration
"""

import json
import os
from populate_database import DatabasePopulator
from datetime import datetime


def load_all_sample_data(backend_url: str = "http://localhost:5000"):
    """Load all sample data files into the database"""
    
    print("\n" + "=" * 70)
    print("BATCH DATA LOADER - Loading All Sample Data")
    print("=" * 70)
    
    # Initialize populator
    populator = DatabasePopulator(backend_url)
    
    # Get credentials
    email = input("\n📧 Email: ").strip()
    password = input("🔐 Password: ").strip()
    
    # Login
    print("\n🔑 Authenticating...")
    if not populator.login(email, password):
        print("❌ Authentication failed")
        return
    
    print("✅ Authenticated successfully\n")
    
    # Define all data loading tasks
    tasks = [
        {
            "name": "E-Commerce Orders",
            "method": populator.populate_ecommerce_from_json,
            "file": "sample_ecommerce_orders.json",
            "schema_name": "E-Commerce Orders"
        },
        {
            "name": "Employees",
            "method": populator.populate_employees_from_csv,
            "file": "sample_employees.csv",
            "schema_name": "Employees"
        },
        {
            "name": "IoT Sensors",
            "method": populator.populate_iot_from_ndjson,
            "file": "sample_iot_sensors.ndjson",
            "schema_name": "IoT Sensors"
        },
        {
            "name": "Inventory Products",
            "method": populator.populate_inventory_from_json,
            "file": "sample_inventory_products.json",
            "schema_name": "Inventory Products"
        },
        {
            "name": "Hospital Patients",
            "method": populator.populate_hospital_from_csv,
            "file": "sample_hospital_patients.csv",
            "schema_name": "Hospital Patients"
        },
        {
            "name": "Real Estate Buildings",
            "method": populator.populate_real_estate_from_json,
            "file": "sample_real_estate_buildings.json",
            "schema_name": "Real Estate Buildings"
        }
    ]
    
    # Load each dataset
    loaded = 0
    failed = 0
    
    for task in tasks:
        print(f"\n📦 Loading: {task['name']}")
        print(f"   File: {task['file']}")
        
        if not os.path.exists(task['file']):
            print(f"   ⚠️  File not found: {task['file']}")
            failed += 1
            continue
        
        try:
            schema_id = task['method'](task['file'])
            if schema_id:
                print(f"   ✅ Success! Schema ID: {schema_id}")
                loaded += 1
            else:
                print(f"   ❌ Failed to load data")
                failed += 1
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
            failed += 1
    
    # Summary
    print("\n" + "=" * 70)
    print("LOADING SUMMARY")
    print("=" * 70)
    print(f"✅ Successfully loaded: {loaded} datasets")
    print(f"❌ Failed: {failed} datasets")
    print(f"📊 Total: {loaded + failed} datasets")
    
    if loaded > 0:
        print("\n💡 Next steps:")
        print("1. Visit http://localhost:3000")
        print("2. Login with your credentials")
        print("3. View schemas in the Schemas page")
        print("4. View records in the Data page")
        print("5. Create reports from the Reports section")
        print("6. Export schemas using the Download button")


def load_single_dataset(backend_url: str = "http://localhost:5000"):
    """Load single dataset interactively"""
    
    print("\n" + "=" * 70)
    print("SINGLE DATASET LOADER")
    print("=" * 70)
    
    datasets = {
        "1": ("E-Commerce Orders", "sample_ecommerce_orders.json", "populate_ecommerce_from_json"),
        "2": ("Employees", "sample_employees.csv", "populate_employees_from_csv"),
        "3": ("IoT Sensors", "sample_iot_sensors.ndjson", "populate_iot_from_ndjson"),
        "4": ("Inventory Products", "sample_inventory_products.json", "populate_inventory_from_json"),
        "5": ("Hospital Patients", "sample_hospital_patients.csv", "populate_hospital_from_csv"),
        "6": ("Real Estate", "sample_real_estate_buildings.json", "populate_real_estate_from_json"),
    }
    
    print("\n📊 Available Datasets:")
    for key, (name, _, _) in datasets.items():
        print(f"{key}. {name}")
    
    choice = input("\nSelect dataset (1-6): ").strip()
    
    if choice not in datasets:
        print("❌ Invalid choice")
        return
    
    name, filepath, method_name = datasets[choice]
    
    # Initialize and login
    populator = DatabasePopulator(backend_url)
    
    email = input("\n📧 Email: ").strip()
    password = input("🔐 Password: ").strip()
    
    print("\n🔑 Authenticating...")
    if not populator.login(email, password):
        print("❌ Authentication failed")
        return
    
    print("✅ Authenticated\n")
    
    # Check file exists
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return
    
    # Load data
    print(f"📦 Loading: {name}")
    print(f"   File: {filepath}")
    
    try:
        method = getattr(populator, method_name)
        schema_id = method(filepath)
        if schema_id:
            print(f"✅ Success!")
            print(f"   Schema ID: {schema_id}")
            print(f"   Name: {name}")
        else:
            print(f"❌ Failed to load data")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


def list_available_data_files():
    """List all available sample data files"""
    
    print("\n" + "=" * 70)
    print("AVAILABLE SAMPLE DATA FILES")
    print("=" * 70)
    
    files = {
        "JSON Format (supports nested objects/arrays)": [
            "sample_ecommerce_orders.json - E-commerce orders with items and metadata",
            "sample_inventory_products.json - Products with specs and dimensions",
            "sample_real_estate_buildings.json - Buildings with facilities and contacts"
        ],
        "CSV Format (tabular data)": [
            "sample_employees.csv - Employee records with skills and departments",
            "sample_hospital_patients.csv - Patient records with medical history"
        ],
        "NDJSON Format (newline-delimited, one per line)": [
            "sample_iot_sensors.ndjson - Sensor readings with hierarchical data"
        ]
    }
    
    for category, file_list in files.items():
        print(f"\n{category}:")
        for file in file_list:
            print(f"  • {file}")
    
    print("\n💾 All files are in the project root directory")
    print("📝 Use batch_loader.py to load multiple datasets at once")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "list":
            list_available_data_files()
        elif sys.argv[1] == "single":
            load_single_dataset()
        elif sys.argv[1] == "all":
            load_all_sample_data()
        else:
            print("Usage:")
            print("  python3 batch_loader.py all      - Load all datasets")
            print("  python3 batch_loader.py single   - Load single dataset")
            print("  python3 batch_loader.py list     - List available files")
    else:
        print("\n" + "=" * 70)
        print("BATCH LOADER - Quick Start")
        print("=" * 70)
        print("\n1. Load all sample data at once:")
        print("   python3 batch_loader.py all")
        print("\n2. Load single dataset:")
        print("   python3 batch_loader.py single")
        print("\n3. List available data files:")
        print("   python3 batch_loader.py list")
        
        choice = input("\nWhat would you like to do? (all/single/list): ").strip().lower()
        
        if choice == "all":
            load_all_sample_data()
        elif choice == "single":
            load_single_dataset()
        elif choice == "list":
            list_available_data_files()
        else:
            print("❌ Invalid choice")
