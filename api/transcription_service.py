import os
import azure.cognitiveservices.speech as speechsdk
import datetime
from pathlib import Path
from pydub import AudioSegment


class TranscriptionService:
    def __init__(self):
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

    def transcribe_file(self, audio_file, output_file, on_segment_callback=None):
        """
        Transcribe audio file with streaming callbacks

        Args:
            audio_file: Path to audio file (WAV or M4A)
            output_file: Path to save transcript
            on_segment_callback: Callback function(timestamp, text) called for each segment
        """
        audio_path = Path(audio_file)

        # Convert M4A to WAV if needed
        if audio_path.suffix.lower() == ".m4a":
            wav_file = audio_path.with_suffix(".wav")
            self.convert_m4a_to_wav(str(audio_path), str(wav_file))
            audio_file = str(wav_file)

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
                on_segment_callback(timestamp, text)

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

        # Start continuous recognition
        speech_recognizer.start_continuous_recognition()

        # Wait for completion
        while not done:
            import time

            time.sleep(0.5)

        # Stop recognition
        speech_recognizer.stop_continuous_recognition()
        f.close()
