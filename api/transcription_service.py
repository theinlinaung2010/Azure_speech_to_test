import os
import time
import logging
import datetime
from pathlib import Path

import azure.cognitiveservices.speech as speechsdk
from pydub import AudioSegment
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


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

    def prepare_audio(self, audio_file):
        """Convert any input audio to 16kHz mono 16-bit WAV required by Azure Speech SDK."""
        audio_path = Path(audio_file)
        out_path = audio_path.parent / f"{audio_path.stem}_azure.wav"

        logger.info(f"Preparing audio: {audio_path.name}")
        audio = AudioSegment.from_file(str(audio_path))

        original_info = f"{audio.frame_rate}Hz, {audio.channels}ch, {audio.sample_width*8}bit"
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        logger.info(f"Converted {original_info} -> 16000Hz, 1ch, 16bit: {out_path.name}")

        audio.export(str(out_path), format="wav")
        return str(out_path)

    def transcribe_file(self, audio_file, output_file, on_segment_callback=None, stop_event=None, on_started_callback=None):
        audio_path = Path(audio_file)

        prepared_file = self.prepare_audio(str(audio_path))
        audio_file = prepared_file

        total_duration = len(AudioSegment.from_file(audio_file)) / 1000.0
        logger.info(f"Audio ready: {Path(audio_file).name}, duration={total_duration:.1f}s")

        speech_config = speechsdk.SpeechConfig(
            subscription=self.speech_key, region=self.speech_region
        )
        speech_config.speech_recognition_language = "my-MM"
        speech_config.output_format = speechsdk.OutputFormat.Detailed
        logger.info(f"Azure SDK configured: language=my-MM, region={self.speech_region}")

        audio_input = speechsdk.AudioConfig(filename=audio_file)
        speech_recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config, audio_config=audio_input
        )

        f = open(output_file, "w", encoding="utf-8")
        done = False
        cancellation_error = None
        segment_count = 0

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

        def canceled_cb(evt):
            nonlocal done, cancellation_error
            if evt.reason == speechsdk.CancellationReason.Error:
                cancellation_error = f"{evt.error_code}: {evt.error_details}"
                logger.error(f"Azure SDK cancellation error: {cancellation_error}")
            else:
                logger.info(f"Recognition canceled (reason={evt.reason})")
            done = True

        def stopped_cb(evt):
            nonlocal done
            logger.info(f"Recognition session stopped, segments recognized={segment_count}")
            done = True

        speech_recognizer.recognized.connect(recognized_cb)
        speech_recognizer.canceled.connect(canceled_cb)
        speech_recognizer.session_stopped.connect(stopped_cb)

        logger.info("Starting continuous recognition")
        if on_started_callback:
            on_started_callback(total_duration)
        speech_recognizer.start_continuous_recognition()

        stop_requested = False
        while not done:
            if stop_event and stop_event.is_set() and not stop_requested:
                logger.info("Stop requested — stopping recognition")
                stop_requested = True
                speech_recognizer.stop_continuous_recognition()
            time.sleep(0.5)

        if not stop_requested:
            speech_recognizer.stop_continuous_recognition()
        f.close()

        if cancellation_error:
            raise RuntimeError(f"Azure Speech SDK error: {cancellation_error}")
