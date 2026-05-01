#!/bin/bash
#
# AWS Lightsail Deployment Script for Azure Speech API
# Run this script on your Lightsail instance
#
# Usage: ./deploy-lightsail.sh
#

set -e  # Exit on error

echo "=========================================="
echo "Azure Speech API - Lightsail Deployment"
echo "=========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -eq 0 ]; then 
    echo -e "${RED}Please do not run this script as root${NC}"
    exit 1
fi

# Step 1: Update system
echo -e "${GREEN}Step 1: Updating system packages...${NC}"
sudo apt update
sudo apt upgrade -y

# Step 2: Install dependencies
echo -e "${GREEN}Step 2: Installing Python, pip, ffmpeg, and git...${NC}"
sudo apt install -y python3 python3-pip python3-venv ffmpeg git

# Verify installations
echo "Verifying installations..."
python3 --version
pip3 --version
ffmpeg -version | head -1

# Step 3: Create application directory
echo -e "${GREEN}Step 3: Creating application directory...${NC}"
sudo mkdir -p /opt/azure-speech-api
sudo chown $USER:$USER /opt/azure-speech-api

# Step 4: Prompt for source
echo ""
echo -e "${YELLOW}How do you want to install the API code?${NC}"
echo "1) Clone from GitHub repository"
echo "2) I will upload files manually via SCP/SFTP (skip this step)"
read -p "Enter choice (1 or 2): " source_choice

if [ "$source_choice" = "1" ]; then
    read -p "Enter GitHub repository URL: " repo_url
    cd /opt/azure-speech-api
    git clone "$repo_url" .
    
    # If code is in 'api' subdirectory, move it
    if [ -d "api" ]; then
        mv api/* .
        rmdir api
    fi
elif [ "$source_choice" = "2" ]; then
    echo -e "${YELLOW}Please upload your API files to /opt/azure-speech-api/ using SCP or SFTP${NC}"
    echo "Press Enter when files are uploaded..."
    read -p ""
fi

cd /opt/azure-speech-api

# Step 5: Create virtual environment
echo -e "${GREEN}Step 5: Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate

# Step 6: Install Python packages
echo -e "${GREEN}Step 6: Installing Python dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Step 7: Configure environment
echo -e "${GREEN}Step 7: Configuring environment variables...${NC}"
echo ""
echo -e "${YELLOW}Please enter your Azure Speech Service credentials:${NC}"
read -p "Azure Speech Key: " speech_key
read -p "Azure Speech Region (e.g., eastus): " speech_region

cat > .env << EOF
SPEECH_KEY=$speech_key
SPEECH_REGION=$speech_region
EOF

echo ".env file created"

# Step 8: Create required directories
echo -e "${GREEN}Step 8: Creating uploads and output directories...${NC}"
mkdir -p uploads out
chmod 755 uploads out

# Step 9: Test the API
echo -e "${GREEN}Step 9: Testing Flask API...${NC}"
echo "Starting test server..."
timeout 5 python app.py &
sleep 3

if curl -f http://localhost:3333/api/health 2>/dev/null; then
    echo -e "${GREEN}✓ API health check passed!${NC}"
else
    echo -e "${RED}✗ API health check failed${NC}"
    echo "Please check the configuration manually"
fi

# Kill the test server
pkill -f "python app.py" 2>/dev/null || true

# Step 10: Create systemd service
echo -e "${GREEN}Step 10: Creating systemd service...${NC}"
sudo tee /etc/systemd/system/azure-speech-api.service > /dev/null << 'EOF'
[Unit]
Description=Azure Speech-to-Text Flask API
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/azure-speech-api
Environment="PATH=/opt/azure-speech-api/venv/bin"
EnvironmentFile=/opt/azure-speech-api/.env
ExecStart=/opt/azure-speech-api/venv/bin/gunicorn --config gunicorn_config.py app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Step 11: Set permissions
echo -e "${GREEN}Step 11: Setting correct permissions...${NC}"
sudo chown -R www-data:www-data /opt/azure-speech-api
sudo chmod 644 /opt/azure-speech-api/.env

# Step 12: Enable and start service
echo -e "${GREEN}Step 12: Enabling and starting service...${NC}"
sudo systemctl daemon-reload
sudo systemctl enable azure-speech-api
sudo systemctl start azure-speech-api

# Wait a moment for service to start
sleep 2

# Step 13: Verify service
echo -e "${GREEN}Step 13: Verifying service status...${NC}"
if sudo systemctl is-active --quiet azure-speech-api; then
    echo -e "${GREEN}✓ Service is running!${NC}"
    sudo systemctl status azure-speech-api --no-pager
else
    echo -e "${RED}✗ Service failed to start${NC}"
    echo "Check logs with: sudo journalctl -u azure-speech-api -n 50"
fi

# Step 14: Test the running service
echo ""
echo -e "${GREEN}Step 14: Testing the deployed service...${NC}"
if curl -f http://localhost:3333/api/health 2>/dev/null; then
    echo -e "${GREEN}✓ Service health check passed!${NC}"
else
    echo -e "${RED}✗ Service health check failed${NC}"
fi

# Setup log rotation
echo -e "${GREEN}Step 15: Setting up log rotation...${NC}"
sudo tee /etc/logrotate.d/azure-speech-api > /dev/null << 'EOF'
/opt/azure-speech-api/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload azure-speech-api > /dev/null 2>&1 || true
    endscript
}
EOF

echo ""
echo "=========================================="
echo -e "${GREEN}Flask API Deployment Complete!${NC}"
echo "=========================================="
echo ""
echo "Service Status:"
echo "  Command: sudo systemctl status azure-speech-api"
echo ""
echo "View Logs:"
echo "  sudo journalctl -u azure-speech-api -f"
echo "  tail -f /opt/azure-speech-api/transcription.log"
echo ""
echo "Next Steps:"
echo "  1. Install WordPress plugin (see DEPLOYMENT_LIGHTSAIL.md Part 4)"
echo "  2. Configure plugin settings (API URL: http://localhost:3333)"
echo "  3. Create test page with [azure_transcribe] shortcode"
echo "  4. Test the complete system"
echo ""
echo "Important Files:"
echo "  Config: /opt/azure-speech-api/.env"
echo "  Service: /etc/systemd/system/azure-speech-api.service"
echo "  Logs: /opt/azure-speech-api/*.log"
echo ""
