#!/usr/bin/env python3
"""
Verify all new features are properly implemented
"""

import os
import sys

print("\n" + "="*70)
print("🔍 FEATURE VERIFICATION REPORT")
print("="*70)

# 1. Check backend files
print("\n1️⃣  Backend Files:")
backend_files = [
    'flask_backend/app/services/data_import_service.py',
    'flask_backend/app/routes/uploads.py',
    'flask_backend/app/routes/metadata.py',
]

for file in backend_files:
    exists = os.path.exists(file)
    status = "✅" if exists else "❌"
    print(f"   {status} {file}")

# 2. Check frontend files  
print("\n2️⃣  Frontend Files:")
frontend_files = [
    'Frontend/src/components/FileImportDialog.tsx',
    'Frontend/src/pages/DataPage.tsx',
]

for file in frontend_files:
    exists = os.path.exists(file)
    status = "✅" if exists else "❌"
    print(f"   {status} {file}")

# 3. Check sample data
print("\n3️⃣  Sample Data Files:")
sample_files = [
    'sample_employees.csv',
    'sample_projects.json',
    'sample_products.xlsx',
]

for file in sample_files:
    exists = os.path.exists(file)
    status = "✅" if exists else "❌"
    print(f"   {status} {file}")

# 4. Check documentation
print("\n4️⃣  Documentation:")
docs = [
    'DATA_IMPORT_UPDATE_GUIDE.md',
    'TESTING_GUIDE.md',
    'IMPLEMENTATION_SUMMARY.md',
]

for doc in docs:
    exists = os.path.exists(doc)
    status = "✅" if exists else "❌"
    print(f"   {status} {doc}")

# 5. Check Python syntax
print("\n5️⃣  Python Syntax Check:")
try:
    import py_compile
    py_compile.compile('flask_backend/app/services/data_import_service.py', doraise=True)
    py_compile.compile('flask_backend/app/routes/uploads.py', doraise=True)
    py_compile.compile('flask_backend/app/routes/metadata.py', doraise=True)
    print("   ✅ All Python files compile successfully")
except Exception as e:
    print(f"   ❌ Syntax error: {e}")

# 6. Check dependencies
print("\n6️⃣  Dependencies:")
try:
    import openpyxl
    print("   ✅ openpyxl (Excel support)")
except:
    print("   ❌ openpyxl not installed")

try:
    import pandas
    print("   ✅ pandas")
except:
    print("   ❌ pandas not installed")

# 7. Check server
print("\n7️⃣  Server Status:")
import subprocess
result = subprocess.run(['pgrep', '-f', 'python3 main.py'], capture_output=True)
if result.returncode == 0:
    print("   ✅ Flask server is running")
else:
    print("   ❌ Flask server is not running")

print("\n" + "="*70)
print("✨ VERIFICATION COMPLETE")
print("="*70)
print("\nNext Steps:")
print("  1. Start Frontend: cd Frontend && npm run dev")
print("  2. Login: admin@test.com / password")
print("  3. Go to Data Page")
print("  4. Click 'Import File' to test")
print("  5. Select sample_employees.csv, sample_projects.json, or sample_products.xlsx")
print("\nSee TESTING_GUIDE.md for comprehensive test scenarios")
print("="*70 + "\n")

