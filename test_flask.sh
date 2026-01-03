#!/bin/bash
cd /home/akash/Desktop/DBMS_PROJECT/DBMS_LAB_PROJECT/flask_backend

echo "=== Testing Flask Backend ==="
echo ""

# Kill old processes
pkill -9 -f "flask_backend.*main.py" 2>/dev/null
sleep 1

# Start Flask in background
nohup ./venv/bin/python3 ./main.py > /tmp/flask_test.log 2>&1 &
FLASK_PID=$!

echo "Flask started with PID: $FLASK_PID"
sleep 4

# Test if running
if ps -p $FLASK_PID > /dev/null; then
    echo "✅ Flask is running"
    
    # Test root endpoint
    echo ""
    echo "Testing root endpoint..."
    RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost:5000/ 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
    echo "$RESPONSE" | grep -v "HTTP_CODE:"
    
    if [ "$HTTP_CODE" == "200" ]; then
        echo "✅ Root endpoint working (200)"
    else
        echo "❌ Root endpoint failed ($HTTP_CODE)"
    fi
    
    # Test metadata endpoint (without auth - should fail with 401)
    echo ""
    echo "Testing /metadata/47/data endpoint..."
    RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" http://localhost:5000/metadata/47/data 2>&1)
    HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
    echo "$RESPONSE" | grep -v "HTTP_CODE:"
    
    if [ "$HTTP_CODE" == "401" ]; then
        echo "✅ Endpoint exists (401 = needs auth)"
    elif [ "$HTTP_CODE" == "404" ]; then
        echo "❌ Endpoint not found (404)"
    else
        echo "⚠️  Got HTTP $HTTP_CODE"
    fi
    
    echo ""
    echo "Flask logs (last 20 lines):"
    tail -20 /tmp/flask_test.log
    
else
    echo "❌ Flask failed to start"
    echo ""
    echo "Error logs:"
    cat /tmp/flask_test.log
fi

echo ""
echo "Flask is running in background (PID: $FLASK_PID)"
echo "To stop: kill $FLASK_PID"
echo "To view logs: tail -f /tmp/flask_test.log"
