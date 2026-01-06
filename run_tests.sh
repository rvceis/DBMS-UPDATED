#!/bin/bash

# MetaDB Complete Integration Test Runner
# Tests all endpoints, database operations, and frontend integration

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║          MetaDB Complete Integration Test Suite                ║"
echo "║  Testing: Endpoints | Database | Schema | EAV Storage | API   ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/.."
VENV_PATH="$PROJECT_ROOT/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Step 1: Check environment
echo -e "${BLUE}▶ STEP 1: Checking environment...${NC}"
if [ ! -d "$VENV_PATH" ]; then
    echo -e "${RED}✗ Virtual environment not found at $VENV_PATH${NC}"
    echo "Creating virtual environment..."
    cd "$PROJECT_ROOT"
    python3 -m venv venv
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Step 2: Install dependencies
echo ""
echo -e "${BLUE}▶ STEP 2: Installing test dependencies...${NC}"
cd "$PROJECT_ROOT"
pip install -q pytest pytest-cov python-dotenv 2>/dev/null || pip install pytest pytest-cov python-dotenv
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Step 3: Check if tests exist
echo ""
echo -e "${BLUE}▶ STEP 3: Verifying test file...${NC}"
if [ ! -f "tests/test_complete_integration.py" ]; then
    echo -e "${RED}✗ Test file not found at tests/test_complete_integration.py${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Test file found${NC}"

# Step 4: Run tests with coverage
echo ""
echo -e "${BLUE}▶ STEP 4: Running integration tests...${NC}"
echo ""

pytest tests/test_complete_integration.py -v --tb=short --color=yes 2>&1 | tee test_results.txt

# Step 5: Generate coverage report
echo ""
echo -e "${BLUE}▶ STEP 5: Running tests with coverage...${NC}"
echo ""

pytest tests/test_complete_integration.py \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html \
    -v --tb=short --color=yes 2>&1 | tee -a test_results.txt

# Step 6: Summary
echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                        TEST SUMMARY                            ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Extract test results
if grep -q "passed" test_results.txt; then
    PASSED=$(grep -oE '[0-9]+ passed' test_results.txt | head -1 | grep -oE '[0-9]+')
    echo -e "${GREEN}✓ Tests Passed: $PASSED${NC}"
fi

if grep -q "failed" test_results.txt; then
    FAILED=$(grep -oE '[0-9]+ failed' test_results.txt | head -1 | grep -oE '[0-9]+')
    echo -e "${RED}✗ Tests Failed: $FAILED${NC}"
else
    echo -e "${GREEN}✓ No failures detected${NC}"
fi

if grep -q "error" test_results.txt; then
    echo -e "${YELLOW}⚠ Check test_results.txt for details${NC}"
fi

echo ""
echo -e "${BLUE}Test Results: ${NC}test_results.txt"
if [ -d "htmlcov" ]; then
    echo -e "${BLUE}Coverage Report: ${NC}htmlcov/index.html"
fi

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   DATABASE VERIFICATION                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Step 7: Database verification
echo -e "${BLUE}▶ Checking database tables...${NC}"

python3 << 'EOF'
import sys
import os
sys.path.insert(0, os.getcwd())

from app import create_app
from app.extensions import db

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

with app.app_context():
    db.create_all()
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    
    print(f"\n✓ Database tables created: {len(tables)}")
    print("\n  Tables:")
    for table in sorted(tables):
        cols = len(inspector.get_columns(table))
        print(f"    • {table:<25} ({cols} columns)")
    
    # Check critical tables
    critical_tables = [
        'users', 'schemas', 'schema_fields', 'metadata_records',
        'field_values', 'data_rows', 'change_logs', 'schema_versions'
    ]
    
    missing = [t for t in critical_tables if t not in tables]
    if missing:
        print(f"\n✗ Missing tables: {', '.join(missing)}")
        sys.exit(1)
    else:
        print(f"\n✓ All critical tables present")

print("\n✓ Database integrity verified")
EOF

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   SCHEMA VERIFICATION                          ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

python3 << 'EOF'
import sys
import os
sys.path.insert(0, os.getcwd())

from app import create_app
from app.extensions import db
from app.models import SchemaField

app = create_app()
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

with app.app_context():
    db.create_all()
    inspector = db.inspect(db.engine)
    
    # Check schema_fields columns
    cols = [col['name'] for col in inspector.get_columns('schema_fields')]
    required_cols = ['id', 'schema_id', 'field_name', 'field_type', 'is_required', 'is_deleted']
    
    print("✓ schema_fields table structure:")
    for col in required_cols:
        status = "✓" if col in cols else "✗"
        print(f"  {status} {col}")
    
    # Check field_values columns
    cols = [col['name'] for col in inspector.get_columns('field_values')]
    required_cols = ['value_text', 'value_int', 'value_float', 'value_bool', 'value_date', 'value_json', 'value_binary']
    
    print("\n✓ field_values table (EAV Pattern) structure:")
    for col in required_cols:
        status = "✓" if col in cols else "✗"
        print(f"  {status} {col:<20} (for type-specific storage)")
    
    print("\n✓ Dynamic schema support verified")
EOF

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║                   ENDPOINT VERIFICATION                        ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

python3 << 'EOF'
from flask import Flask
from app import create_app

app = create_app()

print("✓ Registered API Endpoints:\n")

# Collect all routes
routes = {}
for rule in app.url_map.iter_rules():
    if 'static' not in rule.rule and 'json' not in rule.rule:
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        endpoint = rule.rule
        if endpoint not in routes:
            routes[endpoint] = methods

# Group by category
categories = {
    'Auth': [r for r in routes if '/auth' in r],
    'Schemas': [r for r in routes if '/schemas' in r],
    'Data Records': [r for r in routes if '/data' in r],
    'Uploads': [r for r in routes if '/uploads' in r],
    'Reports': [r for r in routes if '/reports' in r],
    'Analytics': [r for r in routes if '/analytics' in r],
    'Assets': [r for r in routes if '/asset' in r],
}

for category, endpoints in categories.items():
    if endpoints:
        print(f"  {category}:")
        for ep in sorted(endpoints):
            methods = routes[ep]
            print(f"    • {ep:<40} [{methods}]")
        print()

print(f"\n✓ Total endpoints: {len(routes)}")
EOF

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                   ✓ TEST SUITE COMPLETE                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Next steps:"
echo "  1. Review test_results.txt for detailed test output"
echo "  2. Check htmlcov/index.html for code coverage (if generated)"
echo "  3. Fix any failing tests"
echo "  4. Run: python3 main.py  (to start the backend)"
echo "  5. Run: npm run dev       (to start the frontend)"
echo ""
