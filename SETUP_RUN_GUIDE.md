# Complete Setup & Run Guide

## 🚀 Quick Start (5 minutes)

### Prerequisites
- Python 3.9+
- Node.js 16+
- SQLite3 (included with Python)

### Step 1: Start the Backend

```bash
cd flask_backend

# Activate virtual environment
source venv/bin/activate

# Start Flask server
python3 main.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

### Step 2: Start the Frontend

In a NEW terminal window:

```bash
cd Frontend

# Install dependencies (first time only)
npm install

# Start Vite development server
npm run dev
```

You should see:
```
VITE v7.2.0  ready in 123 ms

➜  Local:   http://localhost:5173/
```

### Step 3: Login & View Data

1. Open browser: `http://localhost:5173`
2. Login with:
   - **Email**: `admin@test.com`
   - **Password**: `password`
3. Click "Data" in sidebar
4. View the 14 test records across 7 different schemas

---

## 📊 Backend Setup Details

### Initial Setup (One-time)

```bash
cd flask_backend

# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Initialize database (creates tables & admin user)
python3 init_db.py

# Seed asset types
python3 seed_asset_types.py
```

### Verify Backend Status

```bash
# Check if database exists
ls -la instance/database.db

# Check if tables are created
source venv/bin/activate
cd flask_backend
python3 << 'EOF'
from app import create_app
from sqlalchemy import text
from app.extensions import db

app = create_app()
with app.app_context():
    result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).fetchall()
    print("Tables in database:")
    for (name,) in result:
        print(f"  ✓ {name}")
EOF
```

### Environment Variables

**File**: `flask_backend/.env`

```env
# Database
DATABASE_URL=sqlite:///instance/database.db

# JWT
JWT_SECRET_KEY=your-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# Flask
FLASK_ENV=development
FLASK_DEBUG=true
```

---

## 🎨 Frontend Setup Details

### Initial Setup (One-time)

```bash
cd Frontend

# Install dependencies
npm install

# Install missing packages if needed
npm install lucide-react zustand axios
```

### Environment Variables

**File**: `Frontend/.env.local`

```env
VITE_API_URL=http://localhost:5000
```

Note: The Vite development server is configured to proxy `/api` requests to `http://localhost:5000` via `vite.config.js`.

### Build for Production

```bash
cd Frontend

# Build optimized bundle
npm run build

# Output will be in dist/ folder
# Serve with: npx serve dist
```

---

## 🧪 Test Data

### Generate Test Data

```bash
cd /path/to/project/root
source flask_backend/venv/bin/activate
python3 generate_test_data.py
```

This will:
- Authenticate with admin credentials
- Create 7 dynamic schemas
- Generate 14+ test records
- Output success/failure for each record

### Sample Test Queries

```bash
# Get all records
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5000/api/data

# Get records for specific schema
curl -H "Authorization: Bearer YOUR_TOKEN" \
  "http://localhost:5000/api/data?schema_id=1"

# Create a record
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test","first_name":"John","email":"john@example.com"}' \
  http://localhost:5000/api/data
```

---

## 🔍 Database Management

### View Database Contents

```bash
cd flask_backend
source venv/bin/activate

# Python script to view data
python3 << 'EOF'
from app import create_app
from sqlalchemy import text
from app.extensions import db

app = create_app()
with app.app_context():
    # Count records
    result = db.session.execute(text('SELECT COUNT(*) FROM metadata_records')).scalar()
    print(f"Total records: {result}")
    
    # Show schemas
    schemas = db.session.execute(text('SELECT id, name FROM schemas')).fetchall()
    print("\nSchemas:")
    for id, name in schemas:
        count = db.session.execute(text(f'SELECT COUNT(*) FROM metadata_records WHERE schema_id = {id}')).scalar()
        print(f"  {id}. {name}: {count} records")
EOF
```

### Reset Database

```bash
cd flask_backend
source venv/bin/activate

# Remove old database
rm instance/database.db

# Recreate from scratch
python3 init_db.py
python3 seed_asset_types.py

# Verify
python3 main.py  # Should start with fresh database
```

### Export Database

```bash
# Backup database
cp flask_backend/instance/database.db flask_backend/instance/database.db.backup

# View as JSON (using script)
cd flask_backend
source venv/bin/activate
python3 << 'EOF'
import json
from sqlalchemy import text
from app import create_app
from app.extensions import db

app = create_app()
with app.app_context():
    records = db.session.execute(text('SELECT * FROM metadata_records')).fetchall()
    print(json.dumps([dict(r) for r in records], indent=2))
EOF
```

