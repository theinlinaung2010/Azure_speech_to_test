from pydub import AudioSegment


def convert_m4a_to_wav(m4a_file, wav_file):
    audio = AudioSegment.from_file(m4a_file, format="m4a")
    audio.export(wav_file, format="wav")


# Usage
convert_m4a_to_wav(
    "D:/Downloads/GMT20260218-123853_Recording.m4a",
    "./audio/ThetKaMoeNyo.wav",
)
