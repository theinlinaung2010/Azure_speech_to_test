# AWS Lightsail Deployment Guide

Complete step-by-step guide to deploy Azure Speech Transcription plugin on your existing AWS Lightsail WordPress instance.

## Prerequisites

✅ Existing AWS Lightsail instance with WordPress  
✅ SSH access to your Lightsail instance  
✅ Azure Speech Service credentials (SPEECH_KEY and SPEECH_REGION)  
✅ Domain/IP for your WordPress site

## Overview

You'll install two components on the same Lightsail server:

1. **WordPress Plugin** - Frontend interface
2. **Flask API** - Backend transcription service (runs on localhost:3333)

---

## Part 1: Prepare Your Lightsail Instance

### Step 1.1: SSH into Your Server

```bash
# From your local machine
ssh -i /path/to/your-key.pem ubuntu@your-lightsail-ip

# Or use Lightsail browser-based SSH from the AWS console
```

### Step 1.2: Update System Packages

```bash
sudo apt update
sudo apt upgrade -y
```

### Step 1.3: Install Required System Packages

```bash
# Install Python 3, pip, and ffmpeg (required for audio conversion)
sudo apt install -y python3 python3-pip python3-venv ffmpeg git

# Verify installations
python3 --version    # Should show Python 3.8 or higher
ffmpeg -version      # Should show ffmpeg version
pip3 --version       # Should show pip version
```

---

## Part 2: Deploy Flask API Backend

### Step 2.1: Create Application Directory

```bash
# Create directory for the Flask API
sudo mkdir -p /opt/azure-speech-api
sudo chown $USER:$USER /opt/azure-speech-api
cd /opt/azure-speech-api
```

### Step 2.2: Upload Flask API Files

**Option A: Using Git (Recommended)**

```bash
cd /opt/azure-speech-api
git clone https://github.com/yourusername/Azure_speech_to_test.git .
# Or if you have the code locally, use option B
```

**Option B: Using SCP from your local machine**

```bash
# From your LOCAL machine (in the project directory)
scp -i /path/to/your-key.pem -r api/* ubuntu@your-lightsail-ip:/opt/azure-speech-api/
```

**Option C: Using SFTP**

```bash
# Use an SFTP client like FileZilla or WinSCP
# Connect to your-lightsail-ip
# Upload the entire 'api' folder contents to /opt/azure-speech-api/
```

### Step 2.3: Create Python Virtual Environment

```bash
cd /opt/azure-speech-api
python3 -m venv venv
source venv/bin/activate

# Your prompt should now show (venv)
```

### Step 2.4: Install Python Dependencies

```bash
# Make sure you're in the venv
pip install --upgrade pip
pip install -r requirements.txt

# This will install:
# - Flask
# - flask-cors
# - azure-cognitiveservices-speech
# - pydub
# - gunicorn
```

### Step 2.5: Configure Environment Variables

```bash
# Create .env file
nano .env
```

Add your Azure credentials:

```
SPEECH_KEY=your_azure_speech_key_here
SPEECH_REGION=your_azure_region_here
```

Save and exit (Ctrl+X, then Y, then Enter)

**Verify the .env file:**

```bash
cat .env
# Should show your credentials
```

### Step 2.6: Create Required Directories

```bash
mkdir -p uploads out
chmod 755 uploads out
```

### Step 2.7: Test Flask API Manually (Optional but Recommended)

```bash
# Still in venv
python app.py

# You should see:
# * Running on http://127.0.0.1:3333

# Open another SSH session and test:
curl http://localhost:3333/api/health
# Should return: {"status":"healthy"}

# If it works, stop the server (Ctrl+C) and continue
```

---

## Part 3: Setup Flask API as System Service

### Step 3.1: Create Systemd Service File

```bash
sudo nano /etc/systemd/system/azure-speech-api.service
```

Paste this configuration:

