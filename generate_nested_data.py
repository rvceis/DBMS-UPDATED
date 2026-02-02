#!/usr/bin/env python3
"""
Nested Data Generator - Creates complex nested/relational test data
Shows schema flexibility with arrays, objects, and optional fields
"""

import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any


class NestedDataGenerator:
    """Generate realistic nested and relational test data"""
    
    @staticmethod
    def generate_company_hierarchy(depth: int = 3) -> List[Dict]:
        """Generate organizational hierarchy with nested departments and employees"""
        departments = ["Engineering", "Sales", "Marketing", "HR", "Finance"]
        locations = ["New York", "San Francisco", "London", "Tokyo", "Berlin"]
        
        records = []
        record_id = 1
        
        for dept_idx, dept in enumerate(departments):
            for loc_idx, loc in enumerate(locations):
                for emp_idx in range(random.randint(3, 8)):
                    records.append({
                        "employee_id": f"EMP-{record_id:05d}",
                        "name": f"Employee_{record_id}",
                        "department": dept,
                        "location": loc,
                        "level": random.randint(1, 5),
                        "salary": random.randint(50000, 200000),
                        "start_date": (datetime.now() - timedelta(days=random.randint(365, 3650))).strftime('%Y-%m-%d'),
                        "manager_id": f"EMP-{random.randint(1, record_id-1):05d}" if record_id > 1 else None,
                        "skills": random.sample(
                            ["Python", "JavaScript", "SQL", "AWS", "Kubernetes", "Docker", "React", "Java", "Go"], 
                            k=random.randint(2, 5)
                        ),
                        "contact": {
                            "email": f"emp{record_id}@company.com",
                            "phone": f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
                            "office": f"{loc} - Floor {random.randint(1, 10)}"
                        },
                        "performance": {
                            "rating": round(random.uniform(2.5, 5.0), 1),
                            "reviews_count": random.randint(1, 20),
                            "goals_completed": random.randint(0, 20)
                        },
                        "is_active": random.choice([True, True, True, False])  # 75% active
                    })
                    record_id += 1
        
        return records[:50]  # Limit to 50 records
    
    @staticmethod
    def generate_ecommerce_transactions(count: int = 20) -> List[Dict]:
        """Generate e-commerce transactions with nested items and metadata"""
        statuses = ["pending", "processing", "shipped", "delivered", "cancelled", "returned"]
        payment_methods = ["credit_card", "debit_card", "paypal", "apple_pay", "bank_transfer"]
        countries = ["USA", "UK", "Germany", "France", "Japan", "Australia", "Canada"]
        
        records = []
        for idx in range(count):
            order_date = datetime.now() - timedelta(days=random.randint(1, 365))
            item_count = random.randint(1, 5)
            
            items = []
            total_amount = 0
            for _ in range(item_count):
                price = round(random.uniform(10, 500), 2)
                qty = random.randint(1, 5)
                items.append({
                    "product_id": f"PROD-{random.randint(10000, 99999)}",
                    "name": f"Product {random.randint(1, 10000)}",
                    "price": price,
                    "quantity": qty,
                    "subtotal": round(price * qty, 2),
                    "discount": round(price * qty * random.uniform(0, 0.3), 2) if random.random() > 0.7 else 0
                })
                total_amount += items[-1]['subtotal'] - items[-1]['discount']
            
            records.append({
                "order_id": f"ORD-{datetime.now().strftime('%Y%m%d')}-{idx:06d}",
                "customer_id": f"CUST-{random.randint(10000, 99999)}",
                "order_date": order_date.strftime('%Y-%m-%d'),
                "status": random.choice(statuses),
                "items": items,
                "total_amount": round(total_amount, 2),
                "currency": random.choice(["USD", "EUR", "GBP", "JPY"]),
                "payment": {
                    "method": random.choice(payment_methods),
                    "status": random.choice(["completed", "pending", "failed"]),
                    "transaction_id": f"TXN-{random.randint(100000000, 999999999)}"
                },
                "shipping": {
                    "country": random.choice(countries),
                    "city": f"City_{random.randint(1, 100)}",
                    "postal_code": f"{random.randint(10000, 99999)}",
                    "tracking_number": f"TRACK-{random.randint(1000000000, 9999999999)}" if random.random() > 0.3 else None
                },
                "notes": f"Order notes {random.randint(1, 1000)}" if random.random() > 0.5 else None,
                "tags": random.sample(["vip", "bulk_order", "rush", "fragile", "high_value"], k=random.randint(0, 3))
            })
        
        return records
    
    @staticmethod
    def generate_sensor_network_data(count: int = 30) -> List[Dict]:
        """Generate IoT sensor network data with hierarchical readings"""
        sensor_types = ["temperature", "humidity", "pressure", "air_quality", "motion"]
        statuses = ["normal", "warning", "critical", "offline"]
        locations = [
            ("Building_A", "Floor_1"), ("Building_A", "Floor_2"), ("Building_A", "Floor_3"),
            ("Building_B", "Floor_1"), ("Building_B", "Floor_2"),
            ("Building_C", "Floor_1"), ("Building_C", "Floor_2"),
        ]
        
        records = []
        for idx in range(count):
            sensor_type = random.choice(sensor_types)
            building, floor = random.choice(locations)
            timestamp = datetime.now() - timedelta(minutes=random.randint(0, 1440))
            
            records.append({
                "sensor_id": f"SNS-{building}-{floor}-{random.randint(100, 999)}",
                "type": sensor_type,
                "location": {
                    "building": building,
                    "floor": floor,
                    "room": f"Room_{random.randint(1, 20)}"
                },
                "timestamp": timestamp.isoformat(),
                "readings": {
                    "current": round(random.uniform(20, 40), 2) if sensor_type == "temperature" else round(random.uniform(0, 100), 1),
                    "min": round(random.uniform(18, 25), 2),
                    "max": round(random.uniform(35, 45), 2),
                    "avg": round(random.uniform(25, 35), 2),
                    "count": random.randint(100, 1000)
                },
                "status": random.choice(statuses),
                "thresholds": {
                    "warning_low": round(random.uniform(15, 20), 2),
                    "warning_high": round(random.uniform(35, 40), 2),
                    "critical_low": round(random.uniform(10, 15), 2),
                    "critical_high": round(random.uniform(40, 50), 2)
                },
                "maintenance": {
                    "last_checked": (datetime.now() - timedelta(days=random.randint(1, 365))).strftime('%Y-%m-%d'),
                    "battery_level": random.randint(20, 100) if random.random() > 0.3 else None,
                    "next_service": (datetime.now() + timedelta(days=random.randint(1, 180))).strftime('%Y-%m-%d')
                },
                "alerts": random.randint(0, 5) if random.random() > 0.7 else 0
            })
        
        return records
    
    @staticmethod
    def generate_document_management(count: int = 15) -> List[Dict]:
        """Generate document management system data with versioning and metadata"""
        doc_types = ["report", "proposal", "contract", "specification", "procedure", "memo"]
        statuses = ["draft", "review", "approved", "published", "archived"]
        categories = ["Finance", "Legal", "Operations", "Marketing", "Technical", "HR"]
        
        records = []
        for idx in range(count):
            created_date = datetime.now() - timedelta(days=random.randint(1, 730))
            
            records.append({
                "document_id": f"DOC-{datetime.now().strftime('%Y')}-{idx:05d}",
                "title": f"Document_{random.randint(1, 10000)}",
                "type": random.choice(doc_types),
                "category": random.choice(categories),
                "status": random.choice(statuses),
                "created_date": created_date.strftime('%Y-%m-%d'),
                "modified_date": (created_date + timedelta(days=random.randint(0, 365))).strftime('%Y-%m-%d'),
                "author": {
                    "name": f"Author_{random.randint(1, 100)}",
                    "email": f"author{random.randint(1, 1000)}@company.com",
                    "department": random.choice(categories)
                },
                "version_info": {
                    "current_version": random.randint(1, 10),
                    "total_versions": random.randint(1, 15),
                    "last_reviewer": f"Reviewer_{random.randint(1, 50)}" if random.random() > 0.4 else None
                },
                "access_control": {
                    "owner": f"Owner_{random.randint(1, 50)}",
                    "shared_with": [f"user_{random.randint(1, 100)}" for _ in range(random.randint(0, 5))],
                    "is_public": random.choice([True, False, False])
                },
                "metadata": {
                    "keywords": random.sample(
                        ["strategic", "confidential", "technical", "approved", "review", "urgent", "final"],
                        k=random.randint(1, 4)
                    ),
                    "file_size_mb": round(random.uniform(0.1, 50), 1),
                    "page_count": random.randint(1, 100) if random.random() > 0.3 else None
                },
                "comments_count": random.randint(0, 20),
                "attachments": random.randint(0, 5)
            })
        
        return records
    
    @staticmethod
    def generate_medical_records(count: int = 20) -> List[Dict]:
        """Generate medical records with patient history and encounters"""
        blood_types = ["A+", "A-", "B+", "B-", "O+", "O-", "AB+", "AB-"]
        encounter_types = ["consultation", "follow_up", "emergency", "routine_checkup", "procedure"]
        
        records = []
        for idx in range(count):
            dob = datetime.now() - timedelta(days=random.randint(365*18, 365*85))
            
            encounters = []
            for _ in range(random.randint(1, 5)):
                encounter_date = datetime.now() - timedelta(days=random.randint(1, 365))
                encounters.append({
                    "date": encounter_date.strftime('%Y-%m-%d'),
                    "type": random.choice(encounter_types),
                    "provider": f"Dr_{random.randint(1, 100)}",
                    "diagnosis": [random.choice(["Hypertension", "Diabetes", "Asthma", "Arthritis", "Migraine"]) for _ in range(random.randint(1, 3))],
                    "notes": f"Encounter notes {random.randint(1, 1000)}"
                })
            
            records.append({
                "patient_id": f"PAT-{random.randint(100000, 999999)}",
                "name": f"Patient_{random.randint(1, 10000)}",
                "date_of_birth": dob.strftime('%Y-%m-%d'),
                "age": (datetime.now() - dob).days // 365,
                "blood_type": random.choice(blood_types),
                "gender": random.choice(["M", "F"]),
                "contact": {
                    "phone": f"+1-{random.randint(200, 999)}-{random.randint(200, 999)}-{random.randint(1000, 9999)}",
                    "email": f"patient{random.randint(1, 10000)}@email.com",
                    "emergency_contact": f"Contact_{random.randint(1, 100)}"
                },
                "allergies": random.sample(
                    ["Penicillin", "Aspirin", "Ibuprofen", "Latex", "Shellfish", "Peanuts"],
                    k=random.randint(0, 3)
                ),
                "medical_history": random.sample(
                    ["Hypertension", "Diabetes Type 2", "Asthma", "COPD", "Heart Disease", "Thyroid Disease"],
                    k=random.randint(0, 3)
                ),
                "current_medications": [
                    {"name": f"Med_{random.randint(1, 100)}", "dosage": f"{random.randint(100, 1000)}mg", "frequency": random.choice(["daily", "twice_daily", "as_needed"])}
                    for _ in range(random.randint(0, 5))
                ],
                "encounters": encounters,
                "insurance": {
                    "provider": f"Insurance_{random.randint(1, 50)}",
                    "policy_number": f"POL-{random.randint(1000000, 9999999)}",
                    "valid_until": (datetime.now() + timedelta(days=random.randint(1, 730))).strftime('%Y-%m-%d')
                }
            })
        
        return records


