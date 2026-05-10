import os
import time
import logging
import threading
import datetime
from pathlib import Path

import subprocess
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# 1 second of 16kHz 16-bit mono = 32000 bytes
_CHUNK_BYTES = 32000

# How far ahead of the latest recognition result (tail_time) we allow the push
# loop (head_time) to get. When head_time - tail_time exceeds this, pushing
# pauses until Azure catches up. Keep this small so that after Stop is pressed,
# Azure has at most this many seconds of pre-buffered audio left to finalise.
_MAX_AHEAD_SECONDS = 15


class TranscriptionService:
    def __init__(self):
        load_dotenv()

        self.speech_key = os.environ.get("SPEECH_KEY")
        self.speech_region = os.environ.get("SPEECH_REGION")

        if not self.speech_key or not self.speech_region:
            raise ValueError(
                "SPEECH_KEY and SPEECH_REGION environment variables must be set"
            )

        logger.info(f"TranscriptionService initialized (region={self.speech_region})")

    def _get_duration(self, audio_file):
        """Get audio duration in seconds via ffprobe (instant metadata read, no decode)."""
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(audio_file),
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            try:
                return float(result.stdout.strip())
            except ValueError:
                pass
        logger.warning("ffprobe could not determine duration")
        return 0.0

    def transcribe_file(self, audio_file, output_file, on_segment_callback=None, stop_event=None, on_started_callback=None, on_progress_callback=None):
        audio_path = Path(audio_file)

        # Duration via ffprobe — fast metadata read, no decoding required
        total_duration = self._get_duration(str(audio_path))
        logger.info(f"Audio: {audio_path.name}, duration={total_duration:.1f}s")

        speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key, region=self.speech_region
        )
        speech_config.speech_recognition_language = "my-MM"
        speech_config.output_format = speechsdk.OutputFormat.Detailed
        logger.info(f"Azure SDK configured: language=my-MM, region={self.speech_region}")

        # PushAudioInputStream bypasses ALSA device init in headless Docker containers.
        audio_format = speechsdk.audio.AudioStreamFormat(
            samples_per_second=16000, bits_per_sample=16, channels=1
        )
        push_stream = speechsdk.audio.PushAudioInputStream(audio_format)
        audio_config = speechsdk.audio.AudioConfig(stream=push_stream)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, audio_config=audio_config
        )

        f = open(output_file, "w", encoding="utf-8")
        session_done = threading.Event()
        cancellation_error = [None]
        segment_count = 0
        # tail_time: audio-position (seconds) of the end of the latest recognized segment.
        # head_time: audio-position (seconds) of the last byte pushed to Azure.
        # Backpressure: pause pushing when head_time - tail_time > _MAX_AHEAD_SECONDS.
        tail_time = [0.0]
        tail_lock = threading.Lock()

        def recognized_cb(evt):
            nonlocal segment_count
            result = evt.result
            text = result.text.replace(" ", "")
            if not text:
                return
            segment_count += 1
            offset = result.offset / 10000000
            duration = result.duration / 10000000
            start_time = datetime.timedelta(seconds=offset)
            end_time = start_time + datetime.timedelta(seconds=duration)
            timestamp = "{} --> {}".format(
                str(start_time).split(".")[0], str(end_time).split(".")[0]
            )
            f.write(timestamp + "\n")
            f.write(text + "\n\n")
            f.flush()
            logger.info(f"Segment {segment_count} [{timestamp}]: {text[:60]}{'...' if len(text) > 60 else ''}")
            if on_segment_callback:
                on_segment_callback(timestamp, text, offset)
            with tail_lock:
                tail_time[0] = max(tail_time[0], offset + duration)

        def canceled_cb(evt):
            if evt.reason == speechsdk.CancellationReason.Error:
                cancellation_error[0] = f"{evt.error_code}: {evt.error_details}"
                logger.error(f"Azure SDK cancellation error: {cancellation_error[0]}")
                session_done.set()
            else:
                logger.info(f"Recognition canceled (reason={evt.reason})")

        def stopped_cb(evt):
            logger.info(f"Recognition session stopped, segments recognized={segment_count}")
            session_done.set()

        speech_recognizer.recognized.connect(recognized_cb)
        speech_recognizer.canceled.connect(canceled_cb)
        speech_recognizer.session_stopped.connect(stopped_cb)

        # Fire the started callback and begin recognition before any decoding —
        # the user sees the progress bar immediately.
        logger.info("Starting continuous recognition")
        if on_started_callback:
            on_started_callback(total_duration)
        speech_recognizer.start_continuous_recognition()

        # Stream ffmpeg raw PCM output directly into the push stream.
        # Conversion and transcription happen concurrently — no temp WAV file needed.
        proc = subprocess.Popen(
            [
                "ffmpeg", "-i", str(audio_path),
                "-ar", "16000", "-ac", "1", "-f", "s16le",
                "pipe:1",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )

        head_time = 0.0
        last_progress_head = -2.0  # emit progress every 2 seconds of audio
        try:
            while True:
                if stop_event and stop_event.is_set():
                    logger.info("Stop requested — terminating ffmpeg")
                    proc.kill()
                    break

                # Backpressure: wait until Azure catches up before pushing more audio.
                # Times out after _MAX_AHEAD_SECONDS to handle silent sections where
                # no recognized events fire to advance tail_time.
                wait_start = None
                while True:
                    with tail_lock:
                        current_tail = tail_time[0]
                    if head_time - current_tail <= _MAX_AHEAD_SECONDS:
                        break
                    if wait_start is None:
                        wait_start = time.monotonic()
                        logger.debug(f"Backpressure: head={head_time:.1f}s tail={current_tail:.1f}s, waiting")
                    elif time.monotonic() - wait_start > _MAX_AHEAD_SECONDS:
                        # Silent section or slow first recognition — advance tail_time to
                        # head_time so the push loop can send another full window of audio
                        # instead of drip-feeding one chunk per timeout period.
                        with tail_lock:
                            tail_time[0] = head_time
                        logger.debug("Backpressure timeout (silence), resuming push")
                        break
                    if stop_event and stop_event.wait(timeout=0.2):
                        break

                if stop_event and stop_event.is_set():
                    logger.info("Stop requested — terminating ffmpeg")
                    proc.kill()
                    break

                frames = proc.stdout.read(_CHUNK_BYTES)
                if not frames:
                    break
                push_stream.write(frames)
                # len(frames) / _CHUNK_BYTES gives fractional seconds of 16kHz s16le mono
                head_time += len(frames) / _CHUNK_BYTES

                if on_progress_callback and head_time - last_progress_head >= 2.0:
                    on_progress_callback(head_time, total_duration)
                    last_progress_head = head_time

        finally:
            proc.stdout.close()
            proc.wait()
            # Original upload no longer needed once ffmpeg has finished reading it
            try:
                audio_path.unlink()
                logger.info(f"Deleted upload: {audio_path.name}")
            except Exception as e:
                logger.warning(f"Could not delete upload {audio_path}: {e}")

        push_stream.close()
        logger.info("Audio stream closed, waiting for recognition to finish")
        session_done.wait()
        f.close()

        if cancellation_error[0]:
            raise RuntimeError(f"Azure Speech SDK error: {cancellation_error[0]}")