```ini
[Unit]
Description=Azure Speech-to-Text Flask API
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/opt/azure-speech-api
Environment="PATH=/opt/azure-speech-api/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
EnvironmentFile=/opt/azure-speech-api/.env
ExecStart=/opt/azure-speech-api/venv/bin/gunicorn --config gunicorn_config.py app:app
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Save and exit (Ctrl+X, then Y, then Enter)

### Step 3.2: Set Correct Permissions

```bash
# Change ownership to www-data (same user as Apache/WordPress)
sudo chown -R www-data:www-data /opt/azure-speech-api

# Make sure .env is readable
sudo chmod 644 /opt/azure-speech-api/.env
```

### Step 3.3: Update Gunicorn Config for Production

```bash
nano /opt/azure-speech-api/gunicorn_config.py
```

Ensure it has:

```python
bind = "127.0.0.1:3333"
workers = 2
worker_class = "sync"
timeout = 300
keepalive = 75
accesslog = "/opt/azure-speech-api/access.log"
errorlog = "/opt/azure-speech-api/error.log"
loglevel = "info"
```

### Step 3.4: Enable and Start the Service

```bash
# Reload systemd to recognize new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable azure-speech-api

# Start the service
sudo systemctl start azure-speech-api

# Check status
sudo systemctl status azure-speech-api
```

**Expected output:**

```
● azure-speech-api.service - Azure Speech-to-Text Flask API
   Loaded: loaded (/etc/systemd/system/azure-speech-api.service; enabled)
   Active: active (running) since...
```

### Step 3.5: Verify API is Running

```bash
# Test health endpoint
curl http://localhost:3333/api/health

# Should return: {"status":"healthy"}

# Check logs if there are issues
sudo journalctl -u azure-speech-api -f
```

---

## Part 4: Install WordPress Plugin

### Step 4.1: Upload Plugin Files

**Option A: Using SCP from local machine**

```bash
# From your LOCAL machine
cd wordpress-plugin
scp -i /path/to/your-key.pem -r azure-speech-transcribe ubuntu@your-lightsail-ip:/tmp/
```

Then on the server:

```bash
# SSH into server
sudo mv /tmp/azure-speech-transcribe /opt/bitnami/wordpress/wp-content/plugins/
sudo chown -R bitnami:daemon /opt/bitnami/wordpress/wp-content/plugins/azure-speech-transcribe
```

**Option B: Using WordPress Admin (easier)**

1. On your local machine, compress the plugin:

   ```bash
   cd wordpress-plugin
   zip -r azure-speech-transcribe.zip azure-speech-transcribe/
   ```

2. In WordPress Admin:
   - Go to **Plugins → Add New → Upload Plugin**
   - Choose the `.zip` file
   - Click **Install Now**
   - Click **Activate**

**Option C: Using SFTP**

1. Use FileZilla/WinSCP
2. Navigate to `/opt/bitnami/wordpress/wp-content/plugins/`
3. Upload the `azure-speech-transcribe` folder

### Step 4.2: Set Correct Permissions

```bash
# If you uploaded manually via SCP/SFTP
cd /opt/bitnami/wordpress/wp-content/plugins/
sudo chown -R bitnami:daemon azure-speech-transcribe
sudo chmod -R 755 azure-speech-transcribe
```

### Step 4.3: Activate Plugin in WordPress

1. Log in to your WordPress admin panel
2. Go to **Plugins**
3. Find "Azure Speech Transcribe"
4. Click **Activate**

### Step 4.4: Configure Plugin Settings

1. Go to **Settings → Azure Speech Transcribe**
2. Configure:
   - **Access Password**: Choose a strong password (users will need this)
   - **Flask API URL**: `http://localhost:3333`
   - **Max File Size**: `50` (MB) or adjust as needed
3. Click **Save Settings**

---

## Part 5: Create Test Page

### Step 5.1: Create WordPress Page

1. Go to **Pages → Add New**
2. Title: "Audio Transcription"
3. Add the shortcode in the content:
   ```
   [azure_transcribe]
   ```
4. Click **Publish**
5. Note the page URL

### Step 5.2: Test the Complete System

