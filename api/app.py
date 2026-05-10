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
MAX_FILE_SIZE = 200 * 1024 * 1024  # 200MB

UPLOAD_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

# Job storage
jobs = {}
jobs_lock = threading.Lock()

# Event queues for SSE
event_queues = {}
queues_lock = threading.Lock()

# Stop events for in-progress jobs
stop_events = {}
stop_events_lock = threading.Lock()

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


def create_stop_event(job_id):
    with stop_events_lock:
        event = threading.Event()
        stop_events[job_id] = event
        return event


def get_stop_event(job_id):
    with stop_events_lock:
        return stop_events.get(job_id)


def cleanup_job_resources(job_id, delay=300):
    """Release in-memory resources for a finished job after a short delay."""
    def _cleanup():
        time.sleep(delay)
        with queues_lock:
            event_queues.pop(job_id, None)
        with stop_events_lock:
            stop_events.pop(job_id, None)
        with jobs_lock:
            jobs.pop(job_id, None)
        logger.info(f"Released in-memory resources for job: {job_id}")
    threading.Thread(target=_cleanup, daemon=True).start()


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

    # Get audio duration via ffprobe
    duration = transcription_service._get_duration(str(filepath))

    # Initialize job (transcription not started yet)
    with jobs_lock:
        jobs[job_id] = {
            "id": job_id,
            "filename": filename,
            "filepath": str(filepath),
            "status": "uploaded",
            "created_at": datetime.now().isoformat(),
            "output_file": None,
            "duration": duration,
        }

    # Create event queue for this job
    create_event_queue(job_id)

    return jsonify({"job_id": job_id, "filename": filename, "duration": duration}), 200


@app.route("/api/start/<job_id>", methods=["POST"])
def start_transcription_job(job_id):
    """Begin transcription for an uploaded job, optionally with a time range."""
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    if job["status"] != "uploaded":
        return jsonify({"error": "Job is not in uploaded state"}), 400

    data = request.get_json(silent=True) or {}
    start_seconds = data.get("start_seconds", 0.0)
    end_seconds = data.get("end_seconds", None)

    total_duration = job.get("duration", 0)

    # Validate range
    try:
        start_seconds = float(start_seconds)
        end_seconds = float(end_seconds) if end_seconds is not None else None
    except (TypeError, ValueError):
        return jsonify({"error": "Invalid time range values"}), 400

    if start_seconds < 0:
        return jsonify({"error": "Start time cannot be negative"}), 400
    if end_seconds is not None:
        if total_duration > 0 and end_seconds > total_duration:
            return jsonify({"error": f"End time ({end_seconds:.1f}s) exceeds audio duration ({total_duration:.1f}s)"}), 400
        if start_seconds >= end_seconds:
            return jsonify({"error": "Start time must be less than end time"}), 400

    update_job(job_id, {"status": "queued", "start_seconds": start_seconds, "end_seconds": end_seconds})

    thread = threading.Thread(target=process_transcription, args=(job_id,))
    thread.daemon = True
    thread.start()

    return jsonify({"message": "Transcription started"}), 200


def process_transcription(job_id):
    """Process transcription in background thread"""
    try:
        job = get_job(job_id)
        if not job:
            logger.error(f"Job not found: {job_id}")
            return

        filepath = Path(job["filepath"])
        start_seconds = job.get("start_seconds", 0.0)
        end_seconds = job.get("end_seconds", None)
        logger.info(f"Starting transcription for job: {job_id}")

        # Setup output file
        output_file = OUTPUT_FOLDER / f"{job_id}.txt"

        def on_started(duration_seconds):
            update_job(job_id, {"status": "processing", "duration": duration_seconds})
            emit_event(job_id, "started", {"duration": duration_seconds})

        def on_segment(timestamp, text, offset_seconds):
            emit_event(job_id, "segment", {"timestamp": timestamp, "text": text, "offset": offset_seconds})

        def on_progress(processed_seconds, total_seconds):
            emit_event(job_id, "progress", {"processed": processed_seconds, "total": total_seconds})

        # Run transcription
        stop_event = create_stop_event(job_id)
        transcription_service.transcribe_file(
            str(filepath), str(output_file), on_segment, stop_event=stop_event, on_started_callback=on_started, on_progress_callback=on_progress,
            start_seconds=start_seconds, end_seconds=end_seconds
        )

        if stop_event.is_set():

            has_content = output_file.exists() and output_file.stat().st_size > 0
            update_job(job_id, {
                "status": "stopped",
                "output_file": str(output_file) if has_content else None,
                "stopped_at": datetime.now().isoformat(),
            })
            emit_event(job_id, "stopped", {"has_content": has_content})
            logger.info(f"Transcription stopped for job: {job_id}")
        else:
            update_job(job_id, {
                "status": "completed",
                "output_file": str(output_file),
                "completed_at": datetime.now().isoformat(),
            })
            emit_event(job_id, "completed", {"output_file": str(output_file)})
            logger.info(f"Transcription completed for job: {job_id}")

    except Exception as e:
        logger.error(f"Transcription error for job {job_id}: {e}")
        update_job(job_id, {"status": "error", "error": str(e)})
        emit_event(job_id, "error", {"message": str(e)})

    finally:
        # Schedule release of in-memory resources 5 minutes after job finishes
        cleanup_job_resources(job_id, delay=300)


