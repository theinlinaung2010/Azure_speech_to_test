# AWS Lightsail Deployment Checklist

Quick reference checklist for deploying Azure Speech Transcription on Lightsail.

## Pre-Deployment

- [ ] AWS Lightsail instance running with WordPress
- [ ] SSH access configured
- [ ] Azure Speech Service credentials ready
  - [ ] SPEECH_KEY
  - [ ] SPEECH_REGION
- [ ] Plugin files ready for upload

---

## Flask API Deployment

### System Setup
- [ ] SSH into Lightsail: `ssh -i key.pem ubuntu@your-ip`
- [ ] Update system: `sudo apt update && sudo apt upgrade -y`
- [ ] Install dependencies: `sudo apt install -y python3 python3-pip python3-venv ffmpeg git`
- [ ] Verify installations: `python3 --version`, `ffmpeg -version`

### API Installation

**Option A: Automated (Recommended)**
- [ ] Upload `deploy-lightsail.sh` to server
- [ ] Make executable: `chmod +x deploy-lightsail.sh`
- [ ] Run script: `./deploy-lightsail.sh`
- [ ] Follow prompts for Azure credentials
- [ ] Verify service: `sudo systemctl status azure-speech-api`

**Option B: Manual**
- [ ] Create directory: `sudo mkdir -p /opt/azure-speech-api`
- [ ] Upload API files to `/opt/azure-speech-api/`
- [ ] Create venv: `python3 -m venv venv`
- [ ] Activate venv: `source venv/bin/activate`
- [ ] Install deps: `pip install -r requirements.txt`
- [ ] Create `.env` with Azure credentials
- [ ] Create directories: `mkdir -p uploads out`
- [ ] Test manually: `python app.py`
- [ ] Create systemd service (see guide)
- [ ] Set permissions: `sudo chown -R www-data:www-data /opt/azure-speech-api`
- [ ] Start service: `sudo systemctl start azure-speech-api`

### Verification
- [ ] Service running: `sudo systemctl status azure-speech-api`
- [ ] Health check: `curl http://localhost:3333/api/health`
- [ ] Returns: `{"status":"healthy"}`
- [ ] Check logs: `sudo journalctl -u azure-speech-api -n 20`
- [ ] No errors in logs

---

## WordPress Plugin Installation

### Plugin Upload

**Option A: WordPress Admin (Easiest)**
- [ ] Compress plugin: `zip -r azure-speech-transcribe.zip azure-speech-transcribe/`
- [ ] WordPress Admin → Plugins → Add New → Upload Plugin
- [ ] Upload zip file
- [ ] Click Install Now
- [ ] Click Activate

**Option B: SCP Upload**
- [ ] From local: `scp -r azure-speech-transcribe ubuntu@ip:/tmp/`
- [ ] On server: `sudo mv /tmp/azure-speech-transcribe /opt/bitnami/wordpress/wp-content/plugins/`
- [ ] Set permissions: `sudo chown -R bitnami:daemon /opt/bitnami/wordpress/wp-content/plugins/azure-speech-transcribe`
- [ ] Activate in WordPress Admin

### Configuration
- [ ] Go to Settings → Azure Speech Transcribe
- [ ] Set Access Password: `___________________`
- [ ] Set Flask API URL: `http://localhost:3333`
- [ ] Set Max File Size: `50` MB
- [ ] Click Save Settings

---

## Testing

### Create Test Page
- [ ] Pages → Add New
- [ ] Title: "Audio Transcription"
- [ ] Content: `[azure_transcribe]`
- [ ] Publish
- [ ] Note URL: `___________________`

### End-to-End Test
- [ ] Visit test page
- [ ] Enter password
- [ ] Upload small WAV/M4A file (< 5MB for first test)
- [ ] Verify upload progress shows
- [ ] Verify transcription streams in real-time
- [ ] Verify text appears segment by segment
- [ ] Test Copy button
- [ ] Test Download button
- [ ] Verify downloaded file contains full transcript

---

## Security

- [ ] Port 3333 NOT exposed to internet: `sudo ufw status`
- [ ] Only ports 22, 80, 443 should be open
- [ ] Strong password set in WordPress plugin
- [ ] .env file has correct permissions: `ls -la /opt/azure-speech-api/.env`
- [ ] Service runs as www-data (not root)

---

## Monitoring

- [ ] Service auto-starts on boot: `sudo systemctl is-enabled azure-speech-api`
- [ ] Log rotation configured: `ls /etc/logrotate.d/azure-speech-api`
- [ ] Know how to check logs:
  - Service logs: `sudo journalctl -u azure-speech-api -f`
  - App logs: `tail -f /opt/azure-speech-api/transcription.log`
  - Error logs: `tail -f /opt/azure-speech-api/error.log`

---

## Troubleshooting Commands

### Check Service
```bash
sudo systemctl status azure-speech-api    # Status
sudo systemctl restart azure-speech-api   # Restart
sudo journalctl -u azure-speech-api -n 50 # Recent logs
```

### Test API
```bash
curl http://localhost:3333/api/health     # Health check
ps aux | grep gunicorn                    # Check process
sudo lsof -i :3333                        # Check port
```

### Check Files
```bash
ls -la /opt/azure-speech-api/             # List files
cat /opt/azure-speech-api/.env            # View config
tail /opt/azure-speech-api/error.log      # Check errors
```

### Fix Permissions
```bash
sudo chown -R www-data:www-data /opt/azure-speech-api
sudo chmod 755 /opt/azure-speech-api/uploads
sudo chmod 755 /opt/azure-speech-api/out
```

---

## Post-Deployment

- [ ] Service is running and healthy
- [ ] WordPress plugin is active and configured
- [ ] Test page created and working
- [ ] End-to-end test successful
- [ ] Backup created of .env file
- [ ] Documentation saved for future reference
- [ ] Team members notified (if applicable)
- [ ] Monitoring set up (if applicable)

---

## Quick Reference

| Component | Location |
|-----------|----------|
| Flask API | `/opt/azure-speech-api/` |
| WordPress Plugin | `/opt/bitnami/wordpress/wp-content/plugins/azure-speech-transcribe/` |
| Service Config | `/etc/systemd/system/azure-speech-api.service` |
| Environment | `/opt/azure-speech-api/.env` |
| Logs | `/opt/azure-speech-api/*.log` |

| Command | Purpose |
|---------|---------|
| `sudo systemctl status azure-speech-api` | Check service status |
| `curl http://localhost:3333/api/health` | Test API health |
| `sudo journalctl -u azure-speech-api -f` | Follow service logs |
| `sudo systemctl restart azure-speech-api` | Restart service |

---

## Notes

Date Deployed: ___________________  
Lightsail IP: ___________________  
WordPress URL: ___________________  
Plugin Password: ___________________  

Issues Encountered:
- 
-
-

---

**Deployment Status:** ⬜ Not Started | ⬜ In Progress | ⬜ Complete

For detailed instructions, see: [DEPLOYMENT_LIGHTSAIL.md](DEPLOYMENT_LIGHTSAIL.md)