1. Visit the page you just created
2. Enter the password you configured
3. Upload a small audio file (WAV or M4A)
4. Watch the transcription stream in real-time
5. Test copy and download functions

---

## Part 6: Security Hardening

### Step 6.1: Firewall Configuration

```bash
# Ensure port 3333 is NOT exposed to the internet
# The Flask API should only be accessible from localhost

# Check firewall status
sudo ufw status

# If UFW is active, ensure only necessary ports are open:
# - Port 80 (HTTP)
# - Port 443 (HTTPS)
# - Port 22 (SSH)
# Port 3333 should NOT be in this list
```

### Step 6.2: Secure WordPress Plugin Access

1. Use a strong password in plugin settings
2. Consider adding IP restrictions in WordPress if needed
3. Enable WordPress security plugins if desired

### Step 6.3: File Permissions Check

```bash
# Verify API directory permissions
ls -la /opt/azure-speech-api/
# uploads/ and out/ should be writable by www-data

# If needed:
sudo chown -R www-data:www-data /opt/azure-speech-api/uploads
sudo chown -R www-data:www-data /opt/azure-speech-api/out
sudo chmod 755 /opt/azure-speech-api/uploads
sudo chmod 755 /opt/azure-speech-api/out
```

---

## Part 7: Monitoring and Maintenance

### Step 7.1: Set Up Log Rotation

```bash
sudo nano /etc/logrotate.d/azure-speech-api
```

Add:

```
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
```

### Step 7.2: Monitor Service Status

```bash
# Check if service is running
sudo systemctl status azure-speech-api

# View recent logs
sudo journalctl -u azure-speech-api -n 100

# Follow logs in real-time
sudo journalctl -u azure-speech-api -f

# Check application logs
tail -f /opt/azure-speech-api/transcription.log
tail -f /opt/azure-speech-api/error.log
```

### Step 7.3: Service Management Commands

```bash
# Start service
sudo systemctl start azure-speech-api

# Stop service
sudo systemctl stop azure-speech-api

# Restart service (after code updates)
sudo systemctl restart azure-speech-api

# View service status
sudo systemctl status azure-speech-api

# Disable service (prevent auto-start)
sudo systemctl disable azure-speech-api

# Enable service (auto-start on boot)
sudo systemctl enable azure-speech-api
```

---

## Part 8: Updating the Application

### When You Need to Update Code:

```bash
# SSH into server
cd /opt/azure-speech-api

# Pull latest changes (if using git)
sudo -u www-data git pull

# Or upload new files via SCP/SFTP

# Install any new dependencies
source venv/bin/activate
pip install -r requirements.txt

# Restart the service
sudo systemctl restart azure-speech-api

# Check status
sudo systemctl status azure-speech-api
```

---

## Troubleshooting

### Flask API Not Starting

**Check logs:**

```bash
sudo journalctl -u azure-speech-api -n 50
tail -f /opt/azure-speech-api/error.log
```

**Common issues:**

- Missing .env file: Create `/opt/azure-speech-api/.env`
- Wrong permissions: `sudo chown -R www-data:www-data /opt/azure-speech-api`
- Port already in use: `sudo lsof -i :3333`
- Missing dependencies: Reinstall with `pip install -r requirements.txt`

### WordPress Shows "Connection Error"

**Test API connectivity:**

```bash
# From SSH
curl http://localhost:3333/api/health
```

**If fails:**

1. Check if service is running: `sudo systemctl status azure-speech-api`
2. Check API URL in WordPress settings is `http://localhost:3333`
3. Restart service: `sudo systemctl restart azure-speech-api`

### Transcription Fails

**Check Azure credentials:**

```bash
cat /opt/azure-speech-api/.env
# Verify SPEECH_KEY and SPEECH_REGION are correct
```

**Test manually:**

```bash
cd /opt/azure-speech-api
source venv/bin/activate
python app.py
# Upload a file via test.html and watch server output
```

### FFmpeg Warning in Logs

**If you see "Couldn't find ffmpeg" warnings:**

