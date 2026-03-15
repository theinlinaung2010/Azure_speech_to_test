# Azure Speech-to-Text Flask API

Real-time audio transcription API using Azure Cognitive Services Speech SDK with Server-Sent Events (SSE) streaming.

## Features

- Real-time transcription streaming via SSE
- Support for WAV and M4A audio formats
- Automatic M4A to WAV conversion
- Job-based processing with unique IDs
- Automatic cleanup of old files (24-hour retention)
- Comprehensive logging
- CORS support for cross-origin requests

## Prerequisites

- Python 3.8+
- Azure Cognitive Services Speech subscription
- ffmpeg (for M4A conversion)

## Installation

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Install ffmpeg:
   - Windows: Download from https://ffmpeg.org and add to PATH
   - Linux: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`

3. Configure environment variables:

```bash
cp .env.example .env
```

Edit `.env` and add your Azure credentials:

```
SPEECH_KEY=your_azure_speech_key
SPEECH_REGION=your_azure_region
```

## Running the Server

### Development

```bash
python app.py
```

### Production with Gunicorn

```bash
gunicorn -c gunicorn_config.py app:app
```

## API Endpoints

### POST /api/upload

Upload an audio file for transcription.

**Request:**

- Content-Type: multipart/form-data
- Body: file (WAV or M4A)

**Response:**

```json
{
  "job_id": "uuid",
  "filename": "original_filename.wav"
}
```

### GET /api/stream/{job_id}

Stream transcription events via SSE.

**Events:**

- `connected`: Connection established
- `started`: Transcription started
- `segment`: New transcription segment
  ```json
  {
    "type": "segment",
    "timestamp": "0:00:03 --> 0:00:36",
    "text": "transcribed text"
  }
  ```
- `completed`: Transcription finished
- `error`: Error occurred

### GET /api/download/{job_id}

Download the completed transcript file.

### GET /api/status/{job_id}

Get job status and metadata.

### GET /api/health

Health check endpoint.

## Configuration

- `UPLOAD_FOLDER`: Location for uploaded files (default: ./uploads)
- `OUTPUT_FOLDER`: Location for transcripts (default: ./out)
- `MAX_FILE_SIZE`: Maximum upload size in bytes (default: 50MB)
- `ALLOWED_EXTENSIONS`: Allowed file types (default: wav, m4a)

## Logging

Logs are written to:

- `transcription.log`: Application logs
- `access.log`: HTTP access logs (Gunicorn)
- `error.log`: Error logs (Gunicorn)

## File Cleanup

The cleanup service automatically removes files older than 24 hours from both upload and output directories. This runs every hour in the background.

## Security Considerations

- The API binds to localhost by default (127.0.0.1:5000)
- Use a reverse proxy (nginx, Apache) for production
- Implement authentication/authorization as needed
- Consider rate limiting for production use

## Testing

```bash
# Upload a file
curl -F "file=@test.wav" http://localhost:5000/api/upload

# Stream transcription (requires the job_id from upload response)
curl -N http://localhost:5000/api/stream/UUID_HERE

# Download transcript
curl http://localhost:5000/api/download/UUID_HERE -o transcript.txt
```
