#!/bin/bash

echo "Starting Azure Speech-to-Text Flask API..."
echo ""

cd "$(dirname "$0")/api"

if [ ! -f ".env" ]; then
    echo "ERROR: .env file not found!"
    echo "Please copy .env.example to .env and configure your Azure credentials."
    exit 1
fi

mkdir -p uploads
mkdir -p out

echo "Checking Python environment..."
python3 --version

echo ""
echo "Starting Flask server on http://localhost:5000"
echo "Press Ctrl+C to stop"
echo ""

python3 app.py
