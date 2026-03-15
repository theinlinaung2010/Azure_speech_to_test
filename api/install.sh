#!/bin/bash

echo "Installing Azure Speech-to-Text API dependencies..."
echo ""

cd "$(dirname "$0")"

# Check Python version
echo "Checking Python version..."
python3 --version

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Create directories
mkdir -p uploads
mkdir -p out

# Setup environment file
if [ ! -f ".env" ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your Azure credentials before running the server!"
fi

echo ""
echo "✅ Installation complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your Azure Speech credentials"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python app.py"
