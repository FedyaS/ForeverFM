import soundfile as sf
import os

def get_wav_duration(file_path):
    with sf.SoundFile(file_path) as file:
        duration = len(file) / file.samplerate  # len(file) gives number of frames
    return duration

