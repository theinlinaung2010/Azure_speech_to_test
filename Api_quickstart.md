# Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Step 1: Install Flask API

```bash
cd api

# Windows
install.bat

# Linux/Mac
chmod +x install.sh
./install.sh
```

### Step 2: Configure Azure Credentials

Edit `api/.env`:

```
SPEECH_KEY=paste_your_azure_key_here
SPEECH_REGION=your_region_here
```

### Step 3: Start the API Server

```bash
# Windows
..\start-api.bat

# Linux/Mac
../start-api.sh
```

You should see:

```
Starting Flask server on http://localhost:5000
```

### Step 4: Test the API

Open a new terminal and test:

```bash
# Health check
curl http://localhost:5000/api/health

# Should return: {"status":"healthy"}
```

### Step 5: Install WordPress Plugin

1. Copy the plugin folder:

```bash
wordpress-plugin/azure-speech-transcribe/
```

to your WordPress installation:

```
/wp-content/plugins/azure-speech-transcribe/
```

2. In WordPress Admin:
   - Go to **Plugins** → Activate "Azure Speech Transcribe"
   - Go to **Settings** → **Azure Speech Transcribe**
   - Set your password (e.g., `test123`)
   - Set API URL: `http://localhost:5000`
   - Save settings

### Step 6: Create a Page

1. Create a new page in WordPress
2. Add this shortcode:

```
[azure_transcribe]
```

3. Publish the page

### Step 7: Test Transcription

1. Visit your page
2. Enter the password you configured
3. Upload a WAV or M4A audio file
4. Watch the transcription stream in real-time! 🎉

## Troubleshooting

### API won't start

```bash
# Check Python version (need 3.8+)
python --version

# Check if port 5000 is in use
# Windows:
netstat -ano | findstr :5000
# Linux/Mac:
lsof -i :5000
```

### WordPress shows "Connection error"

1. Verify API is running: `curl http://localhost:5000/api/health`
2. Check API URL in WordPress settings
3. Try using `127.0.0.1` instead of `localhost`

### "Invalid password"

- Check Settings → Azure Speech Transcribe → Access Password
- Rate limit: Max 5 attempts per 5 minutes

### Audio upload fails

1. Check file format (WAV or M4A only)
2. Check file size (default max: 50MB)
3. Check browser console for errors (F12)

## Testing with Sample Files

If you have sample audio files in the `audio/` directory:

```bash
# Upload via command line
curl -F "file=@audio/your-file.wav" http://localhost:5000/api/upload

# Response will include a job_id
# Stream the transcription:
curl -N http://localhost:5000/api/stream/YOUR_JOB_ID
```

## Production Checklist

Before deploying to production:

- [ ] Set a strong password in WordPress settings
- [ ] Configure proper file size limits
- [ ] Set up HTTPS
- [ ] Use Gunicorn instead of Flask dev server
- [ ] Set up reverse proxy (Nginx/Apache)
- [ ] Configure firewall rules
- [ ] Set up monitoring and logs
- [ ] Test with production Azure account
- [ ] Enable WordPress caching
- [ ] Set up automated backups

## Next Steps

- Read [api/README.md](api/README.md) for API details
- Read [wordpress-plugin/azure-speech-transcribe/README.md](wordpress-plugin/azure-speech-transcribe/README.md) for plugin customization
- Check [PROJECT_README.md](PROJECT_README.md) for full documentation

## Support

- Azure Speech Service: https://docs.microsoft.com/azure/cognitive-services/speech-service/
- WordPress Codex: https://codex.wordpress.org/
- Flask Documentation: https://flask.palletsprojects.com/

---

**Need Help?** Check the logs:

- API logs: `api/transcription.log`
- WordPress logs: `wp-content/debug.log` (if WP_DEBUG is enabled)