---

## 🚨 Troubleshooting

### Backend won't start

**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solution**:
```bash
cd flask_backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Frontend can't connect to backend

**Error**: `ECONNREFUSED 127.0.0.1:5000` or `CORS error`

**Solution**:
1. Make sure backend is running: `python3 flask_backend/main.py`
2. Check Vite proxy in `Frontend/vite.config.js` has correct backend URL
3. Verify `/api` prefix is being used in frontend requests

### Database is locked

**Error**: `database is locked`

**Solution**:
```bash
# Kill any Python processes
killall python3

# Wait a moment, then restart
cd flask_backend && source venv/bin/activate && python3 main.py
```

### Test data creation fails

**Error**: `Field validation failed: ["Field 'tags': Unsupported type..."]`

**Solution**: See [FIELD_TYPES_GUIDE.md](FIELD_TYPES_GUIDE.md) - Use `json` instead of `array<string>`

### 404 errors on API endpoints

**Error**: `GET /api/data 404 Not Found`

**Solution**:
1. Backend must be running on port 5000
2. Route must be registered in Flask app
3. JWT token must be valid in Authorization header

---

## 📝 Development Workflow

### Adding a New Schema

**Via API**:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "CustomSchema",
    "fields": [
      {"name": "title", "type": "string", "required": true},
      {"name": "count", "type": "integer", "required": false}
    ]
  }' \
  http://localhost:5000/api/schemas
```

**Via Frontend**:
1. Go to Schemas page
2. Click "New Schema"
3. Define fields and save

### Adding Test Data

**Via API**:
```bash
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Item", "count": 42}' \
  http://localhost:5000/api/data
```

**Via Frontend**:
1. Go to Data page
2. Click "Create Record"
3. Fill in fields
4. Submit

---

## 🔐 User Management

### Create New User

```bash
cd flask_backend
source venv/bin/activate
python3 << 'EOF'
from app import create_app
from app.extensions import db
from app.models import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    user = User(
        username="newuser",
        email="newuser@example.com",
        password=generate_password_hash("password123"),
        role="editor"  # or "viewer"
    )
    db.session.add(user)
    db.session.commit()
    print(f"Created user: {user.email}")
EOF
```

### List All Users

```bash
cd flask_backend
source venv/bin/activate
python3 << 'EOF'
from app import create_app
from app.models import User

app = create_app()
with app.app_context():
    users = User.query.all()
    for u in users:
        print(f"{u.email} ({u.role})")
EOF
```

---

## 🔄 Workflow with PostgreSQL (Production)

### 1. Update Connection String

**File**: `flask_backend/.env`

```env
# Change from SQLite:
DATABASE_URL=postgresql://user:password@localhost:5432/dbms_db

# Install PostgreSQL driver:
# pip install psycopg2-binary
```

### 2. Create Database

```bash
createdb dbms_db

# Or with credentials:
createdb -U postgres -h localhost dbms_db
```

### 3. Run Migrations

```bash
cd flask_backend
source venv/bin/activate

# Initialize tables
python3 init_db.py

# Seed data
python3 seed_asset_types.py
```

### 4. Restart Application

```bash
python3 main.py
```

All existing code works without changes!

---

## 📚 Documentation Files

- **[SYSTEM_STATUS.md](SYSTEM_STATUS.md)** - Current system status and validation results
- **[FIELD_TYPES_GUIDE.md](FIELD_TYPES_GUIDE.md)** - Supported field types and validation
- **[BACKEND_ARCHITECTURE.md](BACKEND_ARCHITECTURE.md)** - Backend design and components
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Project overview and features

---

## 🎊 Success Checklist

- [ ] Backend running on http://localhost:5000
- [ ] Frontend running on http://localhost:5173
- [ ] Can login with admin@test.com / password
- [ ] Can see 14 test records on Data page
- [ ] Can create new records
- [ ] Can view record details
- [ ] Can delete records
- [ ] Can filter records by schema

---

## 📞 Support

If you encounter issues:

1. Check the relevant documentation file above
2. Review backend logs: `flask_backend/app.log`
3. Check browser console for frontend errors (F12)
4. Verify both backend and frontend are running
5. Try resetting database: `rm flask_backend/instance/database.db && python3 init_db.py`

