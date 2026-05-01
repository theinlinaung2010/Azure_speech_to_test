import os
import azure.cognitiveservices.speech as speechsdk
import datetime
from pathlib import Path
from pydub import AudioSegment
from dotenv import load_dotenv


class TranscriptionService:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()
        
        self.speech_key = os.environ.get("SPEECH_KEY")
        self.speech_region = os.environ.get("SPEECH_REGION")

        if not self.speech_key or not self.speech_region:
            raise ValueError(
                "SPEECH_KEY and SPEECH_REGION environment variables must be set"
            )

    def convert_m4a_to_wav(self, m4a_file, wav_file):
        """Convert M4A file to WAV format"""
        audio = AudioSegment.from_file(m4a_file, format="m4a")
        audio.export(wav_file, format="wav")

    def transcribe_file(self, audio_file, output_file, on_segment_callback=None, stop_event=None, on_started_callback=None):
        """
        Transcribe audio file with streaming callbacks

        Args:
            audio_file: Path to audio file (WAV or M4A)
            output_file: Path to save transcript
            on_segment_callback: Callback function(timestamp, text, offset_seconds) called for each segment
            on_started_callback: Callback function(duration_seconds) called before recognition starts
        """
        audio_path = Path(audio_file)

        # Convert M4A to WAV if needed
        if audio_path.suffix.lower() == ".m4a":
            wav_file = audio_path.with_suffix(".wav")
            self.convert_m4a_to_wav(str(audio_path), str(wav_file))
            audio_file = str(wav_file)

        # Get total duration for real progress tracking
        total_duration = len(AudioSegment.from_file(audio_file)) / 1000.0

        # Configure speech recognition
        speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key, region=self.speech_region
        )
        speech_config.speech_recognition_language = "my-MM"
        speech_config.output_format = speechsdk.OutputFormat.Detailed

        # Create audio configuration
        audio_input = speechsdk.AudioConfig(filename=audio_file)

        # Create recognizer
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, audio_config=audio_input
        )

        # Open output file
        f = open(output_file, "w", encoding="utf-8")

        # Event to signal completion
        done = False

        def recognized_cb(evt):
            """Callback for recognized speech segments"""
            nonlocal done

            result = evt.result
            text = result.text.replace(" ", "")

            if not text:
                return

            # Calculate timestamp
            offset = result.offset / 10000000
            duration = result.duration / 10000000
            start_time = datetime.timedelta(seconds=offset)
            end_time = start_time + datetime.timedelta(seconds=duration)
            timestamp = "{} --> {}".format(
                str(start_time).split(".")[0], str(end_time).split(".")[0]
            )

            # Write to file
            f.write(timestamp + "\n")
            f.write(text + "\n\n")
            f.flush()

            # Call callback if provided
            if on_segment_callback:
                on_segment_callback(timestamp, text, offset)

        def canceled_cb(evt):
            """Callback for cancellation"""
            nonlocal done
            if evt.reason == speechsdk.CancellationReason.Error:
                print(f"Cancellation error: {evt.error_details}")
            done = True

        def stopped_cb(evt):
            """Callback for session stopped"""
            nonlocal done
            done = True

        # Connect callbacks
        speech_recognizer.recognized.connect(recognized_cb)
        speech_recognizer.canceled.connect(canceled_cb)
        speech_recognizer.session_stopped.connect(stopped_cb)

        # Notify caller of total duration then start recognition
        if on_started_callback:
            on_started_callback(total_duration)
        speech_recognizer.start_continuous_recognition()

        # Wait for completion or stop signal
        import time
        stop_requested = False
        while not done:
            if stop_event and stop_event.is_set() and not stop_requested:
                stop_requested = True
                speech_recognizer.stop_continuous_recognition()
            time.sleep(0.5)

        if not stop_requested:
            speech_recognizer.stop_continuous_recognition()
        f.close()
