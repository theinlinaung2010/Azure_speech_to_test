import os
import time
import azure.cognitiveservices.speech as speechsdk
import datetime
import atexit

directory = 'D:/Downloads/FFM audios/'

# store the files in the directory into a list
files = os.listdir(directory)

# append the directory name to each file name
fnames = [directory + file for file in files]

# only keep the .wav files
fnames = [file for file in fnames if file.endswith('.wav')]

# counter to keep track of the current file
fcounter = 0    

f = open('dummy.txt', 'w', encoding='utf-8') # file stream object
f.close()

# Setup speech config
# Set environment variables for subscription key and region prior to running this script
# Create an instance of a speech config with specified subscription key and service region.
speech_config = speechsdk.SpeechConfig(subscription=os.environ.get('SPEECH_KEY'), region=os.environ.get('SPEECH_REGION'))
speech_config.speech_recognition_language="my-MM"
speech_config.output_format = speechsdk.OutputFormat.Detailed

speech_recognizer = ()


# Define callbacks for events
def recognized_cb(evt):
    global f
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


def canceled_cb(evt):
    print('CANCELED: Reason={}'.format(evt.reason))
    if evt.reason == speechsdk.CancellationReason.Error:
        print('CANCELED: ErrorDetails={}'.format(evt.error_details))


def session_stopped_cb(evt):
    global f

    f.close()
    print('Completed session. Continuing in 10 minute...')
    time.sleep(600)
    os.system('cls')
    next_file()
    

def next_file():
    global f, fcounter, speech_config, speech_recognizer

    # get file name with path and extension    
    filename = fnames[fcounter]
    print("Working on ", filename)

    # open file for writingss
    f = open(filename.split('.')[0] + '.txt', 'w', encoding='utf-8')

    # Create an audio configuration that points to an audio file.
    audio_filename = filename
    audio_input = speechsdk.AudioConfig(filename=audio_filename)

    # Create a recognizer with the given settings
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

    # Connect callbacks to events
    speech_recognizer.recognized.connect(recognized_cb)
    speech_recognizer.canceled.connect(canceled_cb)
    speech_recognizer.session_stopped.connect(session_stopped_cb)

    # Start continuous recognition
    speech_recognizer.start_continuous_recognition()
    
    fcounter += 1

    # Wait for completion
    input("Press any key to stop...\n")
    exit_handler()


def exit_handler():
    global speech_recognizer

    print("Manual termination. Exiting...")    
    f.close()


if __name__ == '__main__':
    next_file()
