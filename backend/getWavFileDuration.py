import soundfile as sf
import os

def get_wav_duration(file_name, mocking=True):
    if mocking:
        file_path = os.path.join('./mock_data', 'audio', file_name)
    else:
        file_path = os.path.join('./audio', file_name)
    with sf.SoundFile(file_path) as file:
        duration = len(file) / file.samplerate  # len(file) gives number of frames
    return duration