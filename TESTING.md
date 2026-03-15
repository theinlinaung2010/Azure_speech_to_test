# Testing Guide - Azure Speech API

Test your Flask API locally before deploying to production WordPress.

## Prerequisites

1. **Start the Flask API**

   ```bash
   cd api
   python app.py
   ```

   You should see:

   ```
   * Running on http://localhost:3333
   ```

2. **Verify Azure credentials** are set in `api/.env`:
   ```
   SPEECH_KEY=your_key_here
   SPEECH_REGION=your_region_here
   ```

## Test Methods

### Method 1: Web Browser Test (Easiest)

1. **Open test.html in your browser:**

   ```bash
   # Windows
   start api/test.html

   # Mac/Linux
   open api/test.html
   ```

2. **What to check:**
   - ✅ API Status shows "Online"
   - Upload a WAV or M4A file (drag & drop or click)
   - Watch transcription stream in real-time
   - Test Copy and Download buttons

3. **Expected behavior:**
   - File uploads successfully
   - Progress bar shows status
   - Transcription appears segment by segment
   - Text auto-scrolls
   - Download button appears when complete

### Method 2: Command Line Test

1. **Run the test script:**

   ```bash
   cd api
   python test_api.py path/to/your/audio.wav
   ```

2. **Example:**

   ```bash
   python test_api.py ../audio/sample.wav
   ```

3. **Expected output:**

   ```
   Testing health endpoint...
   ✅ Health check: healthy

   Uploading file: ../audio/sample.wav
   ✅ Upload successful!
      Job ID: abc123...

   🎤 Transcription started...

   0:00:03 --> 0:00:36
   [Transcribed text here]

   ✅ Transcription completed!
   📝 Saved to: test_output_abc123.txt
   ```

### Method 3: Manual API Testing with cURL

Test individual endpoints:

```bash
# 1. Health check
curl http://localhost:3333/api/health

# 2. Upload file
curl -F "file=@path/to/audio.wav" http://localhost:3333/api/upload

# Response will include job_id, use it below:

# 3. Check status
curl http://localhost:3333/api/status/YOUR_JOB_ID

# 4. Stream transcription (real-time)
curl -N http://localhost:3333/api/stream/YOUR_JOB_ID

# 5. Download completed transcript
curl http://localhost:3333/api/download/YOUR_JOB_ID -o transcript.txt
```

## What to Test

### ✅ Basic Functionality

- [ ] API health check returns "healthy"
- [ ] WAV file uploads successfully
- [ ] M4A file uploads successfully
- [ ] Invalid file types are rejected
- [ ] Large files (>50MB) are rejected

### ✅ Transcription

- [ ] Transcription starts automatically
- [ ] Segments stream in real-time (SSE)
- [ ] Timestamps appear in HH:MM:SS format
- [ ] Text appears without spaces (Burmese text)
- [ ] Transcription completes successfully

### ✅ Download

- [ ] Download button appears after completion
- [ ] Downloaded file contains full transcript
- [ ] File format is plain text (.txt)

### ✅ Error Handling

- [ ] Empty file upload shows error
- [ ] Invalid file type shows error
- [ ] Non-existent job ID returns 404
- [ ] Network errors are handled gracefully

## Common Issues

### "API Status: Offline"

**Problem:** Flask API not running  
**Solution:**

```bash
cd api
python app.py
```

### "Connection error"

**Problem:** Port mismatch or firewall  
**Solution:**

- Check app.py runs on port 3333
- Update test.html if using different port (line 136)
- Check firewall allows localhost connections

### "Transcription error"

**Problem:** Azure credentials issue  
**Solution:**

- Verify `.env` file exists in `api/` directory
- Check SPEECH_KEY and SPEECH_REGION are correct
- Test Azure credentials directly in Azure portal

### M4A conversion fails

**Problem:** ffmpeg not installed  
**Solution:**

```bash
# Windows: Download from https://ffmpeg.org
# Add to PATH

# Mac
brew install ffmpeg

# Linux
sudo apt-get install ffmpeg
```

### No transcription output

**Problem:** Wrong language or empty audio  
**Solution:**

- Check audio file has actual speech
- Verify language setting in `transcription_service.py` (line 31):
  ```python
  speech_config.speech_recognition_language = "my-MM"  # Burmese
  # Change to "en-US" for English, etc.
  ```

## Test Files

If you need sample audio files:

1. **Create test WAV:**

   ```bash
   # Record a short audio clip on your device
   # Save as .wav format
   ```

2. **Test with existing files:**
   ```bash
   # Check if you have any in audio/ directory
   ls audio/
   ```

## Logs

Check logs for detailed information:

```bash
# Application log
tail -f api/transcription.log

# Console output (if running in terminal)
# Watch the terminal where python app.py is running
```

## Next Steps After Testing

Once all tests pass:

1. **Deploy to AWS Lightsail:**
   - Install Python, Flask, ffmpeg on server
   - Configure as systemd service
   - Set up environment variables

2. **Install WordPress Plugin:**
   - Upload plugin to `/wp-content/plugins/`
   - Activate in WordPress admin
   - Configure API URL: `http://localhost:3333`

3. **Production Testing:**
   - Test with real users
   - Monitor logs
   - Check performance with concurrent uploads

## Performance Benchmarks

Expected times (approximate):

- Upload (10MB file): 2-5 seconds
- M4A → WAV conversion: 1-3 seconds
- Transcription (1 min audio): 30-60 seconds
- Download: < 1 second

## Support

If tests fail:

1. Check `api/transcription.log` for errors
2. Verify all files in [IMPLEMENTATION_SUMMARY.md](../IMPLEMENTATION_SUMMARY.md)
3. Run validation: `python validate.py`

Happy testing! 🎉
