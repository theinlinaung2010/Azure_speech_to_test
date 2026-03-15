import os
import uuid
import json
import time
import queue
import threading
import logging
from datetime import datetime
from pathlib import Path
from flask import Flask, request, Response, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename
from transcription_service import TranscriptionService
from utils import JobCleanupService, logger

app = Flask(__name__)
CORS(app)

# Configure Flask logging
app.logger.setLevel(logging.INFO)

# Configuration
UPLOAD_FOLDER = Path("./uploads").resolve()
OUTPUT_FOLDER = Path("./out").resolve()
ALLOWED_EXTENSIONS = {"wav", "m4a"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

# Job storage
jobs = {}
jobs_lock = threading.Lock()

# Event queues for SSE
event_queues = {}
queues_lock = threading.Lock()

transcription_service = TranscriptionService()

# Initialize cleanup service
cleanup_service = JobCleanupService(UPLOAD_FOLDER, OUTPUT_FOLDER, retention_hours=24)
cleanup_service.start()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_job(job_id):
    with jobs_lock:
        return jobs.get(job_id)


def update_job(job_id, updates):
    with jobs_lock:
        if job_id in jobs:
            jobs[job_id].update(updates)


def create_event_queue(job_id):
    with queues_lock:
        event_queues[job_id] = queue.Queue()
    return event_queues[job_id]


def get_event_queue(job_id):
    with queues_lock:
        return event_queues.get(job_id)


def emit_event(job_id, event_type, data=None):
    """Emit an event to the SSE stream for a job"""
    q = get_event_queue(job_id)
    if q:
        event = {"type": event_type, "timestamp": datetime.now().isoformat()}
        if data:
            event.update(data)
        q.put(event)


@app.route("/api/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        logger.warning("Upload attempt with no file")
        return jsonify({"error": "No file provided"}), 400

    file = request.files["file"]
    if file.filename == "":
        logger.warning("Upload attempt with empty filename")
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        logger.warning(f"Upload attempt with invalid file type: {file.filename}")
        return jsonify({"error": "Invalid file type. Only WAV and M4A allowed"}), 400

    # Create job
    job_id = str(uuid.uuid4())
    filename = secure_filename(file.filename)
    filepath = UPLOAD_FOLDER / f"{job_id}_{filename}"

    file.save(filepath)
    logger.info(f"File uploaded: {filename} (Job: {job_id})")

    # Initialize job
    with jobs_lock:
        jobs[job_id] = {
            "id": job_id,
            "filename": filename,
            "filepath": str(filepath),
            "status": "uploaded",
            "created_at": datetime.now().isoformat(),
            "output_file": None,
        }

    # Create event queue for this job
    create_event_queue(job_id)

    # Start transcription in background thread
    thread = threading.Thread(target=process_transcription, args=(job_id,))
    thread.daemon = True
    thread.start()

    return jsonify({"job_id": job_id, "filename": filename}), 200


def process_transcription(job_id):
    """Process transcription in background thread"""
    try:
        job = get_job(job_id)
        if not job:
            logger.error(f"Job not found: {job_id}")
            return

        filepath = Path(job["filepath"])
        logger.info(f"Starting transcription for job: {job_id}")

        # Emit started event
        emit_event(job_id, "started")
        update_job(job_id, {"status": "processing"})

        # Setup output file
        output_file = OUTPUT_FOLDER / f"{job_id}.txt"

        # Define callback for recognized segments
        def on_segment(timestamp, text):
            emit_event(job_id, "segment", {"timestamp": timestamp, "text": text})

        # Run transcription
        transcription_service.transcribe_file(
            str(filepath), str(output_file), on_segment
        )

        # Emit completed event
        update_job(
            job_id,
            {
                "status": "completed",
                "output_file": str(output_file),
                "completed_at": datetime.now().isoformat(),
            },
        )
        emit_event(job_id, "completed", {"output_file": str(output_file)})
        logger.info(f"Transcription completed for job: {job_id}")

    except Exception as e:
        logger.error(f"Transcription error for job {job_id}: {e}")
        update_job(job_id, {"status": "error", "error": str(e)})
        emit_event(job_id, "error", {"message": str(e)})


@app.route("/api/stream/<job_id>", methods=["GET"])
def stream_events(job_id):
    """SSE endpoint for streaming transcription events"""

    def generate():
        q = get_event_queue(job_id)
        if not q:
            yield f"data: {json.dumps({'type': 'error', 'message': 'Job not found'})}\n\n"
            return

        # Send initial connection confirmation
        yield f"data: {json.dumps({'type': 'connected', 'job_id': job_id})}\n\n"

        last_heartbeat = time.time()

        while True:
            try:
                # Non-blocking get with timeout
                event = q.get(timeout=1)
                yield f"data: {json.dumps(event)}\n\n"

                # Stop streaming if job is completed or errored
                if event["type"] in ["completed", "error"]:
                    break

            except queue.Empty:
                # Send heartbeat to keep connection alive
                current_time = time.time()
                if current_time - last_heartbeat > 15:
                    yield f": heartbeat\n\n"
                    last_heartbeat = current_time

                # Check if job is done
                job = get_job(job_id)
                if job and job["status"] in ["completed", "error"]:
                    break

    return Response(generate(), mimetype="text/event-stream")


@app.route("/api/download/<job_id>", methods=["GET"])
def download_transcript(job_id):
    """Download the completed transcript file"""
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if job["status"] != "completed":
        return jsonify({"error": "Transcription not completed yet"}), 400

    output_file = job.get("output_file")
    if not output_file:
        return jsonify({"error": "Output file not found"}), 404
    
    output_path = Path(output_file)
    if not output_path.exists():
        logger.error(f"Output file does not exist: {output_file}")
        return jsonify({"error": "Output file not found"}), 404

    return send_file(
        str(output_path), as_attachment=True, download_name=f"{job['filename']}.txt"
    )


@app.route("/api/status/<job_id>", methods=["GET"])
def get_status(job_id):
    """Get job status"""
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify(job), 200


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy"}), 200


if __name__ == "__main__":
    app.run(host="localhost", port=3333, threaded=True, debug=True)
