# Azure Speech-to-Text Streaming Transcription

Complete WordPress plugin solution with Flask API backend for real-time audio transcription using Azure Cognitive Services Speech-to-Text with Server-Sent Events (SSE) streaming.

## Overview

This project provides:

- **Flask API**: Backend service for audio transcription with real-time streaming
- **WordPress Plugin**: Password-protected frontend with live transcription display
- Support for Burmese (my-MM) and other languages
- Real-time streaming of transcription segments as they're recognized
- Automatic M4A to WAV conversion

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────────┐
│  WordPress  │  HTTP   │  Flask API   │  Azure  │  Azure Speech   │
│   Plugin    │────────▶│   (SSE)      │────────▶│    Services     │
│  Frontend   │◀────────│   Backend    │◀────────│                 │
└─────────────┘         └──────────────┘         └─────────────────┘
```

## Features

- ✅ Real-time transcription streaming via Server-Sent Events
- ✅ Password-protected access
- ✅ Drag-and-drop file upload
- ✅ Support for WAV and M4A formats
- ✅ Auto-scrolling transcript display with timestamps
- ✅ Copy to clipboard and download functionality
- ✅ Automatic file cleanup (24-hour retention)
- ✅ Rate limiting on password attempts
- ✅ Comprehensive logging
- ✅ Responsive design

## Project Structure

```
Azure_speech_to_test/
├── api/                           # Flask API Backend
│   ├── app.py                     # Main Flask application
│   ├── transcription_service.py   # Azure Speech SDK wrapper
│   ├── utils.py                   # Logging and cleanup utilities
│   ├── requirements.txt           # Python dependencies
│   ├── gunicorn_config.py         # Production server config
│   ├── .env.example              # Environment variables template
│   └── README.md                 # API documentation
├── wordpress-plugin/              # WordPress Plugin
│   └── azure-speech-transcribe/
│       ├── azure-speech-transcribe.php  # Main plugin file
│       ├── includes/              # PHP classes
│       ├── assets/                # CSS and JavaScript
│       ├── templates/             # HTML templates
│       └── README.md             # Plugin documentation
├── src/                          # Original source files
│   ├── continuous_recog.py       # Original Azure Speech code
│   └── m4a_to_wav_converter.py  # Audio conversion utility
├── audio/                        # Sample audio files
├── start-api.bat                # Windows startup script
├── start-api.sh                 # Linux/Mac startup script
└── README.md                    # This file
```

## Quick Start

### 1. Set Up Flask API

```bash
# Navigate to API directory
cd api

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your Azure credentials

# Create required directories
mkdir uploads out

# Start the server
python app.py
```

Or use the startup scripts:

- Windows: Double-click `start-api.bat`
- Linux/Mac: `./start-api.sh`

### 2. Install WordPress Plugin

1. Copy the entire `wordpress-plugin/azure-speech-transcribe` folder to your WordPress installation:

   ```
   /wp-content/plugins/azure-speech-transcribe/
   ```

2. Activate the plugin in WordPress admin

3. Configure settings at **Settings > Azure Speech Transcribe**:
   - Set access password
   - Set Flask API URL (default: `http://localhost:5000`)
   - Set max file size

### 3. Use the Plugin

1. Add shortcode to any page or post:

   ```
   [azure_transcribe]
   ```

2. Users enter the password to access the form

3. Upload an audio file (WAV or M4A)

4. Watch the transcription stream in real-time!

## Requirements

### Flask API

- Python 3.8+
- Azure Cognitive Services Speech subscription
- ffmpeg (for M4A conversion)

### WordPress Plugin

- WordPress 5.0+
- PHP 7.4+
- jQuery (included with WordPress)

## Configuration

### Azure Speech Service

1. Create an Azure account at https://azure.microsoft.com
2. Create a Speech Service resource
3. Copy the Key and Region
4. Add to `api/.env`:
   ```
   SPEECH_KEY=your_key_here
   SPEECH_REGION=your_region_here
   ```

### Language Configuration

By default, the system is configured for Burmese (my-MM). To change the language, edit [api/transcription_service.py](api/transcription_service.py):

```python
speech_config.speech_recognition_language = "en-US"  # Change to your language
```

Supported languages: https://docs.microsoft.com/azure/cognitive-services/speech-service/language-support

## API Endpoints

- `POST /api/upload` - Upload audio file, returns job_id
- `GET /api/stream/{job_id}` - SSE stream of transcription events
- `GET /api/download/{job_id}` - Download completed transcript
- `GET /api/status/{job_id}` - Get job status
- `GET /api/health` - Health check

## Development

### Testing the API

```bash
# Upload a file
curl -F "file=@audio/test.wav" http://localhost:5000/api/upload

# Stream transcription (replace JOB_ID)
curl -N http://localhost:5000/api/stream/JOB_ID

# Download transcript
curl http://localhost:5000/api/download/JOB_ID -o transcript.txt
```

### WordPress Development

The plugin follows WordPress coding standards. Key files:

- [includes/class-admin-settings.php](wordpress-plugin/azure-speech-transcribe/includes/class-admin-settings.php) - Admin interface
- [includes/class-shortcode.php](wordpress-plugin/azure-speech-transcribe/includes/class-shortcode.php) - Shortcode handler
- [assets/js/transcribe.js](wordpress-plugin/azure-speech-transcribe/assets/js/transcribe.js) - Frontend JavaScript with SSE

## Production Deployment

### Flask API with Gunicorn

```bash
cd api
gunicorn -c gunicorn_config.py app:app
```

### Reverse Proxy (Nginx)

```nginx
location /api/ {
    proxy_pass http://127.0.0.1:5000/api/;
    proxy_http_version 1.1;
    proxy_set_header Connection "";
    proxy_buffering off;
    proxy_cache off;
    chunked_transfer_encoding off;
}
```

## Security Considerations

- Flask API binds to localhost by default (127.0.0.1)
- Use reverse proxy for production
- Password-protect the WordPress form
- Rate limiting enabled (5 attempts per 5 minutes)
- File type validation
- Automatic cleanup of old files

## Troubleshooting

### API won't start

- Check Python version (3.8+)
- Verify .env file exists with Azure credentials
- Check if port 5000 is available

### WordPress connection errors

- Verify Flask API is running
- Check API URL in plugin settings
- Test API endpoint directly: `curl http://localhost:5000/api/health`

### Transcription not working

- Verify Azure credentials are correct
- Check API logs: `api/transcription.log`
- Ensure audio format is supported (WAV, M4A)
- Verify internet connection for Azure API

### M4A conversion fails

- Install ffmpeg
- Check ffmpeg is in system PATH
- Test: `ffmpeg -version`

## Logging

- API logs: `api/transcription.log`
- Access logs: `api/access.log` (Gunicorn)
- Error logs: `api/error.log` (Gunicorn)
- WordPress logs: Check WordPress debug.log

## License

GPL v2 or later

## Credits

Built using:

- Azure Cognitive Services Speech SDK
- Flask
- WordPress
- jQuery
- pydub for audio conversion

## Support

For Azure Speech Service issues: https://docs.microsoft.com/azure/cognitive-services/speech-service/

For WordPress plugin issues: Check the plugin README.md

## Changelog

### Version 1.0.0 (2026-03-05)

- Initial release
- Real-time SSE streaming
- Password protection
- WAV and M4A support
- WordPress plugin with drag-and-drop
- Automatic file cleanup
- Comprehensive logging