def main():
    print("=" * 70)
    print("Nested Data Generator - Complex Relational Test Data")
    print("=" * 70)
    
    generators = {
        "1": ("Company Hierarchy", NestedDataGenerator.generate_company_hierarchy),
        "2": ("E-Commerce Transactions", NestedDataGenerator.generate_ecommerce_transactions),
        "3": ("Sensor Network Data", NestedDataGenerator.generate_sensor_network_data),
        "4": ("Document Management", NestedDataGenerator.generate_document_management),
        "5": ("Medical Records", NestedDataGenerator.generate_medical_records),
    }
    
    print("\n📋 Available Nested Data Types:")
    for key, (name, _) in generators.items():
        print(f"{key}. {name}")
    
    choice = input("\nSelect data type (1-5): ").strip()
    
    if choice not in generators:
        print("❌ Invalid choice")
        return
    
    name, generator = generators[choice]
    print(f"\n🔄 Generating {name}...")
    
    if choice in ["1", "2", "3", "4", "5"]:
        count_map = {"1": None, "2": 20, "3": 30, "4": 15, "5": 20}
        if count_map[choice]:
            data = generator(count_map[choice])
        else:
            data = generator()
    
    output_file = f"nested_data_{name.lower().replace(' ', '_')}.json"
    with open(output_file, 'w') as f:
        json.dump({
            "data_type": name,
            "generated_at": datetime.now().isoformat(),
            "record_count": len(data),
            "records": data
        }, f, indent=2)
    
    print(f"✅ Generated {output_file}")
    print(f"   Records: {len(data)}")
    print("\n📄 Sample record:")
    print(json.dumps(data[0], indent=2)[:500] + "..." if len(json.dumps(data[0], indent=2)) > 500 else json.dumps(data[0], indent=2))


if __name__ == "__main__":
    main()