```bash
# Verify ffmpeg is installed
which ffmpeg
ffmpeg -version

# If not found, install it
sudo apt install -y ffmpeg

# Verify www-data user can access it
sudo -u www-data which ffmpeg
```

The warning is usually harmless if ffmpeg is installed system-wide, but if audio conversion fails, ensure ffmpeg is in the system PATH.

### File Upload/Download Issues

**Check directory permissions:**

```bash
ls -la /opt/azure-speech-api/
sudo chown -R www-data:www-data /opt/azure-speech-api/uploads
sudo chown -R www-data:www-data /opt/azure-speech-api/out
sudo chmod 755 /opt/azure-speech-api/uploads
sudo chmod 755 /opt/azure-speech-api/out
```

### High Memory Usage

**Adjust Gunicorn workers:**

```bash
nano /opt/azure-speech-api/gunicorn_config.py
# Reduce workers = 2 to workers = 1 for smaller instances
sudo systemctl restart azure-speech-api
```

---

## Performance Optimization

### For Lightsail 1GB Instance:

- Keep `workers = 1` in gunicorn_config.py
- Set shorter retention time (12 hours instead of 24)
- Monitor memory: `free -h`

### For Lightsail 2GB+ Instance:

- Use `workers = 2` (default)
- Can handle more concurrent transcriptions

---

## Backup and Recovery

### Backup Important Files:

```bash
# Backup .env file
sudo cp /opt/azure-speech-api/.env /opt/azure-speech-api/.env.backup

# Backup completed transcripts (optional)
sudo tar -czf /home/ubuntu/transcripts-backup.tar.gz /opt/azure-speech-api/out/
```

### Recovery After Instance Restart:

The service should start automatically on boot. If not:

```bash
sudo systemctl start azure-speech-api
sudo systemctl status azure-speech-api
```

---

## Quick Reference

### Service Commands

```bash
sudo systemctl status azure-speech-api    # Check status
sudo systemctl start azure-speech-api     # Start
sudo systemctl stop azure-speech-api      # Stop
sudo systemctl restart azure-speech-api   # Restart
```

### Log Locations

```bash
/opt/azure-speech-api/transcription.log   # Application logs
/opt/azure-speech-api/error.log           # Error logs
/opt/azure-speech-api/access.log          # Access logs
sudo journalctl -u azure-speech-api       # System service logs
```

### File Locations

```bash
/opt/azure-speech-api/                    # Flask API root
/opt/bitnami/wordpress/wp-content/plugins/azure-speech-transcribe/  # WordPress plugin
```

### Test Commands

```bash
curl http://localhost:3333/api/health     # Health check
sudo systemctl status azure-speech-api    # Service status
ps aux | grep gunicorn                    # Check if running
```

---

## Post-Deployment Checklist

- [ ] Flask API service is running: `sudo systemctl status azure-speech-api`
- [ ] Health endpoint returns "healthy": `curl http://localhost:3333/api/health`
- [ ] WordPress plugin is activated
- [ ] Plugin settings are configured (password, API URL)
- [ ] Test page created with shortcode `[azure_transcribe]`
- [ ] Test transcription works end-to-end
- [ ] Firewall does NOT expose port 3333
- [ ] Log rotation is configured
- [ ] Service auto-starts on boot: `sudo systemctl is-enabled azure-speech-api`
- [ ] Backups of .env file created

---

## Support

If you encounter issues:

1. **Check service status**: `sudo systemctl status azure-speech-api`
2. **Review logs**: `sudo journalctl -u azure-speech-api -n 100`
3. **Test API**: `curl http://localhost:3333/api/health`
4. **Check permissions**: `ls -la /opt/azure-speech-api/`
5. **Verify Azure credentials**: `cat /opt/azure-speech-api/.env`

For WordPress-specific issues, check:

- WordPress debug.log: `/opt/bitnami/wordpress/wp-content/debug.log`
- Apache error log: `/opt/bitnami/apache/logs/error_log`

---

**Deployment Complete! 🎉**

Your Azure Speech Transcription plugin is now running on AWS Lightsail.
