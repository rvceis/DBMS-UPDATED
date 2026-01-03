#!/bin/bash
cd /home/akash/Desktop/DBMS_PROJECT/DBMS_LAB_PROJECT/flask_backend
echo "Checking Python syntax..."
./venv/bin/python3 -m py_compile app/__init__.py app/routes/metadata.py
if [ $? -eq 0 ]; then
    echo "✅ Syntax OK"
    echo "Stopping old Flask processes..."
    pkill -9 -f "flask_backend.*main.py"
    sleep 2
    echo "Starting Flask backend..."
    nohup ./venv/bin/python3 ./main.py > /tmp/flask.log 2>&1 &
    PID=$!
    echo "Flask started with PID: $PID"
    sleep 3
    echo "Checking if running..."
    if ps -p $PID > /dev/null; then
        echo "✅ Flask is running"
        tail -20 /tmp/flask.log
    else
        echo "❌ Flask failed to start"
        tail -50 /tmp/flask.log
    fi
else
    echo "❌ Syntax error"
fi
