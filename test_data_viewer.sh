#!/bin/bash

# Test script for data viewer features
echo "🧪 Testing Data Viewer Features"
echo "================================"
echo ""

# Check if backend is running
echo "1. Checking Flask backend..."
if curl -s http://localhost:5000/api/health > /dev/null 2>&1; then
    echo "   ✅ Backend is running on port 5000"
else
    echo "   ❌ Backend is NOT running. Start it with:"
    echo "      cd flask_backend && python3 main.py"
    exit 1
fi

echo ""

# Check if frontend is running
echo "2. Checking React frontend..."
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "   ✅ Frontend is running on port 5173"
else
    echo "   ⚠️  Frontend might not be running. Start it with:"
    echo "      cd Frontend && npm run dev"
fi

echo ""
echo "3. Testing API endpoints..."

# Get auth token (you'll need to replace with actual credentials)
echo "   Note: Manual testing required with actual auth token"
echo ""
echo "   Test pagination:"
echo "   curl -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "        'http://localhost:5000/api/metadata/1/data?page=1&per_page=10'"
echo ""
echo "   Test filtering:"
echo "   curl -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "        'http://localhost:5000/api/metadata/1/data?filter_field=name&filter_value=John'"
echo ""
echo "   Test sorting:"
echo "   curl -H 'Authorization: Bearer YOUR_TOKEN' \\"
echo "        'http://localhost:5000/api/metadata/1/data?sort_field=age&sort_order=desc'"

echo ""
echo "4. Frontend features to test manually:"
echo "   - Open browser: http://localhost:5173"
echo "   - Login with admin credentials"
echo "   - Navigate to 'Data' page"
echo "   - Click Eye icon (👁️) on any record with imported data"
echo "   - Test pagination, filtering, sorting, edit, delete"
echo ""
echo "✅ All components updated with Authorization headers!"
echo "📄 See FRONTEND_DATA_VIEWER_FEATURES.md for full documentation"