@app.route("/api/stop/<job_id>", methods=["POST"])
def stop_transcription(job_id):
    """Signal a running transcription job to stop"""
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    if job["status"] in ("completed", "stopped", "error"):
        return jsonify({"error": "Job is not currently running"}), 400
    event = get_stop_event(job_id)
    if event:
        event.set()
    return jsonify({"message": "Stop signal sent"}), 200


@app.route("/api/stream/<job_id>", methods=["GET"])
def stream_events(job_id):
    """SSE endpoint for streaming transcription events"""

    def generate():
        q = get_event_queue(job_id)
        if not q:
            # Queue gone — either job never existed or already cleaned up.
            # Check whether the job itself is still in memory and synthesize
            # a terminal event so reconnecting clients don't hang.
            job = get_job(job_id)
            if job and job["status"] in ("completed", "stopped", "error"):
                terminal = {"type": job["status"], "timestamp": datetime.now().isoformat()}
                if job["status"] == "stopped":
                    terminal["has_content"] = bool(job.get("output_file"))
                elif job["status"] == "error":
                    terminal["message"] = job.get("error", "Transcription error")
                yield f"data: {json.dumps(terminal)}\n\n"
            else:
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

                # Stop streaming if job is done
                if event["type"] in ["completed", "stopped", "error"]:
                    break

            except queue.Empty:
                # Send heartbeat to keep connection alive
                current_time = time.time()
                if current_time - last_heartbeat > 15:
                    yield f": heartbeat\n\n"
                    last_heartbeat = current_time

                # Check if job finished while queue is empty (e.g. terminal event
                # was consumed by a previous connection that then dropped).
                # Synthesize the terminal event so the client reaches a final state.
                job = get_job(job_id)
                if job and job["status"] in ["completed", "stopped", "error"]:
                    terminal = {"type": job["status"], "timestamp": datetime.now().isoformat()}
                    if job["status"] == "stopped":
                        terminal["has_content"] = bool(job.get("output_file"))
                    elif job["status"] == "error":
                        terminal["message"] = job.get("error", "Transcription error")
                    yield f"data: {json.dumps(terminal)}\n\n"
                    break

    response = Response(generate(), mimetype="text/event-stream")
    # Prevent reverse-proxy (Nginx / Render) from buffering SSE chunks
    response.headers["Cache-Control"] = "no-cache"
    response.headers["X-Accel-Buffering"] = "no"
    return response


@app.route("/api/download/<job_id>", methods=["GET"])
def download_transcript(job_id):
    """Download the completed transcript file"""
    job = get_job(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404

    if job["status"] not in ("completed", "stopped"):
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


ACCESS_PASSWORD = os.environ.get("AST_PASSWORD", "demo")


@app.route("/")
def index():
    return send_file(Path(__file__).parent / "index.html")


@app.route("/api/validate-password", methods=["POST"])
def validate_password():
    password = request.form.get("password", "")
    if password == ACCESS_PASSWORD:
        return jsonify({"success": True, "data": {"message": "Password validated"}})
    return jsonify({"success": False, "data": {"message": "Invalid password"}})


if __name__ == "__main__":
    app.run(host="localhost", port=3333, threaded=True, debug=False)
