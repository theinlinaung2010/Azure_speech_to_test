import os
import azure.cognitiveservices.speech as speechsdk
import datetime

# Input audio and output file names
AUDIO_IN = "audio_test_5min-2.wav"
FILE_OUT = "result-2_nospace.txt"

# Set environment variables for subscription key and region prior to running this script
# Create an instance of a speech config with specified subscription key and service region.
speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
speech_config.speech_recognition_language="my-MM"
speech_config.output_format = speechsdk.OutputFormat.Detailed

# Create an audio configuration that points to an audio file.
audio_filename = AUDIO_IN
audio_input = speechsdk.AudioConfig(filename=audio_filename)

# Create a recognizer with the given settings
speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

# Open file for writing
f = open(FILE_OUT, 'w', encoding='utf-8')


# Define callbacks for events
def recognized_cb(evt):
    # Get detailed result
    result = evt.result

    # Get text with highest confidence
    text = result.text
    # Remove spaces
    text = text.replace(' ', '')

    # Get offset and duration in seconds
    offset = result.offset / 10000000
    duration = result.duration / 10000000
    # Format timestamp as hh:mm:ss.mmm
    start_time = datetime.timedelta(seconds=offset)
    end_time = start_time + datetime.timedelta(seconds=duration)
    timestamp = '{} --> {}'.format(str(start_time).split('.')[0], str(end_time).split('.')[0])

    # Print subtitle line
    print(timestamp)
    print(text)

    # Save to file
    f.write(timestamp + '\n')
    f.write(text + '\n\n')
    f.flush()


def recognized_cb_simple(evt):
    print('Recognized: {}'.format(evt.result.text))


def canceled_cb(evt):
    print('CANCELED: Reason={}'.format(evt.reason))
    if evt.reason == speechsdk.CancellationReason.Error:
        print('CANCELED: ErrorDetails={}'.format(evt.error_details))


def session_stopped_cb(evt):
    print('Session stopped.')


# Connect callbacks to events
speech_recognizer.recognized.connect(recognized_cb)
speech_recognizer.canceled.connect(canceled_cb)
speech_recognizer.session_stopped.connect(session_stopped_cb)


# Start continuous recognition
speech_recognizer.start_continuous_recognition()

# Wait for completion
input("Press any key to stop...\n")

# Stop recognition
speech_recognizer.stop_continuous_recognition()
f.close()