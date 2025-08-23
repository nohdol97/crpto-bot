#!/bin/bash

# Start the API server for the dashboard

echo "Starting Crypto Bot API Server..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Install required packages if needed
pip install flask flask-cors

# Start the API server
python api_server.py