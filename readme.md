# Burmese speech recognition test using Azure speech SDK

This sample code tests the accuracy of speech recognition (speech-to-text) for Burmese language using speech SDK from Azure Cognitive Services.

`speech_to_text_api.ipynb` is a Jupyter notebook for testing short sentences recognition using either a microphone or recorded audio file (8kHz wav).

`conginuous_recog.py` is designed for continuous speech-to-text conversion of long audio files. It includes event handlers for parsing and saving the output from Azure speech API.

Two environment variables `SPEECH_KEY` and `SPEECH_REGION` must be set prior to running the scripts [[ref]](https://learn.microsoft.com/en-au/azure/cognitive-services/Speech-Service/get-started-speech-to-text):

*Windows*
```
setx SPEECH_KEY your-key
setx SPEECH_REGION your-region
```

*Linux and macOS*
```
export SPEECH_KEY=your-key
export SPEECH_REGION=your-region
```

Usage of the scripts is simple and should be self-explanatory.


## Learn more about Azure speech services

https://azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services/

https://learn.microsoft.com/en-au/azure/cognitive-services/speech-service/speech-sdk


Azure and related services are the properties of Microsoft.